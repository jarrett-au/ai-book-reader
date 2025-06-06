# 本地PDF转Markdown转换器

基于PyMuPDF的高性能本地PDF转换解决方案，提供更好的兼容性和丰富的功能选项。

## 🔧 最近更新

### v2.0 (修复版本)
- ✅ **修复了参数兼容性问题**: 调整了与PyMuPDF4LLM 0.0.24的参数对应关系
- ✅ **优化了参数映射**: 使用正确的API参数名称 (`write_images`, `ignore_images`, `dpi`等)
- ✅ **改进了错误处理**: 提供更清晰的错误信息和调试信息
- ✅ **完善了测试框架**: 添加了完整的测试用例和示例PDF生成

## 功能特性

### ✨ 核心优势

- **🔧 本地处理**: 无需依赖外部API服务器，完全本地化处理
- **⚡ 高性能**: 基于PyMuPDF的C++内核，处理速度快
- **🎯 高精度**: 支持复杂布局、表格、图片和公式识别
- **🔄 多格式支持**: 输出Markdown、HTML、XML、纯文本等多种格式
- **🎨 自定义标题**: 支持自定义标题识别逻辑
- **📊 文档分析**: 提供详细的文档信息和页面分析

### 🛠️ 主要功能

1. **PDF转Markdown**: 高质量的PDF到Markdown转换
2. **自定义标题识别**: 支持学术论文、书籍等不同文档类型的标题识别
3. **文本提取**: 支持多种文本提取格式（text、html、xml、dict等）
4. **图片处理**: 支持图片提取、嵌入和质量控制
5. **表格识别**: 自动识别和转换表格结构
6. **OCR支持**: 可选的OCR功能处理图像化文本
7. **文档信息**: 获取PDF文档的详细元数据和页面信息

## 安装依赖

```bash
# 基础安装
pip install pymupdf pymupdf4llm

# 完整安装（包含OCR支持）
pip install 'pymupdf[optional]' pymupdf4llm pytesseract Pillow

# 从requirements.txt安装
pip install -r requirements.txt
```

## 快速开始

### 基本使用

```python
from src.local_pdf_converter import create_local_pdf_converter
from pathlib import Path

# 创建转换器
converter = create_local_pdf_converter(
    extract_images=True,
    preserve_layout=True,
    use_ocr=False
)

# 转换PDF文件
pdf_path = Path("document.pdf")
output_dir = Path("output")

md_path = converter.convert(
    pdf_path=pdf_path,
    target_dir=output_dir,
    show_progress=True,
    table_strategy='lines_strict',  # 表格检测策略
    write_images=True,              # 提取图片
    dpi=150                         # 图片分辨率
)

print(f"转换完成: {md_path}")
```

### 自定义标题识别

```python
from src.local_pdf_converter import academic_paper_headers, book_chapter_headers

# 使用学术论文标题识别
md_path = converter.convert_with_custom_headers(
    pdf_path=pdf_path,
    target_dir=output_dir,
    header_func=academic_paper_headers,
    ignore_images=True
)

# 使用书籍章节标题识别
md_path = converter.convert_with_custom_headers(
    pdf_path=pdf_path,
    target_dir=output_dir,
    header_func=book_chapter_headers,
    force_text=True
)
```

### 统一转换器接口

```python
from src.pdf_converter_adapter import auto_select_converter

# 自动选择最佳转换器
converter = auto_select_converter()

# 使用统一接口转换
md_path = converter.convert(
    pdf_path=pdf_path,
    target_dir=output_dir,
    enable_table=True,           # 启用表格检测
    enable_image_caption=True,   # 启用图片处理
    header_style='academic'      # 学术论文标题样式
)
```

## API 参数说明

### 核心参数 (PyMuPDF4LLM支持)

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `pages` | list/range | None | 指定转换的页面范围 |
| `write_images` | bool | False | 是否提取并保存图片 |
| `embed_images` | bool | False | 是否将图片嵌入为base64 |
| `ignore_images` | bool | False | 是否忽略图片 |
| `ignore_graphics` | bool | False | 是否忽略矢量图形 |
| `dpi` | int | 150 | 图片分辨率 |
| `table_strategy` | str | 'lines_strict' | 表格检测策略 |
| `show_progress` | bool | False | 是否显示进度条 |
| `force_text` | bool | True | 强制提取重叠文本 |
| `margins` | float/list | 0 | 页面边距设置 |

### 高级选项

