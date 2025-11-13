"""
临时脚本：从 PNG 文件生成 ICO 和 ICNS 文件
使用方法: 
  python convert_ico_to_icns.py <png文件路径> [--ico 输出ico路径] [--icns 输出icns路径]
  
  如果不指定输出路径，会自动生成到同一目录

依赖:
  - Pillow: pip install Pillow
  - macOS 系统工具: iconutil (仅 macOS 系统自带，用于生成 ICNS)
"""
import sys
import os
import subprocess
import argparse

# 检查 Pillow 是否安装
try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装 Pillow 库")
    print("请运行: pip install Pillow")
    sys.exit(1)

def create_ico_from_png(png_path: str, ico_path: str) -> bool:
    """
    从 PNG 文件创建 ICO 文件（Windows 格式）
    
    Args:
        png_path: PNG 文件路径
        ico_path: 输出的 ICO 文件路径
    
    Returns:
        是否成功
    """
    try:
        # 打开 PNG 文件
        img = Image.open(png_path)
        
        # 转换为 RGBA 模式（ICO 需要支持透明度）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"输入图像尺寸: {img.size}")
        
        # ICO 文件通常包含多个尺寸
        # Windows 常用的 ICO 尺寸
        ico_sizes = [
            (64, 64),
            (128, 128),
            (256, 256)
        ]
        
        # 创建不同尺寸的图像列表
        images = []
        sizes_list = []
        for width, height in ico_sizes:
            # 使用高质量缩放
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            images.append(resized)
            sizes_list.append((width, height))
            print(f"  ✓ 生成尺寸: {width}x{height}")
        
        # 保存为 ICO 文件（Pillow 需要 sizes 参数来保存多尺寸）
        # 使用第一个图像作为基础，但指定所有尺寸
        images[0].save(ico_path, format='ICO', sizes=sizes_list)
        
        print(f"✓ 成功创建 ICO 文件: {ico_path}")
        return True
        
    except Exception as e:
        print(f"错误: 无法创建 ICO 文件: {e}")
        return False

def create_iconset_from_png(png_path: str, iconset_dir: str) -> bool:
    """
    从 PNG 文件创建 .iconset 目录（包含不同尺寸的 PNG 图像，用于生成 ICNS）
    
    Args:
        png_path: PNG 文件路径
        iconset_dir: 输出的 .iconset 目录路径
    
    Returns:
        是否成功
    """
    # 创建 iconset 目录
    os.makedirs(iconset_dir, exist_ok=True)
    
    # 打开 PNG 文件
    try:
        img = Image.open(png_path)
        
        # 转换为 RGBA 模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"输入图像尺寸: {img.size}")
        
    except Exception as e:
        print(f"错误: 无法打开 PNG 文件: {e}")
        return False
    
    # macOS ICNS 需要的标准尺寸
    # 格式: icon_<width>x<height>.png 和 icon_<width>x<height>@2x.png
    sizes = [
        (16, 16),
        (32, 32),
        (128, 128),
        (256, 256),
        (512, 512),
        (1024, 1024)
    ]
    
    # 生成所有需要的尺寸
    created_files = []
    for width, height in sizes:
        # 标准分辨率
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        filename_1x = f"icon_{width}x{height}.png"
        filepath_1x = os.path.join(iconset_dir, filename_1x)
        resized.save(filepath_1x, "PNG")
        created_files.append(filepath_1x)
        print(f"  ✓ 创建: {filename_1x}")
        
        # 高分辨率 (@2x)
        resized_2x = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        filename_2x = f"icon_{width}x{height}@2x.png"
        filepath_2x = os.path.join(iconset_dir, filename_2x)
        resized_2x.save(filepath_2x, "PNG")
        created_files.append(filepath_2x)
        print(f"  ✓ 创建: {filename_2x}")
    
    return len(created_files) > 0

