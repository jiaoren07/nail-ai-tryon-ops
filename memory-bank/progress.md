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

### ✅ Step 0.5 · 后端统一配置加载与启动健康检查 — 2026-06-06

**做了什么：**
- 新建 3 个文件：
  - `backend/app/__init__.py`（空，让 `app/` 成为 Python 包）
  - `backend/app/config.py`：`pydantic-settings` 的 `Settings` 类，14 个字段与 `.env` 一一对应，含 `case_sensitive=True` 和 `extra="ignore"`；模块底部直接 `settings = Settings()` 单例。
  - `backend/app/main.py`：FastAPI 应用 `app = FastAPI(title="Nail Demo API", version="0.1.0")` + `CORSMiddleware`（allow_origins=`["http://localhost:5173"]`）+ `GET /api/health` 路由，返回 `{code:0, msg:"ok", data:{service:"nail-demo", env:{IMAGE_PROVIDER, SCHEDULER_ENABLED}}}`。
- **未做**（避免提前优化）：health 路由没声明 `response_model`，Swagger Example Value 显示为通用 `{"additionalProp1":{}}` 占位；实际响应正常。统一响应包装留到 Step 2.2 做。

**验证结果：**
1. `python -c "from app.main import app, settings; ..."` import 成功，settings 正确加载 `.env`（IMAGE_PROVIDER=mock、SCHEDULER_ENABLED=true）；`app.routes` 含 `/api/health`。
2. `uvicorn app.main:app --port 8000` 启动，curl `/api/health` → HTTP 200，body 完全符合 Step 0.5 规格：`{"code":0,"msg":"ok","data":{"service":"nail-demo","env":{"IMAGE_PROVIDER":"mock","SCHEDULER_ENABLED":true}}}`。
3. curl 带 `Origin: http://localhost:5173` 的 OPTIONS 预检 → 返回 `Access-Control-Allow-Origin: http://localhost:5173`，CORS 配置生效。
4. 用户浏览器访问 `/docs` → Swagger UI 渲染正常，能看到 `GET /api/health`。

**Swagger UI 一次性空白事件（已解决，记录为参考）：**
- 第一次浏览器打开 `/docs` 是空白页面（HTML 框架返回了，但 Swagger UI 资源没渲染）。沙箱测 `cdn.jsdelivr.net/npm/swagger-ui-dist@5/...` 可达（HTTP 200）、`/openapi.json` 正常。**用户新开窗口重访即恢复**，判定为 jsdelivr CDN 一次性网络抖动，非代码 bug。
- 风险点：jsdelivr 在国内不稳是已知问题。如果后续频繁踩坑，再考虑换 `cdn.staticfile.org`（七牛云）或自托管 swagger-ui 静态文件到 `backend/static/swagger/`。**Step 0.5 不预先处理**。

**给后续开发者的提示：**
- **启动后端**：`cd d:\github仓库1\backend && .\.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000`。`--reload` 仅开发用，生产去掉。
- **配置访问**：在路由/服务里 `from app.config import settings` 直接拿单例，不要每次 `Settings()`（每次重新 parse `.env` 浪费）。
- **新增 .env 字段**：必须三处同步——`backend/.env`、`backend/.env.example`、`backend/app/config.py` 的 `Settings` 类。任何一处漏，下次启动可能崩或字段读不到。
- **`extra="ignore"`** 让多余字段不报错——如果用户 `.env` 里有 `OPENAI_API_KEY` 之类历史字段，pydantic 不会因此拒绝启动；但**也不会被读取**，要用必须先在 `Settings` 加字段。
- **`/docs` 空白时的快速判定**：F12 → Network 看 `swagger-ui-bundle.js` 状态码。200 = 资源拉到了去看 Console JS 错误；failed/pending = CDN 网络问题。
- Step 1.1 用 SQLAlchemy 模型，导入连接字符串走 `settings.DATABASE_URL`（aiosqlite URL，相对 backend/ 目录的 `nail_demo.db`）。

---

### ✅ Step 1.1 · 定义 6 张表的 SQLAlchemy 模型 — 2026-06-06