```python
# 高级转换选项
md_path = converter.convert(
    pdf_path=pdf_path,
    target_dir=output_dir,
    
    # 页面选择
    page_numbers=[0, 1, 2],        # 只转换前3页
    
    # 表格处理
    table_strategy='lines_strict',  # 'lines_strict', 'lines', None
    
    # 图片选项
    write_images=True,             # 提取图片
    embed_images=False,            # 不嵌入，单独保存
    image_format='png',            # 图片格式
    image_size_limit=0.05,         # 图片大小阈值
    
    # 文本选项
    force_text=True,               # 提取重叠文本
    ignore_code=False,             # 保留代码格式
    
    # 页面设置
    margins=(50, 50, 50, 50),      # 左、上、右、下边距
    
    # 其他选项
    show_progress=True,            # 显示进度
    use_glyphs=False              # 使用字形而非字符
)
```

## 错误排查

### 常见问题

1. **参数错误**: `to_markdown() got an unexpected keyword argument 'xxx'`
   - **解决方案**: 确保使用的参数名称与PyMuPDF4LLM API一致
   - **检查方法**: 参考上面的API参数表

2. **中文字符显示问题**
   - **原因**: PDF中使用的字体不支持中文或字体嵌入问题
   - **解决方案**: 使用支持中文的字体或检查原PDF文件

3. **图片提取失败**
   - **检查**: `write_images=True` 和适当的 `dpi` 设置
   - **路径**: 确保 `image_path` 目录存在且可写

4. **表格识别不准确**
   - **尝试**: 不同的 `table_strategy` 选项
   - **选项**: `'lines_strict'`, `'lines'`, `None`

### 调试模式

```python
# 启用详细日志
converter = create_local_pdf_converter(extract_images=True)

# 获取文档信息
doc_info = converter.get_document_info(pdf_path)
print(f"页面数: {doc_info['page_count']}")
print(f"文档元数据: {doc_info['metadata']}")

# 提取纯文本进行调试
text_path = converter.extract_text_only(
    pdf_path=pdf_path,
    target_dir=output_dir,
    method='text'
)
```

## 测试用例

运行完整测试：

```bash
# 创建测试PDF
python tests/create_test_pdf.py

# 运行完整测试套件
python tests/test_local_converter.py

# 运行简单测试
python tests/simple_test.py
```

## 性能优化建议

1. **大文件处理**: 使用 `page_numbers` 分批处理
2. **图片密集文档**: 设置 `ignore_images=True` 加速处理
3. **表格很多**: 使用 `table_strategy=None` 跳过表格检测
4. **矢量图形多**: 设置适当的 `graphics_limit`

## 版本兼容性

- **PyMuPDF**: >= 1.25.5
- **PyMuPDF4LLM**: >= 0.0.24
- **Python**: >= 3.8

## 更新日志

### v2.0.0 (当前版本)
- 修复了PyMuPDF4LLM 0.0.24的参数兼容性问题
- 优化了参数映射和错误处理
- 添加了完整的测试框架
- 改进了文档和示例

### v1.0.0 (初始版本)
- 基础PDF转Markdown功能
- 自定义标题识别
- 统一转换器接口

## 技术架构

```
本地PDF转换器架构
├── LocalPDFToMarkdownConverter (核心转换器)
├── UnifiedPDFConverter (统一接口)
├── 预定义标题识别函数
│   ├── academic_paper_headers
│   ├── book_chapter_headers
│   └── create_font_size_header_func
└── 工具函数
    ├── auto_select_converter
    ├── create_local_converter
    └── create_server_converter
```

## 代码质量分析

这个本地PDF转换器实现展现了良好的可扩展性和可维护性：

**优势：**
1. **模块化设计**: 核心转换器、适配器和工具函数分离，职责明确
2. **统一接口**: 通过适配器模式提供一致的API，便于切换转换方式
3. **丰富的自定义选项**: 支持多种标题识别策略和转换参数
4. **良好的错误处理**: 提供详细的错误信息和故障排除指导
5. **性能优化**: 支持页面范围控制和内存优化选项

**建议改进：**
1. **配置管理**: 可以添加配置文件支持，方便管理默认参数
2. **缓存机制**: 对于重复转换的文档，可以添加缓存支持
3. **并行处理**: 大文档可以考虑多线程/多进程并行处理
4. **插件系统**: 可以设计插件接口，支持更多自定义处理逻辑

这个实现为项目提供了强大的本地PDF处理能力，显著提高了系统的兼容性和处理效率。 