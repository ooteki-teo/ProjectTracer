from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QFrame, QAbstractItemView, QHeaderView,
                               QStyledItemDelegate, QStyleOptionViewItem, QGridLayout,
                               QListWidget, QListWidgetItem, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QMimeData, QByteArray, QDataStream, QIODevice, QSize
from PySide6.QtGui import QColor, QPainter, QDragEnterEvent, QDropEvent
from database import Database
from datetime import datetime
from models import Status

class TaskItemWidget(QWidget):
    """任务项自定义 widget，包含任务信息和完成按钮"""
    def __init__(self, task, project_name, overview_page, parent=None):
        super().__init__(parent)
        self.task = task
        self.overview_page = overview_page
        self._has_description = bool(task.description)

        # 设置样式和背景
        self.setObjectName("taskItemWidget")
        self.setStyleSheet(
            """
            QWidget#taskItemWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            """
        )
        
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # 左侧：任务信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 任务名称
        name_label = QLabel(task.name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #1e1e1e;
            }
        """)
        info_layout.addWidget(name_label)
        
        # 项目、日期、状态信息
        status_map = {
            'planned': '计划中',
            'in_progress': '进行中',
            'completed': '已完成',
            'overdue': '已超时'
        }
        status_text = status_map.get(task.status.value, task.status.value)
        
        detail_text = f"📁 {project_name} | 📅 {task.start_date} ~ {task.end_date} | {status_text}"
        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #666666;
            }
        """)
        info_layout.addWidget(detail_label)
        
        # 描述（如果有）
        if task.description:
            desc = task.description[:40] + "..." if len(task.description) > 40 else task.description
            desc_label = QLabel(f"📝 {desc}")
            desc_label.setStyleSheet("""
                QLabel {
                    font-size: 11px;
                    color: #888888;
                }
            """)
            info_layout.addWidget(desc_label)
        
        # 根据状态设置颜色
        if task.status.value == 'completed':
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: 500;
                    color: #2ecc71;
                }
            """)
        elif task.status.value == 'overdue':
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: 500;
                    color: #e74c3c;
                }
            """)
        elif task.status.value == 'in_progress':
            name_label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: 500;
                    color: #3498db;
                }
            """)
        
        main_layout.addLayout(info_layout, 1)
        
        # 右侧：完成按钮（如果任务未完成）
        if task.status.value != 'completed':
            complete_btn = QPushButton("✓ 完成")
            complete_btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    background-color: #2ecc71;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #229954;
                }
            """)
            complete_btn.clicked.connect(self.on_complete_clicked)
            main_layout.addWidget(complete_btn)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def sizeHint(self):
        base_height = 68
        if self._has_description:
            base_height += 20
        return QSize(0, base_height)

    def on_complete_clicked(self):
        """完成按钮点击事件"""
        if self.task and self.overview_page:
            # 更新任务状态为完成
            self.overview_page.db.update_task(
                self.task.id,
                status=Status.COMPLETED.value
            )
            # 刷新数据显示
            self.overview_page.refresh_data()

class DraggableTaskListWidget(QListWidget):
    """可拖拽的任务列表组件"""
    def __init__(self, quadrant_widget, overview_page, parent=None):
        super().__init__(parent)
        self.quadrant_widget = quadrant_widget  # 所属象限
        self.overview_page = overview_page  # 总览页面引用
        # 启用拖拽
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        # 存储正在拖拽的项
        self.dragged_item = None
    
    def startDrag(self, supportedActions):
        """开始拖拽时保存被拖拽的项"""
        self.dragged_item = self.currentItem()
        super().startDrag(supportedActions)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            # 获取源列表
            source_list = None
            if event.source() and isinstance(event.source(), DraggableTaskListWidget):
                source_list = event.source()
            
            # 如果是在同一个列表中移动，不处理（因为标签没变）
            if source_list == self:
                # 允许在同一列表内移动位置（虽然不会改变标签）
                super().dropEvent(event)
                return
            
            # 从 MimeData 中解析被拖拽的项
            mime_data = event.mimeData()
            byte_array = mime_data.data("application/x-qabstractitemmodeldatalist")
            data_stream = QDataStream(byte_array, QIODevice.ReadOnly)
            
            # 读取数据
            row = -1
            col = -1
            data_map = {}
            
            while not data_stream.atEnd():
                data_stream >> row >> col >> data_map
            
            # 从源列表获取被拖拽的项
            source_item = None
            if source_list and row >= 0:
                source_item = source_list.item(row)
            
            # 如果还是找不到，尝试使用当前项
            if not source_item and source_list:
                source_item = source_list.currentItem()
            
            if source_item:
                task_id = source_item.data(Qt.UserRole)
                if task_id:
                    # 获取目标象限的标签
                    target_is_important = self.quadrant_widget.is_important
                    target_is_urgent = self.quadrant_widget.is_urgent
                    
                    # 更新任务的标签
                    self.overview_page.db.update_task(
                        task_id,
                        is_important=target_is_important,
                        is_urgent=target_is_urgent
                    )
                    
                    # 刷新所有象限的显示
                    self.overview_page.refresh_data()
                    
                    event.acceptProposedAction()
                    return
        
        event.ignore()

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
            if option.state & QStyleOptionViewItem.State_Selected:
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

