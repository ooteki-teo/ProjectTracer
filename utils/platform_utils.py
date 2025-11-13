"""
平台工具函数：用于跨平台兼容性处理
"""
import os
import re
import sys
import platform

def is_windows() -> bool:
    """判断是否为 Windows 系统"""
    return sys.platform == 'win32' or sys.platform == 'cygwin'

def is_macos() -> bool:
    """判断是否为 macOS 系统"""
    return sys.platform == 'darwin'

def is_linux() -> bool:
    """判断是否为 Linux 系统"""
    return sys.platform.startswith('linux')

def get_machine_name() -> str:
    """获取当前电脑名称（用于本地路径区分），返回经过清洗的字符串"""
    name = ""
    try:
        name = platform.node() or ""
    except Exception:
        name = ""

    if not name:
        # 尝试从环境变量获取
        name = (
            os.environ.get("COMPUTERNAME")
            or os.environ.get("HOSTNAME")
            or ""
        )

    if not name and hasattr(os, "uname"):
        try:
            name = os.uname().nodename
        except Exception:
            name = ""

    # 如果依然为空，使用默认名称
    if not name:
        name = "unknown-machine"

    # 规范化名称：只保留字母、数字、点、下划线和中划线
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)

    return name.strip() or "unknown-machine"

def get_platform_icon_paths() -> list:
    """
    根据平台返回图标路径列表（按优先级排序）
    用于窗口标题栏等位置
    
    Returns:
        图标路径列表，按优先级从高到低
    """
    if is_macos():
        # macOS 优先使用 .icns，然后是 .ico
        return [
            "resources/app.icns",
            "resources/app.ico"
        ]
    elif is_windows():
        # Windows 优先使用 .ico
        return [
            "resources/app.ico"
        ]
    else:
        # Linux 和其他平台优先使用 .ico，然后是 .png
        return [
            "resources/app.ico",
            "resources/app.png"
        ]

def get_high_quality_icon_paths() -> list:
    """
    获取高精度图标路径列表（用于系统任务栏和程序图标）
    macOS 上使用 .icns 文件，Windows/Linux 上使用 .ico 文件
    
    Returns:
        高精度图标路径列表，按优先级从高到低
    """
    if is_macos():
        # macOS 使用 .icns 文件（包含多个尺寸，系统会自动选择最合适的尺寸）
        return [
            "resources/app.icns",
            "resources/app.ico"
        ]
    else:
        # Windows 和 Linux 使用 ICO 文件（ICO 文件包含多个尺寸，系统会自动选择最高精度）
        return [
            "resources/app.ico"
        ]

def get_highest_quality_icon_path() -> str:
    """
    获取最高精度图标路径（用于主页面左上角Logo）
    使用 PNG 原图
    
    Returns:
        最高精度图标路径（相对路径），调用者需要使用 resource_path() 来获取完整路径
    """
    # 只使用 PNG 原图，返回相对路径
    # 调用者应该使用 resource_path() 来获取完整路径并检查文件是否存在
    return "resources/app.png"

def get_png_icon_paths() -> list:
    """
    获取 PNG 图标路径列表（用于系统任务栏和程序图标）
    使用 PNG 原图以获得最高清晰度
    
    Returns:
        PNG 图标路径列表
    """
    return [
        "resources/app.png"
    ]

def get_pyinstaller_icon_path() -> str:
    """
    获取 PyInstaller 打包时使用的图标路径
    
    Returns:
        图标文件路径，如果不存在则返回 None
    """
    import os
    
    if is_macos():
        # macOS 使用 .icns
        icon_path = "resources/app.icns"
    elif is_windows():
        # Windows 使用 .ico
        icon_path = "resources/app.ico"
    else:
        # Linux 和其他平台使用 .png 或 .ico
        icon_path = "resources/app.png"
        if not os.path.exists(icon_path):
            icon_path = "resources/app.ico"
    
    if os.path.exists(icon_path):
        return os.path.abspath(icon_path)
    
    # 如果平台特定图标不存在，尝试通用格式
    fallback_paths = ["resources/app.ico", "resources/app.png"]
    for path in fallback_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