def convert_iconset_to_icns(iconset_dir: str, icns_path: str) -> bool:
    """
    使用 macOS 的 iconutil 命令将 .iconset 目录转换为 .icns 文件
    
    Args:
        iconset_dir: .iconset 目录路径
        icns_path: 输出的 .icns 文件路径
    
    Returns:
        是否成功
    """
    # 检查是否在 macOS 上
    if sys.platform != 'darwin':
        print("警告: iconutil 命令仅在 macOS 上可用")
        print("如果不在 macOS 上，请手动在 macOS 上运行以下命令:")
        print(f"  iconutil -c icns {iconset_dir} -o {icns_path}")
        return False
    
    try:
        # 使用 iconutil 命令
        cmd = ['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ 成功创建 ICNS 文件: {icns_path}")
            return True
        else:
            print(f"错误: iconutil 执行失败:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("错误: 找不到 iconutil 命令（仅在 macOS 上可用）")
        return False
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='从 PNG 文件生成 ICO 和 ICNS 文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 同时生成 ICO 和 ICNS（自动命名）
  python convert_ico_to_icns.py resources/app.png
  
  # 只生成 ICO
  python convert_ico_to_icns.py resources/app.png --ico resources/app.ico
  
  # 只生成 ICNS
  python convert_ico_to_icns.py resources/app.png --icns resources/app.icns
  
  # 同时生成并指定路径
  python convert_ico_to_icns.py resources/app.png --ico resources/app.ico --icns resources/app.icns
        """
    )
    
    parser.add_argument('png_path', help='输入的 PNG 文件路径')
    parser.add_argument('--ico', dest='ico_path', help='输出的 ICO 文件路径（可选）')
    parser.add_argument('--icns', dest='icns_path', help='输出的 ICNS 文件路径（可选）')
    
    args = parser.parse_args()
    
    png_path = args.png_path
    ico_path = args.ico_path
    icns_path = args.icns_path
    
    # 检查 PNG 文件是否存在
    if not os.path.exists(png_path):
        print(f"错误: PNG 文件不存在: {png_path}")
        sys.exit(1)
    
    # 如果没有指定任何输出，默认同时生成两种格式
    if not ico_path and not icns_path:
        # 自动生成输出路径
        base_name = os.path.splitext(os.path.basename(png_path))[0]
        png_dir = os.path.dirname(png_path) if os.path.dirname(png_path) else '.'
        ico_path = os.path.join(png_dir, f"{base_name}.ico")
        icns_path = os.path.join(png_dir, f"{base_name}.icns")
    else:
        # 如果只指定了一个，另一个不生成
        if not ico_path:
            base_name = os.path.splitext(os.path.basename(png_path))[0]
            png_dir = os.path.dirname(png_path) if os.path.dirname(png_path) else '.'
            ico_path = os.path.join(png_dir, f"{base_name}.ico")
        if not icns_path:
            base_name = os.path.splitext(os.path.basename(png_path))[0]
            png_dir = os.path.dirname(png_path) if os.path.dirname(png_path) else '.'
            icns_path = os.path.join(png_dir, f"{base_name}.icns")
    
    print(f"输入文件: {png_path}")
    print()
    
    success_count = 0
    total_count = 0
    
    # 生成 ICO 文件
    if ico_path:
        total_count += 1
        print("=" * 50)
        print("生成 ICO 文件（Windows 格式）...")
        print("=" * 50)
        if create_ico_from_png(png_path, ico_path):
            success_count += 1
        print()
    
    # 生成 ICNS 文件
    if icns_path:
        total_count += 1
        print("=" * 50)
        print("生成 ICNS 文件（macOS 格式）...")
        print("=" * 50)
        
        # 创建临时 iconset 目录
        iconset_dir = icns_path.replace('.icns', '.iconset')
        
        # 如果 iconset 目录已存在，先删除
        if os.path.exists(iconset_dir):
            import shutil
            shutil.rmtree(iconset_dir)
            print(f"清理旧的 iconset 目录: {iconset_dir}")
        
        print("步骤 1: 从 PNG 文件创建 iconset 目录...")
        if create_iconset_from_png(png_path, iconset_dir):
            print()
            print("步骤 2: 将 iconset 转换为 ICNS 文件...")
            if convert_iconset_to_icns(iconset_dir, icns_path):
                success_count += 1
                # 清理临时 iconset 目录
                import shutil
                if os.path.exists(iconset_dir):
                    shutil.rmtree(iconset_dir)
                    print(f"✓ 清理临时目录: {iconset_dir}")
            else:
                print()
                print("⚠ iconset 目录已创建，但无法转换为 ICNS")
                print(f"iconset 目录位置: {iconset_dir}")
                if sys.platform != 'darwin':
                    print("\n提示: 请在 macOS 上运行以下命令完成转换:")
                    print(f"  iconutil -c icns {iconset_dir} -o {icns_path}")
        else:
            print("错误: 无法创建 iconset 目录")
        print()
    
    # 总结
    print("=" * 50)
    if success_count == total_count:
        print(f"✓ 全部完成！成功生成 {success_count}/{total_count} 个文件")
        if ico_path:
            print(f"  - ICO: {ico_path}")
        if icns_path:
            print(f"  - ICNS: {icns_path}")
    elif success_count > 0:
        print(f"⚠ 部分完成：成功生成 {success_count}/{total_count} 个文件")
    else:
        print("✗ 生成失败")
    print("=" * 50)

if __name__ == "__main__":
    main()
