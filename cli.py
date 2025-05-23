"""
命令行接口，提供用户交互和程序入口
"""
import argparse
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from termcolor import colored
from tqdm import tqdm
import concurrent.futures
from dotenv import load_dotenv

from src.llm import get_llm
load_dotenv(".env")

# 导入自定义模块
from config import (
    BASE_DIR, 
    CHUNK_SIZE, CHUNK_OVERLAP, 
    SUMMARY_INTERVAL, MAX_WORKERS, SUPPORTED_FORMATS,
    DEPTH_OPTIONS, DEFAULT_DEPTH
)
from src.document_processor import DocumentProcessor
from src.toc_extractor import TOCExtractor
from src.chunk_analyzer import ChunkAnalyzer
from src.summary_generator import SummaryGenerator
from src.output_integrator import OutputIntegrator
from src.utils import setup_directories, format_elapsed_time


def setup_llm():
    """初始化LLM"""
    return get_llm(provider="siliconflow", model="Pro/deepseek-ai/DeepSeek-V3")
    # return get_llm(provider="azure", model="gpt-4.1")


def print_welcome_message():
    """打印欢迎信息和使用说明"""
    welcome_text = f"""
📚 AI书籍阅读工具 📚
---------------------------
功能：
1. 提取文档目录
2. 分割文本为chunks（大小: {CHUNK_SIZE} tokens，重叠: {CHUNK_OVERLAP} tokens）
3. 分析每个chunk并提取关键信息
4. 每 {SUMMARY_INTERVAL} 个chunk生成一个中间摘要
5. 生成整体摘要
6. 整合目录、摘要和整体摘要成完整报告

支持的文件格式: {', '.join(SUPPORTED_FORMATS)}
支持的深度选项: {', '.join(DEPTH_OPTIONS)}

使用方式：
python cli.py --file your_file.md [--chunk-size 5000] [--overlap 500] [--interval 5] [--workers 3] [--depth standard]

按Enter继续或Ctrl+C退出...
"""
    print(colored(welcome_text, "cyan"))
    input()


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI书籍阅读工具')
    parser.add_argument('--file', '-f', required=True, help='要分析的文件路径')
    parser.add_argument('--chunk-size', type=int, default=CHUNK_SIZE, help=f'分割大小（字符数），默认为{CHUNK_SIZE}')
    parser.add_argument('--overlap', type=int, default=CHUNK_OVERLAP, help=f'chunk重叠大小（字符数），默认为{CHUNK_OVERLAP}')
    parser.add_argument('--interval', type=int, default=SUMMARY_INTERVAL, help=f'摘要生成间隔（chunk数量），默认为{SUMMARY_INTERVAL}')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f'并行处理线程数，默认为{MAX_WORKERS}')
    parser.add_argument('--depth', choices=DEPTH_OPTIONS, default=DEFAULT_DEPTH, help=f'分析深度 (conceptual/standard/detailed), 默认为{DEFAULT_DEPTH}')
    return parser.parse_args()


def process_chunks(chunks: List[str], chunk_analyzer: ChunkAnalyzer, max_workers: int) -> List[Dict[str, Any]]:
    """并行处理chunks
    
    Args:
        chunks: 分割后的chunks
        chunk_analyzer: chunk分析器
        max_workers: 最大并行数
        
    Returns:
        分析结果列表
    """
    results = []
    
    print(colored(f"\n🔎 正在分析 {len(chunks)} 个chunks (并行工作线程: {max_workers})...", "cyan"))
    
    start_time = time.time()
    
    # 使用ThreadPoolExecutor进行并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建futures
        futures = {executor.submit(chunk_analyzer.analyze_chunk, chunk, i): i for i, chunk in enumerate(chunks)}
        
        # 使用tqdm显示进度
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="处理chunks"):
            chunk_idx = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(colored(f"\n❌ 处理chunk {chunk_idx} 时出错: {e}", "red"))
                results.append({
                    "chunk_idx": chunk_idx,
                    "has_content": False,
                    "knowledge": [],
                    "error": str(e)
                })
    
    elapsed_time = time.time() - start_time
    elapsed_str = format_elapsed_time(elapsed_time)
    print(colored(f"\n✅ 完成所有chunks处理 (总耗时: {elapsed_str})", "green"))
    
    # 按索引排序结果
    return sorted(results, key=lambda x: x.get('chunk_idx', 0))


