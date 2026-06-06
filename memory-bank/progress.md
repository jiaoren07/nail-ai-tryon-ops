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

### 📝 设计修订（非 Step）· L0 + U0/U1 swap + O7=设置中心 + 品牌色板 — 2026-06-06

**背景：**
用户提供原型 Board 0~9（共 11 张图，含一张早期合并版）+ 17 色品牌色板。比对发现 4 处现行 docu 与原型差异：
1. 原型 Board 0 是 L0 双端入口 landing，docu 里 `/` 直接 redirect 到 `/upload`，缺这一层
2. 原型流程是"先性别后上传"（Board 1 三屏顺序：U0 性别 → U1 上传 → U2 推荐），docu 是反的
3. 原型 Board 9 是"设置中心"4 tab，不是 docu 里写的"O7 报告中心"独立页面
4. docu 里没有品牌色板的 single source of truth，前端配色无锚

**做了什么（commit `e7f91a4`）：**

- **L0 双端入口落入 design-docu §6.0**：双端入口 + `/` 改为完整页面而非 redirect；implementation-plan 新增 Step 5.2 "L0 双端入口"，原 Phase 5 步骤 5.2~5.7 顺序下移并改名：5.3=U0 性别、5.4=U1 上传、5.5=U2 推荐、5.6=U3 浏览、5.7=U4 对比、5.8=U5 结果。Phase 5 标题从"6 步"改"8 步"。
- **U0/U1 swap**：design-docu §6.1 = U0 性别选择页（路由 `/gender`，无前置守卫，从 L0 跳来或直接访问都允许）、§6.2 = U1 手图上传页（路由 `/upload`，前置守卫检查 sessionStorage 的 `userGender` 存在）。implementation-plan Step 5.3 / 5.4 同步重写。
- **O7 重定义为设置中心**：design-docu §7.7 完整改写——4 tab（账号工作台 / 通知与邮件订阅 / AI 助手偏好 / 显示与界面）。原"独立报告中心 `/ops/reports` 列表"取消，历史报告列表降级到「通知与邮件订阅」tab 底部最近 10 条；报告详情路由 `/ops/reports/:id` 保留（铃铛通知或设置中心列表行点击进入）。**后端 APScheduler + reports/notifications 表 + 邮件发送子系统全部保留**——只是前端入口集中。Phase 9 标题改为"报告通知子系统 + O7 设置中心"，Step 9.4 重写为"O7 设置中心前端（含通知与邮件订阅 tab + 报告详情）"。§13.3 标题去掉"O7 报告中心叙事"措辞。
- **品牌色板入 tech-stack §2.5**：核心 5 色记忆点（`#FFD100` Brand / `#111111` Ink / `#FAF8F2` Page / `#FFFFFF` Card / `#7C5CFF` AI Purple）+ 完整 17 色 token 表（brand / surface / text / line / ai / semantic 六大类）+ Tailwind config（用户端）+ antd ConfigProvider token（运营端）双端映射。声明为 single source of truth，新颜色一律先回到 §2.5 加 token；组件内禁止裸写 hex。

**附带改动：**
- design-docu §2.1 架构图：把"展现层"加一行"共享入口 L0（/，双端分流 landing）"
- §11.2 路由表：完整刷新（/=L0、/gender=U0、/upload=U1、/ops/setting=O7、/ops/reports/:id 保留为详情入口）
- §10 / §12.2 / §13.3 / 附录 A 文件结构里所有"报告中心"措辞统一改"设置中心"或"报告/通知子系统"
- §1.3 演示故事主线**没动**——原文本来就符合"先选性别再上传"的流程
- tech-stack §2.2 `O1-O6` 笔误改 `O1-O7`，并补一句"两端共用 §2.5 色板"
- implementation-plan Step 5.1 验证路径数从"约 13 个"改"约 15 个"（L0 + 7 user + 7 ops）

**验证：**用户在 AskUserQuestion 里逐项拍板（Landing 编号=L0、铃铛保留、4 份 docu 一次性 commit、色板按表 = 5 核心 + 完整 17）。docu 改完镜像 root ↔ memory-bank 三对全部 SHA256 一致。

