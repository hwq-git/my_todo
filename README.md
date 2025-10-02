个人任务管理器（全栈版）
A full-stack personal task manager with schedule import, daily task filtering, and task lifecycle management.
项目简介
这是一个基于 前后端分离架构 开发的个人任务管理应用，核心目标是帮助用户高效管理日常日程与课程表，聚焦当日待办事项，避免信息过载。支持手动添加任务、标记完成 / 删除任务，还能通过 Excel 课表文件批量导入课程，自动同步至当日日程，特别适合学生或需要规律管理时间的用户。
核心功能
功能模块	具体描述
📅 当日任务筛选	自动识别系统日期，仅展示当天的待办任务（如 “星期三” 只显示周三的日程 / 课程）
✅ 任务生命周期管理	支持「添加任务」「标记完成」「删除任务」，已完成任务与待办任务分类展示
📊 课表批量导入	支持上传 .xlsx 格式课表文件，自动解析课程时间（上午 / 下午 / 晚上）、星期几、课程名称，批量导入至任务库
⏰ 当前任务高亮	实时对比系统时间，高亮显示当前时间段应进行的任务（如 14:30 时高亮 “14:30 开会”）
🗂️ 数据本地存储	基于 SQLite 数据库存储任务数据，无需额外配置数据库服务，开箱即用
技术栈
层面	技术 / 工具	说明
前端	Vue 3 + Axios + CSS	轻量级前端框架，实现数据绑定与 API 交互
后端	Flask + Flask-CORS	轻量级 Python Web 框架，处理 API 请求与跨域
数据处理	SQLite + Pandas + OpenPyXL	SQLite 存储任务数据；Pandas 解析 Excel 课表
版本控制	Git	代码提交与分支管理
快速开始
1. 克隆仓库
```
git clone https://github.com/hwq-git/my_todo.git
cd 你的仓库名
```
2. 启动后端服务
```
# 进入后端目录
cd todo-backend
# 激活虚拟环境（若未创建，先执行 python -m venv todoenv）
# Windows: todoenv\Scripts\activate
# macOS/Linux: source todoenv/bin/activate
# 安装依赖
pip install -r requirements.txt
# 启动 Flask 服务（默认端口 5000）
python app.py
```
3. 打开前端页面
直接双击 todo-list-project/index.html 文件，或用浏览器打开该文件即可使用。
项目结构
```
my-todo-app/                  # 项目根目录
├── todo-backend/             # 后端服务目录
│   ├── app.py                # 后端核心逻辑（API 接口、数据库操作、Excel 解析）
│   ├── tasks.db              # SQLite 数据库文件（自动生成）
│   ├── requirements.txt      # 后端依赖列表
│   └── todoenv/              # Python 虚拟环境（git 已忽略）
├── todo-list-project/        # 前端页面目录
│   ├── index.html            # 前端核心页面（任务展示、添加、导入功能）
│   └── style.css             # 前端样式（任务卡片、按钮、空状态提示）
├── .gitignore                # Git 忽略文件（虚拟环境、数据库、日志等）
└── README.md                 # 项目说明文档（当前文档）
```
待优化方向
✅ 任务提醒功能：支持设置任务时间提醒（如弹窗 / 浏览器通知）
📤 Excel 任务导出：支持将当前任务列表导出为 Excel 文件备份
🔐 用户登录：添加简单的用户认证，支持多用户数据隔离
📱 响应式适配：优化移动端显示，支持手机端操作
贡献说明
欢迎提交 Issue 或 Pull Request 改进功能！若发现 Bug 或有新需求，可直接在 GitHub 仓库提交 Issue 反馈。