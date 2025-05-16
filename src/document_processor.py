"""
文档处理器，负责加载文档、转换格式和分割文本
"""
import os
from pathlib import Path
from typing import List, Optional, Callable
import fitz  # PyMuPDF
from termcolor import colored
import shutil

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP, SUPPORTED_FORMATS
from src.utils import copy_file_to_workspace


class DocumentProcessor:
    """文档处理类，负责加载文档、转换格式和分割文本"""
    
    def __init__(self, file_path: Path):
        """初始化文档处理器
        
        Args:
            file_path: 文档路径
        """
        self.file_path = Path(file_path)
        self.file_name = self.file_path.name
        self.file_ext = self.file_path.suffix.lower()
        
        # 检查文件格式
        if self.file_ext not in SUPPORTED_FORMATS:
            raise ValueError(f"不支持的文件格式: {self.file_ext}，支持的格式: {', '.join(SUPPORTED_FORMATS)}")
    
    def process(self, target_dir: Path, pdf_to_md_converter: Optional[Callable] = None) -> Path:
        """处理文档
        
        Args:
            target_dir: 目标目录
            pdf_to_md_converter: PDF转Markdown转换器函数
        
        Returns:
            处理后的文档路径
        """
        # 复制文件到工作目录
        workspace_file = copy_file_to_workspace(self.file_path, target_dir)
        
        # 如果是PDF并且提供了转换器，则转换为Markdown
        if self.file_ext == '.pdf' and pdf_to_md_converter:
            print(colored("🔄 将PDF转换为Markdown格式...", "cyan"))
            md_path = pdf_to_md_converter(workspace_file)
            print(colored(f"✅ PDF已转换为Markdown: {md_path}", "green"))
            return md_path
        
        return workspace_file
    
    def load_text(self) -> str:
        """加载文档文本内容
        
        Returns:
            文档文本内容
        """
        # 根据文件类型选择不同的加载方法
        if self.file_ext == '.pdf':
            return self._load_pdf_text()
        else:  # .txt or .md
            return self._load_text_file()
    
    def _load_pdf_text(self) -> str:
        """加载PDF文档文本
        
        Returns:
            PDF文档文本内容
        """
        try:
            pdf_document = fitz.open(self.file_path)
            text = ""
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text() + "\n\n"
            
            return text
        except Exception as e:
            raise ValueError(f"加载PDF文档时发生错误: {str(e)}")
    
    def _load_text_file(self) -> str:
        """加载文本文件
        
        Returns:
            文本文件内容
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            encodings = ['latin-1', 'gbk', 'gb2312', 'big5']
            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            raise ValueError(f"无法解码文件 {self.file_path}，请指定正确的编码")
    
    def split_text(self, text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
        """将文本分割成chunks
        
        Args:
            text: 要分割的文本
            chunk_size: 每个chunk的大小（字符数）
            chunk_overlap: chunk之间的重叠大小（字符数）
        
        Returns:
            分割后的文本列表
        """
        print(colored(f"📏 将文本分割成chunks (chunk_size={chunk_size}, overlap={chunk_overlap})...", "cyan"))
        
        # 使用RecursiveCharacterTextSplitter进行分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )
        
        chunks = text_splitter.split_text(text)
        
        print(colored(f"✅ 文本已分割为{len(chunks)}个chunks", "green"))
        return chunks 