**影响范围：**
- 6 个文件改动：`design-docu.md` / `implementation-plan.md` / `tech-stack.md` 各 root + memory-bank 副本，单次 commit `e7f91a4` 提交（478 insertions / 232 deletions）
- 后续 Step 5.x **必须按修订后的顺序与编号**执行
- 前端实现要严格按 tech-stack §2.5 的 token 配置 Tailwind 与 antd
- Step 0.1 ~ 0.4 全部保持有效，无回滚

**给后续开发者的提示：**
- 看到 Step 5.2 / 5.3 这种编号请按**修订后**的语义理解：Step 5.2 = L0 landing、5.3 = U0 性别、5.4 = U1 上传。**不是**旧版的"5.2=上传、5.3=性别"。
- `/ops/reports`（列表）路径已经不存在，只剩 `/ops/reports/:id` 详情；不要复活旧的独立列表页路由。
- 颜色一律从 tech-stack §2.5 引用，禁止在组件文件里裸写 hex。AI 紫不在 antd 标准 token 里，运营端通过 CSS var `--ai-purple` 引用。
- O4 没有独立 UI Board——它的前端入口被合并到 O7 设置中心 →「通知与邮件订阅」tab 底部。
- 关联的原型图在仓库根 `原型1/` 下（Board_00 ~ Board_09），文件按 Board 编号 + 模块名规范命名（详见下一条 prototype 整理记录）。

---

### 🗂 原型1/ 目录整理（非 Step）— 2026-06-06

**做了什么：**
- 用户提供的 11 张设计稿原型放在 `原型1/`，原文件名是 `image(5).png ~ image(10).png` + 5 个 UUID 命名 PNG，无序、不可读。
- AI 比对每张图的 Board 标签与内容，给出对齐方案；用户拍板确认。
- `image(10).png` 是早期 Board 6 三合一汇总版（同时画 O4 日报 + O5 助手 + O6 列表），后期被拆成独立 Board 6 (O3)、Board 7 (O5)、Board 8 (O6) 取代——**直接删除**（不保留 legacy 副本，避免与正式 Board 6 编号冲突）。
- 其他 10 张按 `Board_NN_<前端>_<模块>_<语义>.png` 模式重命名，详见 commit。

**命名规则：**`Board_NN_<侧>_[模块号_]<语义>.png`
- `NN` = 两位数 Board 序号，与原型自标 Board 一致（00~09）
- `<侧>` = `L0` / `user` / `ops` 三种之一
- `<模块号>` = 仅运营端 ops 侧带（O1~O7），用户端因为一张 Board 通常含多个 U 模块而省略
- 例：`Board_00_L0_landing.png`、`Board_07_ops_O5_ai_chat.png`

**与现行 docu 的对应：**
- Board 0 ↔ design-docu §6.0 (L0)
- Board 1 ↔ §6.1 + §6.2 + §6.3 (U0/U1/U2 三屏同框)
- Board 2 ↔ §6.4 + §6.5 (U3/U4)
- Board 3 ↔ §6.6 + §6.7 (U5/U6)
- Board 4 ↔ §7.1 (O1)
- Board 5 ↔ §7.2 (O2)
- Board 6 ↔ §7.3 (O3)
- Board 7 ↔ §7.5 (O5) ← **注意 §7.4 O4 没有对应 Board**，因为 O4 是后端业务逻辑，前端入口被合并到 O7 设置中心
- Board 8 ↔ §7.6 (O6)
- Board 9 ↔ §7.7 (O7 设置中心)

**给后续开发者的提示：**
- 实现 Step 5.x / 7.x 时直接打开对应 Board PNG 对照，不要凭记忆推 UI 细节。
- `原型1/` 目录约 16.85 MB（10 张 PNG），已纳入 git，未来增删要走正式 commit。
- 如果设计需要迭代（出现 `原型2/`），按相同 `Board_NN_*` 规则命名；不要混到 `原型1/` 里。

---
