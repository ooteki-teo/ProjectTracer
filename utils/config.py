"""
配置管理模块：保存和加载应用程序配置
"""
import json
import os
from typing import Optional
from utils.platform_utils import is_macos, is_windows

APP_DIR_NAME = "ProjectTracing"
CONFIG_FILE_NAME = "project_tracing_config.json"


def _get_app_data_directory() -> str:
    """获取跨平台的应用数据目录，并确保其存在"""
    home_dir = os.path.expanduser("~")

    if is_windows():
        base_dir = os.environ.get("APPDATA") or os.path.join(home_dir, "AppData", "Roaming")
    elif is_macos():
        base_dir = os.path.join(home_dir, "Library", "Application Support")
    else:
        base_dir = os.path.join(home_dir, ".local", "share")

    app_data_dir = os.path.join(base_dir, APP_DIR_NAME)

    try:
        os.makedirs(app_data_dir, exist_ok=True)
    except Exception:
        pass

    return app_data_dir


def get_default_db_path() -> str:
    """获取数据库的默认存储路径"""
    return os.path.join(_get_app_data_directory(), "project_tracing.db")


def get_config_path() -> str:
    """获取配置文件路径"""
    return os.path.join(_get_app_data_directory(), CONFIG_FILE_NAME)


def load_config() -> dict:
    """加载配置"""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config: dict):
    """保存配置"""
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_db_path() -> Optional[str]:
    """获取数据库路径配置"""
    config = load_config()
    return config.get("db_path")


def set_db_path(db_path: str):
    """设置数据库路径配置"""
    config = load_config()
    config["db_path"] = db_path
    save_config(config)

