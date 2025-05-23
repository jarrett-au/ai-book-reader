"""
输出整合器，负责整合所有输出内容
"""
from pathlib import Path
from typing import List
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
        
        # 4. 使用滑动窗口法整合内容并生成一个概要前言
        try:
            # 根据深度获取对应的prompt
            section_integration_prompt = get_prompt("section_integration", self.depth)
            
            # 使用滑动窗口方法整合内容，获取content和partial_toc，传入原始目录
            integrated_sections = self._sliding_window_integration(interval_summaries, section_integration_prompt)
            
            # 生成一个概要前言
            introduction_content = self._generate_introduction(meta_summary_content)
            
            # 直接通过代码整合内容，不再使用LLM进行最终整合
            final_content = self._assemble_final_content(
                toc_content=toc_content,
                introduction=introduction_content,
                integrated_sections=integrated_sections,
                meta_summary=meta_summary_content
            )
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            elapsed_str = format_elapsed_time(elapsed_time)
            print(colored(f"✅ 内容整合成功！(耗时: {elapsed_str})", "green"))
            
            # 保存整合内容
            output_path = self._save_integrated_content(final_content)
            print(colored(f"📄 整合内容已保存到: {output_path}", "green"))
            
            return final_content
            
        except Exception as e:
            print(colored(f"❌ 整合内容时出错: {e}", "red"))
            return ""
    
    def _sliding_window_integration(self, interval_summaries: List[str], prompt_template: str) -> List[str]:
        """使用滑动窗口法整合内容
        
        Args:
            interval_summaries: 区间摘要列表
            prompt_template: 提示模板
            
        Returns:
            整合后的部分列表，每个部分包含content和toc
        """
        if not interval_summaries:
            return []
        
        if len(interval_summaries) == 1:
            # 对于单个摘要，创建一个空的目录结构
            return [interval_summaries[0]]
            
        print(colored(f"🔄 使用滑动窗口法整合 {len(interval_summaries)} 个区间摘要...", "cyan"))
        integrated_sections = []
        
        # 创建带结构化输出的LLM实例
        # structured_llm = self.llm.with_structured_output(SectionIntegrationResult)
        
        # 对于所有相邻的摘要对进行整合
        for i in range(len(interval_summaries) - 1):
            print(colored(f"  - 整合区间 {i+1} 和 {i+2}...", "cyan"))
            try:
                # 构建用户提示，包含原始标题信息和目录参考
                user_prompt = prompt_template.format(
                    interval_1=interval_summaries[i],
                    interval_2=interval_summaries[i+1],
                    section_number=i+1,
                    next_section=i+2,
                )
                
                # 使用结构化输出调用LLM
                result = self.llm.invoke([
                    {"role": "user", "content": user_prompt}
                ])
                
                # 直接添加结构化结果
                integrated_sections.append(result.content)
                print(colored(f"  ✓ 成功整合区间 {i+1} 和 {i+2} (内容长度: {len(result.content)}字符)", "green"))
                
            except Exception as e:
                print(colored(f"❌ 整合区间 {i+1} 和 {i+2} 时出错: {e}", "red"))
                # 如果整合失败，直接使用原始摘要作为备用方案
                combined_content = f"## 区间 {i+1} 到 {i+2} 的内容\n\n{interval_summaries[i]}\n\n---\n\n{interval_summaries[i+1]}"
                integrated_sections.append(combined_content)
                print(colored(f"  ⚠️ 使用备用方案整合区间 {i+1} 和 {i+2}", "yellow"))
        
        return integrated_sections
        
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
            # metadata=metadata # 暂时不添加元数据
        )
        
        return output_path
    
    def _generate_introduction(self, meta_summary: str) -> str:
        """生成概要前言
        
        Args:
            meta_summary: 元摘要内容
            
        Returns:
            生成的概要前言
        """
        try:
            # 根据深度获取对应的prompt模板
            introduction_prompt = f"""你是一位专业的文档分析专家。请根据以下元摘要内容，生成一个简短的概要前言(不超过500字)，
用于放置在文档开始位置，简要介绍文档内容。前言应概述文档的主要主题和价值。
保留原始元摘要的核心内容，但使其更加简洁明了。

元摘要内容：
{meta_summary}

请生成一个简洁的概要前言.格式：
## 前言
<introduction>"""

            # 调用LLM生成概要前言
            completion = self.llm.invoke([
                {"role": "user", "content": introduction_prompt}
            ])
            
            introduction = completion.content
            print(colored("✅ 概要前言生成成功", "green"))
            return introduction.strip()
        except Exception as e:
            print(colored(f"❌ 生成概要前言时出错: {e}", "yellow"))
            return "## 前言\n\n本文档是对原始内容的分析整理，包含主要概念和知识点。"
    
    def _assemble_final_content(self, toc_content: str, introduction: str, integrated_sections: List[str], meta_summary: str) -> str:
        """组装最终内容
        
        Args:
            toc_content: 目录内容
            introduction: 概要前言
            integrated_sections: 整合后的各部分内容
            meta_summary: 元摘要内容
            
        Returns:
            最终整合的内容
        """
        # 准备组装各个部分
        document_parts = []
        
        # 1. 添加文档标题
        document_parts.append(f"# {self.base_name} - 阅读分析报告")
        
        # 2. 生成综合目录 - 结合原始目录和动态生成的目录
        # document_parts.append("# 目录")
        
        # 合并从各部分内容中提取的目录
        # merged_toc = self._merge_partial_tocs(integrated_sections)
        
        # 如果有原始目录，优先使用它，如果它看起来合理完整
        # if toc_content and len(toc_content.splitlines()) > 5:  # 简单检查原始目录是否足够完整
        #     document_parts.append(toc_content)
        # else:
        #     # 否则使用从内容中提取的合并目录
        #     if merged_toc:
        #         document_parts.append(merged_toc)
        #     else:
        #         document_parts.append("*目录提取失败，请参考文档内容*")
        document_parts.append(toc_content)
        
        document_parts.append("\n---\n")  # 分隔线
        
        # 3. 添加前言
        document_parts.append(introduction)
        document_parts.append("\n---\n")  # 分隔线
        
        # 4. 添加主要内容
        document_parts.append("## 内容详解")
        
        # 将整合后的各部分内容按顺序组合
        for i, section in enumerate(integrated_sections):
            # document_parts.append(f"\n## 第{i+1}部分")
            document_parts.append(section)
            document_parts.append("\n")  # 添加空行分隔
        
        # 5. 添加综合分析（使用元摘要）
        # document_parts.append("\n# 综合分析")
        # document_parts.append(meta_summary)
        
        # 6. 组合所有内容
        return "\n\n".join(document_parts)