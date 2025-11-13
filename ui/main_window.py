from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QListWidget, QListWidgetItem, QStackedWidget, 
                               QLabel, QFrame, QPushButton, QMessageBox, QFileDialog,
                               QDialog, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from database import Database
from utils.resource_path import resource_path
from utils.config import get_db_path, set_db_path
from utils.platform_utils import get_platform_icon_paths
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Project Tracing")
        self.setMinimumSize(1200, 800)
        
        # 设置窗口图标（窗口标题栏）
        # macOS 上使用 .icns 文件，Windows 上使用 .ico 文件
        from utils.platform_utils import get_platform_icon_paths, is_macos
        icon_paths = get_platform_icon_paths()
        for icon_path in icon_paths:
            try:
                full_path = resource_path(icon_path)
                if os.path.exists(full_path):
                    self.setWindowIcon(QIcon(full_path))
                    # 在 macOS 上，确保使用 .icns 文件
                    if is_macos() and icon_path.endswith('.icns'):
                        break
                    elif not is_macos():
                        break
            except:
                pass
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航
        nav_frame = QFrame()
        nav_frame.setMaximumWidth(200)
        nav_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: none;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: none;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 16px;
                border: none;
                min-height: 20px;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """)
        
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo - 使用图标图片
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(12, 16, 12, 16)
        logo_layout.setSpacing(6)
        
        # 图标 - 主页面左上角Logo（使用最高精度PNG原图，宽度限制与文字对齐）
        logo_icon = QLabel()
        from utils.platform_utils import get_highest_quality_icon_path
        from PySide6.QtGui import QFontMetrics
        
        # 计算文字宽度（"Project Tracing"）
        # 使用与文字标签相同的字体样式
        from PySide6.QtGui import QFont
        font = self.font()
        font.setPointSize(16)
        font.setWeight(QFont.Weight.DemiBold)  # 600 对应 DemiBold
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.boundingRect("Project Tracing").width()
        # 添加一些边距，使图标稍微小一点，更美观
        icon_max_width = int(text_width * 0.9)  # 图标宽度为文字宽度的90%
        
        icon_loaded = False
        # 优先使用最高精度的PNG原图
        high_quality_path = get_highest_quality_icon_path()
        if high_quality_path:
            try:
                full_path = resource_path(high_quality_path)
                # 使用 resource_path 后检查文件是否存在（兼容打包环境）
                if os.path.exists(full_path):
                    pixmap = QPixmap(full_path)
                    # 如果 pixmap 为空，说明文件加载失败
                    if not pixmap.isNull():
                        # 限制宽度与文字对齐，保持宽高比
                        # 使用最高质量缩放，宽度限制为文字宽度
                        scaled_pixmap = pixmap.scaled(
                            icon_max_width, icon_max_width, 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        )
                        logo_icon.setPixmap(scaled_pixmap)
                        icon_loaded = True
            except Exception as e:
                # 调试信息（可选）
                # print(f"加载图标失败: {e}")
                pass
        
        # 如果 PNG 原图不存在，不显示图标（只显示文字）
        
        if not icon_loaded:
            # 如果没有图标，显示文字
            logo_icon.setText("Project\nTracing")
            logo_icon.setStyleSheet("font-size: 18px; font-weight: 600; color: #ffffff;")
        
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_icon)
        
        # 文字标题
        logo_text = QLabel("Project Tracing")
        logo_text.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffffff; letter-spacing: 0.5px;")
        logo_text.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_text)
        
        nav_layout.addWidget(logo_widget)
        
        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.addItem(QListWidgetItem("📊 今日任务"))
        self.nav_list.addItem(QListWidgetItem("📁 项目列表"))
        self.nav_list.addItem(QListWidgetItem("📜 历史项目"))
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        nav_layout.addWidget(self.nav_list)
        
        nav_layout.addStretch()
        
        # 设置按钮（左下角）
        settings_btn = QPushButton("⚙️ 数据库设置")
        settings_btn.clicked.connect(self.show_db_settings)
        settings_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                min-height: 20px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
        """)
        nav_layout.addWidget(settings_btn)
        
        # 主内容区
        self.stack_widget = QStackedWidget()
        
        # 初始化页面
        from ui.overview_page import OverviewPage
        from ui.project_list_page import ProjectListPage
        from ui.history_page import HistoryPage
        
        self.overview_page = OverviewPage(self.db, self)
        self.project_list_page = ProjectListPage(self.db)
        self.project_list_page.main_window = self  # 设置引用以便刷新历史页面
        self.history_page = HistoryPage(self.db, self)
        
        self.stack_widget.addWidget(self.overview_page)
        self.stack_widget.addWidget(self.project_list_page)
        self.stack_widget.addWidget(self.history_page)
        
        # 布局
        main_layout.addWidget(nav_frame)
        main_layout.addWidget(self.stack_widget, 1)
        
    def on_nav_changed(self, index):
        self.stack_widget.setCurrentIndex(index)

        # 根据导航选项刷新对应页面数据
        if index == 0 and hasattr(self, 'overview_page'):
            self.overview_page.refresh_data()
        elif index == 1 and hasattr(self, 'project_list_page'):
            self.project_list_page.refresh_projects()
        elif index == 2 and hasattr(self, 'history_page'):
            self.history_page.refresh_projects()
    
    def show_db_settings(self):
        """显示数据库设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("数据库设置")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #1e1e1e;
            }
            QLineEdit {
                font-size: 14px;
                padding: 8px 10px;
                border: 2px solid #e0e0e0;
                background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                min-height: 20px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 说明标签
        info_label = QLabel("设置数据库存储位置。数据库文件和备份将保存在指定目录下。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # 路径输入区域
        path_layout = QHBoxLayout()
        path_label = QLabel("数据库路径:")
        path_label.setMinimumWidth(100)
        path_layout.addWidget(path_label)
        
        path_edit = QLineEdit()
        current_path = get_db_path()
        if current_path:
            path_edit.setText(current_path)
        else:
            # 显示默认路径
            default_path = os.path.join(os.getcwd(), "project_tracing.db")
            path_edit.setText(default_path)
        path_layout.addWidget(path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        browse_btn.clicked.connect(lambda: self._browse_db_path(path_edit))
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # 当前路径显示
        current_info = QLabel()
        if current_path:
            current_info.setText(f"当前数据库: {current_path}")
        else:
            current_info.setText(f"当前使用默认路径: {os.path.join(os.getcwd(), 'project_tracing.db')}")
        current_info.setStyleSheet("color: #666666; font-size: 12px; padding: 8px; background-color: #f5f5f5;")
        current_info.setWordWrap(True)
        layout.addWidget(current_info)
        
        # 警告标签
        warning_label = QLabel("⚠️ 更改数据库路径后需要重启程序才能生效。")
        warning_label.setStyleSheet("color: #d13438; font-size: 12px;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        save_btn.clicked.connect(lambda: self._save_db_path(path_edit, dialog))
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _browse_db_path(self, path_edit: QLineEdit):
        """浏览选择数据库路径"""
        current_path = path_edit.text()
        if current_path:
            initial_dir = os.path.dirname(current_path) if os.path.dirname(current_path) else os.getcwd()
        else:
            initial_dir = os.getcwd()
        
        # 选择保存数据库文件的目录
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "选择数据库存储目录",
            initial_dir
        )
        
        if selected_dir:
            # 生成数据库文件路径
            db_file_path = os.path.join(selected_dir, "project_tracing.db")
            path_edit.setText(db_file_path)
    
    def _save_db_path(self, path_edit: QLineEdit, dialog: QDialog):
        """保存数据库路径"""
        new_path = path_edit.text().strip()
        
        if not new_path:
            QMessageBox.warning(self, "错误", "请输入数据库路径！")
            return
        
        # 验证路径
        db_dir = os.path.dirname(new_path)
        if not db_dir:
            QMessageBox.warning(self, "错误", "无效的数据库路径！")
            return
        
        # 确保目录存在
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法创建目录：\n{str(e)}")
            return
        
        # 保存配置
        set_db_path(new_path)
        
        QMessageBox.information(
            self,
            "设置已保存",
            f"数据库路径已设置为：\n{new_path}\n\n请重启程序以使设置生效。"
        )
        
        dialog.accept()