**做了什么：**
- 新建 `backend/app/models/__init__.py`（121 行）：`Base` (DeclarativeBase) + 6 个 ORM 模型 `Style` / `Tryon` / `StyleStats` / `OpsAction` / `Report` / `Notification`。字段名、类型、可空、默认值严格对照 design-docu §4.2。
- 新建 `backend/app/db.py`（12 行）：用 `settings.DATABASE_URL` 创建 `engine = create_async_engine(...)`，提供 `async def init_db()`，调用 `Base.metadata.create_all` 建所有表（已存在则跳过）。
- 5 个索引按 §4.3 声明在各模型的 `__table_args__` 里：`ix_tryons_style_created` / `ix_tryons_user_created` / `ix_style_stats_date_tryons` / `ix_reports_type_end` / `ix_notifications_unread_recent`。
- `style_stats` 表加 `UniqueConstraint(style_id, stat_date, name="uq_style_stats_style_date")`——SQLAlchemy 自动落为唯一索引。

**Step 1.1 验证（全部 PASS）：**
1. `await init_db()` 跑一次 → `backend/nail_demo.db` 被创建（56 KB）。
2. `sqlite_master` 查 6 张表：`notifications/ops_actions/reports/style_stats/styles/tryons` 全部出现，字段数依次为 8/6/11/7/13/9，与 design-docu 完全一致。
3. `sqlite_master` 查显式索引：5 条全部出现（即 §4.3 列出的 5 条；UNIQUE 索引 + FK 自动索引不计入这 5 条）。
4. 再跑一次 `await init_db()` 无报错、无重复建表（`create_all` 自带 IF NOT EXISTS）。✅ 幂等。

**设计偏离 / 选择（与 docu 对齐但有理由）：**

| 项 | 选择 | 原因 |
|---|---|---|
| `is_active` / `is_collected` / `is_read` | `Integer` 0/1 | docu §4.2 标 "INT"，0/1 语义在 seed 脚本里更直观；SQLite 反正都是 INT 存 |
| `DateTime` 默认值（app 层） | `default=_utcnow`（Python 函数） | docu §4 时区约定要求 UTC；seed 脚本会显式覆盖 |
| `DateTime` 默认值（docu 明示 `CURRENT_TIMESTAMP`） | `server_default=func.current_timestamp()` | `reports.generated_at` + `notifications.created_at` 走 SQL 层默认（SQLite 的 CURRENT_TIMESTAMP 是 UTC，符合时区约定） |
| `style_tags` | `Text`（JSON 字符串） | docu §4.2 标 "TEXT (JSON array)"；app 层 `json.dumps/loads`，不引入 SQLAlchemy 的 JSON 列类型（aiosqlite 对 JSON 支持需额外配置，过度工程） |
| 5 个索引省略 `DESC` 修饰 | 直接按列建 ASC | docu §4.3 标 DESC 是查询提示；SQLite B-tree 双向遍历，对 `ORDER BY ... DESC` 无影响；Step 1.1 验收"等价命名"允许 |
| `Base` 位置 | 放在 `app/models/__init__.py` 顶部 | 6 个模型一共 100 行，单文件最简；未来拆分再说，避免过早抽象 |
| 模型不分文件 | 6 个模型全部写在 `app/models/__init__.py` | 同上 |
| `app/db.py` 在 Step 1.1 创建（而非按 plan 等 Step 2.1） | 提前创建只放 engine + init_db | 避免 Step 1.1 init_db 与 Step 2.1 engine 产生两份独立 engine；Step 2.1 只在 db.py 增加 `async_session_maker` + `get_db` 依赖即可，不冲突 |

**给后续开发者的提示：**
- **新增模型**：在 `app/models/__init__.py` 里加新类（继承 `Base`），写到 `__all__` 列表，重启后端就会建表（dev 期）。生产环境用 Alembic 迁移，Demo 阶段不引入 Alembic。
- **新增索引**：在 `__table_args__` 里加 `Index(...)`，删 db 再 `init_db()` 重建。`create_all` **不会**自动迁移已存在表的 schema（这是 SQLAlchemy 不是 ORM 缺陷）。
- **engine 单例**：`from app.db import engine` 拿，不要 `create_async_engine` 创第二份；连接池配置统一在 `db.py` 调（目前默认配置足够 Demo）。
- **Base 是登记处**：任何继承 `Base` 的模型只要被 import 过一次，就会出现在 `Base.metadata.tables` 里。Step 2.1 init_db 调用前，确保 `from app.models import ...` 已经执行（`__init__.py` 顶部 import 就够了）。
- **seed 脚本（Step 1.2-1.5）操作模式**：直接用 `from app.db import engine` + `AsyncSession(engine)` 自己写 with-block；不需要走 FastAPI 的 `get_db` 依赖。
- **删 nail_demo.db 想从头来**：直接删文件即可，下次启动 `init_db()` 自动重建；`*.db` 在 `.gitignore` 里不进仓。

