from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QComboBox, QPushButton,
                               QDateEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from database import Database
from models import Status, Task

class TaskDialog(QDialog):
    def __init__(self, db: Database, project_id: str, parent=None, task_id: str = None):
        super().__init__(parent)
        self.db = db
        self.project_id = project_id
        self.task_id = task_id
        self.task = None
        
        if task_id:
            # 编辑模式：获取任务信息
            tasks = self.db.get_tasks_by_project(project_id)
            self.task = next((t for t in tasks if t.id == task_id), None)
            if not self.task:
                QMessageBox.warning(self, "错误", "找不到该任务！")
                self.reject()
                return
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if self.task:
            self.setWindowTitle("编辑任务")
        else:
            self.setWindowTitle("新建任务")
        
        self.setMinimumWidth(550)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        label_style = "font-size: 14px; font-weight: 500; color: #1e1e1e;"
        input_style = """
            QLineEdit, QTextEdit, QComboBox, QDateEdit {
                font-size: 14px;
                padding: 8px 12px;
                border: 2px solid #e0e0e0;
                background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """
        
        # 任务名称
        name_label = QLabel("任务名称 *")
        name_label.setStyleSheet(label_style)
        layout.addWidget(name_label)
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(input_style)
        if self.task:
            self.name_edit.setText(self.task.name)
        layout.addWidget(self.name_edit)
        
        # 开始日期
        start_label = QLabel("开始日期 *")
        start_label.setStyleSheet(label_style)
        layout.addWidget(start_label)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setStyleSheet(input_style)
        if self.task:
            start_date = QDate.fromString(self.task.start_date, "yyyy-MM-dd")
            if start_date.isValid():
                self.start_date_edit.setDate(start_date)
        layout.addWidget(self.start_date_edit)
        
        # 截止日期
        end_label = QLabel("截止日期 *")
        end_label.setStyleSheet(label_style)
        layout.addWidget(end_label)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.setStyleSheet(input_style)
        if self.task:
            end_date = QDate.fromString(self.task.end_date, "yyyy-MM-dd")
            if end_date.isValid():
                self.end_date_edit.setDate(end_date)
        layout.addWidget(self.end_date_edit)
        
        # 状态
        status_label = QLabel("状态")
        status_label.setStyleSheet(label_style)
        layout.addWidget(status_label)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["计划中", "进行中", "已完成"])
        self.status_combo.setStyleSheet(input_style)
        if self.task:
            status_map = {"planned": 0, "in_progress": 1, "completed": 2}
            self.status_combo.setCurrentIndex(status_map[self.task.status.value])
        layout.addWidget(self.status_combo)
        
        # 描述
        desc_label = QLabel("描述")
        desc_label.setStyleSheet(label_style)
        layout.addWidget(desc_label)
        self.desc_edit = QTextEdit()
        self.desc_edit.setStyleSheet(input_style)
        if self.task:
            self.desc_edit.setPlainText(self.task.description)
        self.desc_edit.setMaximumHeight(100)
        layout.addWidget(self.desc_edit)
        
        # 备注
        notes_label = QLabel("备注")
        notes_label.setStyleSheet(label_style)
        layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(input_style)
        if self.task:
            self.notes_edit.setPlainText(self.task.notes)
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
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
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_task)
        save_btn.setStyleSheet("""
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
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def save_task(self):
        """保存任务"""
        # 验证必填字段
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "错误", "请输入任务名称！")
            return
        
        # 验证日期
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "错误", "开始日期不能晚于截止日期！")
            return
        
        # 获取状态
        status_map = {0: "planned", 1: "in_progress", 2: "completed"}
        status = status_map[self.status_combo.currentIndex()]
        
        # 保存到数据库
        if self.task:
            # 更新任务
            self.db.update_task(
                self.task_id,
                name=self.name_edit.text().strip(),
                start_date=start_date,
                end_date=end_date,
                status=status,
                description=self.desc_edit.toPlainText(),
                notes=self.notes_edit.toPlainText()
            )
        else:
            # 创建新任务
            self.db.create_task(
                self.project_id,
                self.name_edit.text().strip(),
                start_date,
                end_date,
                self.desc_edit.toPlainText(),
                self.notes_edit.toPlainText()
            )
        
        QMessageBox.information(self, "成功", "任务已保存！")
        self.accept()

