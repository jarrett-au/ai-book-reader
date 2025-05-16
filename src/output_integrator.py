"""
输出整合器，负责整合所有输出内容
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from termcolor import colored
import time

from langchain_openai import AzureChatOpenAI
from config import DEFAULT_DEPTH
from prompt import get_prompt
from src.utils import save_markdown, format_elapsed_time


class OutputIntegrator:
    """输出整合器，负责整合目录、摘要和元摘要"""
    
    def __init__(self, llm: AzureChatOpenAI, output_dir: Path, file_name: str, depth: str = DEFAULT_DEPTH):
        """初始化输出整合器
        
        Args:
            llm: LangChain的Azure OpenAI LLM实例
            output_dir: 输出目录
            file_name: 文件名
            depth: 分析深度，可选值为"conceptual"、"standard"、"detailed"
        """
        self.llm = llm
        self.output_dir = output_dir
        self.file_name = file_name
        self.base_name = Path(file_name).stem
        self.depth = depth
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def integrate_output(self, toc_path: Path, summary_dir: Path, meta_summary_path: Path) -> str:
        """整合输出
        
        Args:
            toc_path: 目录文件路径
            summary_dir: 摘要目录
            meta_summary_path: 元摘要文件路径
            
        Returns:
            整合后的内容
        """
        start_time = time.time()
        print(colored(f"\n🔄 开始整合输出 (深度: {self.depth})...", "cyan"))
        
        # 1. 读取目录内容
        toc_content = self._read_file(toc_path)
        if not toc_content:
            print(colored("⚠️ 未找到目录内容", "yellow"))
            toc_content = "未能成功提取目录内容"
        
        # 2. 读取中间摘要，优先读取当前深度的摘要
        interval_summaries = []
        summary_files = sorted(summary_dir.glob(f"interval_summary_*_{self.depth}.md"))
        
        # 如果没有找到当前深度的摘要，尝试读取任何可用的摘要
        if not summary_files:
            summary_files = sorted(summary_dir.glob("interval_summary_*.md"))
            
        for summary_file in summary_files:
            content = self._read_file(summary_file)
            if content:
                interval_summaries.append(content)
        
        # 3. 读取元摘要，优先读取当前深度的元摘要
        meta_summary_path_with_depth = Path(str(meta_summary_path).replace("_meta_summary.md", f"_meta_summary_{self.depth}.md"))
        
        # 先尝试读取带深度的元摘要文件
        meta_summary_content = self._read_file(meta_summary_path_with_depth)
        
        # 如果没有找到带深度的元摘要，尝试读取原始元摘要
        if not meta_summary_content:
            meta_summary_content = self._read_file(meta_summary_path)
            
        if not meta_summary_content:
            print(colored("⚠️ 未找到元摘要内容", "yellow"))
            meta_summary_content = "未能成功生成元摘要内容"
        
        # 4. 使用LLM整合内容
        try:
            # 根据深度获取对应的prompt
            output_integration_prompt = get_prompt("output_integration", self.depth)
            
            # 调用LLM整合内容
            completion = self.llm.invoke(
                [
                    {"role": "system", "content": output_integration_prompt},
                    {"role": "user", "content": output_integration_prompt.format(
                        toc=toc_content,
                        interval_summaries="\n\n---\n\n".join(interval_summaries),
                        meta_summary=meta_summary_content
                    )}
                ]
            )
            
            integrated_content = completion.content
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            elapsed_str = format_elapsed_time(elapsed_time)
            print(colored(f"✅ 内容整合成功！(耗时: {elapsed_str})", "green"))
            
            # 保存整合内容
            output_path = self._save_integrated_content(integrated_content)
            print(colored(f"📄 整合内容已保存到: {output_path}", "green"))
            
            return integrated_content
            
        except Exception as e:
            print(colored(f"❌ 整合内容时出错: {e}", "red"))
            return ""
    
    def _read_file(self, file_path: Path) -> str:
        """读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        if not file_path.exists():
            print(colored(f"⚠️ 文件不存在: {file_path}", "yellow"))
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(colored(f"❌ 读取文件时出错: {file_path} - {e}", "red"))
            return ""
    
    def _save_integrated_content(self, content: str) -> Path:
        """保存整合内容
        
        Args:
            content: 整合后的内容
            
        Returns:
            保存的文件路径
        """
        # 创建保存路径
        output_path = self.output_dir / f"{self.base_name}_integrated_{self.depth}.md"
        
        # 创建元数据
        metadata = {
            "file_name": self.file_name,
            "type": "integrated_output",
            "depth": self.depth,
            "generated_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存markdown
        save_markdown(
            content=content,
            file_path=output_path,
            title=f"{self.base_name} - 阅读分析报告 (深度: {self.depth})",
            metadata=metadata
        )
        
        return output_path 