---

### ✅ Step 1.2 · 导入款式库的 seed 脚本 — 2026-06-06

**做了什么：**
- 新建 `backend/scripts/seed_styles.py`（124 行）：从外部数据集 `d:\美团AI HACKATHON\dataset\` 把 25 女 + 15 男 = 40 款入库 + 复制 40 张封面图到 `backend/static/styles/` + 复制 17 张示例手图到 `backend/static/samples/`。
- 表字段映射严格按 implementation-plan §1.2：
  - 女款 25：从 `styles/tags_qwen.json` 读，id = key 去 `_enh.png`（如 `f_01`），cover_url=`/static/styles/{id}_enh.png`，gender 强制 `female`
  - 男款 15：从 `styles/male/tags_qwen.json` 读，id = key 去 `.jpg`（如 `m_01`），cover_url=`/static/styles/{id}.jpg`，gender 信打标 JSON 的 `parsed.gender`（实测全部 `male`，无 `both`）
  - `name` = `style_tags[:3]` 拼接（如 `纯色极简`、`深色系个性酷炫`），允许后续人工覆盖
  - `style_tags` 存 `json.dumps(tags, ensure_ascii=False)`，保留中文原文
  - `color_main` / `color_tone` / `length_pref` / `complexity` / `gender` 全部从打标 JSON 的 `parsed` 字段直接映射
  - `heat_score=50.0`，`is_active=1`，`created_at=now(UTC)`
  - `display_order` 全局按 id 字典序填 0–39（女款占 0–24，男款占 25–39）
- 17 张手图 glob 用 `[0-9][0-9].png` 严格匹配编号文件，防止抓到非编号 PNG。
- 脚本顶部 `sys.path.insert(0, BACKEND_ROOT)`，让 `from app.X import` 在任何 CWD 下都能解析；DATASET_DIR 用绝对路径 `r"d:\美团AI HACKATHON\dataset"`。
- 幂等：`DELETE FROM styles` 再 INSERT；静态文件 `shutil.copyfile` 直接覆盖。

**git 配置同步（用户拍板）：**
- 根 `.gitignore` 新增 2 条：`backend/static/styles/` 和 `backend/static/samples/`。理由：两个目录都是 seed 脚本生成的派生资产，源头在外部 `d:\美团AI HACKATHON\dataset\`（CLAUDE.md 已经声明 dataset 在 repo 外），进 git 会带来 10~15 MB 重复存储 + 赛题数据集授权不明问题。与已存在的 `cache/` / `uploads/` 一致都归"运行时生成"忽略。
- 注释行同步从"recreated at runtime"改为"recreated by seed scripts or at runtime"。

**Step 1.2 验证（6/6 PASS）：**
1. `SELECT COUNT(*) FROM styles` = **40** ✅
2. `WHERE gender='female'` = **25**；`gender IN ('male','both')` 合计 = **15** ✅
3. `SELECT id FROM styles ORDER BY id` 首 5 = `f_01..f_05`，末 5 = `m_11..m_15` ✅
4. `backend/static/styles/` 含 **40 文件**（25 `f_*_enh.png` + 15 `m_*.jpg`）✅
5. `backend/static/samples/` 含 **17 PNG** ✅
6. 静态文件 URL 可访问 → **按 plan 延后到 Step 2.4**（静态挂载尚未实现）
7. 附加：`display_order` 0–39 全部 distinct，无重复 ✅
8. 附加：第二次 `python scripts/seed_styles.py` 总数仍 40，**幂等** ✅
9. 附加：CJK 字段写入与读取无 mojibake（如 `m_15.name = "深色系个性酷炫"`）✅

**给后续开发者的提示：**
- **跑 seed 之前**：`$env:PYTHONIOENCODING="utf-8"` 否则 print CJK 会乱码（不影响入库，只影响日志可读）。
- **数据集路径硬编码**：`DATASET_DIR = r"d:\美团AI HACKATHON\dataset"` 写死在脚本里，别人 clone 后必须有同样路径才能 seed。如果未来需要可移植，把它提到 `.env` 的 `DATASET_DIR` 即可（独立小改动）。
- **DELETE FROM styles 安全**：SQLite 默认 `PRAGMA foreign_keys=OFF`，引用 styles 的 tryons / style_stats 不会阻塞删表，但**单独跑 seed_styles 会留下悬挂的 style_id 引用**。要么连带 seed_tryons + seed_stats 一起重跑，要么用 Step 1.6 的 `seed_all.py` 一键全清。
- **`name` 字段不要随便改**：当前是 `style_tags[:3]` 拼接，前端 U2/U3 推荐页直接展示。如果人工覆盖个别款的 name 后再跑 seed，覆盖会被 DELETE+INSERT 抹掉——所以"人工覆盖"应该等 demo 稳定后再做，或把覆盖写成 SQL 文件版本化。
- **男款 gender 字段**：所有 15 个目前都是 `male`。如果未来改 VLM 模型重新打标，可能出现 `both`——seed 脚本会自动信赖 JSON，无需改代码。
- **静态文件被 gitignore 不进 git**：clone 后必须先 `python scripts/seed_styles.py` 才有图，否则后端 `/static/styles/...` 会 404。Step 2.4 静态挂载后也要先 seed。

---

### ✅ Step 1.3 · 人工指定款式角色（爆款/冷门/热门候选）— 2026-06-07

**做了什么：**
- 在 `backend/scripts/` 下创建两份配置：
  - `style_roles.json`：分 `female` / `male` 两个 pool，每个 pool 下 4 键 `stable_hot` / `emerging_hot` / `cold` / `long_tail`，对应 `style_id` 数组。
  - `style_roles_README.md`：40 行解释，每行 `<id>: <角色> — <一句话理由>`，对照 [tags_qwen.json](file:///d:/美团AI%20HACKATHON/dataset/styles/tags_qwen.json) 的打标维度做选定推导。
- AI 提议分配 + 用户拍板。完整 40 款角色见 [`style_roles.json`](../backend/scripts/style_roles.json)；推导依据见 [`style_roles_README.md`](../backend/scripts/style_roles_README.md)。

**角色分配速览：**

| pool | stable_hot | emerging_hot | cold | long_tail |
|---|---|---|---|---|
| female (25) | f_01, f_13, f_14 | f_09, f_15 | f_05, f_08, f_11 | 其余 17 款 |
| male (15) | m_01, m_06 | m_15 | m_10, m_13 | 其余 10 款 |

**关键选定策略（与 implementation-plan §1.3 三条原则的对应）：**
- `stable_hot` 命中"纯色/极简/法式/哑光/商务"等通用关键字 + 低复杂度。男款 `m_01` (warm) 与 `m_06` (cool) 故意选不同 tone，制造"两种稳态"对比。
- `emerging_hot` 选视觉辨识度最高的款：`f_09`（跳色+镶钻+复杂图案三冲击）、`f_15`（warm + 几何稀缺维度）、`m_15`（黑色 cool + 酷炫几何）。
- `cold` 选风格小众/反主流：`f_05`（25 款女款里唯一 short）、`f_08`/`f_11`（透明少见维度）、`m_10`/`m_13`（朋克标签极小众）。
- `long_tail` 兜底其余。

**Step 1.3 验证（全部 PASS）：**
1. `style_roles.json` 女款合并集合 = `f_01..f_25`，无重复无遗漏 ✅
2. `style_roles.json` 男款合并集合 = `m_01..m_15`，无重复无遗漏 ✅
3. 各角色名额数量精确匹配 plan（3/2/3/17 + 2/1/2/10）✅
4. `style_roles_README.md` 共 40 行 entry，格式 `- \`<id>: <角色> — <理由>\`` ✅
5. README ↔ JSON 每个 id 的角色赋值零冲突 ✅

