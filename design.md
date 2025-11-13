# Project Tracing - 个人项目追踪管理软件

## 项目概述
这是一个项目驱动的小型个人科研和工作项目管理软件，用于个人项目进度规划和管理。软件设计为轻量化、单机版应用，可编译为独立的Windows可执行文件。

## 功能需求

### 核心功能
1. **项目管理**
   - 创建、编辑、删除项目
   - 项目状态管理（计划、进行中、已完成）
   - 项目基本信息：名称、描述、创建时间、更新时间

2. **任务管理**
   - 创建、编辑、删除任务
   - 任务基本信息：名称、描述、备注
   - 时间管理：开始时间、截止时间
   - 任务状态：计划、进行中、已完成
   - 任务关联到项目

3. **总览页面**
   - **甘特图视图**：展示所有项目的任务时间线和进度
   - **今日任务**：汇总所有项目中今日进行中的任务
   - 项目进度统计（完成率、任务数量等）

4. **项目详情页面**
   - 项目信息展示和编辑
   - 任务列表（支持筛选、排序）
   - 项目内任务甘特图

### 数据持久化
- 使用本地文件存储（JSON或SQLite数据库）
- 支持数据导入/导出
- 自动保存机制

## 数据模型设计

### 项目（Project）
```typescript
interface Project {
  id: string;                    // 唯一标识符（UUID）
  name: string;                  // 项目名称
  description?: string;          // 项目描述
  status: 'planned' | 'in_progress' | 'completed';  // 项目状态
  createdAt: string;              // 创建时间（ISO 8601）
  updatedAt: string;              // 更新时间（ISO 8601）
  tasks: Task[];                  // 关联的任务列表
}
```

### 任务（Task）
```typescript
interface Task {
  id: string;                     // 唯一标识符（UUID）
  projectId: string;              // 所属项目ID
  name: string;                   // 任务名称
  description?: string;           // 任务描述
  notes?: string;                 // 备注
  startDate: string;              // 开始日期（YYYY-MM-DD）
  endDate: string;                // 截止日期（YYYY-MM-DD）
  status: 'planned' | 'in_progress' | 'completed';  // 任务状态
  createdAt: string;              // 创建时间
  updatedAt: string;              // 更新时间
}
```

## 用户界面设计

