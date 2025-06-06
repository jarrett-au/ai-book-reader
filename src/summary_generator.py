"""
摘要生成器，负责生成中间摘要和整体摘要
"""
from pathlib import Path
from typing import List
from termcolor import colored
import time

from langchain_openai import AzureChatOpenAI
from config import DEFAULT_DEPTH
from prompt import get_prompt
from src.utils import save_markdown, format_elapsed_time


class SummaryGenerator:
    """摘要生成器，负责生成中间摘要和整体摘要"""
    
    def __init__(self, llm: AzureChatOpenAI, summary_dir: Path, meta_summary_dir: Path, file_name: str, depth: str = DEFAULT_DEPTH):
        """初始化摘要生成器
        
        Args:
            llm: LangChain的Azure OpenAI LLM实例
            summary_dir: 摘要目录
            meta_summary_dir: 元摘要目录
            file_name: 文件名
            depth: 分析深度，可选值为"conceptual"、"standard"、"detailed"
        """
        self.llm = llm
        self.summary_dir = summary_dir
        self.meta_summary_dir = meta_summary_dir
        self.file_name = file_name
        self.base_name = Path(file_name).stem
        self.depth = depth
        
        # 确保目录存在
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        self.meta_summary_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_interval_summary(self, knowledge_points: List[str], interval_num: int) -> str:
        """生成中间摘要
        
        Args:
            knowledge_points: 知识点列表
            interval_num: 间隔编号
            
        Returns:
            生成的摘要内容
        """
        if not knowledge_points:
            print(colored(f"\n⚠️ 跳过第 {interval_num} 个间隔摘要：没有知识点", "yellow"))
            return ""
            
        start_time = time.time()
        print(colored(f"\n🤔 生成第 {interval_num} 个间隔摘要 ({len(knowledge_points)} 个知识点, 深度: {self.depth})...", "cyan"))
        
        try:
            # 根据深度选择对应的prompt
            interval_summary_prompt = get_prompt("interval_summary", self.depth)
            
            # 调用LLM生成摘要
            completion = self.llm.invoke(
                [
                    {"role": "system", "content": interval_summary_prompt},
                    {"role": "user", "content": f"Analyze this content:\n" + "\n".join(knowledge_points)}
                ]
            )
            
            summary = completion.content
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            elapsed_str = format_elapsed_time(elapsed_time)
            print(colored(f"✅ 间隔摘要生成成功！(耗时: {elapsed_str})", "green"))
            
            # 保存摘要
            self._save_interval_summary(summary, interval_num)
            
            return summary
            
        except Exception as e:
            print(colored(f"❌ 生成间隔摘要时出错: {e}", "red"))
            return ""
    
    def _save_interval_summary(self, summary: str, interval_num: int) -> Path:
        """保存间隔摘要到文件
        
        Args:
            summary: 摘要内容
            interval_num: 间隔编号
            
        Returns:
            保存的文件路径
        """
        if not summary:
            print(colored("⏭️ 跳过摘要保存: 没有内容", "yellow"))
            return None
            
        # 创建保存路径
        summary_path = self.summary_dir / f"interval_summary_{interval_num:03d}_{self.depth}.md"
        
        # 创建元数据
        metadata = {
            "interval_num": interval_num,
            "file_name": self.file_name,
            "type": "interval_summary",
            "depth": self.depth
        }
        
        # 保存markdown
        save_markdown(
            content=summary,
            file_path=summary_path,
            title=f"间隔摘要 #{interval_num}: {self.base_name} (深度: {self.depth})",
            metadata=metadata
        )
        
        return summary_path
    
    def generate_meta_summary(self) -> str:
        """根据所有已生成的摘要创建元摘要
        
        Returns:
            生成的元摘要内容
        """
        # 读取所有已生成的摘要（仅包含间隔摘要）
        all_summaries = []
        
        # 读取间隔摘要，优先读取当前深度的摘要
        interval_summaries = sorted(self.summary_dir.glob(f"interval_summary_*_{self.depth}.md"))
        
        # 如果没有找到当前深度的摘要，尝试读取任何可用的摘要
        if not interval_summaries:
            interval_summaries = sorted(self.summary_dir.glob("interval_summary_*.md"))
        
        for summary_file in interval_summaries:
            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_summaries.append(content)
        
        if not all_summaries:
            print(colored("\n⚠️ 无法生成元摘要：未找到任何摘要文件", "yellow"))
            return ""
        
        start_time = time.time()
        print(colored(f"\n🔍 正在基于 {len(all_summaries)} 个摘要创建元摘要 (深度: {self.depth})...", "cyan"))
        
        try:
            # 根据深度选择对应的prompt
            meta_summary_prompt = get_prompt("meta_summary", self.depth)
            
            # 使用AI生成元摘要
            completion = self.llm.invoke(
                [
                    {"role": "system", "content": meta_summary_prompt},
                    {"role": "user", "content": f"基于以下摘要创建一个综合性的元摘要：\n\n" + "\n\n---\n\n".join(all_summaries)}
                ]
            )
            
            meta_summary = completion.content
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            elapsed_str = format_elapsed_time(elapsed_time)
            print(colored(f"✅ 元摘要生成成功！(耗时: {elapsed_str})", "green"))
            
            # 保存元摘要
            self._save_meta_summary(meta_summary)
            
            return meta_summary
            
        except Exception as e:
            print(colored(f"❌ 生成元摘要时出错: {e}", "red"))
            return ""
    
    def _save_meta_summary(self, meta_summary: str) -> Path:
        """保存元摘要到文件
        
        Args:
            meta_summary: 元摘要内容
            
        Returns:
            保存的文件路径
        """
        if not meta_summary:
            print(colored("⏭️ 跳过元摘要保存: 没有内容", "yellow"))
            return None
            
        # 创建保存路径
        meta_summary_path = self.meta_summary_dir / f"{self.base_name}_meta_summary_{self.depth}.md"
        
        # 创建元数据
        metadata = {
            "file_name": self.file_name,
            "type": "meta_summary",
            "depth": self.depth
        }
        
        # 保存markdown
        save_markdown(
            content=meta_summary,
            file_path=meta_summary_path,
            title=f"元摘要: {self.base_name} (深度: {self.depth})",
            metadata=metadata
        )
        
        return meta_summary_path 