**给后续开发者的提示：**
- **不在 DB 里**：角色分配是 seed 阶段的"导演控制"，不写入 `styles` 表。Step 1.4 `seed_tryons.py` 读这份 JSON 决定每款的 60 天行为分布。
- **改了角色就要重跑后续 seed**：调整某款的 cold→long_tail 等，跑 1.4 + 1.5 重生成行为/聚合数据才会生效，DB 里的 `styles` 表不需要动。
- **plan 里的 stable_hot 数量 (3)** 跟分配数量对应。所有数值改动要同时改 plan 和 README（不要单边偏移），否则 Step 1.4 的概率分布会算错。
- **README 的 markdown 格式很严格**：每条 entry 必须是 `` - `<id>: <role> — <reason>` ``（反引号包整段、有 em-dash 分隔），否则 Step 1.4 的脚本如果想读 README 解析角色会失败。Step 1.4 实际读 JSON 不读 README，README 只是给人看的依据。
- **角色不是性能 KPI**：演示阶段 `emerging_hot` 在最后 5 天指数增长 → O2 爆款看板会高亮；`cold` 在 O3 冷门看板会预警。前端实际是按 `style_stats` 聚合表读数，不直接读这份 JSON。

---

### ✅ Step 1.4 · 生成 60 天历史试戴行为 — 2026-06-07

