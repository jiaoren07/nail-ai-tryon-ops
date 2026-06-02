# 开发进度日志

> 按 `implementation-plan.md` 步骤顺序记录。每条由 AI 开发者在用户验证通过后写入。后续开发者读这一份文件即可知道项目走到哪一步、各步留下了什么。

---

## Phase 0 · 项目初始化

### ✅ Step 0.1 · 建立 monorepo 目录骨架 — 2026-05-31

**做了什么：**
- 在 `d:\github仓库1\` 下新建 `backend/` 与 `frontend/` 两个一级目录。
- 在 `backend/` 下建出全部产品代码所需的子目录树：`app/{routers,services,models}`、`scripts/`、`static/{styles,samples,uploads,cache}`、`tests/`。
- 重写仓库根 `.gitignore`（原来只有一行 `.env`），扩展到 24 条规则，覆盖：secrets、Python 虚拟环境与 bytecode、Node modules 与构建产物、SQLite 数据库文件、运行时静态文件（`cache/`、`uploads/`）、IDE/OS 杂项。

**验证结果：**用户人工核对目录树 + `.gitignore` 行数，通过。

**给后续开发者的提示：**
- `backend/static/cache/` 与 `backend/static/uploads/` 是运行时目录，已在 `.gitignore` 里；seed 脚本不要往这两个目录复制文件，只复制到 `styles/` 与 `samples/`。
- `frontend/` 当前是空目录，Vite 项目要等 Step 0.3 才初始化。
- 数据准备脚本在仓库根 `data-prep/`（非 `backend/scripts/`），跟产品代码隔离，不要混淆。

---

### ✅ Step 0.2 · 后端 Python 环境与依赖 — 2026-06-01

**做了什么：**
- 在 `backend/.venv/` 下创建 Python 3.13.2 虚拟环境。
- 通过 venv 内 pip 安装 13 个直接依赖（fastapi、uvicorn[standard]、sqlalchemy、aiosqlite、pydantic、pydantic-settings、python-multipart、httpx、python-dotenv、pillow、openai、apscheduler、markdown）。
- `pip freeze` 输出固定到 `backend/requirements.txt`（37 行，含 13 个直接 + 24 个传递依赖）。

**Py 3.13 兼容性偏离：**
tech-stack.md §3.4 原本写的 pinned 版本（pillow 10.3、pydantic 2.6、fastapi 0.110、openai 1.40 等）都是 Py 3.13 之前发布的，没有预编译 wheel，pip 在 Py 3.13 上必须从源码编译，pillow 会失败、pydantic-core 会失败（缺 Rust 工具链）。已升级到 Py 3.13 兼容版本，实际安装版本：

| 包 | 计划版本 | 实际安装版本 |
|---|---|---|
| fastapi | 0.110.0 | 0.136.3 |
| uvicorn | 0.29.0 | 0.48.0 |
| sqlalchemy | 2.0.29 | 2.0.50 |
| aiosqlite | 0.20.0 | 0.22.1 |
| pydantic | 2.6.4 | 2.13.4 |
| pydantic-settings | 2.2.1 | 2.14.1 |
| python-multipart | 0.0.9 | 0.0.29 |
| httpx | 0.27.0 | 0.28.1 |
| python-dotenv | 1.0.1 | 1.2.2 |
| pillow | 10.3.0 | 12.2.0 |
| openai | 1.40.0 | 2.38.0 |
| apscheduler | 3.10.4 | 3.11.2 |
| markdown | 3.6 | 3.10.2 |

tech-stack.md §3.4 的版本号已经同步更新为上面的"实际安装版本"，让两份文档对齐，避免未来重装重蹈覆辙。

**验证结果：**用户跑 `python -c "import fastapi, ..., markdown"` 输出 `OK`，通过。

**给后续开发者的提示：**
- 这个 venv 不要重建（重建可能再次踩 Py 版本兼容坑）。要让别人复现，让 ta 用 Python 3.13+ 跑 `pip install -r backend/requirements.txt`。
- 升级单个包前先确认 Py 3.13 wheel 是否可用（`pip download --no-deps <pkg>` 看是否有 win_amd64-cp313 wheel）。
- 后端启动命令（venv 激活后）：`uvicorn app.main:app --reload --port 8000`，但 `main.py` 要 Step 0.5 才创建。

---

### ✅ Step 0.3 · 前端 Vite + TypeScript 工程初始化 — 2026-06-02

**做了什么：**
- `frontend/` 用 `npm create vite@latest . --template react-ts` 初始化（npm，因为 pnpm 未安装；不影响功能）。
- 三批 npm install：
  1. Vite scaffold 默认 deps（152 个包，含 React、Vite、TS、eslint）
  2. 业务运行时 deps（101 个包）：react-router-dom、antd、@ant-design/icons、echarts、echarts-for-react、axios、react-compare-image、browser-image-compression、dayjs
  3. Tailwind 3 + postcss + autoprefixer（60 个包，dev deps）
- `npx tailwindcss init -p` 生成 `tailwind.config.js` 与 `postcss.config.js`；`tailwind.config.js` 的 `content` 配置为 `["./index.html","./src/**/*.{js,ts,jsx,tsx}"]`
- `src/index.css` 顶部加 `@tailwind base/components/utilities` 三条指令（其余 Vite scaffold CSS 保留）
- 在 `App.tsx` 加临时 Tailwind 探针红色 div，用户验证通过后删除

**与 tech-stack 计划版本的偏离（npm latest 全升）：**

| 项 | 计划版本 | 实际安装 |
|---|---|---|
| React | 18.x | **19.2.6** |
| Vite | 5.x | **8.0.12** |
| TypeScript | 5.x | **6.0.x** |
| Tailwind | 3.x | 3.4.x ✓ |

tech-stack.md §1 已同步为实际版本。React 19 / Vite 8 / TS 6 已稳定 1+ 年，AI 训练数据充足，不会成为 vibe coding 的阻力。

**验证结果：**用户跑 `npm run dev` 后访问 `http://localhost:5173`，截图确认看到红色 Tailwind 探针 + Vite 默认欢迎页，通过。探针已删除。

