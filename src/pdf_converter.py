"""
PDF转Markdown转换器，负责与PDF解析API交互
"""
import os
import time
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from termcolor import colored

from config import (
    PDF_API_BASE_URL, 
    PDF_API_TIMEOUT, 
    PDF_API_RETRY_COUNT, 
    PDF_API_RETRY_DELAY,
    PDF_DEFAULT_PARAMS
)


class PDFToMarkdownConverter:
    """PDF转Markdown转换器类"""
    
    def __init__(self, base_url: str = PDF_API_BASE_URL):
        """初始化转换器
        
        Args:
            base_url: API服务器基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = PDF_API_TIMEOUT
        
    def convert(self, pdf_path: Path, target_dir: Path, **kwargs) -> Path:
        """转换PDF为Markdown
        
        Args:
            pdf_path: PDF文件路径
            target_dir: 目标目录
            **kwargs: 额外的处理参数
        
        Returns:
            转换后的Markdown文件路径
        """
        print(colored(f"🔄 开始转换PDF: {pdf_path.name}", "cyan"))
        
        try:
            # 1. 上传文件并创建任务
            batch_id = self._upload_file(pdf_path, **kwargs)
            print(colored(f"✅ 文件上传成功，任务ID: {batch_id}", "green"))
            
            # 2. 轮询任务状态
            self._wait_for_completion(batch_id)
            print(colored(f"✅ PDF处理完成", "green"))
            
            # 3. 下载结果
            md_path = self._download_result(batch_id, target_dir, pdf_path.stem)
            print(colored(f"✅ Markdown文件已保存: {md_path}", "green"))
            
            return md_path
            
        except Exception as e:
            print(colored(f"❌ PDF转换失败: {str(e)}", "red"))
            raise
    
    def _upload_file(self, pdf_path: Path, **kwargs) -> str:
        """上传PDF文件
        
        Args:
            pdf_path: PDF文件路径
            **kwargs: 处理参数
        
        Returns:
            任务批次ID
        """
        url = f"{self.base_url}/api/v1/pdf/upload"
        
        # 合并默认参数和用户参数
        params = {**PDF_DEFAULT_PARAMS, **kwargs}
        
        # 准备文件和数据
        files = {
            'files': (pdf_path.name, open(pdf_path, 'rb'), 'application/pdf')
        }
        
        data = {
            'enable_formula': params.get('enable_formula', False),
            'enable_table': params.get('enable_table', False),
            'enable_image_caption': params.get('enable_image_caption', False),
            'language': params.get('language', 'ch'),
            'is_ocr': params.get('is_ocr', False)
        }
        
        try:
            response = self._make_request_with_retry(
                'POST', url, files=files, data=data
            )
            
            # 关闭文件
            files['files'][1].close()
            
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"API返回错误: {result.get('msg', '未知错误')}")
            
            # 获取batch_id，可能在不同的字段中
            data = result.get('data', {})
            batch_id = data.get('batch_id') or data.get('id') or data.get('task_id')
            
            if not batch_id:
                raise Exception(f"API响应中未找到batch_id: {result}")
            
            return batch_id
            
        except Exception as e:
            # 确保文件被关闭
            if 'files' in locals():
                files['files'][1].close()
            raise Exception(f"文件上传失败: {str(e)}")
    
    def _wait_for_completion(self, batch_id: str) -> None:
        """等待任务完成
        
        Args:
            batch_id: 任务批次ID
        """
        url = f"{self.base_url}/api/v1/pdf/status/{batch_id}"
        
        print(colored("⏳ 等待PDF处理完成...", "cyan"))
        
        start_time = time.time()
        while True:
            try:
                response = self._make_request_with_retry('GET', url)
                result = response.json()
                
                if result.get('code') != 0:
                    raise Exception(f"状态查询失败: {result.get('msg', '未知错误')}")
                
                data = result.get('data', {})
                status = data.get('overall_status', 'unknown')
                print(colored(f"📊 当前状态: {status}", "cyan"))
                
                # 处理各种可能的状态
                if status in ['completed', 'success', 'finished']:
                    return
                elif status in ['failed', 'error']:
                    error_msg = data.get('error') or data.get('message') or '处理失败'
                    raise Exception(f"PDF处理失败: {error_msg}")
                elif status in ['processing', 'running', 'pending', 'queued']:
                    # 继续等待
                    pass
                else:
                    print(colored(f"⚠️ 未知状态: {status}，继续等待...", "yellow"))
                
                # 检查超时
                elapsed = time.time() - start_time
                if elapsed > PDF_API_TIMEOUT:
                    raise Exception(f"处理超时 ({PDF_API_TIMEOUT}秒)")
                
                # 等待后重试
                time.sleep(10)  # 每10秒检查一次状态
                
            except Exception as e:
                if "处理超时" in str(e) or "处理失败" in str(e):
                    raise
                print(colored(f"⚠️ 状态查询出错，将重试: {str(e)}", "yellow"))
                time.sleep(5)
    
    def _download_result(self, batch_id: str, target_dir: Path, base_name: str) -> Path:
        """下载处理结果
        
        Args:
            batch_id: 任务批次ID
            target_dir: 目标目录
            base_name: 基础文件名
        
        Returns:
            Markdown文件路径
        """
        url = f"{self.base_url}/api/v1/pdf/download/{batch_id}"
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 下载ZIP文件
            zip_path = temp_path / f"{batch_id}.zip"
            
            response = self._make_request_with_retry('GET', url, stream=True)
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(colored(f"📦 ZIP文件下载完成: {zip_path}", "green"))
            
            # 解压ZIP文件
            extract_dir = temp_path / "extracted"
            extract_dir.mkdir()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 查找full.md文件
            md_file = self._find_full_md(extract_dir)
            if not md_file:
                raise Exception("在解压文件中未找到full.md文件")
            
            # 复制到目标位置
            target_path = target_dir / f"{base_name}.md"
            shutil.copy2(md_file, target_path)
            
            return target_path
    
    def _find_full_md(self, extract_dir: Path) -> Optional[Path]:
        """在解压目录中查找full.md文件
        
        Args:
            extract_dir: 解压目录
        
        Returns:
            full.md文件路径，如果未找到则返回None
        """
        # 递归搜索full.md文件
        for root, dirs, files in os.walk(extract_dir):
            if 'full.md' in files:
                return Path(root) / 'full.md'
        return None
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """带重试机制的HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 请求参数
        
        Returns:
            响应对象
        """
        last_exception = None
        
        for attempt in range(PDF_API_RETRY_COUNT):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except Exception as e:
                last_exception = e
                if attempt < PDF_API_RETRY_COUNT - 1:
                    print(colored(f"⚠️ 请求失败，{PDF_API_RETRY_DELAY}秒后重试 (尝试 {attempt + 1}/{PDF_API_RETRY_COUNT}): {str(e)}", "yellow"))
                    time.sleep(PDF_API_RETRY_DELAY)
                else:
                    print(colored(f"❌ 请求最终失败: {str(e)}", "red"))
        
        raise last_exception


def create_pdf_converter(**kwargs) -> PDFToMarkdownConverter:
    """创建PDF转换器实例
    
    Args:
        **kwargs: 转换器参数
    
    Returns:
        PDF转换器实例
    """
    return PDFToMarkdownConverter(**kwargs) 