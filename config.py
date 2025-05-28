"""
配置文件，包含所有prompt和可配置参数
"""
import os
from pathlib import Path

# 文件路径配置
BASE_DIR = Path("book_analysis")
FILE_DIR = BASE_DIR / "files"
TOC_DIR = BASE_DIR / "toc"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
SUMMARIES_DIR = BASE_DIR / "summaries"
META_SUMMARY_DIR = BASE_DIR / "meta_summaries"
INTEGRATED_DIR = BASE_DIR / "integrated"

# 处理配置
CHUNK_SIZE = 5000  # token per chunk
CHUNK_OVERLAP = 500  # chunk的重叠部分
SUMMARY_INTERVAL = 5  # 每处理多少个chunk生成一次中间摘要
MAX_WORKERS = 5  # 最大并行工作线程数

# 支持的文件格式
SUPPORTED_FORMATS = ['.pdf', '.md', '.txt']

# 深度选项配置
DEPTH_OPTIONS = ["conceptual", "standard", "detailed"]
DEFAULT_DEPTH = "standard"

# PDF转换API配置
PDF_API_BASE_URL = os.getenv("PDF_API_BASE_URL", "http://192.168.8.95:8001")
PDF_API_TIMEOUT = 600  # 10分钟超时
PDF_API_RETRY_COUNT = 3  # 重试次数
PDF_API_RETRY_DELAY = 5  # 重试间隔（秒）

# PDF处理默认参数
PDF_DEFAULT_PARAMS = {
    "enable_formula": False,
    "enable_table": False,
    "enable_image_caption": False,
    "language": "ch",
    "is_ocr": False
}