# Project Tracing

轻量级的个人项目管理工具，使用 Python + PySide6 开发，提供项目、任务管理和今日任务概览等功能，支持本地路径导航和 SQLite 数据持久化。支持windows mac和linux。

## 功能特性
- 项目与任务的生命周期管理（计划、进行中、完成、归档、逾期）
- 今日任务面板：自动刷新、快捷完成、双击跳转到项目详情，按照重要/紧急分成四个象限，可以手动直接拖动
- 支持为项目和任务指定本地工作目录，并一键打开。工作路径与机器绑定，不同机器之间的工作路径互不影响
- 自定义数据库的路径，方便在不同平台之间用第三方同步工具同步


## 目录结构
```text
ProjectTracing/
├─ build.py               # PyInstaller 打包脚本
├─ main.py                # 应用入口，负责启动主窗口
├─ database.py            # SQLite 数据访问与迁移逻辑
├─ models.py              # Project 与 Task 数据模型
├─ ui/                    # 所有界面文件（MainWindow、ProjectList、Overview、History）
├─ utils/                 # 工具函数（资源路径定位等）
├─ resources/             # 应用图标等静态资源
├─ requirements.txt       # 依赖列表
└─ README.md              # 使用说明（本文档）
```

## 环境要求
- Windows 10 及以上（开发环境）
- Python 3.10+（建议使用虚拟环境）
- 依赖详见 `requirements.txt`

## 快速开始
```powershell
# 1. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

首次运行会在项目根目录创建默认的 SQLite 数据库文件（`project_tracing.db`）。

## 打包发布
生成可执行文件（开发/测试用）
项目提供了 `build.py`，封装了 PyInstaller 的打包流程：
```powershell
python build.py
```
脚本默认使用 `--onefile` 模式, 启动速度会略慢。

生成路径示例：
- `dist/ProjectTracing/ProjectTracing.exe`：默认的 onedir 产物
- `resources/app.ico`：应用图标
- `ui/logo.jpg`：导航栏使用的高分辨率图标

## 许可证
本项目采用 MIT 许可证，详见 `LICENSE` 文件。
