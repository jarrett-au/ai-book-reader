"""
PDF转换器工厂，提供简单的转换接口
"""
from pathlib import Path
from typing import Optional, Dict, Any

from src.pdf_converter import create_pdf_converter


def create_pdf_to_md_converter(**converter_kwargs) -> callable:
    """创建PDF转Markdown转换器函数
    
    Args:
        **converter_kwargs: 转换器初始化参数
    
    Returns:
        转换器函数
    """
    converter = create_pdf_converter(**converter_kwargs)
    
    def pdf_to_md_converter(pdf_path: Path, **process_kwargs) -> Path:
        """PDF转Markdown转换函数
        
        Args:
            pdf_path: PDF文件路径
            **process_kwargs: 处理参数
        
        Returns:
            转换后的Markdown文件路径
        """
        # 目标目录就是PDF文件所在目录
        target_dir = pdf_path.parent
        return converter.convert(pdf_path, target_dir, **process_kwargs)
    
    return pdf_to_md_converter 