**做了什么：**
- 新建 `backend/scripts/seed_tryons.py`：从 `style_roles.json` 读两个 pool 的角色分配，生成 60 天试戴行为。
- 新建 `backend/scripts/_check_tryons.py`（内部校验工具，下划线打头）：一键跑 Step 1.4 全部 5 条验证项，避免 5 条内联 PowerShell SQL 命令踩双重引号坑。
- 时间窗口：`[今天−59, 今天]` 共 60 天（含今天），以北京时区（UTC+8）为锚。事件时间存储为 naive UTC，SQL 查询统一加 `'localtime'` 修饰符转回北京日，符合 design-docu §4 时区约定。
- 字段分布：
  - `user_id` 随机 UUID v4
  - `user_gender` 永远从 `style.gender` 派生（女款 → female，男款 → male，both 50/50；严守 plan 警告"不要 70/30 全局抽样"）
  - `skin_tone` / `hand_shape` 各从 5/3 个枚举均匀抽取
  - `from_module` 按 50/30/20 概率取 `recommend`/`browse`/`compare`
  - `is_collected` 按角色概率：stable_hot 25% / emerging_hot 30% / cold 5% / long_tail 12%
  - `created_at` 北京时间 hour ∈ [8, 23]，转 UTC 存储

**plan §1.4 字面表述歧义 + 我的解读（透明告知）：**
implementation-plan 的 "stable_hot 款每日 80-150 次" 等没明示 per-style / per-pool / per-bucket-global 哪种。三种解读分别算下来：

| 解读 | 总数估算 | 验证 [4000, 18000] |
|---|---|---|
| per-style（每款独立跑） | ~75000 | ❌ 远超 |
| per-pool-per-bucket（性别 × 角色独立日配额） | ~19000 | ❌ 略超 |
| **混合**（用过的最终方案） | ~12000~13000 | ✅ 稳过 |

**混合解读分桶规则**：

| 角色桶 | 解读 | 理由 |
|---|---|---|
| stable_hot | bucket-global（5 款共享 80-150/日） | 不然单桶就破 18000 |
| long_tail | bucket-global（27 款共享 5-40/日） | 同上 |
| **emerging_hot** | **per-style** + spike base [30, 40] | bucket-global 会让 3 款共分 spike 峰值被稀释到 ~30，达不到 plan 要求的 5× peak ratio |
| cold | per-style ≤ 20 | 验证文明文要求 |

**spike base 调整**：plan 字面是 [10, 30]，但 plan 自己要求 peak day ≥ 5× pre-55 avg。pre-55 avg 是 20（[10, 30] 中点），所以 peak day 需要 ≥ 100。mult=3.5 时 base 必须 ≥ 28.6。用 [30, 40] 留 margin，确保多次 reseed 都过。

**Step 1.4 验证（5/5 PASS，独立 reseed 三次都过）：**

| 验证项 | 实测 |
|---|---|
| 1. 总数 ∈ [4000, 18000] | 12590 / 13050 / 13233（用户验证那次） |
| 2. 日期范围 = [2026-04-09, 2026-06-07] | 精确匹配北京日 |
| 3. emerging_hot 每款 peak ratio ≥ 5× | f_09=6.23×, f_15=7.30×, m_15=6.11×（用户验证） |
| 4. cold 每款 ≤ 20 | 最大 19（17, 19, 11, 14, 17） |
| 5. cross-pollination = 0 | female_style × male_user = 0，male_style × female_user = 0 |

**副产物自检**（不在硬验证里但顺便看）：
- `is_collected` 收藏率：stable 25% / emerging 31% / cold 7% / long_tail 12% → 与配置概率高度吻合
- `from_module` 来源分布：49.6% / 30.4% / 20.0% → 精确匹配 50/30/20 概率
- 时间分布：北京 8:00–23:59 内随机，转 UTC 后 `date(created_at, 'localtime')` 仍能正确回到北京日

