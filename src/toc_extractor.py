"""
目录提取器，负责从文档中提取目录
"""
from pathlib import Path
from typing import Dict, Any, Optional, List
from termcolor import colored
import re
import traceback

from langchain_openai import AzureChatOpenAI
from config import PROMPTS


class TOCExtractor:
    """目录提取器，从文档中提取目录"""
    
    def __init__(self, llm: AzureChatOpenAI):
        """初始化目录提取器
        
        Args:
            llm: LangChain的Azure OpenAI LLM实例
        """
        self.llm = llm
        
        # 常见目录指示词
        self.toc_indicators = [
            "目录", "contents", "table of contents", "章节", "chapters",
            "index", "索引", "大纲", "outline"
        ]
    
    def find_toc_position(self, text: str) -> int:
        """查找目录标记词的位置
        
        Args:
            text: 文档文本
            
        Returns:
            目录位置索引，如果未找到则返回-1
        """
        min_pos = float('inf')
        
        # 查找所有目录指示词的位置，取最靠前的
        for indicator in self.toc_indicators:
            # 尝试精确匹配
            pos = text.find(indicator)
            if pos >= 0 and pos < min_pos:
                min_pos = pos
            
            # 尝试大小写不敏感匹配
            lower_text = text.lower()
            lower_indicator = indicator.lower()
            pos = lower_text.find(lower_indicator)
            if pos >= 0 and pos < min_pos:
                min_pos = pos
        
        return min_pos if min_pos != float('inf') else -1
    
    def extract_toc(self, text: str, window_size: int = 10000) -> str:
        """提取文档中的目录
        
        Args:
            text: 文档文本内容
            window_size: 目录提取窗口大小
            
        Returns:
            提取的目录文本
        """
        print(colored("🔍 开始提取文档目录...", "cyan"))
        
        # 1. 查找目录位置
        toc_pos = self.find_toc_position(text)
        if toc_pos < 0:
            print(colored("⚠️ 未找到目录标记，将从文档开头提取", "yellow"))
            toc_pos = 0
        else:
            print(colored(f"✅ 在位置 {toc_pos} 处找到目录标记", "green"))
            
            # 稍微向前移动，确保捕获完整的目录标题行
            toc_pos = max(0, toc_pos - 50)
        
        # 2. 提取目录窗口文本
        end_pos = min(len(text), toc_pos + window_size)
        toc_window = text[toc_pos:end_pos]
        
        # 3. 使用LLM提取目录
        try:
            toc_content = self._extract_toc_with_llm(toc_window)
            print(colored("✅ 目录提取成功", "green"))
            return toc_content
        except Exception as e:
            print(colored(f"❌ 使用LLM提取目录时出错: {e}", "red"))
            traceback.print_exc()
            return "目录提取失败，请检查LLM配置或重试。"
    
    def _extract_toc_with_llm(self, text: str) -> str:
        """使用LLM提取目录
        
        Args:
            text: 包含目录的文本窗口
            
        Returns:
            提取的目录文本
        """
        if not self.llm:
            raise ValueError("错误：未配置LLM")
        
        # 使用配置的提示词
        prompt = PROMPTS["toc_extraction"].format(text=text)
        
        try:
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(colored(f"❌ LLM调用出错: {e}", "red"))
            raise
    
    def save_toc(self, toc_content: str, output_path: Path) -> None:
        """保存提取的目录到文件
        
        Args:
            toc_content: 目录内容
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(toc_content)
            
            print(colored(f"💾 目录已保存到: {output_path}", "green"))
            
            # 打印预览
            preview_lines = min(10, toc_content.count('\n') + 1)
            preview = '\n'.join(toc_content.split('\n')[:preview_lines])
            print(colored("\n目录预览:", "cyan"))
            print(colored("-" * 40, "cyan"))
            print(preview)
            if preview_lines < toc_content.count('\n') + 1:
                print("...")
            print(colored("-" * 40, "cyan"))
        except Exception as e:
            print(colored(f"❌ 保存目录时出错: {e}", "red"))
            raise 