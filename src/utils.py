"""
工具函数库，包含共用功能
"""
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from termcolor import colored


def setup_directories(base_dir: Path, file_name: str) -> Dict[str, Path]:
    """
    创建所有必要的目录结构并返回目录路径字典
    
    Args:
        base_dir: 基础目录
        file_name: 文件名
    
    Returns:
        包含所有目录路径的字典
    """
    base_name = Path(file_name).stem
    
    # 创建目录结构
    dirs = {
        "file": base_dir / "files",
        "toc": base_dir / "toc",
        "knowledge": base_dir / "knowledge" / base_name,
        "summaries": base_dir / "summaries" / base_name,
        "meta_summary": base_dir / "meta_summaries",
        "integrated": base_dir / "integrated",
    }
    
    # 创建所有目录
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print(colored(f"📁 已创建目录结构，基础目录: {base_dir}", "blue"))
    return dirs


def copy_file_to_workspace(file_path: Path, target_dir: Path) -> Path:
    """
    将文件复制到工作目录
    
    Args:
        file_path: 原始文件路径
        target_dir: 目标目录
    
    Returns:
        复制后的文件路径
    """
    target_path = target_dir / file_path.name
    
    if not target_path.exists():
        shutil.copy2(file_path, target_path)
        print(colored(f"📄 已复制文件到工作目录: {target_path}", "green"))
    else:
        print(colored(f"📄 文件已存在于工作目录: {target_path}", "cyan"))
    
    return target_path


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """
    保存JSON数据到文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(colored(f"💾 已保存数据到: {file_path}", "green"))


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    从文件加载JSON数据
    
    Args:
        file_path: 文件路径
    
    Returns:
        加载的数据
    """
    if not file_path.exists():
        print(colored(f"⚠️ 文件不存在: {file_path}", "yellow"))
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(colored(f"📂 已加载数据从: {file_path}", "green"))
    return data


def save_markdown(content: str, file_path: Path, title: str = None, metadata: Dict[str, Any] = None) -> None:
    """
    保存Markdown内容到文件，并添加元数据
    
    Args:
        content: Markdown内容
        file_path: 文件路径
        title: 文档标题
        metadata: 附加元数据
    """
    header = []
    
    if title:
        header.append(f"# {title}")
    
    if metadata:
        header.append("---")
        for key, value in metadata.items():
            header.append(f"{key}: {value}")
        header.append("---")
    
    header.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    header.append("")  # 空行
    
    # 组装完整内容
    full_content = "\n".join(header) + "\n" + content + "\n\n---\n*由AI书籍阅读工具生成*"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(colored(f"📝 已保存Markdown到: {file_path}", "green"))


def get_formatted_time() -> str:
    """获取格式化的当前时间字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_elapsed_time(seconds: float) -> str:
    """格式化经过的时间"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}分{int(remaining_seconds)}秒"
    else:
        hours = seconds // 3600
        remaining = seconds % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{int(hours)}小时{int(minutes)}分{int(seconds)}秒" 