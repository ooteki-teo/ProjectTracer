import json
import sqlite3
import uuid
import os
import shutil
import glob
from datetime import datetime
from typing import List, Optional
from models import Project, Task, Status, ProjectStatus
from utils.config import get_db_path, set_db_path, get_default_db_path
from utils.platform_utils import get_machine_name

class Database:
    LEGACY_PATH_KEY = "__default__"

    def __init__(self, db_path=None):
        self.machine_name = get_machine_name() or "unknown-machine"

        # 如果没有指定路径，从配置文件读取
        if db_path is None:
            config_path = get_db_path()
            if config_path:
                # 配置文件中保存的是用户指定路径
                # 确保目录存在
                if not os.path.isabs(config_path):
                    config_path = os.path.abspath(config_path)
                db_dir = os.path.dirname(config_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                self.db_path = config_path
            else:
                # 使用默认路径（跨平台用户目录）
                default_path = get_default_db_path()
                default_dir = os.path.dirname(default_path)
                if default_dir and not os.path.exists(default_dir):
                    os.makedirs(default_dir, exist_ok=True)
                self.db_path = default_path
                try:
                    set_db_path(self.db_path)
                except Exception:
                    pass
        else:
            # 调用方传入自定义路径
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            self.db_path = db_path
        
        # 先处理备份和恢复
        self._handle_backup_and_restore()
        self.init_database()
    
    def get_db_directory(self) -> str:
        """获取数据库所在目录"""
        abs_path = os.path.abspath(self.db_path)
        db_dir = os.path.dirname(abs_path)
        # 如果目录为空（当前目录），返回当前目录
        return db_dir if db_dir else os.getcwd()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'archived')),
                    local_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_pinned INTEGER DEFAULT 0
                )
            """)
            
            # 迁移现有数据库：添加归档状态支持
            # SQLite不支持直接修改CHECK约束，需要重建表
            try:
                # 检查表是否存在且需要迁移
                cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='projects'")
                result = cursor.fetchone()
                if result and 'archived' not in result[0]:
                    # 需要迁移：重建表
                    conn.execute("BEGIN TRANSACTION")
                    # 创建新表
                    # 检查是否需要添加 local_path 字段
                    cursor = conn.execute("PRAGMA table_info(projects)")
                    columns = [row[1] for row in cursor.fetchall()]
                    has_local_path = 'local_path' in columns
                    
                    if has_local_path:
                        # 如果已有 local_path 字段，直接重建表
                        conn.execute("""
                            CREATE TABLE projects_new (
                                id TEXT PRIMARY KEY,
                                name TEXT NOT NULL,
                                description TEXT,
                                status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'archived')),
                                local_path TEXT,
                                created_at TEXT NOT NULL,
                                updated_at TEXT NOT NULL,
                                is_pinned INTEGER DEFAULT 0
                            )
                        """)
                        conn.execute("""
                            INSERT INTO projects_new (id, name, description, status, local_path, created_at, updated_at)
                            SELECT id, name, description, status, local_path, created_at, updated_at FROM projects
                        """)
                    else:
                        # 如果没有 local_path 字段，需要添加
                        conn.execute("""
                            CREATE TABLE projects_new (
                                id TEXT PRIMARY KEY,
                                name TEXT NOT NULL,
                                description TEXT,
                                status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'archived')),
                                local_path TEXT,
                                created_at TEXT NOT NULL,
                                updated_at TEXT NOT NULL,
                                is_pinned INTEGER DEFAULT 0
                            )
                        """)
                        conn.execute("""
                            INSERT INTO projects_new (id, name, description, status, created_at, updated_at)
                            SELECT id, name, description, status, created_at, updated_at FROM projects
                        """)
                    # 删除旧表
                    conn.execute("DROP TABLE projects")
                    # 重命名新表
                    conn.execute("ALTER TABLE projects_new RENAME TO projects")
                    conn.execute("COMMIT")
            except Exception as e:
                # 如果迁移失败，尝试回滚
                try:
                    conn.execute("ROLLBACK")
                except:
                    pass
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    notes TEXT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed', 'overdue')),
                    local_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)
            
            # 迁移 tasks 表：添加 local_path 字段
            try:
                cursor = conn.execute("PRAGMA table_info(tasks)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'local_path' not in columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN local_path TEXT")
            except:
                pass
            
            # 迁移 tasks 表：添加标签字段（兼容老数据库）
            try:
                cursor = conn.execute("PRAGMA table_info(tasks)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'is_important' not in columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN is_important INTEGER DEFAULT 0")
                if 'is_urgent' not in columns:
                    conn.execute("ALTER TABLE tasks ADD COLUMN is_urgent INTEGER DEFAULT 0")
            except:
                pass
            
            # 迁移现有数据库：更新 CHECK 约束（SQLite 不支持直接修改约束，需要重建表）
            # 这里先检查是否需要迁移
            try:
                conn.execute("ALTER TABLE tasks ADD COLUMN temp_status TEXT")
                conn.execute("UPDATE tasks SET temp_status = status")
                conn.execute("UPDATE tasks SET status = 'overdue' WHERE status = 'planned' AND end_date < date('now')")
                conn.execute("UPDATE tasks SET status = temp_status")
                conn.execute("ALTER TABLE tasks DROP COLUMN temp_status")
            except:
                pass  # 如果表已存在新结构，忽略错误
            
            # 添加置顶字段（兼容老数据库）
            try:
                cursor = conn.execute("PRAGMA table_info(projects)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'is_pinned' not in columns:
                    conn.execute("ALTER TABLE projects ADD COLUMN is_pinned INTEGER DEFAULT 0")
            except:
                pass
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_dates ON tasks(start_date, end_date)")
    
    def _load_path_map(self, raw_value) -> dict:
        """将数据库中的 local_path 值解析为 {machine_name: path} 字典"""
        if raw_value is None:
            return {}
        if isinstance(raw_value, bytes):
            try:
                raw_value = raw_value.decode("utf-8")
            except Exception:
                raw_value = raw_value.decode("utf-8", errors="ignore")
        raw_value = str(raw_value).strip()
        if not raw_value:
            return {}
        try:
            data = json.loads(raw_value)
            if isinstance(data, dict):
                cleaned = {}
                for key, value in data.items():
                    if isinstance(key, str) and isinstance(value, str) and value.strip():
                        cleaned[key] = value.strip()
                return cleaned
        except Exception:
            pass
        # 旧格式：直接保存一个字符串路径
        return {self.LEGACY_PATH_KEY: raw_value}

    def _serialize_path_map(self, path_map: dict) -> str:
        """将路径字典序列化为 JSON 字符串"""
        if not path_map:
            return ""
        return json.dumps(path_map, ensure_ascii=False)

    def _get_local_path_for_current_machine(self, raw_value) -> str:
        """获取当前电脑对应的本地路径，如果不存在则返回空字符串"""
        path_map = self._load_path_map(raw_value)
        return path_map.get(self.machine_name, "")

    def _update_path_map_for_current_machine(self, raw_value, new_path: str) -> str:
        """更新当前电脑的路径，并返回新的 JSON 字符串"""
        path_map = self._load_path_map(raw_value)
        sanitized_path = (new_path or "").strip()
        if sanitized_path:
            path_map[self.machine_name] = sanitized_path
            # 更新后移除旧的默认路径，避免其他电脑误用
            path_map.pop(self.LEGACY_PATH_KEY, None)
        else:
            path_map.pop(self.machine_name, None)

        # 保留其他机器的路径（包括 legacy）
        path_map = {k: v for k, v in path_map.items() if v}

        return self._serialize_path_map(path_map)

    def _ensure_path_map_for_new_entry(self, path: str) -> str:
        """创建新数据库记录时，将路径包装为路径映射格式"""
        sanitized_path = (path or "").strip()
        if not sanitized_path:
            return ""
        return self._serialize_path_map({self.machine_name: sanitized_path})

    # 项目操作方法
    def create_project(self, name: str, description: str = "", local_path: str = "") -> str:
        project_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        stored_path = self._ensure_path_map_for_new_entry(local_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO projects (id, name, description, status, local_path, created_at, updated_at, is_pinned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, name, description, "planned", stored_path, now, now, 0)
            )
        return project_id
    
    def get_all_projects(self, include_archived=False) -> List[Project]:
        """获取所有项目，默认不包括已归档和已完成的"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if include_archived:
                rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects WHERE status NOT IN ('completed', 'archived') ORDER BY updated_at DESC"
                ).fetchall()
            return [self._row_to_project(row) for row in rows]
    
    def get_history_projects(self) -> List[Project]:
        """获取历史项目（已完成和已归档的）"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM projects WHERE status IN ('completed', 'archived') ORDER BY updated_at DESC"
            ).fetchall()
            return [self._row_to_project(row) for row in rows]
    
    def get_project(self, project_id: str) -> Optional[Project]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            return self._row_to_project(row) if row else None
    
    def update_project(self, project_id: str, **kwargs):
        now = datetime.now().isoformat()
        kwargs['updated_at'] = now
        with sqlite3.connect(self.db_path) as conn:
            if 'local_path' in kwargs:
                cursor = conn.execute(
                    "SELECT local_path FROM projects WHERE id = ?",
                    (project_id,)
                )
                row = cursor.fetchone()
                raw_value = row[0] if row else ""
                kwargs['local_path'] = self._update_path_map_for_current_machine(raw_value, kwargs['local_path'])

            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [project_id]
            conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
    
    def delete_project(self, project_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    
    # 任务操作方法
    def create_task(self, project_id: str, name: str, start_date: str, end_date: str, 
                    description: str = "", notes: str = "", local_path: str = "",
                    is_important: bool = False, is_urgent: bool = False) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        stored_path = self._ensure_path_map_for_new_entry(local_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (id, project_id, name, description, notes, start_date, end_date, status, local_path, is_important, is_urgent, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, project_id, name, description, notes, start_date, end_date, 
                 Status.PLANNED.value, stored_path, 1 if is_important else 0, 1 if is_urgent else 0, now, now)
            )
        return task_id
    
    def get_tasks_by_project(self, project_id: str) -> List[Task]:
        """获取项目的所有任务，并自动更新状态"""
        # 先自动更新任务状态
        self.update_task_status_auto()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM tasks WHERE project_id = ? ORDER BY start_date", 
                (project_id,)
            ).fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def update_task_status_auto(self):
        """根据时间自动更新任务状态"""
        today = datetime.now().strftime("%Y-%m-%d")
        now_iso = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            # 更新已超时的任务（截止日期已过且未完成）
            conn.execute("""
                UPDATE tasks 
                SET status = 'overdue', updated_at = ?
                WHERE status != 'completed' 
                AND status != 'overdue'
                AND end_date < ?
            """, (now_iso, today))
            
            # 更新应该进行中的任务（开始日期已到，截止日期未到，且不是已完成或已超时）
            conn.execute("""
                UPDATE tasks 
                SET status = 'in_progress', updated_at = ?
                WHERE status IN ('planned', 'overdue')
                AND start_date <= ?
                AND end_date >= ?
            """, (now_iso, today, today))

            # 更新尚未开始的任务为计划中（开始日期在未来）
            conn.execute("""
                UPDATE tasks
                SET status = 'planned', updated_at = ?
                WHERE status != 'completed'
                AND start_date > ?
            """, (now_iso, today))
    
    def get_today_tasks(self, include_history=False) -> List[Task]:
        """获取今日任务（包括已超时的任务），默认不包括历史项目的任务"""
        # 先自动更新任务状态
        self.update_task_status_auto()
        
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if include_history:
                # 包括所有项目
                rows = conn.execute("""
                    SELECT t.* FROM tasks t 
                    JOIN projects p ON t.project_id = p.id
                    WHERE ((t.start_date <= ? AND t.end_date >= ?)
                       OR (t.end_date < ? AND t.status = 'overdue'))
                    AND t.status != 'completed'
                    ORDER BY 
                        CASE WHEN t.status = 'overdue' THEN 0 ELSE 1 END,
                        t.end_date
                """, (today, today, today)).fetchall()
            else:
                # 不包括已完成和已归档的项目
                rows = conn.execute("""
                    SELECT t.* FROM tasks t 
                    JOIN projects p ON t.project_id = p.id
                    WHERE ((t.start_date <= ? AND t.end_date >= ?)
                       OR (t.end_date < ? AND t.status = 'overdue'))
                    AND t.status != 'completed'
                    AND p.status NOT IN ('completed', 'archived')
                    ORDER BY 
                        CASE WHEN t.status = 'overdue' THEN 0 ELSE 1 END,
                        t.end_date
                """, (today, today, today)).fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def update_task(self, task_id: str, **kwargs):
        now = datetime.now().isoformat()
        kwargs['updated_at'] = now
        
        # 转换布尔值为整数（SQLite 使用 INTEGER 存储布尔值）
        if 'is_important' in kwargs:
            kwargs['is_important'] = 1 if kwargs['is_important'] else 0
        if 'is_urgent' in kwargs:
            kwargs['is_urgent'] = 1 if kwargs['is_urgent'] else 0
        if 'is_pinned' in kwargs:
            kwargs['is_pinned'] = 1 if kwargs['is_pinned'] else 0
        
        with sqlite3.connect(self.db_path) as conn:
            if 'local_path' in kwargs:
                cursor = conn.execute(
                    "SELECT local_path FROM tasks WHERE id = ?",
                    (task_id,)
                )
                row = cursor.fetchone()
                raw_value = row[0] if row else ""
                kwargs['local_path'] = self._update_path_map_for_current_machine(raw_value, kwargs['local_path'])

            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [task_id]
            conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    
    def delete_task(self, task_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    # 辅助方法
    def _row_to_project(self, row) -> Project:
        # sqlite3.Row 不支持 get 方法，需要检查列是否存在
        try:
            raw_local_path = row['local_path']
        except (KeyError, IndexError):
            raw_local_path = ""
        
        path_map = self._load_path_map(raw_local_path)
        local_path = path_map.get(self.machine_name, "")
        
        try:
            is_pinned = bool(row['is_pinned']) if row['is_pinned'] is not None else False
        except (KeyError, IndexError):
            is_pinned = False
        
        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'] or "",
            status=row['status'],  # 直接使用字符串
            local_path=local_path,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_pinned=is_pinned
        )
        project.local_path_map = dict(path_map)
        return project
    
    def complete_project(self, project_id: str):
        """完成项目：将所有任务标记为完成，项目状态设为已完成"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            # 更新项目状态
            conn.execute(
                "UPDATE projects SET status = 'completed', updated_at = ? WHERE id = ?",
                (now, project_id)
            )
            # 更新所有任务状态为完成
            conn.execute(
                "UPDATE tasks SET status = 'completed', updated_at = ? WHERE project_id = ?",
                (now, project_id)
            )
    
    def archive_project(self, project_id: str):
        """归档项目"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET status = 'archived', updated_at = ? WHERE id = ?",
                (now, project_id)
            )
    
    def restore_project(self, project_id: str):
        """恢复项目：从历史恢复到进行中状态"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE projects SET status = 'in_progress', updated_at = ? WHERE id = ?",
                (now, project_id)
            )
    
    def _row_to_task(self, row) -> Task:
        # 处理可能的旧状态值
        status_value = row['status']
        try:
            status = Status(status_value)
        except ValueError:
            # 如果状态值不在枚举中，默认为 planned
            status = Status.PLANNED
        
        # sqlite3.Row 不支持 get 方法，需要检查列是否存在
        try:
            raw_local_path = row['local_path']
        except (KeyError, IndexError):
            raw_local_path = ""
        
        path_map = self._load_path_map(raw_local_path)
        local_path = path_map.get(self.machine_name, "")
        
        # 读取标签字段（兼容老数据库，默认值为 False）
        try:
            is_important = bool(row['is_important']) if row['is_important'] is not None else False
        except (KeyError, IndexError):
            is_important = False
        
        try:
            is_urgent = bool(row['is_urgent']) if row['is_urgent'] is not None else False
        except (KeyError, IndexError):
            is_urgent = False
        
        return Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'] or "",
            notes=row['notes'] or "",
            start_date=row['start_date'],
            end_date=row['end_date'],
            status=status,
            local_path=local_path,
            is_important=is_important,
            is_urgent=is_urgent,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        task.local_path_map = dict(path_map)
        return task
    
    def _handle_backup_and_restore(self):
        """处理数据库备份和恢复"""
        # 检查默认数据库是否存在
        default_db_exists = os.path.exists(self.db_path)
        
        if not default_db_exists:
            # 如果默认数据库不存在，尝试从最新备份恢复
            self._restore_from_latest_backup()
        
        # 执行备份操作
        self._backup_database()
        
        # 清理旧备份，只保留最新的7个
        self._cleanup_old_backups()
    
    def _get_backup_filename(self, date_str: str = None) -> str:
        """获取备份文件名（完整路径）"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        backup_name = f"PT_{date_str}.db"
        # 备份文件保存在数据库所在目录
        db_dir = self.get_db_directory()
        return os.path.join(db_dir, backup_name)
    
    def _backup_database(self):
        """备份数据库"""
        if not os.path.exists(self.db_path):
            return
        
        # 获取今日备份文件名
        today_backup = self._get_backup_filename()
        
        # 如果今日备份已存在，跳过
        if os.path.exists(today_backup):
            return
        
        try:
            # 复制数据库文件作为备份
            shutil.copy2(self.db_path, today_backup)
        except Exception as e:
            # 备份失败时静默处理，不影响主程序运行
            pass
    
    def _restore_from_latest_backup(self):
        """从最新备份恢复数据库"""
        # 在数据库目录中查找所有备份文件
        db_dir = self.get_db_directory()
        backup_pattern = os.path.join(db_dir, "PT_*.db")
        backup_files = glob.glob(backup_pattern)
        
        if not backup_files:
            # 没有备份文件，直接返回
            return
        
        # 按修改时间排序，获取最新的备份
        backup_files.sort(key=os.path.getmtime, reverse=True)
        latest_backup = backup_files[0]
        
        try:
            # 复制最新备份为默认数据库
            shutil.copy2(latest_backup, self.db_path)
        except Exception as e:
            # 恢复失败时静默处理
            pass
    
    def _cleanup_old_backups(self):
        """清理旧备份，只保留最新的7个"""
        # 在数据库目录中查找所有备份文件
        db_dir = self.get_db_directory()
        backup_pattern = os.path.join(db_dir, "PT_*.db")
        backup_files = glob.glob(backup_pattern)
        
        if len(backup_files) <= 7:
            # 备份数量不超过7个，不需要清理
            return
        
        # 按修改时间排序
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # 删除最旧的备份（保留最新的7个）
        for old_backup in backup_files[7:]:
            try:
                os.remove(old_backup)
            except Exception as e:
                # 删除失败时静默处理
                pass