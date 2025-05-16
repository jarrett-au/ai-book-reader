"""
配置文件，包含所有prompt和可配置参数
"""
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
MAX_WORKERS = 3  # 最大并行工作线程数

# 支持的文件格式
SUPPORTED_FORMATS = ['.pdf', '.md', '.txt']

# 模型配置
MODEL = "gpt-4.1"
ANALYSIS_MODEL = "gpt-4.1"

# Prompt配置
PROMPTS = {
    # 单个chunk分析的prompt
    "chunk_analysis": """Analyze this content as if you're studying from a document. 
            
    SKIP content if the page/chunk contains:
    - Table of contents
    - Chapter listings
    - Index pages
    - Blank pages
    - Copyright information
    - Publishing details
    - References or bibliography
    - Acknowledgments
    
    DO extract knowledge if the page/chunk contains:
    - Preface content that explains important concepts
    - Actual educational content
    - Key definitions and concepts
    - Important arguments or theories
    - Examples and case studies
    - Significant findings or conclusions
    - Methodologies or frameworks
    - Critical analyses or interpretations
    
    For valid content:
    - Set has_content to true
    - Extract detailed, learnable knowledge points
    - Include important quotes or key statements
    - Capture examples with their context
    - Preserve technical terms and definitions
    
    For pages/chunks to skip:
    - Set has_content to false
    - Return empty knowledge list""",
    
    # 中间摘要的prompt
    "interval_summary": """Create a comprehensive summary of the provided content in a concise but detailed way, using markdown format.
           
    Use markdown formatting:
    - ## for main sections
    - ### for subsections
    - Bullet points for lists
    - `code blocks` for any code or formulas
    - **bold** for emphasis
    - *italic* for terminology
    - > blockquotes for important notes
    
    Return only the markdown summary, nothing else. Do not say 'here is the summary' or anything like that before or after""",
    
    # 整体摘要的prompt
    "meta_summary": """你是一位专业的文档分析专家。你的任务是创建一个高级元摘要，整合多个已有摘要并提取核心思想和主要观点。
    
    在创建元摘要时，请遵循以下准则：
    1. 识别所有摘要中重复出现的核心主题和概念
    2. 综合不同摘要中互补的信息
    3. 解决摘要间可能存在的矛盾或分歧
    4. 按重要性排列关键点
    5. 提供整体性框架，展示知识的结构和连接
    6. 突出最重要的结论和见解
    
    使用markdown格式：
    - # 作为文档标题
    - ## 作为主要部分
    - ### 作为子部分
    - 使用项目符号列表
    - `代码块` 用于任何代码或公式
    - **粗体** 用于强调
    - *斜体* 用于术语
    - > 引用块用于重要注释
    
    仅返回markdown元摘要，不要加入其他内容。不要在开头或结尾说"这是摘要"等类似的话。""",
    
    # 目录提取的prompt
    "toc_extraction": """你是一位精确的目录提取专家。请从以下文本中提取完整的目录内容。只需提取目录，不要包含正文内容。

    遵循以下提取规则：
    1. 如果有明确的"目录"或"Contents"等标题，请从该标题开始提取
    2. 包含所有章节、小节的标题和编号
    3. 保持原始的格式和缩进
    4. 如果目录明显序号/缩进有误，请修正，遵循Markdown列表格式
    5. 确保提取所有列出的内容项目，直到目录结束
    6. 不要添加任何解释或评论，只返回提取的目录

    输入文本：

    {text}

    提取的目录：""",
    
    # 输出整合的prompt
    "output_integration": """你是一位专业的文档整合专家。请将以下内容整合成一个完整的文档：

    1. 目录内容：
    {toc}

    2. 中间摘要内容：
    {interval_summaries}

    3. 整体摘要内容：
    {meta_summary}

    请确保整合后的文档结构清晰，层次分明，内容准确。使用适当的Markdown格式以提高可读性。
    
    整合规则：
    1. 以整体摘要作为文档的主体框架
    2. 在文档开头加入完整的目录
    3. 适当引用中间摘要中的细节信息作为补充
    4. 保持内容的连贯性和逻辑性
    5. 删除重复信息，保留最重要的内容
    
    返回整合后的完整文档，使用规范的Markdown格式。"""
}

# API配置
AZURE_API_SETTINGS = {
    "api_key": "",  # 需要在环境变量或.env文件中设置
    "azure_endpoint": "",  # 需要在环境变量或.env文件中设置
    "api_version": "2025-01-01-preview",
} 