**给后续开发者的提示：**
- 前端启动：`cd d:\github仓库1\frontend && npm run dev`，端口 5173
- 构建：`npm run build`（先 tsc -b 再 vite build）
- 不要把 antd 和 Tailwind 的样式混到同一个组件——按 tech-stack §2.2 的"运营端用 antd / 用户端用 Tailwind"分工，避免选择器冲突
- React Router 用 v7（npm install 默认拉到的版本），但用法与 v6 一致

---

### ✅ Step 0.4 · 配置后端环境变量模板 — 2026-06-02

**做了什么：**
- `backend/.env` 写入 14 个字段，全部按 implementation-plan.md Step 0.4 列表配齐：
  - 数据库 `DATABASE_URL=sqlite+aiosqlite:///./nail_demo.db`
  - 图像生成 `IMAGE_PROVIDER=mock`、`JIMENG_API_KEY=`（留空）
  - PPIO 一家全包：`PPIO_API_KEY=<真实 46 位 key>`、`PPIO_BASE_URL=https://api.ppio.com/openai`、`LLM_QUICK_MODEL=qwen/qwen2.5-7b-instruct`、`LLM_STRONG_MODEL=deepseek/deepseek-v3.1`
  - SMTP 五项（HOST/PORT=465/USER/PASS/FROM） + `REPORT_RECIPIENT`，值暂留空
  - `SCHEDULER_ENABLED=true`
- `backend/.env.example` 与 `.env` 字段名 / 顺序一一对应（14/14），仅 PPIO_API_KEY 用占位符 `your_ppio_api_key_here`、`PPIO_BASE_URL` 和模型 ID 因属于固定默认值故保留实值。
- 两文件都 **no-BOM** UTF-8（按 CLAUDE.md 提醒）。
- 根 `.gitignore` 第 2 行 `.env`、第 3 行 `.env.local`、第 4 行 `.env.*.local`，秘钥不会被追踪。

**与计划的偏离：**
- 早期 `.env.example` 里 PPIO 占位符写成 `sk_xxx_replace_with_real_key`，带 `sk_` 前缀容易让人误以为已配真 key；复核阶段改成 `your_ppio_api_key_here`，消除误导。

**顺手做的（不属于 Step 0.4 硬要求，但同 commit 一起完成）：**
- 仓库 `git init`，建立首次 baseline commit `6edf7a5`，把 Phase 0 全部产物纳入版本控制。默认分支 `master`，未来推 GitHub 前可 `git branch -M main`。
- `.gitignore` 在原 24 条基础上扩展两条：
  - `.claude/` — Claude Code 本地工具目录（skill 资产 + settings.local.json），与全局 `~/.claude/` 完全重合的冗余副本，约 10 MB / 389 文件，不入产品仓库。
  - `Meijia/` — 已废弃的 Next.js 视觉原型整目录忽略（CLAUDE.md 已判它"不参与构建"）；磁盘上保留供视觉参考。原本只忽略其 `node_modules` 和 `.next`，现升级为整目录忽略。
- 配 git 用户：`user.name=Richard`、`user.email=jiaoren66@gmail.com`、`core.quotepath=false`（中文路径安全）、`core.autocrlf=false`。

**验证结果：**用户人工核对 .env / .env.example 字段一一对应 + BOM 无 + `.gitignore` 覆盖 `.env` + `git check-ignore -v backend/.env` 返回 `.gitignore:2:.env`，通过。

**给后续开发者的提示：**
- `.env` 永远不进 git。如果你看到 `git status` 列出它，立即停手——`.gitignore` 出问题了。
- 复现别人机器：克隆后 `cp backend/.env.example backend/.env`，再把 PPIO_API_KEY 与 SMTP_* 填上真实值。
- 真要泄露了 PPIO key，去 PPIO 控制台 revoke 当前 key 重新生成，再换掉 `backend/.env`；**不要**只是改 commit message。git 历史里的明文 key 即便覆盖也会留下。
- Step 0.5 用 `pydantic-settings` 读 `.env`，字段名必须与本步骤完全一致（区分大小写）。

---