### 布局结构
```
┌─────────────────────────────────────────┐
│  [Logo] Project Tracing                 │
├──────────┬──────────────────────────────┤
│          │                              │
│  导航栏   │        主内容区              │
│          │                              │
│  • 总览   │  [根据导航显示不同内容]      │
│  • 项目   │                              │
│          │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

### 页面设计

#### 1. 总览页面
- **左侧导航**：总览、项目列表
- **主内容区**：
  - **甘特图模块**：横向时间轴，展示所有项目的任务
    - 支持时间范围选择（周/月/季度视图）
    - 不同项目用不同颜色区分
    - 任务条显示状态（颜色区分：计划-灰色，进行中-蓝色，已完成-绿色）
  - **今日任务模块**：
    - 列表展示今日进行中的任务
    - 显示任务名称、所属项目、截止时间
    - 支持快速标记完成
  - **统计卡片**：
    - 总项目数、进行中项目数
    - 总任务数、今日任务数、已完成任务数

#### 2. 项目列表页面
- 项目卡片列表或表格视图
- 每个项目显示：名称、状态、进度条、任务数量
- 支持筛选（按状态）和搜索
- 点击进入项目详情

#### 3. 项目详情页面
- 项目信息编辑区
- 任务列表（表格或卡片）
  - 支持按状态筛选
  - 支持按时间排序
  - 支持拖拽排序（可选）
- 项目内任务甘特图
- 添加/编辑任务按钮

#### 4. 任务编辑对话框/页面
- 表单字段：
  - 任务名称（必填）
  - 所属项目（下拉选择）
  - 开始日期（日期选择器）
  - 截止日期（日期选择器）
  - 描述（多行文本）
  - 备注（多行文本）
  - 状态（单选按钮组）

## 技术栈推荐

### 方案一：Tauri + React/Vue（推荐）
**优势**：
- 体积小（最终exe约10-20MB）
- 性能好（Rust后端）
- 现代化UI框架
- 跨平台支持（Windows/Mac/Linux）

**技术栈**：
- **前端**：React + TypeScript + Vite
- **UI组件库**：Ant Design / Material-UI / shadcn/ui
- **甘特图库**：dhtmlx-gantt / react-gantt-timeline / vis-timeline
- **后端**：Tauri (Rust)
- **数据存储**：SQLite（通过Tauri API）
- **打包**：Tauri CLI（自动打包为exe）

**开发难度**：中等
**最终体积**：10-20MB

### 方案二：Python + PySide6
**优势**：
- 开发速度快
- Python生态丰富
- 界面美观（Qt框架）

**技术栈**：
- **语言**：Python 3.10+
- **GUI框架**：PySide6 (Qt6)
- **甘特图**：matplotlib / plotly / 自定义绘制
- **数据存储**：SQLite / JSON文件
- **打包**：PyInstaller / cx_Freeze

**开发难度**：低
**最终体积**：30-50MB（使用PyInstaller）

### 方案三：Go + Fyne
**优势**：
- 体积小
- 性能优秀
- 原生编译

**技术栈**：
- **语言**：Go 1.20+
- **GUI框架**：Fyne
- **甘特图**：自定义绘制（使用Fyne Canvas）
- **数据存储**：SQLite / JSON文件
- **打包**：go build（原生编译）

**开发难度**：中等
**最终体积**：15-25MB

### 方案四：Electron + React/Vue（不推荐，体积较大）
**优势**：开发体验好，生态丰富
**劣势**：体积大（100MB+），不符合轻量化要求

## 推荐方案：Tauri + React + TypeScript

### 技术选型理由
1. **体积小**：最终打包体积约10-20MB，符合轻量化要求
2. **性能好**：Rust后端，性能接近原生应用
3. **开发体验**：React生态成熟，组件库丰富
4. **现代化**：支持TypeScript，类型安全
5. **甘特图**：前端有成熟的甘特图库可用

### 项目结构
```
project-tracing/
├── src/                    # 前端源码（React）
│   ├── components/         # 组件
│   │   ├── GanttChart/    # 甘特图组件
│   │   ├── TaskList/      # 任务列表组件
│   │   ├── ProjectCard/   # 项目卡片组件
│   │   └── ...
│   ├── pages/             # 页面
│   │   ├── Overview/      # 总览页面
│   │   ├── ProjectList/   # 项目列表
│   │   └── ProjectDetail/ # 项目详情
│   ├── stores/            # 状态管理（Zustand/Redux）
│   ├── services/          # API服务层
│   ├── types/             # TypeScript类型定义
│   └── utils/             # 工具函数
├── src-tauri/             # Tauri后端（Rust）
│   ├── src/
│   │   ├── main.rs        # 主入口
│   │   ├── db.rs          # 数据库操作
│   │   └── commands.rs    # Tauri命令
│   └── Cargo.toml
├── public/                # 静态资源
├── package.json
└── tauri.conf.json        # Tauri配置
```

### 核心依赖
**前端**：
- `react` + `react-dom`
- `typescript`
- `vite` + `@vitejs/plugin-react`
- `@tauri-apps/api`
- `zustand`（状态管理）
- `antd` 或 `@mui/material`（UI组件）
- `dhtmlx-gantt` 或 `vis-timeline`（甘特图）
- `date-fns`（日期处理）

**后端（Rust）**：
- `tauri`（核心框架）
- `rusqlite`（SQLite数据库）
- `serde`（序列化）
- `uuid`（生成唯一ID）

## 开发指导

### 开发环境搭建
1. **安装Node.js**（18+）和npm/yarn/pnpm
2. **安装Rust**：`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
3. **安装Tauri CLI**：`npm install -g @tauri-apps/cli`
4. **创建项目**：`npm create tauri-app@latest`

### 开发步骤
1. **数据层开发**
   - 设计SQLite数据库表结构
   - 实现Rust后端的数据操作命令（CRUD）
   - 定义Tauri命令接口

2. **前端开发**
   - 搭建路由和页面结构
   - 开发UI组件（使用组件库）
   - 集成甘特图组件
   - 实现状态管理和数据绑定

3. **功能实现**
   - 项目管理功能
   - 任务管理功能
   - 甘特图数据绑定和交互
   - 今日任务筛选逻辑

4. **打包发布**
   - 配置Tauri打包选项
   - 生成Windows安装包或便携版exe

### 数据库设计（SQLite）
```sql
-- 项目表
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 任务表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    notes TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('planned', 'in_progress', 'completed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_dates ON tasks(start_date, end_date);
```

## 后续开发指导

### 给AI开发者的提示
1. **使用Tauri + React + TypeScript技术栈**
2. **数据存储使用SQLite，通过Tauri命令访问**
3. **UI使用Ant Design或Material-UI组件库**
4. **甘特图使用dhtmlx-gantt或vis-timeline库**
5. **状态管理使用Zustand（轻量）或Redux Toolkit**
6. **严格按照数据模型设计实现数据结构**
7. **实现自动保存功能，避免数据丢失**
8. **注意日期时间处理，使用ISO 8601格式**
9. **项目状态根据任务状态自动计算（可选功能）**
10. **打包时配置Tauri为单文件exe模式**

### 开发优先级
1. **Phase 1**：基础框架搭建、数据模型实现、基础CRUD
2. **Phase 2**：UI界面开发、项目列表和详情页
3. **Phase 3**：甘特图集成、总览页面
4. **Phase 4**：今日任务功能、统计功能
5. **Phase 5**：优化、打包、测试

## 扩展功能（可选）
- 任务依赖关系
- 任务优先级
- 标签/分类系统
- 数据导入/导出（JSON/CSV）
- 深色模式
- 快捷键支持
- 任务提醒通知