**给后续开发者的提示：**
- **re-seed 后必跑 `_check_tryons.py`**：一行命令验证全部，特别是 emerging_hot 5× 验证项对随机方差敏感，连续 reseed 偶尔可能逼近 5× 边缘；几乎所有失败都是 spike base 设置或角色 emerging 数量改变导致的。
- **跑 seed_tryons 前必须先 seed_styles**：`tryons.style_id` 引用 `styles.id`，虽然 SQLite 默认 FK off 不阻塞，但 styles 表为空时随机选不到东西会崩。
- **时间存储约定**：seed 写 naive UTC datetime；查询统一用 `date(<col>, 'localtime')` 转北京日。两边对齐这一条，整个时序逻辑就不会错位。
- **角色概率调整入口**：`COLLECT_PROB_BY_ROLE` 字典在 `seed_tryons.py` 顶部，改动后重跑即可。其他常量（SKIN_TONES、HAND_SHAPES、FROM_MODULES_BAG）同位置。
- **每天试戴量调整**：`_daily_bucket_count`（stable / long_tail）和 `_daily_per_style_emerging_count`（emerging）两个函数是数量旋钮，改这里。如果再改 spike base 或 multipliers，记得跑 `_check_tryons.py` 看 5× 验证是不是还过。
- **`_check_tryons.py` 是工具不是产品**：以下划线开头明示，将来 commit 进仓但不参与运行时；如果觉得碍事可以删，重写一份验证 SQL 也能跑。

---

### ✅ Step 1.5 · 生成 style_stats 聚合数据 — 2026-06-07

**做了什么：**
- 新建 `backend/scripts/seed_stats.py`：从 `tryons` 表按 `(style_id, date(created_at, 'localtime'))` GROUP BY 聚合到 `style_stats`。
- 聚合字段映射：
  - `tryon_count` = `COUNT(*)`
  - `collect_count` = `SUM(CASE WHEN is_collected = 1 THEN 1 ELSE 0 END)`
  - `exposure_count` = `tryon_count × random.uniform(8, 20)`
  - `click_count` = `max(tryon_count, exposure_count × random.uniform(0.05, 0.25))`
- 日期分桶用 `date(created_at, 'localtime')`，把 UTC 存储的 `created_at` 转回北京日，确保聚合粒度是北京日历日（与 design-docu §4 时区约定一致）。
- `stat_date` 从字符串 'YYYY-MM-DD' 通过 `date.fromisoformat()` 转 `datetime.date` 后入库，SQLAlchemy 的 `Date` 列正确写入。
- 幂等：`DELETE FROM style_stats` 再 INSERT。

**Step 1.5 验证（3/3 PASS + 用户手动验证一致）：**

| 验证项 | 实测 | 结果 |
|---|---|---|
| 1) `COUNT(*) FROM style_stats` ∈ [1000, 1500] | **1433** | ✅ |
| 2) 抽 5 行检查 `click >= tryon` 且 `exposure >= click` | 5/5 全部满足不变式 | ✅ |
| 3) `SUM(tryon_count)` == `COUNT(*) FROM tryons` | 13233 == 13233（完全相等）| ✅ |
| 附加：幂等性（重跑 1433 → 1433） | 完全相同 | ✅ |

**plan 验证范围 [1000, 1500] 的边界注释：**
plan 当时假设 25 女款，所以 "25 × 实际有数据的天数 = 1500 上限"。我们现在 40 款，理论上限 40 × 60 = 2400。实测 1433 仍落进原范围，原因是 **long_tail 27 款共享 bucket-global 5-40 events/日，分摊后每款每日期望事件 < 1**，许多 `(style_id, stat_date)` 组合没数据 → 不产生行。这个"自然稀疏"刚好让总数与 plan 旧范围吻合，**纯属巧合不是设计**。如果有人调整 long_tail 数量或 bucket-global → per-style，这个边界会被突破。

**副产物自检（不在硬验证但顺便看）：**
- 不同 stat_date：60（北京日完整覆盖 [2026-04-09, 2026-06-07]）
- 不同 style_id：40（每款都至少一天有数据）
- `exposure / tryon` 倍数实测 [8.0, 19.94]，avg 13.78 → 完全吻合 `random(8, 20)`
- `click / exposure` 比例实测 [0.051, 0.248]，avg 0.136 → 完全吻合 `random(0.05, 0.25)`
- 56% 的行 `collect_count = 0` —— cold/long_tail 的低收藏天数自然占比

