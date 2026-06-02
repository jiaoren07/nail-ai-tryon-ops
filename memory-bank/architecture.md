# 项目架构与文件用途索引

> 实时随开发推进维护。每一步 AI 开发者在用户验证通过后追加新增的目录/文件解释。后续开发者读这一份就能定位"什么放哪里、为什么"。

---

## 仓库顶层目录

```
d:\github仓库1\
├── backend\          产品代码：FastAPI 服务（Step 0.1 创建空骨架）
├── frontend\         产品代码：React + Vite SPA（Step 0.1 创建空目录，Step 0.3 初始化）
├── data-prep\        一次性数据准备工具，与产品代码隔离（已存在，详见下文）
├── Meijia\           早期 Next.js 视觉原型，仅作风格参考，不参与本计划构建
├── memory-bank\      文档实时副本 + 开发进度 + 架构索引
├── .claude\          Claude Code 配置
├── .env              本地 secrets（gitignored）
├── .gitignore        24 条规则；详见 §.gitignore 段
├── design-docu.md    产品设计文档（权威）
├── tech-stack.md     技术选型文档（权威）
├── implementation-plan.md  实施步骤计划（权威，按 Step 编号顺序执行）
└── CLAUDE.md         给未来 Claude Code 实例的项目导览
```

---

## `backend/` 内部结构（Step 0.1 创建）

```
backend\
├── app\
│   ├── routers\      HTTP 路由层。按"消费者端 / 运营端"二分：
│   │                   - user.py 收纳所有 /api/* 的 C 端路由（包括 /api/styles、/api/recommend、/api/tryon 等，不论二级路径）
│   │                   - ops.py  收纳所有 /api/ops/* 的 B 端路由
│   │                  **禁止**为 styles/recommend/tryon 等业务对象拆独立 router 文件（见 implementation-plan Step 2.3 强约定）
│   ├── services\     业务逻辑层（recommend / image_gen / llm / stats / report / mailer / scheduler ...）
│   └── models\       SQLAlchemy ORM 模型（6 张表 styles / tryons / style_stats / ops_actions / reports / notifications）
├── scripts\          产品代码内的 seed 脚本（seed_styles / seed_tryons / seed_stats / seed_all）
├── static\           FastAPI 挂在 /static/ 下对外提供的静态资源
│   ├── styles\       款式封面图（seed 时从 dataset/styles 复制，40 张：25 张 f_*_enh.png + 15 张 m_*.jpg）
│   ├── samples\      示例手图（seed 时从 dataset/hands 复制，17 张 *.png，男女共用）
│   ├── uploads\      用户上传手图（运行时生成，gitignored）
│   └── cache\        试戴结果图缓存（运行时生成，gitignored）
└── tests\            单测/集成测试存放地
```

**已创建的关键文件 / 目录**：
- `backend/.venv/` — Python 3.13.2 虚拟环境（Step 0.2 创建，**gitignored**）。所有命令行调用都用 `backend/.venv/Scripts/python.exe` 或先激活 `Scripts/Activate.ps1`；不要用系统 Python。
- `backend/requirements.txt` — Python 依赖锁定清单（Step 0.2 通过 `pip freeze` 生成，37 行）。重装时跑 `backend/.venv/Scripts/pip install -r backend/requirements.txt`。

**未创建的关键文件**（后续 Step 会出现）：
- `backend/app/main.py` — FastAPI 入口（Step 0.5 创建）
- `backend/app/db.py` — SQLAlchemy engine 与 session 依赖（Step 2.1 创建）
- `backend/.env` 与 `.env.example` — 后端配置（Step 0.4 创建）
- `backend/nail_demo.db` — SQLite 数据库文件（init_db 后生成，gitignored）

---

## `frontend/` 内部结构（Step 0.3 用 Vite 初始化）

