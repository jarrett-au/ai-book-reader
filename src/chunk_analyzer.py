"""
Chunk分析器，负责分析单个chunk并提取关键信息
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from termcolor import colored
import json
import time
from pydantic import BaseModel

from langchain_openai import AzureChatOpenAI
from config import PROMPTS
from src.utils import save_json, format_elapsed_time


class PageContent(BaseModel):
    """知识点提取结果模型"""
    has_content: bool
    knowledge: list[str]


class ChunkAnalyzer:
    """Chunk分析器，负责分析单个chunk并提取关键信息"""
    
    def __init__(self, llm: AzureChatOpenAI, output_dir: Path):
        """初始化Chunk分析器
        
        Args:
            llm: LangChain的Azure OpenAI LLM实例
            output_dir: 输出目录路径
        """
        self.llm = llm
        self.output_dir = output_dir
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_chunk(self, chunk_text: str, chunk_idx: int) -> Dict[str, Any]:
        """分析单个chunk并提取关键信息
        
        Args:
            chunk_text: chunk文本内容
            chunk_idx: chunk索引
            
        Returns:
            分析结果
        """
        start_time = time.time()
        print(colored(f"\n📖 处理chunk {chunk_idx + 1}...", "yellow"))
        
        try:
            # 调用LLM分析chunk
            page_parser = self.llm.with_structured_output(PageContent)
            
            result = page_parser.invoke(
                [
                    {"role": "system", "content": PROMPTS["chunk_analysis"]},
                    {"role": "user", "content": f"Content text: {chunk_text}"}
                ],
            )
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            elapsed_str = format_elapsed_time(elapsed_time)
            
            if result.has_content:
                print(colored(f"✅ 找到 {len(result.knowledge)} 个知识点 (耗时: {elapsed_str})", "green"))
            else:
                print(colored(f"⏭️ 跳过内容 (无相关信息) (耗时: {elapsed_str})", "yellow"))
            
            # 组装返回结果
            analysis_result = {
                "chunk_idx": chunk_idx,
                "has_content": result.has_content,
                "knowledge": result.knowledge if result.has_content else [],
                "processing_time": elapsed_time
            }
            
            # 保存分析结果到文件
            self._save_analysis_result(analysis_result, chunk_idx)
            
            return analysis_result
            
        except Exception as e:
            print(colored(f"❌ 分析chunk时出错: {e}", "red"))
            
            # 返回空结果
            error_result = {
                "chunk_idx": chunk_idx,
                "has_content": False,
                "knowledge": [],
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            
            # 保存错误信息
            self._save_analysis_result(error_result, chunk_idx)
            
            return error_result
    
    def _save_analysis_result(self, result: Dict[str, Any], chunk_idx: int) -> None:
        """保存分析结果到文件
        
        Args:
            result: 分析结果
            chunk_idx: chunk索引
        """
        # 构建输出文件路径
        output_file = self.output_dir / f"chunk_{chunk_idx:04d}.json"
        
        # 保存JSON文件
        save_json(result, output_file)
    
    def load_all_results(self) -> List[Dict[str, Any]]:
        """加载所有分析结果
        
        Returns:
            所有chunk的分析结果列表
        """
        results = []
        result_files = sorted(self.output_dir.glob("chunk_*.json"))
        
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                print(colored(f"⚠️ 加载分析结果时出错 {file_path}: {e}", "yellow"))
        
        return sorted(results, key=lambda x: x.get('chunk_idx', 0))
    
    def get_all_knowledge(self) -> List[str]:
        """获取所有chunk的知识点列表
        
        Returns:
            所有知识点的列表
        """
        results = self.load_all_results()
        all_knowledge = []
        
        for result in results:
            if result.get('has_content', False):
                all_knowledge.extend(result.get('knowledge', []))
        
        return all_knowledge 