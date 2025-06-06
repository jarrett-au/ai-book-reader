# 图片提取功能更新说明

## 更新概述

根据用户需求，本地PDF转换器的图片处理方式已更新，**不再使用base64嵌入图片**，而是将图片保存到指定的目录结构中。

## 主要变更

### 1. 图片保存路径
- **旧方式**: 使用base64编码直接嵌入到Markdown中
- **新方式**: 保存到 `./book_analysis/files/<文件名>/images/` 目录

### 2. 目录结构
```
./book_analysis/files/
├── <PDF文件名>/
│   ├── images/
│   │   ├── <PDF文件名>-<页码>-<图片序号>.png
│   │   └── ...
│   └── ...
```

### 3. Markdown引用方式
- **旧方式**: `![](data:image/png;base64,iVBORw0KG...)`
- **新方式**: `![](book_analysis/files/<文件名>/images/<图片文件名>.png)`

## 配置参数

### 默认设置
- `write_images=True`: 保存图片到文件
- `embed_images=False`: 不使用base64嵌入
- `image_format='png'`: 默认PNG格式
- `dpi=150`: 图片分辨率

### 自定义配置
```python
converter = create_local_pdf_converter(
    extract_images=True,
    dpi=300  # 更高分辨率
)

result = converter.convert(
    pdf_path=pdf_path,
    target_dir=output_dir,
    image_format='jpg',  # 使用JPEG格式
    write_images=True,
    embed_images=False
)
```

## 测试验证

### 测试结果
✅ 成功提取嵌入图片（2个图片，每个3.2KB）
✅ 自动创建目录结构
✅ Markdown正确引用图片路径
✅ 转换速度: 0.05秒

### 测试文件
- `tests/test_real_images.py`: 真实图片提取测试
- `tests/create_pdf_with_real_image.py`: 创建包含图片的测试PDF
- `tests/test_embedded_images.pdf`: 包含嵌入图片的测试PDF

## 优势

### 1. 文件大小优化
- Markdown文件更小（无base64数据）
- 图片可单独管理和优化

### 2. 兼容性提升
- 支持各种Markdown编辑器
- 图片可在文件系统中直接查看

### 3. 维护便利
- 图片路径清晰可见
- 便于图片资源管理
- 支持图片格式转换

## 向后兼容

如需使用base64嵌入方式，可手动设置：
```python
result = converter.convert(
    pdf_path=pdf_path,
    target_dir=output_dir,
    embed_images=True,  # 启用base64嵌入
    write_images=False  # 不保存到文件
)
```

## 使用示例

```python
from src.local_pdf_converter import create_local_pdf_converter
from pathlib import Path

# 创建转换器
converter = create_local_pdf_converter(extract_images=True)

# 转换PDF（图片将自动保存到指定目录）
result = converter.convert(
    pdf_path=Path("document.pdf"),
    target_dir=Path("output"),
    image_format='png',
    dpi=150
)

print(f"转换完成: {result}")
print("图片保存位置: ./book_analysis/files/document/images/")
```

## 注意事项

1. **目录权限**: 确保有创建目录的权限
2. **磁盘空间**: 大量图片可能占用较多空间
3. **路径长度**: Windows系统注意路径长度限制
4. **图片格式**: 支持PNG、JPEG等常见格式

---

**更新日期**: 2024-12-26  
**版本**: v2.1  
**状态**: ✅ 测试通过，已部署 