**给后续开发者的提示：**
- **顺序依赖**：必须先 `seed_styles.py` 再 `seed_tryons.py` 再 `seed_stats.py`。前两步漏掉，`style_stats` 会空表。Step 1.6 的 `seed_all.py` 强制顺序。
- **`exposure_count` 和 `click_count` 是合成数**：plan 没有真实曝光/点击日志，这两列是按 tryon 倍率反向编造，用于 O3 冷门看板的"曝光点击比"诊断。**修改公式会影响 O3 阈值**：plan §7.3 定义"近 7 天点击曝光比 ≤ 2%"为冷门触发条件之一，当前公式给出的实际比例分布在 [5%, 25%]，所以这条规则在现状下不会误报；但如果你调倍率到 [2, 5]，就要相应调阈值。
- **`stat_date` 是北京日**：所有运营端"今日/本周/近 7 天" SQL 都应该用 `date('now', 'localtime')` 跟这一列对齐，不要用裸 `date('now')`（默认 UTC，凌晨 0-8 点会错位 1 天）。
- **重跑 seed_stats 是安全的**：只动 `style_stats` 表，不影响 `tryons` / `styles`。但 seed_stats 的结果依赖当下 `tryons` 内容，所以**改了 seed_tryons.py 后必须连带重跑 seed_stats**，否则 stats 数据与 tryons 不一致。
- **`exposure_count >= click_count` 不变式靠 `max()` 兜底**：极端低 tryon_count 时（如 tryon=1），`exposure ≈ 12`、`click = max(1, exposure × random(0.05, 0.25))` 可能正好等于 `tryon_count`。这是有意的边界保护，不是 bug。

---

### ✅ Step 1.6 · 统一 seed 入口 — 2026-06-08

**做了什么：**
- 新建 `backend/scripts/seed_all.py`（73 行）：一条命令完成 `init_db()` → `seed_styles()` + `_copy_static()` → `seed_tryons()` → `seed_stats()` 全链路。每步打印时间戳 + 受影响行数 + 该步骤耗时。Pipeline 设计成把各步独立函数串起来，不复用各文件的 `_main()`，避免重复 `engine.dispose()` 与 `asyncio.run()` 冲突。
- 改 `seed_tryons.py` + `seed_stats.py`：两个函数入口加 `random.seed(42)`，让任何机器、任何时间跑 `seed_all.py` 给出**严格一致**的结果（满足 plan §1.6 验证要求"数据条数应与第一次完全相同"）。

**为什么固定种子=42 而不是基于时间：**
plan §1.6 验证文明文要"完全相同"。如果不设种子，连续两次跑会得到不同行数（前次实测 12392 → 12751 → 12847）。固定种子让：
1. 验证 4 "幂等" 强约束达到 → 三次连续运行 `seed_all.py` 给出 `12847 / 1432` 三次完全一致
2. 演示数据可复现：bug 出在哪条数据上，跨机器 reseed 一定能重现
3. `_check_tryons.py` 的 peak ratio 等 "接近边界" 验证不再受随机方差影响（实测 6.97×/7.10×/7.22× 稳定通过）

UUID（`user_id`）仍然走 `os.urandom`（uuid.uuid4 的底层），所以每次 `user_id` 不同；只是行数与分布完全一致。

**Step 1.6 验证（4/4 PASS）：**

| 验证项 | 实测 | 状态 |
|---|---|---|
| 删 `nail_demo.db` 后一条命令跑通全 seed | 5.6 秒完成 | ✅ |
| 打印 `styles=40 tryons=XXXX stats=YYYY` 与 DB 一致 | `40 / 12847 / 1432` 三处完全一致 | ✅ |
| 全脚本 < 60 秒 | 5.6 秒（**远**低于 60s 预算） | ✅ |
| 第二次连续运行结果完全相同（幂等） | 三次独立运行均产出 12847/1432 | ✅ |

