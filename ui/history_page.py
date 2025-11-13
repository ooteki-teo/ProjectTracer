from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QAbstractItemView, QSplitter,
                               QLabel, QLineEdit, QTextEdit, QComboBox,
                               QGroupBox, QGridLayout, QTableWidget)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from database import Database
import os

class HistoryPage(QWidget):
    def __init__(self, db: Database, main_window=None):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.current_project_id = None
        self.init_ui()
        self.refresh_projects()
    
    def init_ui(self):
        """初始化UI - 左右分栏布局（类似项目列表）"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== 左侧：历史项目列表 ==========
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 已完成项目列表
        completed_group = QGroupBox("已完成项目")
        completed_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #2196f3;
                border-radius: 6px;
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
        completed_layout = QVBoxLayout(completed_group)
        completed_layout.setContentsMargins(8, 12, 8, 8)
        completed_layout.setSpacing(8)

        self.completed_table = QTableWidget()
        self.completed_table.setColumnCount(1)
        self.completed_table.setHorizontalHeaderLabels(["项目名称"])
        self.completed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.completed_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.completed_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.completed_table.itemSelectionChanged.connect(self.on_completed_project_selected)
        self.completed_table.setMinimumWidth(250)
        self.completed_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                border: 1px solid #bbdefb;
                gridline-color: #e3f2fd;
                background-color: #ffffff;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 10px 6px;
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
            }
        """)
        completed_layout.addWidget(self.completed_table)
        left_layout.addWidget(completed_group)

        # 归档项目列表
        archived_group = QGroupBox("归档项目")
        archived_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #ef9a9a;
                border-radius: 6px;
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
        archived_layout = QVBoxLayout(archived_group)
        archived_layout.setContentsMargins(8, 12, 8, 8)
        archived_layout.setSpacing(8)

        self.archived_table = QTableWidget()
        self.archived_table.setColumnCount(1)
        self.archived_table.setHorizontalHeaderLabels(["项目名称"])
        self.archived_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.archived_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.archived_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.archived_table.itemSelectionChanged.connect(self.on_archived_project_selected)
        self.archived_table.setMinimumWidth(250)
        self.archived_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                border: 1px solid #ffcdd2;
                gridline-color: #ffe5e9;
                background-color: #ffffff;
                selection-background-color: #ffe5e9;
            }
            QTableWidget::item {
                padding: 10px 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #ffe5e9;
                color: #1e1e1e;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #1e1e1e;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 6px;
                border: none;
            }
        """)
        archived_layout.addWidget(self.archived_table)
        left_layout.addWidget(archived_group)
        
        splitter.addWidget(left_widget)
        
        # ========== 右侧：详情区域 ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 创建垂直分割器：上方项目详情，下方任务列表
        detail_splitter = QSplitter(Qt.Vertical)
        
        # 上方：项目详情（只读）
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
        
        # 项目信息表单（只读）
        info_grid = QGridLayout()
        info_grid.setSpacing(10)
        info_grid.setColumnMinimumWidth(0, 80)
        
        label_style = "font-size: 14px; font-weight: 500; color: #1e1e1e;"
        value_style = "font-size: 14px; color: #1e1e1e; padding: 6px; background-color: #f8f8f8; border: 1px solid #e0e0e0;"
        
        name_label = QLabel("项目名称:")
        name_label.setStyleSheet(label_style)
        info_grid.addWidget(name_label, 0, 0)
        self.project_name_label = QLabel("选择项目以查看...")
        self.project_name_label.setStyleSheet(value_style)
        info_grid.addWidget(self.project_name_label, 0, 1)
        
        status_label = QLabel("状态:")
        status_label.setStyleSheet(label_style)
        info_grid.addWidget(status_label, 1, 0)
        self.project_status_label = QLabel("")
        self.project_status_label.setStyleSheet(value_style)
        info_grid.addWidget(self.project_status_label, 1, 1)
        
        desc_label = QLabel("描述:")
        desc_label.setStyleSheet(label_style)
        info_grid.addWidget(desc_label, 2, 0)
        self.project_desc_label = QLabel("")
        self.project_desc_label.setWordWrap(True)
        self.project_desc_label.setStyleSheet(value_style)
        info_grid.addWidget(self.project_desc_label, 2, 1)
        
        # 工作路径
        path_label = QLabel("工作路径:")
        path_label.setStyleSheet(label_style)
        info_grid.addWidget(path_label, 3, 0)
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        self.project_path_label = QLabel("")
        self.project_path_label.setWordWrap(True)
        self.project_path_label.setStyleSheet(value_style)
        path_layout.addWidget(self.project_path_label, 1)
        
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
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        open_path_btn.setEnabled(False)
        self.open_project_path_btn = open_path_btn
        path_layout.addWidget(open_path_btn)
        
        info_grid.addLayout(path_layout, 3, 1)
        
        project_info_layout.addLayout(info_grid)
        
        # 项目操作按钮（只对归档项目显示恢复按钮）
        project_btn_layout = QHBoxLayout()
        project_btn_layout.setSpacing(10)
        
        self.restore_project_btn = QPushButton("恢复项目")
        self.restore_project_btn.clicked.connect(self.restore_current_project)
        self.restore_project_btn.setEnabled(False)
        self.restore_project_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                background-color: #107c10;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0e6e0e;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        project_btn_layout.addWidget(self.restore_project_btn)

        self.delete_project_btn = QPushButton("删除项目")
        self.delete_project_btn.clicked.connect(self.delete_current_project)
        self.delete_project_btn.setEnabled(False)
        self.delete_project_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 500;
                background-color: #d13438;
                color: #ffffff;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #c02a2e;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #9e9e9e;
            }
        """)
        project_btn_layout.addWidget(self.delete_project_btn)
        
        project_btn_layout.addStretch()
        project_info_layout.addLayout(project_btn_layout)
        
        detail_splitter.addWidget(project_info_widget)
        
        # 下方：任务列表（只读，不能添加任务）
        tasks_widget = QGroupBox("任务列表（只读）")
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
        
        # 任务表格
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels(
            ["任务名称", "开始日期", "截止日期", "状态", "备注", "路径"]
        )
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 只读
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
    
    def refresh_projects(self):
        """刷新历史项目列表"""
        projects = self.db.get_history_projects()

        self.completed_projects = [p for p in projects if p.status == 'completed']
        self.archived_projects = [p for p in projects if p.status == 'archived']

        self.completed_table.setRowCount(len(self.completed_projects))
        for row, project in enumerate(self.completed_projects):
            self.completed_table.setItem(row, 0, QTableWidgetItem(project.name))

        self.archived_table.setRowCount(len(self.archived_projects))
        for row, project in enumerate(self.archived_projects):
            self.archived_table.setItem(row, 0, QTableWidgetItem(project.name))

        self._reselect_current_project()
    
    def on_project_selected(self):
        """当选择项目时"""
        pass

    def on_completed_project_selected(self):
        selected_items = self.completed_table.selectedItems()
        if not selected_items:
            return

        # 清除归档表的选择
        self.archived_table.blockSignals(True)
        self.archived_table.clearSelection()
        self.archived_table.blockSignals(False)

        row = selected_items[0].row()
        if row < len(self.completed_projects):
            project = self.completed_projects[row]
            self.load_project_detail(project.id)

    def on_archived_project_selected(self):
        selected_items = self.archived_table.selectedItems()
        if not selected_items:
            return

        # 清除完成表的选择
        self.completed_table.blockSignals(True)
        self.completed_table.clearSelection()
        self.completed_table.blockSignals(False)

        row = selected_items[0].row()
        if row < len(self.archived_projects):
            project = self.archived_projects[row]
            self.load_project_detail(project.id)
    
    def load_project_detail(self, project_id: str):
        """加载项目详情"""
        self.current_project_id = project_id
        project = self.db.get_project(project_id)
        
        if not project:
            return
        
        # 加载项目信息（只读）
        self.project_name_label.setText(project.name)
        
        status_map = {
            'planned': '计划中',
            'in_progress': '进行中',
            'completed': '已完成',
            'archived': '已归档'
        }
        self.project_status_label.setText(status_map.get(project.status, project.status))
        self.project_desc_label.setText(project.description or "无描述")
        
        # 工作路径
        project_path = project.local_path or ""
        self.project_path_label.setText(project_path if project_path else "未设置")
        self.open_project_path_btn.setEnabled(bool(project_path))
        
        # 已完成和已归档项目都可以恢复
        self.restore_project_btn.setEnabled(project.status in ('archived', 'completed'))
        self.delete_project_btn.setEnabled(project.status in ('archived', 'completed'))
        
        # 刷新任务列表
        self.refresh_tasks()
    
    def refresh_tasks(self):
        """刷新任务列表（只读）"""
        if not self.current_project_id:
            self.tasks_table.setRowCount(0)
            return
        
        tasks = self.db.get_tasks_by_project(self.current_project_id)
        self.tasks_table.setRowCount(len(tasks))
        
        status_map = {
            'planned': '计划中',
            'in_progress': '进行中',
            'completed': '已完成',
            'overdue': '已超时'
        }
        
        status_colors = {
            'planned': '#95a5a6',
            'in_progress': '#3498db',
            'completed': '#2ecc71',
            'overdue': '#e74c3c'
        }
        
        for i, task in enumerate(tasks):
            self.tasks_table.setItem(i, 0, QTableWidgetItem(task.name))
            self.tasks_table.setItem(i, 1, QTableWidgetItem(task.start_date))
            self.tasks_table.setItem(i, 2, QTableWidgetItem(task.end_date))
            
            # 状态（带颜色）
            status_item = QTableWidgetItem(status_map.get(task.status.value, task.status.value))
            if task.status.value in status_colors:
                from PySide6.QtGui import QColor
                color = QColor(status_colors[task.status.value])
                status_item.setForeground(Qt.white)
                status_item.setBackground(color)
            self.tasks_table.setItem(i, 3, status_item)
            self.tasks_table.setItem(i, 4, QTableWidgetItem(task.notes[:30] if task.notes else ""))
            
            # 路径按钮
            path_btn_widget = QWidget()
            path_btn_layout = QHBoxLayout(path_btn_widget)
            path_btn_layout.setContentsMargins(2, 2, 2, 2)
            
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
            
            self.tasks_table.setCellWidget(i, 5, path_btn_widget)
    
    def open_project_path(self):
        """打开项目工作路径"""
        if not self.current_project_id:
            return
        
        project = self.db.get_project(self.current_project_id)
        if project and project.local_path:
            self.open_path(project.local_path)
        else:
            QMessageBox.warning(self, "提示", "该项目未设置工作路径！")
    
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
    
    def restore_current_project(self):
        """恢复项目：从历史恢复到项目列表"""
        if not self.current_project_id:
            return
        
        reply = QMessageBox.question(self, "确认恢复", "确定要恢复该项目吗？\n项目将恢复到项目列表，状态设为进行中。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.restore_project(self.current_project_id)
            self.current_project_id = None
            
            self._clear_details()
            self.refresh_projects()
            # 通知主窗口刷新项目列表页面
            if self.main_window and hasattr(self.main_window, 'project_list_page'):
                self.main_window.project_list_page.refresh_projects()
            if self.main_window and hasattr(self.main_window, 'overview_page'):
                self.main_window.overview_page.refresh_data()

    def delete_current_project(self):
        """删除历史项目"""
        if not self.current_project_id:
            return

        reply = QMessageBox.question(self, "确认删除", "确定要永久删除该项目及其所有任务吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_project(self.current_project_id)
            self.current_project_id = None

            self._clear_details()
            self.refresh_projects()

            # 通知主窗口刷新其他页面
            if self.main_window:
                if hasattr(self.main_window, 'project_list_page'):
                    self.main_window.project_list_page.refresh_projects()
                if hasattr(self.main_window, 'overview_page'):
                    self.main_window.overview_page.refresh_data()
                if hasattr(self.main_window, 'history_page'):
                    self.main_window.history_page.refresh_projects()

    def _clear_details(self):
        self.project_name_label.setText("选择项目以查看...")
        self.project_status_label.setText("")
        self.project_desc_label.setText("")
        self.project_path_label.setText("未设置")
        self.open_project_path_btn.setEnabled(False)
        self.restore_project_btn.setEnabled(False)
        self.delete_project_btn.setEnabled(False)
        self.tasks_table.setRowCount(0)
        self.completed_table.blockSignals(True)
        self.completed_table.clearSelection()
        self.completed_table.blockSignals(False)
        self.archived_table.blockSignals(True)
        self.archived_table.clearSelection()
        self.archived_table.blockSignals(False)

    def _reselect_current_project(self):
        if not self.current_project_id:
            return

        # 在已完成项目中查找
        for row, project in enumerate(self.completed_projects):
            if project.id == self.current_project_id:
                self.completed_table.blockSignals(True)
                self.completed_table.selectRow(row)
                self.completed_table.blockSignals(False)
                return

        # 在归档项目中查找
        for row, project in enumerate(self.archived_projects):
            if project.id == self.current_project_id:
                self.archived_table.blockSignals(True)
                self.archived_table.selectRow(row)
                self.archived_table.blockSignals(False)
                return