```
frontend\
├── node_modules\         npm 依赖（gitignored，313 个包）
├── public\               Vite 默认静态资源（vite.svg 等，可按需替换）
├── src\
│   ├── App.tsx           Vite 默认欢迎页；Step 5.x 时会被 React Router 替换为路由出口
│   ├── App.css           Vite scaffold 自带样式，与 Tailwind 共存
│   ├── index.css         全局 CSS，顶部含 @tailwind base/components/utilities 三条指令
│   ├── main.tsx          ReactDOM 挂载入口
│   └── assets\           Vite logo、React logo 等图片资源
├── .gitignore            Vite scaffold 自带（已被仓库根 .gitignore 覆盖，可保留亦可删）
├── eslint.config.js      Vite scaffold 自带的 eslint flat config，演示阶段可忽略
├── index.html            SPA 单入口 HTML
├── package.json          npm 依赖清单与 scripts（dev / build / preview / lint）
├── package-lock.json     npm 锁文件（提交入库）
├── postcss.config.js     PostCSS 配置（Tailwind 通过它接入 Vite）
├── tailwind.config.js    Tailwind 3.x 配置；content 指向 ./index.html + ./src/**/*.{js,ts,jsx,tsx}
├── tsconfig.json         TS 根配置（references 子配置）
├── tsconfig.app.json     应用代码的 TS 配置
├── tsconfig.node.json    Vite / 构建脚本的 TS 配置
└── vite.config.ts        Vite 配置；后续 Step 4.1+ 可能加 proxy 把 /api 转发到 http://localhost:8000
```

**未创建的关键文件 / 目录**（后续 Step 会出现）：
- `frontend/src/pages/user/*` 与 `frontend/src/pages/ops/*` — 业务页面（Step 5.x / Step 7.x）
- `frontend/src/api/index.ts` — axios 实例与统一拦截器（Step 5.1）
- `frontend/src/store/` — React Context + 全局状态（Step 5.1）
- `frontend/src/components/*` — 通用组件（GenderCard、StyleCard、NotificationBell 等）

---

## `data-prep/` 内部结构（已就绪，由 Step 0.1 前的数据准备阶段产生）

```
data-prep\
├── download_dataset.py    从赛题 xlsx 下载 63 张图到 d:\美团AI HACKATHON\dataset\（一次性，已跑完）
├── auto_tag_styles.py     调 PPIO Qwen2.5-VL-72B 给 25 女款打标 → dataset/styles/tags_qwen.json
├── tag_male_styles.py     调 PPIO Qwen3-VL-30B-MoE 给 15 男款打标 → dataset/styles/male/tags_qwen.json
├── probe_ppio.py          PPIO API 连通性探测（一次性）
└── probe_glm.py           PPIO 上 GLM 模型 ID 探测（一次性）
```

**关键约定**：这些脚本**不参与产品运行**，是数据准备阶段的工具。打标输出 JSON 落在 dataset 目录下，由 `backend/scripts/seed_styles.py` 在 seed 时读取入库。

---

## `memory-bank/` 内部结构

```
memory-bank\
├── design-docu.md           产品设计文档副本（与根目录同步）
├── tech-stack.md            技术选型文档副本
├── implementation-plan.md   实施计划副本
├── progress.md              开发进度日志（本步之后开始累积）
└── architecture.md          本文档（架构索引）
```

每完成一步并经过用户验证后，AI 开发者要：
1. 在 `progress.md` 追加该步记录；
2. 在 `architecture.md` 追加新文件/目录的用途说明（如果产生了新工件）。

---

## 外部依赖（不在仓库内）

- **数据集**：`d:\美团AI HACKATHON\dataset\`
  - `hands/01.png ~ 17.png` — 17 张手图样本（13 赛题 + 4 用户补充）
  - `styles/f_01_enh.png ~ f_25_enh.png` + `f_NN_orig.{png|jpg}` — 25 张女款
  - `styles/tags_qwen.json` — 25 张女款的 VLM 标签
  - `styles/male/m_01.jpg ~ m_15.jpg` — 15 张男款
  - `styles/male/tags_qwen.json` — 15 张男款的 VLM 标签

---

## `.gitignore` 规则分类（Step 0.1 写入）

| 类别 | 规则 |
|---|---|
| Secrets | `.env`、`.env.local`、`.env.*.local` |
| Python 环境 | `backend/.venv/`、`.venv/`、`venv/` |
| Python bytecode | `__pycache__/`、`*.pyc`、`*.pyo` |
| Node 模块 | `node_modules/`、`Meijia/node_modules/` |
| 构建产物 | `frontend/dist/`、`frontend/.vite/`、`Meijia/.next/` |
| SQLite | `*.db`、`*.db-journal`、`*.db-shm`、`*.db-wal` |
| 运行时静态 | `backend/static/cache/`、`backend/static/uploads/` |
| IDE / OS | `.vscode/`、`.idea/`、`.DS_Store`、`Thumbs.db` |
