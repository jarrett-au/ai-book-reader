# AI书籍阅读工具

一个强大的AI书籍阅读和分析工具，能够提取文档目录、分析内容、生成摘要和整合输出。

![example](./assets/images/example-1.jpg)
**输出样例**: [置身事内_integrated_detailed_deepseek.pdf](./assets/pdf/置身事内_integrated_detailed_deepseek.pdf)

## 功能特点

- 提取文档目录
- 将文档分割成可管理的chunks
- 分析每个chunk并提取关键信息
- 生成中间摘要和整体摘要
- 整合所有输出为一个完整的阅读报告
- 多线程并行处理，提高效率
- 实时显示处理进度
- 支持多种深度选项，满足不同阅读需求

## 支持的文件格式

- Markdown (.md)
- 纯文本 (.txt)
- PDF (.pdf) - 自动通过API转换为Markdown

## 深度选项

工具提供三种不同的分析深度选项：

- **conceptual**：简明扼要，仅聚焦于核心概念和理论要点，适合快速了解文档的关键内容
- **standard**：平衡详细度，包含概念、例子和应用，适合一般阅读需求
- **detailed**：通俗易懂且详尽全面，包含所有例子、故事和应用场景，适合深入学习

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/ai-book-reader.git
cd ai-book-reader
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 创建`.env`文件并配置API：

```
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here

# PDF转换API配置
PDF_API_BASE_URL=http://192.168.8.95:8001
```

## 使用方法

基本用法：

```bash
python cli.py --file your_book.md
```

高级选项：

```bash
python cli.py --file your_book.md --chunk-size 5000 --overlap 500 --interval 5 --workers 3 --depth standard
```

参数说明：
- `--file`, `-f`: 要分析的文件路径（必填）
- `--chunk-size`: 分割大小（字符数），默认为5000
- `--overlap`: chunk重叠大小（字符数），默认为500
- `--interval`: 摘要生成间隔（chunk数量），默认为5
- `--workers`: 并行处理线程数，默认为3
- `--depth`: 分析深度，可选值为"conceptual"、"standard"、"detailed"，默认为"standard"

PDF处理选项：
- `--enable-formula`: 启用公式识别
- `--enable-table`: 启用表格识别
- `--enable-image-caption`: 启用图片打标
- `--pdf-language`: PDF处理语言，默认为中文(ch)
- `--force-ocr`: 强制使用OCR

## 输出文件

处理完成后，将在以下目录中生成文件：

- `book_analysis/toc/`: 提取的目录
- `book_analysis/knowledge/`: 每个chunk的分析结果
- `book_analysis/summaries/`: 中间摘要
- `book_analysis/meta_summaries/`: 元摘要
- `book_analysis/integrated/`: 整合的最终报告

## 自定义

可以在`config.py`和`prompt.py`文件中修改配置参数和提示词。

## 致谢

本项目受到 [echohive42/AI-reads-books-page-by-page](https://github.com/echohive42/AI-reads-books-page-by-page/tree/main) 项目的启发。该项目提供了一种智能的PDF书籍页面分析方法，通过提取知识点并在指定间隔生成渐进式摘要，为本项目的开发提供了宝贵的参考。特此感谢。