**给后续开发者的提示：**
- **首次 clone 后初始化数据库**：`cd backend && .\.venv\Scripts\Activate.ps1 && del nail_demo.db; python scripts\seed_all.py`，5-6 秒全部就绪。
- **修改了任意 seed 脚本后**：跑 `seed_all.py` 重建全表，而不是只跑改动的那个——避免下游表（如 `style_stats`）与上游（`tryons`）漂移。
- **演示数据想换一套**：改 `random.seed(42)` 里的 42 为别的整数即可，整个数据集会沿同样规则生成新一套确定数据。
- **想恢复"每次都微随机"**：把两处 `random.seed(42)` 删掉，但会失去 plan §1.6 的"完全相同" idempotence。
- **演示前必跑 `seed_all.py`**：保证演示场景从干净基线出发。如果 demo 当中跑了真实试戴生成新 tryons 后想 reset，再跑一次 `seed_all.py` 5 秒内恢复。
- **`_copy_static()` 是同步调用**：seed_all 里没用 await，因为它是普通函数（`shutil.copyfile` 同步）。同样的，未来要并行化 IO 必须改造该函数。
- **Phase 1 全部完成**：6 张表 + 数据全部就位。下一步进 Phase 2 后端基础设施（DB 注入、统一响应包装、路由骨架、静态挂载），开始为 Phase 4 真正的业务 API 铺路。

---

### ✅ Step 2.1 · 数据库依赖注入 — 2026-06-09

**做了什么：**
- `backend/app/db.py` 扩展（在 Step 1.1 已有的 `engine` + `init_db()` 基础上）：
  - 加 `async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)`
  - 加 `async def get_db() -> AsyncIterator[AsyncSession]`：FastAPI 异步生成器依赖，`async with` 自动关 session、异常 rollback。
- `backend/app/main.py` 接入 lifespan：
  - 用 `@asynccontextmanager` 包 `lifespan(app)`，在 `yield` 前调用 `await init_db()`
  - `FastAPI(..., lifespan=lifespan)` 接入
  - 不用已废弃的 `@app.on_event("startup")` 装饰器
- **验证用的 `/api/_debug/count_styles` 路由按 plan 要求加了 → curl → 移除**，main.py 落地状态干净，路由清单仅含 5 条标准（`/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc`, `/api/health`）。

**Step 2.1 验证（5/5 PASS，用户人工核对）：**

| 维度 | 证据 |
|---|---|
| 路由清单干净（无 `_debug` 残留） | 用户跑 import smoke 输出 5 条标准路由 |
| `init_db()` 被 lifespan 调用 | uvicorn 输出 `Application startup complete` |
| `get_db` 撑起接口（plan §2.1 临时调试路由）| 用户 curl `/api/_debug/count_styles` → HTTP 200 body=`40` |
| `/api/health` 响应结构未被破坏 | 用户 curl 返回 `{code:0,msg:"ok",data:{service:"nail-demo",env:{IMAGE_PROVIDER:"mock",SCHEDULER_ENABLED:true}}}` 完全匹配 Step 0.5 形状 |
| 应用能优雅关闭 | Ctrl+C 后 uvicorn 打印 `Application shutdown complete` |

注意：plan 验证 body 写"返回 25"，是 25 女款时代的数字；现在 40 款返回 40，符合预期扩展。

**给后续开发者的提示：**
- **新增需要 DB 的路由**：在 `routers/user.py` / `routers/ops.py`（Phase 2.3 创建）里 `db: AsyncSession = Depends(get_db)`，会自动拿到 session。不要在路由里 `from app.db import async_session_maker` 手动创建——失去 FastAPI 依赖管理的好处（异常 rollback、生命周期对齐请求）。
- **`expire_on_commit=False` 的副作用要懂**：commit 后 ORM 对象的属性不会被标记过期，直接读不会重发 SQL。优点：Step 4.6 "试戴写入后立即返回 id + result_url" 流程不需要 `refresh()`。陷阱：如果某行被别人改了，commit 后再读还是旧值——但 demo 单进程不会触发。
- **lifespan vs on_event**：FastAPI 0.93+ 推荐 lifespan，未来 Step 9.2 接 APScheduler 时会复用——`yield` 前 `scheduler.start()`，`yield` 后 `scheduler.shutdown()`，不用拆两个 startup/shutdown handler。
- **`/api/_debug/*` 调试路由约定**：plan 全篇这种"加→验→删"的临时路由都走 `/api/_debug/` 前缀，commit 时务必清空。一个 grep `_debug` 还能看到东西就是泄漏。
- **`get_db()` 不要嵌套使用**：一个请求一个 session。不要在一个请求里 `async for s in get_db()` 拿第二份，会触发新连接，不必要的开销。

---
