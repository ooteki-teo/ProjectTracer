import sys
import os
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from PySide6.QtGui import QIcon
from utils.resource_path import resource_path
from utils.platform_utils import get_platform_icon_paths, is_macos, get_high_quality_icon_paths

def setup_logging():
    """设置日志输出到文件（用于调试）"""
    try:
        # 获取日志文件路径（在用户主目录下）
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".project_tracing")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "error.log")
        
        # 重定向标准错误输出到文件
        sys.stderr = open(log_file, 'a', encoding='utf-8')
        print(f"日志文件: {log_file}", file=sys.stderr)
        return log_file
    except Exception:
        pass
    return None

def main():
    log_file = None
    try:
        # 在 macOS 上设置日志输出
        if is_macos():
            log_file = setup_logging()
        
        print("正在启动应用程序...", file=sys.stderr if log_file else sys.stdout)
        
        app = QApplication(sys.argv)
        print("QApplication 创建成功", file=sys.stderr if log_file else sys.stdout)
        
        # 设置应用图标（系统任务栏和程序图标）
        # macOS 上使用 .icns 文件，Windows 上使用 .ico 文件
        icon_paths = get_high_quality_icon_paths()
        icon_set = False
        for icon_path in icon_paths:
            try:
                full_path = resource_path(icon_path)
                if os.path.exists(full_path):
                    app.setWindowIcon(QIcon(full_path))
                    icon_set = True
                    if is_macos():
                        print(f"✓ 已设置应用图标: {icon_path} (macOS 使用 .icns)", file=sys.stderr if log_file else sys.stdout)
                    else:
                        print(f"✓ 已设置应用图标: {icon_path}", file=sys.stderr if log_file else sys.stdout)
                    break
            except Exception as e:
                print(f"设置图标失败: {e}", file=sys.stderr if log_file else sys.stdout)
        
        if not icon_set:
            print("⚠ 警告: 未找到应用图标文件", file=sys.stderr if log_file else sys.stdout)
        
        # 设置样式
        app.setStyle("Fusion")
        print("样式设置完成", file=sys.stderr if log_file else sys.stdout)
        
        print("正在创建主窗口...", file=sys.stderr if log_file else sys.stdout)
        window = MainWindow()
        print("主窗口创建成功", file=sys.stderr if log_file else sys.stdout)
        
        window.show()
        print("窗口显示成功，进入事件循环", file=sys.stderr if log_file else sys.stdout)
        
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"应用程序启动失败:\n{str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr if log_file else sys.stdout)
        
        # 尝试显示错误对话框（如果 QApplication 已创建）
        try:
            if 'app' in locals():
                QMessageBox.critical(None, "启动错误", error_msg)
        except:
            pass
        
        # 在 macOS 上，如果日志文件存在，提示用户查看
        if log_file:
            print(f"\n错误日志已保存到: {log_file}", file=sys.stderr)
        
        sys.exit(1)
    finally:
        if log_file and hasattr(sys.stderr, 'close'):
            try:
                sys.stderr.close()
            except:
                pass

if __name__ == "__main__":
    main()