def generate_interval_summaries(chunks_results: List[Dict[str, Any]], summary_generator: SummaryGenerator, interval: int, max_workers: int) -> List[str]:
    """生成间隔摘要
    
    Args:
        chunks_results: chunk分析结果
        summary_generator: 摘要生成器
        interval: 生成摘要的间隔
        
    Returns:
        摘要列表
    """
    # 按区间组织知识点
    interval_knowledge_groups = []
    interval_knowledge = []
    
    for i, result in enumerate(chunks_results):
        if result.get('has_content', False):
            # 收集该片段的知识点
            knowledge = result.get('knowledge', [])
            interval_knowledge.extend(knowledge)
        
        # 检查是否到达间隔或最后一个chunk
        if (i + 1) % interval == 0 or i == len(chunks_results) - 1:
            if interval_knowledge:  # 只在有知识点时收集
                interval_knowledge_groups.append(interval_knowledge)
                interval_knowledge = []  # 重置知识点列表
    
    summaries = []
    
    print(colored(f"\n📝 并行生成 {len(interval_knowledge_groups)} 个间隔摘要 (并行工作线程: {max_workers})...", "cyan"))
    
    start_time = time.time()
    
    # 使用ThreadPoolExecutor进行并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建futures
        futures = {executor.submit(summary_generator.generate_interval_summary, knowledge_group, idx+1): idx 
                   for idx, knowledge_group in enumerate(interval_knowledge_groups)}
        
        # 使用tqdm显示进度
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="生成摘要"):
            idx = futures[future]
            try:
                summary = future.result()
                # 保存结果，需要保证顺序
                summaries.append((idx, summary))
            except Exception as e:
                print(colored(f"\n❌ 生成摘要 {idx+1} 时出错: {e}", "red"))
                summaries.append((idx, f"摘要生成错误: {str(e)}"))
    
    elapsed_time = time.time() - start_time
    elapsed_str = format_elapsed_time(elapsed_time)
    print(colored(f"\n✅ 完成所有摘要生成 (总耗时: {elapsed_str})", "green"))
    
    # 按索引排序并仅返回摘要内容
    return [summary for _, summary in sorted(summaries, key=lambda x: x[0])]


def main():
    """主函数"""
    try:
        # 打印欢迎信息
        print_welcome_message()
        
        # 解析命令行参数
        args = parse_arguments()
        file_path = Path(args.file)
        chunk_size = args.chunk_size
        chunk_overlap = args.overlap
        summary_interval = args.interval
        max_workers = args.workers
        depth = args.depth
        
        print(colored(f"\n📊 分析深度: {depth}", "cyan"))
        
        # 检查文件是否存在
        if not file_path.exists():
            print(colored(f"❌ 文件不存在: {file_path}", "red"))
            return
        
        # 初始化LLM
        print(colored("🤖 初始化LLM...", "cyan"))
        llm = setup_llm()
        
        # 设置目录结构
        dirs = setup_directories(BASE_DIR, file_path.name)
        
        # 1. 处理文档
        print(colored(f"\n📃 处理文档: {file_path.name}...", "cyan"))
        doc_processor = DocumentProcessor(file_path)
        processed_file = doc_processor.process(dirs["file"])
        print(colored(f"✅ 文档处理完成: {processed_file}", "green"))
        
        # 2. 加载文档文本
        print(colored("\n📜 加载文档文本...", "cyan"))
        document_text = doc_processor.load_text()
        print(colored(f"✅ 文档加载完成: {len(document_text)} 个字符", "green"))
        
        # 3. 提取目录
        print(colored("\n📝 提取文档目录...", "cyan"))
        toc_extractor = TOCExtractor(llm)
        toc_content = toc_extractor.extract_toc(document_text)
        toc_path = dirs["toc"] / f"{file_path.stem}_toc.md"
        toc_extractor.save_toc(toc_content, toc_path)
        
        # 4. 分割文本
        print(colored(f"\n✂️ 将文档分割成chunks (大小: {chunk_size}, 重叠: {chunk_overlap})...", "cyan"))
        chunks = doc_processor.split_text(document_text, chunk_size, chunk_overlap)
        print(colored(f"✅ 分割完成: 生成 {len(chunks)} 个chunks", "green"))
        
        # 5. 分析chunks
        chunk_analyzer = ChunkAnalyzer(llm, dirs["knowledge"], depth=depth)
        chunk_results = process_chunks(chunks, chunk_analyzer, max_workers)
        
        # 6. 生成摘要
        print(colored(f"\n📗 准备生成摘要...", "cyan"))
        summary_generator = SummaryGenerator(llm, dirs["summaries"], dirs["meta_summary"], file_path.name, depth=depth)
        
        # 6.1 并行生成间隔摘要
        interval_summaries = generate_interval_summaries(chunk_results, summary_generator, summary_interval, max_workers)
        print(colored(f"✅ 生成了 {len(interval_summaries)} 个间隔摘要", "green"))
        
        # 6.2 生成元摘要
        meta_summary = summary_generator.generate_meta_summary()
        meta_summary_path = dirs["meta_summary"] / f"{file_path.stem}_meta_summary.md"
        
        # 7. 整合输出

        # tmp
        toc_path = dirs["toc"] / f"{file_path.stem}_toc.md"
        meta_summary_path = dirs["meta_summary"] / f"{file_path.stem}_meta_summary.md"

        print(colored("\n🔗 整合所有输出...", "cyan"))
        output_integrator = OutputIntegrator(llm, dirs["integrated"], file_path.name, depth=depth)
        output_integrator.integrate_output(toc_path, dirs["summaries"], meta_summary_path)
        
        print(colored("\n✨ 处理完成！✨", "green", attrs=['bold']))
        integrated_path = dirs["integrated"] / f"{file_path.stem}_integrated_{depth}.md"
        print(colored(f"\n最终报告已生成至: {integrated_path}", "cyan"))
        
    except KeyboardInterrupt:
        print(colored("\n\n❌ 进程被用户取消", "red"))
    except Exception as e:
        print(colored(f"\n\n❌ 处理过程中出错: {e}", "red"))
        traceback.print_exc()


if __name__ == "__main__":
    main() 