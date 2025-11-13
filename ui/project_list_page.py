from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QAbstractItemView, QSplitter,
                               QLabel, QLineEdit, QTextEdit, QComboBox,
                               QGroupBox, QGridLayout, QDateEdit, QScrollArea,
                               QFileDialog, QStyledItemDelegate, QStyleOptionViewItem,
                               QSizePolicy, QCheckBox, QStyle)
from PySide6.QtCore import Qt, QDate, QUrl, QTimer
from PySide6.QtGui import QDesktopServices, QColor, QPainter
from database import Database
from models import Status
import os
from datetime import datetime

class StatusItemDelegate(QStyledItemDelegate):
    """自定义委托，用于绘制状态列，确保选中时也保持原背景色"""
    def paint(self, painter, option, index):
        # 获取背景色和文字颜色
        bg_color = index.data(Qt.BackgroundRole)
        text_color = index.data(Qt.ForegroundRole)
        
        # 如果有自定义背景色，使用它（状态项）
        if bg_color and isinstance(bg_color, QColor):
            # 绘制背景
            painter.fillRect(option.rect, bg_color)
            # 使用自定义文字颜色
            if text_color and isinstance(text_color, QColor):
                painter.setPen(text_color)
            else:
                painter.setPen(QColor("#ffffff"))
        else:
            # 普通项，使用默认绘制
            if option.state & QStyle.StateFlag.State_Selected:
                painter.fillRect(option.rect, QColor("#e3f2fd"))
                painter.setPen(QColor("#1e1e1e"))
            else:
                painter.fillRect(option.rect, QColor("#ffffff"))
                painter.setPen(QColor("#1e1e1e"))
        
        # 设置字体大小
        font = painter.font()
        font.setPointSize(14)
        painter.setFont(font)
        
        # 绘制文字
        text = index.data(Qt.DisplayRole) or ""
        painter.drawText(option.rect, Qt.AlignCenter, text)

class ProjectItemDelegate(QStyledItemDelegate):
    """自定义委托，用于绘制项目列表，处理置顶项目的背景色"""
    def paint(self, painter, option, index):
        # 获取背景色
        bg_color = index.data(Qt.BackgroundRole)
        is_selected = option.state & QStyle.StateFlag.State_Selected
        
        # 如果有自定义背景色（置顶项目）
        if bg_color and isinstance(bg_color, QColor):
            if is_selected:
                # 选中时：使用红色背景
                painter.fillRect(option.rect, QColor("#ffe5e9"))
                painter.setPen(QColor("#b71c1c"))
            else:
                # 未选中时：使用浅蓝色背景（置顶）
                painter.fillRect(option.rect, bg_color)
                painter.setPen(QColor("#1e1e1e"))
        else:
            # 普通项目
            if is_selected:
                # 选中时：使用红色背景
                painter.fillRect(option.rect, QColor("#ffe5e9"))
                painter.setPen(QColor("#b71c1c"))
            else:
                # 未选中时：使用白色背景
                painter.fillRect(option.rect, QColor("#ffffff"))
                painter.setPen(QColor("#1e1e1e"))
        
        # 设置字体
        font = painter.font()
        font.setPointSize(15)
        painter.setFont(font)
        
        # 绘制文字
        text = index.data(Qt.DisplayRole) or ""
        painter.drawText(option.rect, Qt.AlignLeft | Qt.AlignVCenter, text)

class ProjectListPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_project_id = None
        self.current_projects = []
        self.init_ui()
        self.refresh_projects()
    
    def init_ui(self):
        """初始化UI - 左右分栏布局"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== 左侧：项目列表 ==========
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 新建项目按钮（在列表最上方）
        add_project_btn = QPushButton("➕ 新建项目")
        add_project_btn.clicked.connect(self.create_project)
        add_project_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        left_layout.addWidget(add_project_btn)
        
        # 项目列表表格
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(1)
        self.projects_table.setHorizontalHeaderLabels(["项目名称"])
        self.projects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.projects_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.projects_table.itemSelectionChanged.connect(self.on_project_selected)
        self.projects_table.setMinimumWidth(260)
        self.projects_table.verticalHeader().setDefaultSectionSize(50)
        self.projects_table.setStyleSheet("""
            QTableWidget {
                font-size: 15px;
                border: 1px solid #e0e0e0;
                gridline-color: #f0f0f0;
                background-color: #ffffff;
            }
            QTableWidget::item {
                padding: 14px 10px;
                border: none;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #1e1e1e;
                font-size: 15px;
                font-weight: 600;
                padding: 10px 8px;
                border: none;
            }
        """)
        # 为项目列表设置自定义委托
        project_delegate = ProjectItemDelegate(self.projects_table)
        self.projects_table.setItemDelegateForColumn(0, project_delegate)
        left_layout.addWidget(self.projects_table)
        
        splitter.addWidget(left_widget)
        
        # ========== 右侧：详情区域 ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 创建垂直分割器：上方项目详情，下方任务列表
        detail_splitter = QSplitter(Qt.Vertical)
        
        # 上方：项目详情编辑区
        project_info_widget = QGroupBox("项目详情")
        project_info_widget.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                border-radius: 0px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        project_info_layout = QVBoxLayout(project_info_widget)
        project_info_layout.setContentsMargins(12, 18, 12, 12)
        project_info_layout.setSpacing(10)
        
        # 项目信息表单
        info_grid = QGridLayout()
        info_grid.setSpacing(10)
        info_grid.setColumnMinimumWidth(0, 80)
        
        # 统一标签样式
        label_style = "font-size: 14px; font-weight: 500; color: #1e1e1e;"
        input_style = """
            QLineEdit, QTextEdit, QComboBox {
                font-size: 14px;
                padding: 8px 10px;
                border: 2px solid #e0e0e0;
                background-color: #ffffff;
                min-height: 20px;
                color: #1e1e1e;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                selection-background-color: #e3f2fd;
                selection-color: #1e1e1e;
                color: #1e1e1e;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 10px;
                color: #1e1e1e;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e3f2fd;
                color: #1e1e1e;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """
        
        name_label = QLabel("项目名称:")
        name_label.setStyleSheet(label_style)
        info_grid.addWidget(name_label, 0, 0)
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("选择项目以编辑...")
        self.project_name_edit.setStyleSheet(input_style)
        info_grid.addWidget(self.project_name_edit, 0, 1)
        
        # status_label = QLabel("状态:")
        # status_label.setStyleSheet(label_style)
        # info_grid.addWidget(status_label, 1, 0)
        # self.project_status_combo = QComboBox()
        # self.project_status_combo.addItems(["计划中", "进行中", "已完成"])
        # self.project_status_combo.setStyleSheet(input_style)
        # info_grid.addWidget(self.project_status_combo, 1, 1)
        
        desc_label = QLabel("详情:")
        desc_label.setStyleSheet(label_style)
        info_grid.addWidget(desc_label, 2, 0)
        self.project_desc_edit = QTextEdit()
        self.project_desc_edit.setMinimumHeight(160)
        self.project_desc_edit.setMaximumHeight(240)
        self.project_desc_edit.setPlaceholderText("项目详情...")
        self.project_desc_edit.setStyleSheet(input_style)
        info_grid.addWidget(self.project_desc_edit, 2, 1)
        
        # 本地路径
        path_label = QLabel("工作路径:")
        path_label.setStyleSheet(label_style)
        info_grid.addWidget(path_label, 3, 0)
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        self.project_path_edit = QLineEdit()
        self.project_path_edit.setPlaceholderText("选择项目工作文件夹...")
        self.project_path_edit.setStyleSheet(input_style)
        path_layout.addWidget(self.project_path_edit)
        
        select_path_btn = QPushButton("选择")
        select_path_btn.clicked.connect(self.select_project_path)
        select_path_btn.setMinimumWidth(80)
        select_path_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 500;
                background-color: #f5f5f5;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        path_layout.addWidget(select_path_btn)
        
        open_path_btn = QPushButton("打开")
        open_path_btn.clicked.connect(self.open_project_path)
        open_path_btn.setMinimumWidth(80)
        open_path_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 500;
                background-color: #107c10;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
        """)
        path_layout.addWidget(open_path_btn)
        
        info_grid.addLayout(path_layout, 3, 1)
        
        project_info_layout.addLayout(info_grid)
        
        # 项目操作按钮
        project_btn_layout = QHBoxLayout()
        project_btn_layout.setSpacing(12)
        
        button_style_base = """
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:pressed {
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """
        
        self.pin_project_btn = QPushButton("置顶")
        self.pin_project_btn.clicked.connect(self.toggle_pin_project)
        self.pin_project_btn.setEnabled(False)
        self.pin_project_btn.setStyleSheet(button_style_base + "QPushButton { background-color: #2196f3; color: #ffffff; }")
        project_btn_layout.addWidget(self.pin_project_btn)
        
        self.save_project_btn = QPushButton("保存")
        self.save_project_btn.clicked.connect(self.save_project_info)
        self.save_project_btn.setEnabled(False)
        self.save_project_btn.setStyleSheet(button_style_base + "QPushButton { background-color: #0078d4; color: #ffffff; }")
        project_btn_layout.addWidget(self.save_project_btn)
        
        self.complete_project_btn = QPushButton("完成")
        self.complete_project_btn.clicked.connect(self.complete_current_project)
        self.complete_project_btn.setEnabled(False)
        self.complete_project_btn.setStyleSheet(button_style_base + "QPushButton { background-color: #107c10; color: #ffffff; }")
        project_btn_layout.addWidget(self.complete_project_btn)
        
        self.archive_project_btn = QPushButton("归档")
        self.archive_project_btn.clicked.connect(self.archive_current_project)
        self.archive_project_btn.setEnabled(False)
        self.archive_project_btn.setStyleSheet(button_style_base + "QPushButton { background-color: #ffaa44; color: #ffffff; }")
        project_btn_layout.addWidget(self.archive_project_btn)
        
        self.delete_project_btn = QPushButton("删除")
        self.delete_project_btn.clicked.connect(self.delete_current_project)
        self.delete_project_btn.setEnabled(False)
        self.delete_project_btn.setStyleSheet(button_style_base + "QPushButton { background-color: #d13438; color: #ffffff; }")
        project_btn_layout.addWidget(self.delete_project_btn)
        
        project_btn_layout.addStretch()
        project_info_layout.addLayout(project_btn_layout)
        
        detail_splitter.addWidget(project_info_widget)
        
        # 下方：任务列表（占比大）
        tasks_widget = QGroupBox("任务列表")
        tasks_widget.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                border-radius: 0px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(12, 18, 12, 12)
        tasks_layout.setSpacing(10)
        
        # 新建任务按钮
        task_toolbar = QHBoxLayout()
        task_toolbar.setSpacing(12)
        add_task_btn = QPushButton("➕ 新建任务")
        add_task_btn.clicked.connect(self.show_task_form)
        add_task_btn.setEnabled(False)
        add_task_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 600;
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        self.add_task_btn = add_task_btn
        task_toolbar.addWidget(add_task_btn)
        task_toolbar.addStretch()
        tasks_layout.addLayout(task_toolbar)
        
        # 任务表单区域（新建/编辑任务）
        self.task_form_widget = QGroupBox("任务编辑")
        self.task_form_widget.setVisible(False)
        self.task_form_widget.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                border-radius: 0px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #f8f8f8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        task_form_layout = QVBoxLayout(self.task_form_widget)
        task_form_layout.setContentsMargins(12, 18, 12, 12)
        task_form_layout.setSpacing(10)
        
        task_form_grid = QGridLayout()
        task_form_grid.setSpacing(10)
        task_form_grid.setColumnStretch(1, 1)
        task_form_grid.setColumnStretch(3, 1)
        task_form_grid.setColumnStretch(5, 1)
        task_form_grid.setColumnMinimumWidth(0, 80)
        
        form_label_style = "font-size: 14px; font-weight: 500; color: #1e1e1e;"
        form_input_style = """
            QLineEdit, QTextEdit, QDateEdit {
                font-size: 14px;
                padding: 8px 10px;
                border: 2px solid #e0e0e0;
                background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus {
                border: 2px solid #0078d4;
            }
        """
        
        # 第一行：名称、开始、截止日期同一行
        name_label = QLabel("任务名称 *:")
        name_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(name_label, 0, 0)
        self.task_name_edit = QLineEdit()
        self.task_name_edit.setStyleSheet(form_input_style)
        task_form_grid.addWidget(self.task_name_edit, 0, 1)
        
        start_label = QLabel("开始日期 *:")
        start_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(start_label, 0, 2)
        self.task_start_date = QDateEdit()
        self.task_start_date.setCalendarPopup(True)
        self.task_start_date.setDate(QDate.currentDate())
        self.task_start_date.setStyleSheet(form_input_style)
        task_form_grid.addWidget(self.task_start_date, 0, 3)
        
        end_label = QLabel("截止日期 *:")
        end_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(end_label, 0, 4)
        self.task_end_date = QDateEdit()
        self.task_end_date.setCalendarPopup(True)
        self.task_end_date.setDate(QDate.currentDate().addDays(7))
        self.task_end_date.setStyleSheet(form_input_style)
        task_form_grid.addWidget(self.task_end_date, 0, 5)
        
        # 第二行：状态
        status_label = QLabel("状态:")
        status_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(status_label, 1, 0)
        self.task_status_label = QLabel("（根据时间自动设置）")
        self.task_status_label.setStyleSheet("font-size: 12px; color: #757575; font-style: italic;")
        task_form_grid.addWidget(self.task_status_label, 1, 1, 1, 5)
        
        # 标签行：重要和紧急
        tag_label = QLabel("标签:")
        tag_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(tag_label, 2, 0)
        tag_layout = QHBoxLayout()
        tag_layout.setSpacing(20)
        self.task_important_check = QCheckBox("重要")
        self.task_important_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #1e1e1e;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        tag_layout.addWidget(self.task_important_check)
        self.task_urgent_check = QCheckBox("紧急")
        self.task_urgent_check.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #1e1e1e;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        tag_layout.addWidget(self.task_urgent_check)
        tag_layout.addStretch()
        task_form_grid.addLayout(tag_layout, 2, 1, 1, 5)
        
        # 第四行：描述
        desc_label = QLabel("描述:")
        desc_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(desc_label, 3, 0)
        self.task_desc_edit = QTextEdit()
        self.task_desc_edit.setMaximumHeight(100)
        self.task_desc_edit.setStyleSheet(form_input_style)
        task_form_grid.addWidget(self.task_desc_edit, 3, 1, 1, 5)
        
        # 任务工作路径
        path_label = QLabel("工作路径:")
        path_label.setStyleSheet(form_label_style)
        task_form_grid.addWidget(path_label, 4, 0)
        task_path_layout = QHBoxLayout()
        task_path_layout.setSpacing(8)
        self.task_path_edit = QLineEdit()
        self.task_path_edit.setPlaceholderText("选择任务工作文件夹...")
        self.task_path_edit.setStyleSheet(form_input_style)
        task_path_layout.addWidget(self.task_path_edit)
        
        task_select_path_btn = QPushButton("选择")
        task_select_path_btn.clicked.connect(self.select_task_path)
        task_select_path_btn.setMinimumWidth(80)
        task_select_path_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 500;
                background-color: #f5f5f5;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        task_path_layout.addWidget(task_select_path_btn)
        
        task_open_path_btn = QPushButton("打开")
        task_open_path_btn.clicked.connect(self.open_task_path)
        task_open_path_btn.setMinimumWidth(80)
        task_open_path_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 500;
                background-color: #107c10;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
        """)
        task_path_layout.addWidget(task_open_path_btn)
        
        task_form_grid.addLayout(task_path_layout, 4, 1, 1, 5)
        
        task_form_layout.addLayout(task_form_grid)
        
        # 任务表单按钮
        task_form_btn_layout = QHBoxLayout()
        task_form_btn_layout.setSpacing(12)
        task_form_btn_layout.addStretch()
        self.cancel_task_btn = QPushButton("取消")
        self.cancel_task_btn.clicked.connect(self.hide_task_form)
        self.cancel_task_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                background-color: #f5f5f5;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        task_form_btn_layout.addWidget(self.cancel_task_btn)
        self.save_task_btn = QPushButton("保存任务")
        self.save_task_btn.clicked.connect(self.save_task)
        self.save_task_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        task_form_btn_layout.addWidget(self.save_task_btn)
        task_form_layout.addLayout(task_form_btn_layout)
        
        tasks_layout.addWidget(self.task_form_widget)
        
        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels(
            ["任务名称", "开始日期", "截止日期", "状态", "描述", "路径", "操作"]
        )
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tasks_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tasks_table.setColumnWidth(6, 140)  # 操作列固定宽度
        self.tasks_table.setWordWrap(False)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 设置默认行高（增加行高以便更好地显示内容）
        self.tasks_table.verticalHeader().setDefaultSectionSize(40)
        # 为状态列（第4列，索引3）设置自定义委托
        status_delegate = StatusItemDelegate(self.tasks_table)
        self.tasks_table.setItemDelegateForColumn(3, status_delegate)
        self.tasks_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                border: 1px solid #e0e0e0;
                gridline-color: #f0f0f0;
                background-color: #ffffff;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 8px 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1e1e1e;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #1e1e1e;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        tasks_layout.addWidget(self.tasks_table)
        
        detail_splitter.addWidget(tasks_widget)
        
        # 设置分割比例：项目详情占30%，任务列表占70%
        detail_splitter.setSizes([300, 700])
        
        right_layout.addWidget(detail_splitter)
        
        splitter.addWidget(right_widget)
        
        # 设置左右分割比例：左侧30%，右侧70%
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # 初始化任务编辑相关变量
        self.editing_task_id = None
    
    def refresh_projects(self):
        """刷新项目列表"""
        projects = self.db.get_all_projects()  # 不包括已完成和已归档的

        def parse_updated_at(value: str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return datetime(1970, 1, 1)

        sorted_projects = sorted(
            projects,
            key=lambda p: (
                0 if getattr(p, 'is_pinned', False) else 1,
                -parse_updated_at(p.updated_at).timestamp()
            )
        )

        self.current_projects = sorted_projects
        self.projects_table.setRowCount(len(self.current_projects))
        
        for row, project in enumerate(self.current_projects):
            item = QTableWidgetItem(project.name)
            item.setData(Qt.UserRole, project.id)
            if getattr(project, 'is_pinned', False):
                # 使用 setData 设置背景色，这样委托可以正确处理
                item.setData(Qt.BackgroundRole, QColor("#e8f2ff"))
            self.projects_table.setItem(row, 0, item)
    
    def on_project_selected(self):
        """当选择项目时"""
        selected_items = self.projects_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        if row < len(self.current_projects):
            project = self.current_projects[row]
            self.load_project_detail(project.id)
    
    def load_project_detail(self, project_id):
        """加载项目详情"""
        self.current_project_id = project_id
        project = self.db.get_project(project_id)
        
        if not project:
            return
        
        # 加载项目信息
        self.project_name_edit.setText(project.name)
        self.project_desc_edit.setPlainText(project.description or "")
        self.project_path_edit.setText(project.local_path or "")
        is_pinned = getattr(project, 'is_pinned', False)
        self.pin_project_btn.setEnabled(True)
        self.pin_project_btn.setText("取消置顶" if is_pinned else "置顶")
        
        # 启用编辑按钮
        self.save_project_btn.setEnabled(True)
        self.complete_project_btn.setEnabled(True)
        self.archive_project_btn.setEnabled(True)
        self.delete_project_btn.setEnabled(True)
        self.add_task_btn.setEnabled(True)
        
        # 刷新任务列表
        self.refresh_tasks()
    
    def refresh_tasks(self):
        """刷新任务列表"""
        if not self.current_project_id:
            self.tasks_table.setRowCount(0)
            return
        
        tasks = self.db.get_tasks_by_project(self.current_project_id)

        def parse_date(date_str: str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                return datetime.max

        status_priority = {
            'overdue': 0,
            'in_progress': 1,
            'planned': 2,
            'completed': 4
        }

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                status_priority.get(t.status.value, 3),
                parse_date(t.end_date),
                0 if t.is_important else 1,
                0 if t.is_urgent else 1,
                t.name
            )
        )

        self.tasks_table.setRowCount(len(sorted_tasks))
        
        status_map = {
            'planned': '计划中',
            'in_progress': '进行中',
            'completed': '已完成',
            'overdue': '已超时'
        }
        
        status_colors = {
            'planned': '#7f8c8d',  # 更深的灰色，确保白色文字清晰可见
            'in_progress': '#3498db',
            'completed': '#2ecc71',
            'overdue': '#e74c3c'
        }
        
        for i, task in enumerate(sorted_tasks):
            # 任务名称（存储任务ID以便定位）
            name_item = QTableWidgetItem(task.name)
            name_item.setData(Qt.UserRole, task.id)  # 存储任务ID
            self.tasks_table.setItem(i, 0, name_item)
            self.tasks_table.setItem(i, 1, QTableWidgetItem(task.start_date))
            self.tasks_table.setItem(i, 2, QTableWidgetItem(task.end_date))
            
            # 状态（带颜色）
            status_item = QTableWidgetItem(status_map.get(task.status.value, task.status.value))
            status_item.setTextAlignment(Qt.AlignCenter)
            if task.status.value in status_colors:
                color = QColor(status_colors[task.status.value])
                # 使用白色文字，确保在深色背景上清晰可见
                status_item.setForeground(QColor("#ffffff"))
                # 设置背景色，并确保始终显示
                status_item.setBackground(color)
                status_item.setData(Qt.BackgroundRole, color)
                # 设置文本颜色，确保始终可见
                status_item.setData(Qt.ForegroundRole, QColor("#ffffff"))
            else:
                # 如果没有颜色，使用默认的深色文字
                status_item.setForeground(QColor("#1e1e1e"))
                status_item.setBackground(QColor("#ffffff"))
            # 确保状态项不可编辑，保持样式
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.tasks_table.setItem(i, 3, status_item)
            
            # 描述列使用 QLabel 显示完整文本
            desc_text = self.format_task_description(task)
            desc_label = QLabel(desc_text)
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # 垂直居中
            desc_label.setContentsMargins(8, 6, 8, 6)
            desc_label.setStyleSheet("QLabel { font-size: 12px; color: #1e1e1e; }")
            # 设置 size policy 以确保能够正确计算高度
            desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            # 设置最小高度以确保文本能够显示
            desc_label.setMinimumHeight(30)
            self.tasks_table.setCellWidget(i, 4, desc_label)
            
            # 路径按钮
            path_btn_widget = QWidget()
            path_btn_layout = QHBoxLayout(path_btn_widget)
            path_btn_layout.setContentsMargins(0, 0, 0, 0)
            path_btn_layout.addStretch()
            
            if task.local_path:
                open_path_btn = QPushButton("📁")
                open_path_btn.setToolTip(task.local_path)
                open_path_btn.setMinimumWidth(48)
                open_path_btn.setMinimumHeight(32)
                open_path_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0078d4;
                        color: #ffffff;
                        border: none;
                        font-size: 14px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #106ebe;
                    }
                """)
                open_path_btn.clicked.connect(lambda _, path=task.local_path: self.open_path(path))
                path_btn_layout.addWidget(open_path_btn)
            else:
                path_label = QLabel("-")
                path_label.setAlignment(Qt.AlignCenter)
                path_btn_layout.addWidget(path_label)
            
            path_btn_layout.addStretch()
            self.tasks_table.setCellWidget(i, 5, path_btn_widget)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.addStretch()
            btn_layout.setSpacing(6)
            
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda _, tid=task.id: self.edit_task(tid))
            edit_btn.setMinimumWidth(60)
            edit_btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    background-color: #0078d4;
                    color: #ffffff;
                    border: none;
                    min-height: 18px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
            btn_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, tid=task.id: self.delete_task(tid))
            delete_btn.setMinimumWidth(60)
            delete_btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 16px;
                    font-size: 12px;
                    font-weight: 500;
                    background-color: #d13438;
                    color: #ffffff;
                    border: none;
                    min-height: 18px;
                }
                QPushButton:hover {
                    background-color: #c02a2e;
                }
            """)
            btn_layout.addWidget(delete_btn)
            
            btn_layout.addStretch()
            self.tasks_table.setCellWidget(i, 6, btn_widget)
        
        # 所有行设置完成后，统一调整行高
        # 使用 QTimer 延迟调用，确保所有 widget 已完成布局计算
        QTimer.singleShot(10, self._adjust_all_row_heights)
    
    def _adjust_all_row_heights(self):
        """调整所有行的行高以适应内容"""
        for row in range(self.tasks_table.rowCount()):
            self.tasks_table.resizeRowToContents(row)
    
    def format_task_description(self, task) -> str:
        """返回任务描述文本"""
        if task.description and task.description.strip():
            return task.description.strip()
        return "-"
    
    def create_project(self):
        """创建新项目"""
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建项目", "项目名称:")
        if ok and name:
            project_id = self.db.create_project(name)
            self.refresh_projects()
            # 自动选中新创建的项目
            self.load_project_detail(project_id)
            # 选中新项目
            projects = self.db.get_all_projects()
            for i, p in enumerate(projects):
                if p.id == project_id:
                    self.projects_table.selectRow(i)
                    break
    
    def select_project_path(self):
        """选择项目工作路径"""
        path = QFileDialog.getExistingDirectory(self, "选择项目工作文件夹", 
                                                self.project_path_edit.text() or os.path.expanduser("~"))
        if path:
            self.project_path_edit.setText(path)
    
    def open_project_path(self):
        """打开项目工作路径"""
        path = self.project_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先选择或输入工作路径！")
            return
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "错误", f"路径不存在：\n{path}")
            return
        
        # 使用系统默认方式打开文件夹（跨平台）
        try:
            # QDesktopServices.openUrl 在所有平台（Windows/macOS/Linux）都能工作
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开路径：\n{str(e)}")
    
    def save_project_info(self):
        """保存项目信息"""
        if not self.current_project_id:
            return
        
        self.db.update_project(
            self.current_project_id,
            name=self.project_name_edit.text(),
            description=self.project_desc_edit.toPlainText(),
            local_path=self.project_path_edit.text().strip()
        )
        
        # 刷新项目列表和任务列表
        self.refresh_projects()
        self.refresh_tasks()
    
    def complete_current_project(self):
        """完成当前项目"""
        if not self.current_project_id:
            return
        
        reply = QMessageBox.question(self, "确认完成", "确定要完成该项目吗？\n所有任务将自动标记为已完成，项目将移到历史栏。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.complete_project(self.current_project_id)
            self.current_project_id = None
            
            # 清空详情区域
            self.project_name_edit.clear()
            self.project_desc_edit.clear()
            self.project_path_edit.clear()
            self.save_project_btn.setEnabled(False)
            self.complete_project_btn.setEnabled(False)
            self.archive_project_btn.setEnabled(False)
            self.delete_project_btn.setEnabled(False)
            self.add_task_btn.setEnabled(False)
            self.pin_project_btn.setEnabled(False)
            self.pin_project_btn.setText("置顶")
            self.tasks_table.setRowCount(0)
            self.hide_task_form()
            
            self.refresh_projects()
            # 通知主窗口刷新历史页面
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'history_page'):
                    self.main_window.history_page.refresh_projects()
    
    def archive_current_project(self):
        """归档当前项目"""
        if not self.current_project_id:
            return
        
        reply = QMessageBox.question(self, "确认归档", "确定要归档该项目吗？\n项目将移到历史栏，可以稍后恢复。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.archive_project(self.current_project_id)
            self.current_project_id = None
            
            # 清空详情区域
            self.project_name_edit.clear()
            self.project_desc_edit.clear()
            self.project_path_edit.clear()
            self.save_project_btn.setEnabled(False)
            self.complete_project_btn.setEnabled(False)
            self.archive_project_btn.setEnabled(False)
            self.delete_project_btn.setEnabled(False)
            self.add_task_btn.setEnabled(False)
            self.pin_project_btn.setEnabled(False)
            self.pin_project_btn.setText("置顶")
            self.tasks_table.setRowCount(0)
            self.hide_task_form()
            
            self.refresh_projects()
            # 通知主窗口刷新历史页面
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'history_page'):
                    self.main_window.history_page.refresh_projects()
    
    def delete_current_project(self):
        """删除当前项目"""
        if not self.current_project_id:
            return
        
        reply = QMessageBox.question(self, "确认删除", "确定要删除该项目及其所有任务吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_project(self.current_project_id)
            self.current_project_id = None
            
            # 清空详情区域
            self.project_name_edit.clear()
            self.project_desc_edit.clear()
            self.project_path_edit.clear()
            self.save_project_btn.setEnabled(False)
            self.complete_project_btn.setEnabled(False)
            self.archive_project_btn.setEnabled(False)
            self.delete_project_btn.setEnabled(False)
            self.add_task_btn.setEnabled(False)
            self.pin_project_btn.setEnabled(False)
            self.pin_project_btn.setText("置顶")
            self.tasks_table.setRowCount(0)
            self.hide_task_form()
            
            self.refresh_projects()
    
    def select_task_path(self):
        """选择任务工作路径"""
        current_path = self.task_path_edit.text().strip()
        project_path = self.project_path_edit.text().strip()
        initial_dir = current_path or project_path or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(
            self,
            "选择任务工作文件夹",
            initial_dir
        )
        if path:
            self.task_path_edit.setText(path)
    
    def open_task_path(self):
        """打开任务工作路径"""
        path = self.task_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先选择或输入工作路径！")
            return
        
        self.open_path(path)
    
    def open_path(self, path: str):
        """打开指定路径（通用方法）"""
        if not path or not path.strip():
            QMessageBox.warning(self, "提示", "路径为空！")
            return
        
        path = path.strip()
        if not os.path.exists(path):
            QMessageBox.warning(self, "错误", f"路径不存在：\n{path}")
            return
        
        # 使用系统默认方式打开文件夹（跨平台）
        try:
            # QDesktopServices.openUrl 在所有平台（Windows/macOS/Linux）都能工作
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开路径：\n{str(e)}")
    
    def show_task_form(self):
        """显示任务表单（新建模式）"""
        self.editing_task_id = None
        self.task_name_edit.clear()
        self.task_start_date.setDate(QDate.currentDate())
        self.task_end_date.setDate(QDate.currentDate().addDays(7))
        if hasattr(self, 'task_status_label'):
            self.task_status_label.setText("（根据时间自动设置）")
        self.task_desc_edit.clear()
        project_path = self.project_path_edit.text().strip()
        if project_path:
            self.task_path_edit.setText(project_path)
        else:
            self.task_path_edit.clear()
        # 重置标签
        self.task_important_check.setChecked(False)
        self.task_urgent_check.setChecked(False)
        self.task_form_widget.setVisible(True)
        self.task_form_widget.setTitle("新建任务")
    
    def hide_task_form(self):
        """隐藏任务表单"""
        self.task_form_widget.setVisible(False)
        self.editing_task_id = None
    
    def edit_task(self, task_id):
        """编辑任务"""
        if not self.current_project_id:
            return
        
        tasks = self.db.get_tasks_by_project(self.current_project_id)
        task = next((t for t in tasks if t.id == task_id), None)
        
        if not task:
            return
        
        self.editing_task_id = task_id
        self.task_name_edit.setText(task.name)
        
        start_date = QDate.fromString(task.start_date, "yyyy-MM-dd")
        if start_date.isValid():
            self.task_start_date.setDate(start_date)
        
        end_date = QDate.fromString(task.end_date, "yyyy-MM-dd")
        if end_date.isValid():
            self.task_end_date.setDate(end_date)
        
        # 显示当前状态（只读）
        status_map = {
            'planned': '计划中',
            'in_progress': '进行中',
            'completed': '已完成',
            'overdue': '已超时'
        }
        if hasattr(self, 'task_status_label'):
            status_text = status_map.get(task.status.value, task.status.value)
            self.task_status_label.setText(f"当前状态: {status_text}（根据时间自动设置）")
        self.task_desc_edit.setPlainText(task.description or "")
        self.task_path_edit.setText(task.local_path or "")
        
        # 设置标签
        self.task_important_check.setChecked(task.is_important)
        self.task_urgent_check.setChecked(task.is_urgent)
        
        self.task_form_widget.setVisible(True)
        self.task_form_widget.setTitle("编辑任务")
    
    def save_task(self):
        """保存任务"""
        if not self.current_project_id:
            return
        
        # 验证必填字段
        if not self.task_name_edit.text().strip():
            QMessageBox.warning(self, "错误", "请输入任务名称！")
            return
        
        # 验证日期
        start_date = self.task_start_date.date().toString("yyyy-MM-dd")
        end_date = self.task_end_date.date().toString("yyyy-MM-dd")
        
        if self.task_start_date.date() > self.task_end_date.date():
            QMessageBox.warning(self, "错误", "开始日期不能晚于截止日期！")
            return
        
        # 获取标签值
        is_important = self.task_important_check.isChecked()
        is_urgent = self.task_urgent_check.isChecked()
        
        # 保存到数据库（状态会根据时间自动更新）
        if self.editing_task_id:
            # 更新任务（不更新状态，状态会自动更新）
            self.db.update_task(
                self.editing_task_id,
                name=self.task_name_edit.text().strip(),
                start_date=start_date,
                end_date=end_date,
                description=self.task_desc_edit.toPlainText(),
                notes="",
                local_path=self.task_path_edit.text().strip(),
                is_important=is_important,
                is_urgent=is_urgent
            )
            # 更新后自动刷新状态
            self.db.update_task_status_auto()
        else:
            # 创建新任务（状态会根据时间自动设置）
            self.db.create_task(
                self.current_project_id,
                self.task_name_edit.text().strip(),
                start_date,
                end_date,
                self.task_desc_edit.toPlainText(),
                "",
                self.task_path_edit.text().strip(),
                is_important=is_important,
                is_urgent=is_urgent
            )
            # 创建后自动更新状态
            self.db.update_task_status_auto()
        
        # 刷新任务列表并隐藏表单
        self.refresh_tasks()
        # 刷新项目列表以反映任务状态变化
        self.refresh_projects()
        self._reselect_current_project()
        # 通知总览页面刷新数据
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'overview_page'):
                self.main_window.overview_page.refresh_data()
        self.hide_task_form()
    
    def delete_task(self, task_id):
        """删除任务"""
        reply = QMessageBox.question(self, "确认删除", "确定要删除该任务吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_task(task_id)
            self.refresh_tasks()

    def _reselect_current_project(self):
        """刷新项目列表后重新选中当前项目"""
        if not self.current_project_id:
            return
        for row, project in enumerate(self.current_projects):
            if project.id == self.current_project_id:
                self.projects_table.selectRow(row)
                break
    
    def select_project_and_task(self, project_id: str, task_id: str = None):
        """选择项目并定位到指定任务（用于从总览页面跳转）"""
        # 先刷新项目列表，确保项目在列表中
        self.refresh_projects()
        
        # 在项目列表中找到并选中指定的项目
        project_row = -1
        for i, project in enumerate(self.current_projects):
            if project.id == project_id:
                project_row = i
                break
        
        if project_row < 0:
            # 项目不在列表中（可能是已完成或已归档的项目）
            QMessageBox.warning(self, "提示", "该项目不在当前项目列表中，可能已完成或已归档。")
            return
        
        # 选中项目
        self.projects_table.selectRow(project_row)
        # 加载项目详情（这会刷新任务列表）
        self.load_project_detail(project_id)
        
        # 如果指定了任务ID，定位到该任务
        if task_id:
            # 等待任务列表刷新完成后再定位
            QTimer.singleShot(100, lambda: self._scroll_to_task(task_id))
    
    def _scroll_to_task(self, task_id: str):
        """滚动到指定的任务行"""
        if not self.current_project_id:
            return
        
        # 在任务表格中查找任务
        for row in range(self.tasks_table.rowCount()):
            name_item = self.tasks_table.item(row, 0)
            if name_item:
                stored_task_id = name_item.data(Qt.UserRole)
                if stored_task_id == task_id:
                    # 选中该行并滚动到可见区域
                    self.tasks_table.selectRow(row)
                    self.tasks_table.scrollToItem(name_item)
                    # 高亮显示（可选）
                    self.tasks_table.setCurrentCell(row, 0)
                    return

    def toggle_pin_project(self):
        """切换项目置顶状态"""
        if not self.current_project_id:
            return

        project = self.db.get_project(self.current_project_id)
        if not project:
            return

        new_state = not getattr(project, 'is_pinned', False)
        self.db.update_project(self.current_project_id, is_pinned=new_state)

        # 刷新列表和详情
        self.refresh_projects()
        self._reselect_current_project()
        self.load_project_detail(self.current_project_id)
        
        # 通知其他页面刷新数据
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'overview_page'):
                self.main_window.overview_page.refresh_data()
