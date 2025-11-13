"""
资源路径工具：兼容开发环境和PyInstaller打包环境
"""
import sys
import os

def resource_path(relative_path: str) -> str:
    """
    获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境
    
    Args:
        relative_path: 相对于项目根目录的资源路径，如 "resources/app.ico"
    
    Returns:
        资源文件的绝对路径
    """
    try:
        # PyInstaller 打包后的临时文件夹路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境：使用项目根目录
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)

