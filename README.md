# Project Tracing

轻量级的个人项目管理工具，使用 Python + PySide6 开发，提供项目、任务管理和今日任务概览等功能，支持本地路径导航和 SQLite 数据持久化。

## 功能特性
- 项目与任务的生命周期管理（计划、进行中、完成、归档、逾期）
- 项目列表与详情同屏展示，支持直接编辑并批量操作任务
- 历史项目独立展示，可随时恢复归档或已完成的项目
- 今日任务面板：自动刷新、快捷完成、双击跳转到项目详情
- 自动检测任务逾期状态并实时更新
- 支持为项目和任务指定本地工作目录，并一键打开
- 支持使用自定义图标（`resources/app.ico`、`ui/logo.jpg`）
- 自带数据库迁移逻辑，兼容旧版本数据
- 一键打包脚本，便于生成 Windows 可执行程序

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

### 方式一：生成可执行文件（开发/测试用）
项目提供了 `build.py`，封装了 PyInstaller 的打包流程：
```powershell
python build.py
```
脚本默认使用 `--onedir` 模式（启动更快，会生成 `dist/ProjectTracing/` 文件夹）。
如需单个可执行文件，可在 `build.py` 中将 `--onedir` 调整为 `--onefile`，但启动速度会略慢。

生成路径示例：
- `dist/ProjectTracing/ProjectTracing.exe`：默认的 onedir 产物
- `resources/app.ico`：应用图标
- `ui/logo.jpg`：导航栏使用的高分辨率图标

### 方式二：生成 Windows 安装程序（推荐用于分发）
如果需要生成专业的 Windows 安装程序（.exe 安装包），请按以下步骤操作：

1. **安装 Inno Setup**
   - 下载地址：https://jrsoftware.org/isinfo.php
   - 安装时选择"安装所有组件"，包括中文语言包

2. **打包程序**
   ```powershell
   # 先运行 build.py 生成可执行文件
   python build.py
   ```
   在dist/ScienceProjectTracing下就会生成exe文件


## 常见问题
**Q: 打包后的程序启动缓慢？**
- 请使用默认的 `--onedir` 模式，单文件模式需要解压，启动会变慢。

**Q: 打包后图标缺失？**
- 确保 `resources/app.ico` 与 `ui/logo.jpg` 均存在。
- 程序运行时通过 `utils.resource_path` 动态定位资源，避免路径问题。

**Q: 数据库结构更新后无法兼容老数据？**
- `database.py` 内置迁移逻辑，会在启动时自动添加缺失的列和约束。

## 许可证
本项目采用 MIT 许可证，详见 `LICENSE` 文件。