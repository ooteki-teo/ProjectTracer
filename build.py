import PyInstaller.__main__
import os
import shutil
import sys
from utils.platform_utils import get_pyinstaller_icon_path, is_macos, is_windows

def build():
    # 清理旧的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    # 删除旧的spec文件，让PyInstaller重新生成
    if os.path.exists('ProjectTracing.spec'):
        os.remove('ProjectTracing.spec')
    
    # PyInstaller配置
    # 在 macOS 上必须使用 --onedir 才能创建 .app 包
    # 在 Windows 上可以使用 --onefile 创建单文件，或 --onedir 创建文件夹
    args = [
        'main.py',
        '--name=ProjectTracing',  # 生成的exe文件名
        '--hidden-import=PySide6.QtWebEngineWidgets',
        '--hidden-import=pandas',
        '--hidden-import=sqlite3',
        '--hidden-import=utils.resource_path',  # 确保资源路径工具被包含
        '--hidden-import=utils.platform_utils',  # 确保平台工具被包含
        '--clean',                # 清理临时文件
        '--noconfirm',            # 不询问确认
        '--optimize=2'            # 优化级别（0-2，2为最高）
    ]
    
    # 根据平台设置打包模式和窗口模式
    if is_windows():
        # Windows: 使用 --onefile 创建单文件，或 --onedir 创建文件夹
        args.insert(1, '--onefile')  # 在 --name 之后插入
        args.append('--windowed')  # Windows: 无控制台窗口
    elif is_macos():
        # macOS: 必须使用 --onedir 才能创建 .app 包
        args.insert(1, '--onefile')  # 在 --name 之后插入
        args.append('--windowed')
        # macOS: 使用 --windowed 确保创建 .app 包
        # 错误信息会保存到 ~/.project_tracing/error.log
        args.append('--windowed')  # 无控制台窗口，创建 .app 包
    else:
        # Linux: 使用 --onefile 或 --onedir
        args.insert(1, '--onefile')  # 在 --name 之后插入
        args.append('--noconsole')  # Linux: 无控制台窗口
    
    # 添加图标文件（根据平台选择）
    icon_path = get_pyinstaller_icon_path()
    if icon_path:
        args.append(f'--icon={icon_path}')
        print(f"✓ 使用图标: {icon_path}")
    else:
        print("⚠ 警告: 未找到图标文件，将使用默认图标")
        print("   提示: Windows 需要 resources/app.ico")
        print("         macOS 需要 resources/app.icns")
        print("         Linux 需要 resources/app.png")
    
    # 添加资源文件和数据文件
    # PyInstaller在Windows上使用分号，在macOS/Linux上使用冒号
    separator = ';' if is_windows() else ':'
    data_files = []
    
    # 添加resources目录（包含图标文件）
    if os.path.exists('resources'):
        abs_resources = os.path.abspath('resources')
        data_files.append(f'{abs_resources}{separator}resources')
        print(f"✓ 添加资源目录: resources")
    
    # 添加ui目录
    if os.path.exists('ui'):
        abs_ui = os.path.abspath('ui')
        data_files.append(f'{abs_ui}{separator}ui')
        print(f"✓ 添加UI目录: ui")
    
    # 添加所有数据文件
    for data_file in data_files:
        args.append(f'--add-data={data_file}')
    
    # 显示平台信息
    platform_name = "Windows" if is_windows() else ("macOS" if is_macos() else "Linux")
    print(f"\n开始打包 ({platform_name})...")
    
    PyInstaller.__main__.run(args)
    
    # 根据平台显示输出信息
    if is_windows():
        print("\n打包完成！可执行文件在 dist/ProjectTracing.exe")
    elif is_macos():
        print("\n打包完成！应用程序在 dist/ProjectTracing.app")
        print("提示: macOS 应用是一个 .app 包，可以通过 Finder 打开")
    else:
        print("\n打包完成！可执行文件在 dist/ProjectTracing")
        print("提示: Linux 可执行文件可能需要执行权限: chmod +x dist/ProjectTracing")

if __name__ == "__main__":
    build()