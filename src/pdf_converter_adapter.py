"""
PDF转换器适配器，提供统一接口支持本地和服务器两种转换方式
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from termcolor import colored

from .pdf_converter import PDFToMarkdownConverter
from .local_pdf_converter import LocalPDFToMarkdownConverter, academic_paper_headers, book_chapter_headers


class UnifiedPDFConverter:
    """统一PDF转换器，支持本地和服务器两种转换方式"""
    
    def __init__(self, 
                 use_local: bool = True,
                 local_options: Optional[Dict[str, Any]] = None,
                 server_options: Optional[Dict[str, Any]] = None):
        """初始化统一转换器
        
        Args:
            use_local: 是否使用本地转换器
            local_options: 本地转换器选项
            server_options: 服务器转换器选项
        """
        self.use_local = use_local
        self.local_options = local_options or {}
        self.server_options = server_options or {}
        
        # 初始化转换器
        if use_local:
            self.converter = LocalPDFToMarkdownConverter(**self.local_options)
            print(colored("🔧 使用本地PDF转换器 (PyMuPDF)", "green"))
        else:
            self.converter = PDFToMarkdownConverter(**self.server_options)
            print(colored("🔧 使用服务器PDF转换器 (API)", "green"))
    
    def convert(self, 
                pdf_path: Path, 
                target_dir: Path, 
                **kwargs) -> Path:
        """转换PDF为Markdown
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            **kwargs: 转换参数
        
        Returns:
            转换后的Markdown文件路径
        """
        if self.use_local:
            return self._convert_local(pdf_path, target_dir, **kwargs)
        else:
            return self._convert_server(pdf_path, target_dir, **kwargs)
    
    def _convert_local(self, 
                      pdf_path: Path, 
                      target_dir: Path, 
                      **kwargs) -> Path:
        """使用本地转换器"""
        # 映射通用参数到本地转换器参数
        local_kwargs = self._map_to_local_params(kwargs)
        
        # 检查是否需要自定义标题识别
        header_style = kwargs.get('header_style')
        if header_style:
            if header_style == 'academic':
                return self.converter.convert_with_custom_headers(
                    pdf_path, target_dir, academic_paper_headers, **local_kwargs
                )
            elif header_style == 'book':
                return self.converter.convert_with_custom_headers(
                    pdf_path, target_dir, book_chapter_headers, **local_kwargs
                )
        
        return self.converter.convert(pdf_path, target_dir, **local_kwargs)
    
    def _convert_server(self, 
                       pdf_path: Path, 
                       target_dir: Path, 
                       **kwargs) -> Path:
        """使用服务器转换器"""
        # 映射通用参数到服务器转换器参数
        server_kwargs = self._map_to_server_params(kwargs)
        return self.converter.convert(pdf_path, target_dir, **server_kwargs)
    
    def _map_to_local_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """映射通用参数到本地转换器参数"""
        # 直接映射表
        param_mapping = {
            # 通用名称 -> PyMuPDF4LLM 参数名称
            'enable_table': 'table_strategy',
            'enable_image_caption': 'write_images', 
            'enable_formula': 'force_text',
            'language': None,  # PyMuPDF4LLM 不直接支持语言参数
            'is_ocr': None,    # 在转换器初始化时处理
        }
        
        local_params = {}
        
        for key, value in params.items():
            if key in param_mapping:
                mapped_key = param_mapping[key]
                if mapped_key is None:
                    continue  # 跳过不支持的参数
                
                if key == 'enable_table':
                    # 映射表格处理策略
                    if value:
                        local_params['table_strategy'] = 'lines_strict'
                    else:
                        local_params['table_strategy'] = None
                elif key == 'enable_image_caption':
                    # 映射图片处理
                    local_params['write_images'] = value
                elif key == 'enable_formula':
                    # force_text 的逻辑与 enable_formula 相反
                    local_params['force_text'] = not value
                else:
                    local_params[mapped_key] = value
            else:
                # 直接传递未映射的参数
                local_params[key] = value
        
        return local_params
    
    def _map_to_server_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """映射通用参数到服务器转换器参数"""
        # 服务器转换器参数的反向映射
        server_mapping = {
            'table_strategy': 'enable_table',
            'write_images': 'enable_image_caption',
            'force_text': 'enable_formula',
            'ignore_images': None,  # 服务器版本可能不支持
        }
        
        server_params = {}
        
        for key, value in params.items():
            if key in server_mapping:
                mapped_key = server_mapping[key]
                if mapped_key is None:
                    continue  # 跳过不支持的参数
                
                if key == 'table_strategy':
                    # 映射表格策略到布尔值
                    server_params['enable_table'] = value is not None and value != 'none'
                elif key == 'write_images':
                    server_params['enable_image_caption'] = value
                elif key == 'force_text':
                    # 反向映射
                    server_params['enable_formula'] = not value
                else:
                    server_params[mapped_key] = value
            else:
                # 直接传递未映射的参数
                server_params[key] = value
        
        return server_params
    
    def get_document_info(self, pdf_path: Path) -> Dict[str, Any]:
        """获取PDF文档信息
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            文档信息字典
        """
        if self.use_local and hasattr(self.converter, 'get_document_info'):
            return self.converter.get_document_info(pdf_path)
        else:
            # 服务器版本不支持此功能，返回基本信息
            return {
                'message': '服务器版本不支持文档信息获取',
                'converter_type': 'server'
            }
    
    def extract_text_only(self, 
                          pdf_path: Path, 
                          target_dir: Path,
                          method: str = "text",
                          **options) -> Path:
        """仅提取PDF文本
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            method: 提取方法
            **options: 提取选项
        
        Returns:
            提取文本的文件路径
        """
        if self.use_local and hasattr(self.converter, 'extract_text_only'):
            return self.converter.extract_text_only(pdf_path, target_dir, method, **options)
        else:
            raise NotImplementedError("服务器版本不支持纯文本提取功能")
    
    def switch_to_local(self, **options):
        """切换到本地转换器"""
        if not self.use_local:
            self.use_local = True
            self.local_options.update(options)
            self.converter = LocalPDFToMarkdownConverter(**self.local_options)
            print(colored("🔄 已切换到本地PDF转换器", "green"))
    
    def switch_to_server(self, **options):
        """切换到服务器转换器"""
        if self.use_local:
            self.use_local = False
            self.server_options.update(options)
            self.converter = PDFToMarkdownConverter(**self.server_options)
            print(colored("🔄 已切换到服务器PDF转换器", "green"))
    
    def get_converter_type(self) -> str:
        """获取当前转换器类型"""
        return "local" if self.use_local else "server"
    
    def get_converter_info(self) -> Dict[str, Any]:
        """获取转换器信息"""
        info = {
            'type': self.get_converter_type(),
            'options': self.local_options if self.use_local else self.server_options,
        }
        
        if self.use_local:
            info.update({
                'engine': 'PyMuPDF',
                'supports_ocr': True,
                'supports_custom_headers': True,
                'supports_text_only': True,
                'supports_document_info': True,
            })
        else:
            info.update({
                'engine': 'Server API',
                'supports_ocr': True,
                'supports_custom_headers': False,
                'supports_text_only': False,
                'supports_document_info': False,
            })
        
        return info


def create_unified_converter(use_local: bool = True, **kwargs) -> UnifiedPDFConverter:
    """创建统一PDF转换器实例
    
    Args:
        use_local: 是否使用本地转换器
        **kwargs: 转换器参数
    
    Returns:
        统一PDF转换器实例
    """
    return UnifiedPDFConverter(use_local=use_local, **kwargs)


# 便捷函数
def create_local_converter(**kwargs) -> UnifiedPDFConverter:
    """创建本地转换器"""
    return UnifiedPDFConverter(use_local=True, local_options=kwargs)


def create_server_converter(**kwargs) -> UnifiedPDFConverter:
    """创建服务器转换器"""
    if not os.getenv("PDF_API_BASE_URL"):
        raise ValueError("PDF_API_BASE_URL 环境变量未设置")
    return UnifiedPDFConverter(use_local=False, server_options=kwargs)


def auto_select_converter(**kwargs) -> UnifiedPDFConverter:
    """自动选择最佳转换器"""
    try:
        # 尝试导入PyMuPDF
        import pymupdf
        import pymupdf4llm
        print(colored("✅ 检测到PyMuPDF，使用本地转换器", "green"))
        return create_local_converter(**kwargs)
    except ImportError:
        print(colored("⚠️ 未安装PyMuPDF，使用服务器转换器", "yellow"))
        return create_server_converter(**kwargs) 