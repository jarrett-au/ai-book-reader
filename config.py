"""
配置文件，包含所有prompt和可配置参数
"""
from pathlib import Path
from prompt import (
    CHUNK_ANALYSIS,
    INTERVAL_SUMMARY,
    META_SUMMARY,
    TOC_EXTRACTION,
    OUTPUT_INTEGRATION
)

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
MAX_WORKERS = 3  # 最大并行工作线程数

# 支持的文件格式
SUPPORTED_FORMATS = ['.pdf', '.md', '.txt']

# 深度选项配置
DEPTH_OPTIONS = ["conceptual", "standard", "detailed"]
DEFAULT_DEPTH = "standard"

# 不同深度的处理参数
DEPTH_PARAMS = {
    "conceptual": {
        "keep_examples": False,
        "explanation_detail": "low",
        "language_style": "academic"
    },
    "standard": {
        "keep_examples": True,
        "explanation_detail": "medium",
        "language_style": "balanced"
    },
    "detailed": {
        "keep_examples": True,
        "explanation_detail": "high",
        "language_style": "conversational"
    }
}

# 模型配置
MODEL = "gpt-4.1"
ANALYSIS_MODEL = "gpt-4.1"

# API配置
AZURE_API_SETTINGS = {
    "api_key": "",  # 需要在环境变量或.env文件中设置
    "azure_endpoint": "",  # 需要在环境变量或.env文件中设置
    "api_version": "2025-01-01-preview",
} 