class OverviewPage(QWidget):
    def __init__(self, db: Database, main_window=None):
        super().__init__()
        self.db = db
        self.main_window = main_window  # 用于跳转到项目详情
        self.init_ui()
        self.refresh_data()
        
        # 定时刷新（每30秒）
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)
    
    def init_ui(self):
        """初始化UI - 左右分栏：左侧统计，右侧今日任务"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== 左侧：统计信息 ==========
        stats_widget = QGroupBox("统计信息")
        stats_widget.setStyleSheet("""
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
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(12, 18, 12, 12)
        
        # 定义统计项的颜色
        self.stats_colors = {
            'total_projects': '#3498db',
            'active_projects': '#2ecc71',
            'total_tasks': '#9b59b6',
            'active_tasks': '#f39c12',
            'overdue_tasks': '#e74c3c',
            'today_tasks': '#16a085'
        }
        
        # 总项目数
        self.total_projects_widget = self.create_stat_item("总项目数: 0", self.stats_colors['total_projects'])
        stats_layout.addWidget(self.total_projects_widget)
        
        # 进行中项目数
        self.active_projects_widget = self.create_stat_item("进行中项目: 0", self.stats_colors['active_projects'])
        stats_layout.addWidget(self.active_projects_widget)
        
        # 总任务数
        self.total_tasks_widget = self.create_stat_item("总任务数: 0", self.stats_colors['total_tasks'])
        stats_layout.addWidget(self.total_tasks_widget)
        
        # 进行中任务数
        self.active_tasks_widget = self.create_stat_item("进行中任务: 0", self.stats_colors['active_tasks'])
        stats_layout.addWidget(self.active_tasks_widget)
        
        # 已超时任务数
        self.overdue_tasks_widget = self.create_stat_item("已超时任务: 0", self.stats_colors['overdue_tasks'])
        stats_layout.addWidget(self.overdue_tasks_widget)
        
        # 今日任务数
        self.today_tasks_widget = self.create_stat_item("今日任务: 0", self.stats_colors['today_tasks'])
        stats_layout.addWidget(self.today_tasks_widget)
        
        stats_layout.addStretch()
        splitter.addWidget(stats_widget)
        
        # ========== 右侧：任务分类（按象限） ==========
        tasks_widget = QGroupBox("今日任务")
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
        
        # 添加提示标签
        hint_label = QLabel("💡 提示：可以拖拽任务到不同象限来更改标签（重要/紧急）")
        hint_label.setStyleSheet("font-size: 12px; color: #666666; padding: 4px 0;")
        hint_label.setWordWrap(True)
        tasks_layout.addWidget(hint_label)
        
        # 创建2x2网格布局
        quadrants_grid = QGridLayout()
        quadrants_grid.setSpacing(10)
        
        # 四个象限
        self.quadrant_widgets = {}
        quadrant_configs = [
            ("重要紧急", True, True, 0, 0),
            ("不重要紧急", False, True, 0, 1),
            ("重要不紧急", True, False, 1, 0),
            ("不重要不紧急", False, False, 1, 1)
        ]
        
        for title, is_important, is_urgent, row, col in quadrant_configs:
            quadrant_widget = self.create_quadrant_widget(title, is_important, is_urgent)
            quadrants_grid.addWidget(quadrant_widget, row, col)
            self.quadrant_widgets[(is_important, is_urgent)] = quadrant_widget
        
        tasks_layout.addLayout(quadrants_grid)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.clicked.connect(self.refresh_data)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 18px;
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
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        tasks_layout.addWidget(refresh_btn)
        
        splitter.addWidget(tasks_widget)
        
        # 设置分割比例：左侧30%，右侧70%
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # 缓存任务数据，便于双击跳转
        self.all_tasks_data = []
    
    def create_stat_item(self, text: str, color: str) -> QWidget:
        """创建统计项：左侧小正方形，右侧文字"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border: none;
                padding: 4px;
            }
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # 颜色方块
        color_label = QLabel()
        color_label.setFixedSize(16, 16)
        color_label.setStyleSheet(f"background-color: {color}; border: none;")
        layout.addWidget(color_label)
        
        # 文字标签
        text_label = QLabel(text)
        text_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #1e1e1e;
            }
        """)
        layout.addWidget(text_label)
        layout.addStretch()
        
        # 保存标签引用以便更新
        widget.text_label = text_label
        
        return widget
    
    def create_quadrant_widget(self, title: str, is_important: bool, is_urgent: bool) -> QWidget:
        """创建象限组件"""
        quadrant = QGroupBox(title)
        quadrant.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #1e1e1e;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #fafafa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
        """)
        layout = QVBoxLayout(quadrant)
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        
        # 任务列表（使用可拖拽的 QListWidget）
        task_list = DraggableTaskListWidget(quadrant, self)
        task_list.setStyleSheet("""
            QListWidget {
                font-size: 13px;
                border: 1px solid #e0e0e0;
                background-color: #ffffff;
                border-radius: 2px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1e1e1e;
            }
        """)
        task_list.setSpacing(8)
        # 设置最小高度，确保有足够的拖拽空间
        task_list.setMinimumHeight(150)
        layout.addWidget(task_list)
        
        # 存储任务列表引用
        quadrant.task_list = task_list
        quadrant.is_important = is_important
        quadrant.is_urgent = is_urgent
        
        # 添加双击事件
        task_list.itemDoubleClicked.connect(self.on_quadrant_task_double_clicked)
        
        return quadrant
    
    def refresh_data(self):
        """刷新所有数据"""
        # 获取所有项目和任务
        projects = self.db.get_all_projects()
        all_tasks = []
        for p in projects:
            all_tasks.extend(self.db.get_tasks_by_project(p.id))
        
        self.all_tasks_data = all_tasks
        
        # 获取今日任务（用于统计）
        today_tasks = self.db.get_today_tasks()
        
        # 更新统计信息
        self.total_projects_widget.text_label.setText(f"总项目数: {len(projects)}")
        
        active_projects = sum(1 for p in projects if p.status == 'in_progress')
        self.active_projects_widget.text_label.setText(f"进行中项目: {active_projects}")
        
        self.total_tasks_widget.text_label.setText(f"总任务数: {len(all_tasks)}")
        
        active_tasks = sum(1 for t in all_tasks if t.status.value == 'in_progress')
        self.active_tasks_widget.text_label.setText(f"进行中任务: {active_tasks}")
        
        overdue_tasks = sum(1 for t in all_tasks if t.status.value == 'overdue')
        self.overdue_tasks_widget.text_label.setText(f"已超时任务: {overdue_tasks}")
        
        self.today_tasks_widget.text_label.setText(f"今日任务: {len(today_tasks)}")
        
        # 更新象限任务列表
        self.update_quadrants_tasks(all_tasks)
    
    def update_quadrants_tasks(self, tasks):
        """更新象限任务列表"""
        # 获取项目映射
        projects = {p.id: p for p in self.db.get_all_projects()}
        
        # 按象限分类任务
        quadrant_tasks = {
            (True, True): [],   # 重要紧急
            (False, True): [],  # 不重要紧急
            (True, False): [],  # 重要不紧急
            (False, False): []  # 不重要不紧急
        }
        
        for task in tasks:
            key = (task.is_important, task.is_urgent)
            quadrant_tasks[key].append(task)
        
        # 更新每个象限的显示
        for (is_important, is_urgent), quadrant in self.quadrant_widgets.items():
            task_list = quadrant.task_list
            task_list.clear()
            
            for task in quadrant_tasks[(is_important, is_urgent)]:
                # 已完成或计划中的任务不在总览显示
                if task.status.value in ('completed', 'planned'):
                    continue
                project = projects.get(task.project_id)
                project_name = project.name if project else "未知项目"
                
                # 创建自定义任务项 widget
                task_widget = TaskItemWidget(task, project_name, self)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setData(Qt.UserRole, task.id)  # 存储任务ID
                item.setData(Qt.UserRole + 1, task.project_id)  # 存储项目ID
                # 确保任务项可拖拽
                item.setFlags(item.flags() | Qt.ItemIsDragEnabled)
                
                # 将 widget 添加到列表项（先添加 item，再设置 widget）
                task_list.addItem(item)
                task_list.setItemWidget(item, task_widget)
                
                # 设置项的大小（在设置 widget 后）
                item.setSizeHint(task_widget.sizeHint())
            
            # 如果没有任务，显示提示
            if task_list.count() == 0:
                empty_item = QListWidgetItem("（暂无任务）")
                empty_item.setForeground(QColor("#999999"))
                empty_item.setFlags(Qt.NoItemFlags)  # 不可选择
                task_list.addItem(empty_item)
    
    def on_quadrant_task_double_clicked(self, item: QListWidgetItem):
        """双击象限中的任务项时跳转到项目详情页面"""
        if not self.main_window:
            return
        
        task_id = item.data(Qt.UserRole)
        project_id = item.data(Qt.UserRole + 1)
        
        if not task_id or not project_id:
            return
        
        # 切换到项目列表页面
        self.main_window.nav_list.setCurrentRow(1)  # 项目列表是第二个（索引1）
        # 等待页面切换完成后再调用选择方法
        QTimer.singleShot(50, lambda: self.main_window.project_list_page.select_project_and_task(project_id, task_id))
