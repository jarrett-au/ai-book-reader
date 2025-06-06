"""
本地PDF转Markdown转换器，基于PyMuPDF，无需依赖服务器
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union
from termcolor import colored
import pymupdf
import pymupdf4llm


class LocalPDFToMarkdownConverter:
    """本地PDF转Markdown转换器类，基于PyMuPDF"""
    
    def __init__(self, 
                 extract_images: bool = True,
                 preserve_layout: bool = True,
                 use_ocr: bool = False,
                 dpi: int = 150,
                 **kwargs):
        """初始化本地转换器
        
        Args:
            extract_images: 是否提取图片
            preserve_layout: 是否保持布局
            use_ocr: 是否使用OCR
            dpi: 图片DPI设置
            **kwargs: 其他参数
        """
        self.extract_images = extract_images
        self.preserve_layout = preserve_layout
        self.use_ocr = use_ocr
        self.dpi = dpi
        self.kwargs = kwargs
        
    def convert(self, 
                pdf_path: Path, 
                target_dir: Path, 
                **options) -> Path:
        """转换PDF为Markdown
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            **options: 转换选项
        
        Returns:
            转换后的Markdown文件路径
        """
        print(colored(f"🔄 开始本地转换PDF: {pdf_path.name}", "cyan"))
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        try:
            # 确保目标目录存在
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成输出文件路径
            md_path = target_dir / f"{pdf_path.stem}.md"
            
            # 合并选项
            convert_options = {**self.kwargs, **options}
            
            # 使用pymupdf4llm进行转换
            start_time = time.time()
            md_text = self._convert_with_pymupdf4llm(pdf_path, convert_options)
            conversion_time = time.time() - start_time
            
            # 保存Markdown文件
            self._save_markdown(md_text, md_path)
            
            print(colored(f"✅ 转换完成，耗时: {conversion_time:.2f}秒", "green"))
            print(colored(f"📄 Markdown文件已保存: {md_path}", "green"))
            
            return md_path
            
        except Exception as e:
            print(colored(f"❌ PDF转换失败: {str(e)}", "red"))
            raise
    
    def _convert_with_pymupdf4llm(self, 
                                  pdf_path: Path, 
                                  options: Dict[str, Any]) -> str:
        """使用pymupdf4llm进行转换
        
        Args:
            pdf_path: PDF文件路径
            options: 转换选项
        
        Returns:
            Markdown文本
        """
        # 准备转换参数 - 只使用pymupdf4llm实际支持的参数
        convert_params = {}
        
        # 处理页面范围
        page_numbers = options.get('page_numbers')
        if page_numbers:
            convert_params['pages'] = page_numbers
        
        # 处理表格检测策略
        table_strategy = options.get('table_strategy', 'lines_strict')
        convert_params['table_strategy'] = table_strategy
        
        # 处理标题识别
        max_header_levels = options.get('max_header_levels')
        if max_header_levels and max_header_levels < 6:
            # 打开文档以使用自定义header识别
            doc = pymupdf.open(str(pdf_path))
            headers = pymupdf4llm.IdentifyHeaders(doc, max_levels=max_header_levels)
            convert_params['hdr_info'] = headers
            doc.close()
        
        # 处理图片选项 - 保存到指定目录而不是base64嵌入
        if self.extract_images:
            # 默认保存图片到文件，不使用base64嵌入
            convert_params['write_images'] = options.get('write_images', True)
            convert_params['embed_images'] = options.get('embed_images', False)  # 默认不嵌入
            
            # 设置图片保存路径为 ./book_analysis/files/<文件名>/images
            pdf_filename = pdf_path.stem
            images_dir = Path("./book_analysis/files") / pdf_filename / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # 设置图片路径
            convert_params['image_path'] = str(images_dir)
            
            # 其他图片相关设置
            if 'image_format' in options:
                convert_params['image_format'] = options['image_format']
            else:
                convert_params['image_format'] = 'png'  # 默认使用PNG格式
                
            if 'image_size_limit' in options:
                convert_params['image_size_limit'] = options['image_size_limit']
            
            print(colored(f"📁 图片将保存到: {images_dir}", "cyan"))
        else:
            convert_params['ignore_images'] = True
        
        # DPI设置
        convert_params['dpi'] = options.get('dpi', self.dpi)
        
        # 其他直接支持的参数
        supported_params = [
            'ignore_graphics', 'force_text', 'margins', 'page_chunks',
            'page_width', 'page_height', 'graphics_limit', 'ignore_code',
            'extract_words', 'show_progress', 'use_glyphs', 'filename'
        ]
        
        for param in supported_params:
            if param in options:
                convert_params[param] = options[param]
        
        print(colored(f"🔧 转换参数: {convert_params}", "cyan"))
        
        # 执行转换
        if 'hdr_info' in convert_params and hasattr(convert_params['hdr_info'], 'get_header_id'):
            # 使用已创建的header识别对象
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **convert_params)
        else:
            # 直接从文件路径转换
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **convert_params)
        
        return md_text
    
    def _save_markdown(self, md_text: str, md_path: Path) -> None:
        """保存Markdown文件
        
        Args:
            md_text: Markdown文本
            md_path: 保存路径
        """
        # 使用UTF-8编码保存
        md_path.write_bytes(md_text.encode('utf-8'))
    
    def convert_with_custom_headers(self, 
                                   pdf_path: Path, 
                                   target_dir: Path,
                                   header_func: Callable[[Dict, Any], str],
                                   **options) -> Path:
        """使用自定义标题识别函数转换PDF
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            header_func: 自定义标题识别函数
            **options: 其他选项
        
        Returns:
            转换后的Markdown文件路径
        """
        print(colored(f"🔄 使用自定义标题识别转换PDF: {pdf_path.name}", "cyan"))
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            md_path = target_dir / f"{pdf_path.stem}.md"
            
            # 如果启用图片提取且未指定路径，设置默认图片路径
            if self.extract_images and 'image_path' not in options:
                pdf_filename = pdf_path.stem
                images_dir = Path("./book_analysis/files") / pdf_filename / "images"
                images_dir.mkdir(parents=True, exist_ok=True)
                options['image_path'] = str(images_dir)
                print(colored(f"📁 图片将保存到: {images_dir}", "cyan"))
            
            # 准备转换参数
            convert_params = {
                'hdr_info': header_func,
                **options
            }
            
            # 过滤掉不支持的参数
            supported_params = [
                'pages', 'write_images', 'embed_images', 'ignore_images', 
                'ignore_graphics', 'dpi', 'image_path', 'image_format',
                'image_size_limit', 'force_text', 'margins', 'page_chunks',
                'page_width', 'page_height', 'table_strategy', 'graphics_limit',
                'ignore_code', 'extract_words', 'show_progress', 'use_glyphs',
                'filename'
            ]
            
            filtered_params = {k: v for k, v in convert_params.items() 
                             if k in supported_params or k == 'hdr_info'}
            
            print(colored(f"🔧 自定义标题转换参数: {filtered_params}", "cyan"))
            
            # 执行转换
            md_text = pymupdf4llm.to_markdown(str(pdf_path), **filtered_params)
            
            # 保存文件
            self._save_markdown(md_text, md_path)
            
            print(colored(f"✅ 自定义标题转换完成: {md_path}", "green"))
            return md_path
            
        except Exception as e:
            print(colored(f"❌ 自定义标题转换失败: {str(e)}", "red"))
            raise
    
    def extract_text_only(self, 
                          pdf_path: Path, 
                          target_dir: Path,
                          method: str = "text",
                          **options) -> Path:
        """仅提取PDF文本（不使用pymupdf4llm）
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            method: 提取方法 ('text', 'html', 'xml', 'dict', 'blocks', 'words')
            **options: 提取选项
        
        Returns:
            提取文本的文件路径
        """
        print(colored(f"🔄 提取PDF文本: {pdf_path.name} (方法: {method})", "cyan"))
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 确定输出文件扩展名
            ext_map = {
                'text': '.txt',
                'html': '.html', 
                'xml': '.xml',
                'dict': '.json',
                'blocks': '.txt',
                'words': '.txt'
            }
            
            output_path = target_dir / f"{pdf_path.stem}{ext_map.get(method, '.txt')}"
            
            # 打开文档
            doc = pymupdf.open(str(pdf_path))
            
            # 提取文本
            all_text = []
            
            for page_num, page in enumerate(doc):
                print(colored(f"📄 处理第 {page_num + 1} 页", "cyan"))
                
                if self.use_ocr:
                    # 使用OCR
                    tp = page.get_textpage_ocr()
                    text = page.get_text(textpage=tp)
                else:
                    # 常规文本提取
                    if method == "text":
                        text = page.get_text()
                    elif method == "html":
                        text = page.get_text("html")
                    elif method == "xml":
                        text = page.get_text("xml")
                    elif method == "dict":
                        import json
                        text = json.dumps(page.get_text("dict"), indent=2, ensure_ascii=False)
                    elif method == "blocks":
                        blocks = page.get_text("blocks")
                        text = "\n".join([block[4] for block in blocks if len(block) > 4])
                    elif method == "words":
                        words = page.get_text("words")
                        text = " ".join([word[4] for word in words if len(word) > 4])
                    else:
                        text = page.get_text()
                
                all_text.append(text)
            
            doc.close()
            
            # 保存文件
            combined_text = "\n\n--- 页面分隔符 ---\n\n".join(all_text)
            output_path.write_bytes(combined_text.encode('utf-8'))
            
            print(colored(f"✅ 文本提取完成: {output_path}", "green"))
            return output_path
            
        except Exception as e:
            print(colored(f"❌ 文本提取失败: {str(e)}", "red"))
            raise
    
    def get_document_info(self, pdf_path: Path) -> Dict[str, Any]:
        """获取PDF文档信息
        
        Args:
            pdf_path: PDF文件路径
        
        Returns:
            文档信息字典
        """
        try:
            doc = pymupdf.open(str(pdf_path))
            
            info = {
                'page_count': doc.page_count,
                'metadata': doc.metadata,
                'is_pdf': doc.is_pdf,
                'is_encrypted': doc.is_encrypted,
                'needs_pass': doc.needs_pass,
                'permissions': doc.permissions if hasattr(doc, 'permissions') else None,
                'pages_info': []
            }
            
            # 获取每页信息
            for page_num, page in enumerate(doc):
                page_info = {
                    'page_number': page_num + 1,
                    'rect': tuple(page.rect),
                    'rotation': page.rotation,
                    'has_images': len(page.get_images()) > 0,
                    'has_drawings': len(page.get_drawings()) > 0,
                    'text_length': len(page.get_text()),
                }
                info['pages_info'].append(page_info)
            
            doc.close()
            return info
            
        except Exception as e:
            print(colored(f"❌ 获取文档信息失败: {str(e)}", "red"))
            raise


def create_font_size_header_func(sizes: Dict[str, float]) -> Callable:
    """创建基于字体大小的标题识别函数
    
    Args:
        sizes: 字体大小映射，例如 {'h1': 18, 'h2': 16, 'h3': 14}
    
    Returns:
        标题识别函数
    """
    sorted_sizes = sorted(sizes.items(), key=lambda x: x[1], reverse=True)
    
    def header_func(span: Dict, page=None) -> str:
        """基于字体大小识别标题"""
        font_size = span.get('size', 0)
        
        for header_level, min_size in sorted_sizes:
            if font_size >= min_size:
                level = int(header_level[1]) if header_level.startswith('h') else 1
                return '#' * level + ' '
        
        return ''
    
    return header_func


def create_local_pdf_converter(**kwargs) -> LocalPDFToMarkdownConverter:
    """创建本地PDF转换器实例
    
    Args:
        **kwargs: 转换器参数
    
    Returns:
        本地PDF转换器实例
    """
    return LocalPDFToMarkdownConverter(**kwargs)


# 预定义的标题识别函数
def academic_paper_headers(span: Dict, page=None) -> str:
    """学术论文标题识别函数"""
    size = span.get('size', 0)
    flags = span.get('flags', 0)
    
    # 检查是否为粗体
    is_bold = bool(flags & 2**4)
    
    if size > 16 and is_bold:
        return '# '
    elif size > 14 and is_bold:
        return '## '
    elif size > 12 and is_bold:
        return '### '
    elif is_bold and size > 10:
        return '#### '
    
    return ''


def book_chapter_headers(span: Dict, page=None) -> str:
    """书籍章节标题识别函数"""
    size = span.get('size', 0)
    text = span.get('text', '').strip()
    
    # 检查是否包含章节关键词
    chapter_keywords = ['第', '章', 'chapter', 'Chapter', 'CHAPTER']
    is_chapter = any(keyword in text for keyword in chapter_keywords)
    
    if size > 18 or is_chapter:
        return '# '
    elif size > 15:
        return '## '
    elif size > 13:
        return '### '
    elif size > 11:
        return '#### '
    
    return '' 