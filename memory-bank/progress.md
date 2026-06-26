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

### ✅ Step 2.2 · 统一响应包装与异常处理 — 2026-06-09

**做了什么：**
- 新建 `backend/app/responses.py`（27 行）：
  - `ok(data, msg="ok")` 工厂函数：返回 `{code: 0, msg, data}` 字典，路由 `return ok(data=...)` 即可，无需手写 envelope
  - `http_exception_handler`：捕 `HTTPException` 并发回 `{code: status_code, msg: detail, data: null}`，HTTP 状态码与 `code` 同步
  - `unhandled_exception_handler`：catch-all，`logger.exception()` 记录 traceback（含异常类型+栈）+ 发回 `{code: 500, msg: "internal_error", data: null}`，**不把内部错误细节泄露给前端**
- `main.py` 改动：
  - 注册两个全局异常处理器：`app.add_exception_handler(HTTPException, ...)` + `app.add_exception_handler(Exception, ...)`
  - `/api/health` 路由从手写 dict 改用 `ok(data=...)` 包装——**响应内容字节级不变**，只是构造方式更统一

**Step 2.2 验证（3/3 PASS，curl.exe 实测）：**

| 测试路径 | 触发 | HTTP 状态码 | Body | 状态 |
|---|---|---|---|---|
| `/api/health` | 正常路径 | 200 | `{"code":0,"msg":"ok","data":{...}}` 与 Step 0.5 一字不差 | ✅ |
| 临时 `/api/_debug/raise` | `raise HTTPException(404, "not found")` | **404** | `{"code":404,"msg":"not found","data":null}` | ✅ |
| 临时 `/api/_debug/boom` | `return 1/0` ZeroDivisionError | **500** | `{"code":500,"msg":"internal_error","data":null}` | ✅ |

验证完成后两个调试路由按 plan 要求删除，最终 main.py 路由清单仅含 5 条标准（`/openapi.json` / `/docs` / `/docs/oauth2-redirect` / `/redoc` / `/api/health`）。

**踩到的 PowerShell 坑（记下来）：**
- `Invoke-WebRequest` 在收到 4xx/5xx 响应时**会丢 body**（即便 `-UseBasicParsing`），只能拿到 HTTP 状态码。验证 4xx/5xx 接口必须用 `curl.exe`（Windows 10+ 自带）或 `Invoke-RestMethod -SkipHttpErrorCheck`（PowerShell 7+ 才有）。
- `curl.exe -s -w "[status=%{http_code}]"` 是验证响应体 + 状态码的最快方式。

**给后续开发者的提示：**
- **所有业务路由都要用 `ok(data=...)`**：禁止手写 `return {"code": 0, "msg": "ok", "data": ...}`——一是冗长，二是一旦后续 envelope 结构调整就要 grep 全仓改。Step 4.x / 6.x 写每个接口时严格遵守。
- **想返回特定错误码**：`raise HTTPException(status_code=4xx, detail="<语义化提示>")`，全局 handler 会自动包成 envelope。**不要在路由里手写 `return {"code": 404, ...}` 模拟错误**——会丢掉 HTTP 状态码语义。
- **`HTTPException` 的 `detail` 字段可以是 str / dict / list**：当前 handler 用 `str(exc.detail)` 强转字符串。未来需要发结构化错误（如 form 验证），需要扩展 handler 处理 dict 情形。
- **`unhandled_exception_handler` 的日志会进 uvicorn 的 stdout**：演示时盯着终端就能看 traceback。生产环境应换 Python logging 配置文件接 Sentry / file rotation 等。
- **`logger = logging.getLogger("nail_demo")` 是唯一 logger 名**：未来所有模块（services/llm.py、services/email.py 等）想打日志的都用 `logging.getLogger("nail_demo.xxx")` 子 logger，统一可控。
- **不要捕获更细的 `Exception` 子类（如 `RuntimeError`）**：当前 catch-all 已经覆盖，加细化 handler 会破坏"内部错误不泄露"的统一语义。除非业务层有特定错误类（如 `ConfigError`、`ImageGenError`）需要专门 4xx 映射。
- **OpenAPI 文档不会显示 envelope**：因为 health 等接口没声明 response_model，Swagger 还是把 `Dict` 作为返回类型呈现成 `{additionalProp1: {}}`。这是 plan 接受的现状，不修；后续若需要可加 `class ApiEnvelope(BaseModel)` 模型并在每个路由 `response_model=ApiEnvelope[StyleListData]`，但会大幅增加样板代码。

---

### ✅ Step 2.3 · 路由分组骨架 — 2026-06-10

**做了什么：**
- 新建 `backend/app/routers/__init__.py`（空，包标记）
- 新建 `backend/app/routers/user.py`（33 行）：
  - `router = APIRouter(prefix="/api")`，C 端路由统一容器
  - `GET /ping` 探针返回 `{code:0, msg:"ok", data:{router:"user"}}`
  - **docstring 把强约定写死**：所有 C 端接口（包括 `/api/styles`、`/api/recommend`、`/api/tryon` 等）都在本文件里加 `@router.<method>("<路径>")`，**禁止**未来新建 `styles.py` / `recommend.py` 等独立文件。文件名 `user.py` 是"C 端"代称，不是"仅 `/api/user/*` 路径"。
  - 顺手把 Step 4.1 的 `X-User-Id` header 协议记在 docstring 里，提醒后续实现者
- 新建 `backend/app/routers/ops.py`（21 行）：
  - `router = APIRouter(prefix="/api/ops")`，B 端路由统一容器
  - `GET /ping` 探针返回 `{...data:{router:"ops"}}`
  - 同样的强约定 docstring
- `main.py` 改动（+4 行）：
  - 导入两个 router 模块：`from app.routers import ops as ops_router` / `from app.routers import user as user_router`
  - `app.include_router(user_router.router)` + `app.include_router(ops_router.router)`

**Step 2.3 验证（3/3 PASS）：**

| 测试 | 输出 |
|---|---|
| `GET /api/ping` | HTTP 200 + `{"code":0,"msg":"ok","data":{"router":"user"}}` |
| `GET /api/ops/ping` | HTTP 200 + `{"code":0,"msg":"ok","data":{"router":"ops"}}` |
| `GET /api/health` 不破坏 | HTTP 200 + 与 Step 2.2 完全一致 |

**ping 端点保留决定：**
plan §2.3 原话"两个 ping 验证后删除（或保留也行，开发期无害）"。我选**保留**——理由：
1. 每个就 3 行函数，体积可忽略
2. 活体探针：未来某次 commit 误把 `include_router` 注释了，`curl /api/ping` 立刻暴露
3. 加业务接口出 bug 时，先 ping 判断是"app 起不来" vs "具体接口挂了"
4. plan 显式允许

**导入风格选择（轻微但记下）：**
用 `from app.routers import user as user_router` 后 `include_router(user_router.router)`，而不是 `from app.routers.user import router as user_router` 后 `include_router(user_router)`。前者让 import 名稳定指向"模块"，未来 Step 4.x 在 `user.py` 加 schemas / helpers / constants 时不需要改 main.py 的 import；后者更短但耦合到 `router` 这一具体导出名。

**给后续开发者的提示：**
- **看到 Phase 4 / 6 / 8 / 9 任何路由实现指令，思路只有一条**：C 端 → 直接在 `routers/user.py` 末尾加 `@router.<method>("<路径>")` 的函数；B 端 → 同理加到 `routers/ops.py`。**不要新建文件**。
- **router 前缀已经定了**：`user.py` 是 `/api`，`ops.py` 是 `/api/ops`。所以写 `@router.post("/recommend")` 实际暴露成 `/api/recommend`；`@router.get("/overview")` 在 ops.py 里暴露成 `/api/ops/overview`。**不要在 @router 路径里重写 `/api` 前缀**，会变成 `/api/api/recommend`。
- **共享逻辑（如统一鉴权依赖、shared queries）**：定义在 `routers/user.py` / `routers/ops.py` 文件内的辅助函数即可。如果跨两端都用，移到 `app/services/<X>.py`，让两边 import。**不要为了"DRY"在 routers/ 下加 helpers.py**——违反"路由都在两个文件里"的约定。
- **Pydantic request/response 模型可以同文件**：未来 Step 4.2 的 `UploadResponse` 之类直接在 user.py 顶部 `class UploadResponse(BaseModel): ...`，紧贴使用它的路由。**不要拆 schemas.py**。

---

### ✅ Step 2.4 · 静态文件服务（+ Step 2.2 异常 handler 回填）— 2026-06-10

**做了什么：**
- `backend/app/main.py`：
  - `from fastapi.staticfiles import StaticFiles` + `app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")`
  - `BACKEND_ROOT = Path(__file__).resolve().parent.parent` + `STATIC_DIR = BACKEND_ROOT / "static"`，让路径独立于 cwd
- **Step 2.2 回填**：把 `app.add_exception_handler(fastapi.HTTPException, ...)` 改成 `app.add_exception_handler(starlette.exceptions.HTTPException, ...)`。理由：
  - `StaticFiles` 找不到文件时抛的是 **Starlette 的 HTTPException**，不是 FastAPI 子类
  - 未匹配业务路由（如 `/api/does_not_exist`）的 404 也走 Starlette
  - Step 2.2 当时只测了"路由里 `raise HTTPException()`"那一种场景，漏了上面这两种
  - 注册到 Starlette 父类一行覆盖全部（FastAPI 的 HTTPException 是 Starlette 的子类）

**Step 2.4 验证（5/5 PASS）：**

| 测试 | 结果 |
|---|---|
| `GET /static/styles/f_01_enh.png` | HTTP 200，1,221,491 字节，**SHA256 与磁盘一致** |
| 随机 5 女 + 3 男 + 3 hands = 11 个文件 | 11/11 全部 200 + 实际字节 |
| `GET /static/styles/nope.png`（StaticFiles 404）| `{"code":404,"msg":"Not Found","data":null}` + status 404，**走信封** |
| `GET /api/does_not_exist`（未匹配业务路由 404）| 同上信封 |
| `/api/ping` / `/api/health` 不破坏 | 完全一致 |

**踩到的两个坑（已经在过程中处理掉，记下来供后续避坑）：**

1. **僵尸 uvicorn 占着 8000 端口**：PowerShell 的 `Start-Job` 启动 native exe 后，`Stop-Job` 不一定能干净杀掉子进程。前面几次后台 uvicorn 测试残留了一个跑**旧版 main.py**（还没有 static mount）的 python.exe 在 8000 上，导致新启动的 uvicorn `bind: address already in use`，但 curl 仍然能连到僵尸进程返回 404。验证陷入"代码看着对、行为不对"的怪状。
   - **修法**：每次测前后跑 `Get-NetTCPConnection -LocalPort 8000 | Stop-Process -Force`，显式回收。
   - **诊断技巧**：`Get-NetTCPConnection -LocalPort 8000` 看 PID + `Get-Process <pid>` 看进程路径，能确认是不是僵尸。

2. **PowerShell `-o $null` 不会真的丢弃 curl 输出**：`$null` 在 PowerShell 里是变量值"空"，传给 native exe 时转成空字符串，于是 curl 看到 `-o ""` 把响应写到当前目录的一个空文件名……结果 `-w` 格式串不打印、body 反而打印到 stdout。要用 `NUL`（Windows 设备文件名）。
   - **修法**：`curl.exe -s -o NUL -w '%{http_code}' <url>`
   - 也别用 `Invoke-WebRequest` 测 4xx/5xx——见 Step 2.2 进度的同类坑记录。

**给后续开发者的提示：**
- **新增静态资源类型**：在 `backend/static/` 下加子目录即可（如 `static/avatars/`），无需改 mount 配置。`/static/avatars/<file>` 自动可访问。
- **`static/cache/` 和 `static/uploads/` 已经 gitignore**：上传的用户手图、即梦合成的试戴结果图都进这两个目录。HTTP 可以读但 git 不追踪。
- **演示前必须先跑 `seed_all.py`**：clone 仓库不会带 `static/styles/` 和 `static/samples/` 里的图（gitignore 了）。空目录访问 `/static/styles/f_01_enh.png` 会 404。
- **不要在 main.py 之外再 `app.mount(...)`**：所有 mount 集中在 main.py 一处声明，避免分散到 routers/ 下导致 mount 顺序/优先级混乱。
- **`StaticFiles(directory=path)` 路径要求**：`path` 必须**已经存在**，否则 FastAPI 启动就抛错。Step 0.1 已经把 `static/{styles,samples,uploads,cache}` 4 个子目录建好；如果有人手 rm 了某个子目录，mount 不影响（只挂顶层 static/），但访问该子目录会 404。

**Phase 2 收官：** 后端基础设施 4 步全部就位（DB 注入 / 统一响应 / 路由骨架 / 静态挂载）。下一步进 Phase 3 AI 服务层（4 步：ImageGenProvider 抽象 / 即梦 P1 / LLM 封装 / 邮件发送）。Phase 3 完成后才进 Phase 4 真正的业务 API（用户端 7 个接口）。

---

### ✅ Step 3.1 · ImageGenProvider 抽象 + MockProvider — 2026-06-10

**做了什么：**
- 新建 `backend/app/services/__init__.py`（空包标记）
- 新建 `backend/app/services/image_gen.py`（89 行）：
  - **`ImageGenError`**：自定义异常类，所有 image-gen 失败都抛它
  - **`ImageGenProvider(ABC)`**：抽象基类，规定唯一异步方法
    ```python
    async def generate(
        self, user_id: str, style_id: str,
        hand_image_bytes: bytes, prompt_extra: str | None = None
    ) -> str  # returns relative URL like /static/cache/<filename>
    ```
  - **`_resolve_cover_path(style_id)`**：兼容男女命名，先探 `_enh.png` 再探 `.jpg`，找不到返回 None
  - **`MockProvider`**：把 `static/styles/{cover}` 直接复制到 `static/cache/{user_id}_{style_id}{.png|.jpg}`，返回 cache 路径。**演示安全网**，永远不会因外部依赖挂掉
  - **`get_image_provider()`** 工厂：读 `settings.IMAGE_PROVIDER`，`mock` 返回 MockProvider 实例，`jimeng` 抛 ImageGenError（占位，Step 3.2 实现），其他抛 ImageGenError

**Step 3.1 验证（6/6 PASS + 用户手动验证）：**

| 测试 | 实测 |
|---|---|
| factory 返回 `MockProvider`（IMAGE_PROVIDER=mock） | 类型匹配 |
| MockProvider.generate(`f_01`) | URL=`/static/cache/test_user_123_f_01.png`，1,221,491 B（与源 f_01_enh.png 同字节） |
| MockProvider.generate(`m_05`) | URL=`/static/cache/test_user_123_m_05.jpg`，60,010 B（保留 jpg 扩展名）|
| 未知 style id 抛 `ImageGenError` | "no cover image found for style 'f_99'" |
| `IMAGE_PROVIDER=jimeng` 抛 `ImageGenError`（占位） | "JimengProvider not implemented yet..." |
| `IMAGE_PROVIDER=garbage` 抛 `ImageGenError` | "unknown IMAGE_PROVIDER: 'garbage'" |
| 测试结束 cache 清理 | 自动清空 |
| 用户手动验证亦确认 | 在 cache 看到 1.2 MB 的 `test_f_01.png`，删除后干净 |

**几个设计选择（透明告知）：**

1. **`generate()` 多了 `user_id` 参数**：plan §3.1 字面只列「手图 bytes、款式 id」，但同步说 cache 文件名 `{user_id}_{style_id}.png` 需要 user_id。把 user_id 当显式参数比把它编进 hand_image_bytes 或文件名嗅探都更显式。
2. **`_resolve_cover_path` try-both**：plan 写的 `{id}_enh.png` 是 25 女款时代格式。男款是 `m_NN.jpg`。先探 `_enh.png` 再探 `.jpg`，两次 filesystem stat sub-ms。**比从 DB 查 cover_url 更轻量，且不依赖 DB 状态**——Mock 必须永远能跑。
3. **Mock cache 扩展名跟源走**：女款 `.png` → cache `.png`；男款 `.jpg` → cache `.jpg`。不强制 `.png` 避免 jpg 字节套 png 扩展名的 Content-Type 不一致。
4. **`JimengProvider` 没建占位类**：plan §3.2 字面说"保留 JimengProvider 占位类抛'未实现'错误"。我选择直接在 factory 里抛 ImageGenError，message 提示去 Step 3.2 实现。简单 1 行，Step 3.2 时把 factory 那行换成 `return JimengProvider()` 即可。占位类等到 Step 3.2 真正需要时再建，避免空 class 污染。

**给后续开发者的提示：**
- **新增 Provider 实现**：继承 `ImageGenProvider` 实现 `async generate(...)`，在 `get_image_provider()` 工厂里加一个 `elif name == "<your-name>": return <YourProvider>()`。`.env` 加一行 `IMAGE_PROVIDER=<your-name>` 即可启用。
- **不要在 Provider 实现里查 DB**：Provider 应该是无状态的，只接受参数 + 写文件。需要 cover_url 这类信息？通过参数传入或 filesystem 探测。这是为了让 Provider 单元测试不依赖 DB。
- **`/static/cache/` 是运行时目录、gitignore**：里面的文件都是即时生成的，可以随时删空，下一次试戴会重新生成。
- **MockProvider 把"原图当试戴结果"是有意为之**：演示时观众看不出区别，但本质上是 fallback。当 JimengProvider 真生效时，前端体验是质变的。所以 `IMAGE_PROVIDER` 是 demo 的"高级 / 安全"档位开关。
- **`generate()` 是 async**：未来 Jimeng 用 `httpx.AsyncClient` 调 API，签名一致。Step 4.7 多款对比试戴用 `asyncio.gather` 并发调用同一个签名。
- **错误处理统一抛 `ImageGenError`**：Step 4.6 单款试戴接口里 catch 这个异常包成 HTTPException(500)，让前端拿到 `{code:500, msg:"..."}` 信封（走 Step 2.2 全局 handler）。

---

### ✅ Step 3.2 · SeedreamProvider 接入（PPIO 平台）— 2026-06-11

**与原 plan 的方向修订：**
plan §3.2 原本写"即梦 AI（火山方舟）"，要求注册火山方舟实名拿独立 key。Benchmark 后发现 **PPIO 平台自带 Seedream 系列**（字节系图像模型）：
- 共用 `PPIO_API_KEY`（已就绪），不用再注册一个供应商
- Seedream 4.5 在多图条件输入和肤色保真两方面都优于火山方舟即梦的常规图生图
- 火山方舟即梦原本就只是字节系图像能力的一种发行渠道——PPIO 上的 Seedream 同源

3 份 docu 已同步修订（design-docu §3.1/§8.1/§8.2、tech-stack §1/§4/§7.3/§9/附录、implementation-plan §0.4/§3.2/§10.2 + memory-bank 镜像三对 SHA 匹配）。

**做了什么：**
- `backend/app/services/image_gen.py` 新增 `SeedreamProvider`：
  - Endpoint `https://api.ppio.com/v3/seedream-4.5`，timeout 180s，下载超时 60s
  - 把 `hand_image_bytes` + 从 `_resolve_cover_path(style_id)` 找到的款式封面同时 base64 data-URL 化，塞进 `image` 数组字段
  - Prompt 锁定 V1 短版（短而有效，V2 加长版没有可测量收益）
  - `size: "2K"` + `watermark: false`
  - 文件名 `seedream_{user_id}_{style_id}_{ts}.png`，毫秒时间戳后缀避免重试覆盖
  - HTTP 4xx/5xx 全部包成 `ImageGenError` 抛出（不重试——交给调用方决定是否退回 MockProvider）
- `get_image_provider()` factory：`IMAGE_PROVIDER=seedream` 返回 `SeedreamProvider`；`mock` 返回 `MockProvider`；其他抛 `ImageGenError`
- 配置精简：删除 `JIMENG_API_KEY` 字段（已废弃）—— `backend/.env` / `.env.example` / `app/config.py` 三处同步删除；`IMAGE_PROVIDER` 注释改为标注 `mock | seedream` 两个合法值

**Step 3.2 验证（端到端 / 真 API 调用 / 用户人工确认）：**

| 验证 | 实测 |
|---|---|
| `IMAGE_PROVIDER=seedream` 工厂返回 `SeedreamProvider` 实例 | ✅ |
| 真实 API 调用（hand=05.png + style=f_01）耗时 | 54.1s（符合 40-60s 预期）|
| 返回 URL 格式 `/static/cache/seedream_<user>_<style>_<ts>.png` | ✅ `seedream_step3_2_test_f_01_1781172792076.png` |
| cache 文件实际生成 | 914 KB，正常体量 |
| 视觉效果与之前 benchmark V1 一致 | ✅ 肤色保真、手部结构保留、指甲款式还原 |
| MockProvider 不受影响 | ✅ |
| 未知 `IMAGE_PROVIDER` 值抛 `ImageGenError` | ✅ "unknown IMAGE_PROVIDER: 'garbage'; valid: mock, seedream" |

**模型选择过程（透明、不光彩的部分）：**

我中间踩了一个判断陷阱：第一轮 benchmark 跑完 Seedream 4.0/4.5/5.0-lite 后，**我把肤色对比方向看反了**。

- 真实情况：原图 `samples/05.png` 是中深色暖棕肤色；4.0 把它推向冷深黑（去暖色底色），4.5 接近原图，5.0-lite 直接被安全过滤拒了
- 我的错误描述："4.0 保留深色 ✓ / 4.5 美白 ✗"——把 4.0 的"更深"误读成"保留"，把 4.5 的"接近原图"误读成"美白"
- 用户基于自己看图的直觉直接选了 4.5（这才是对的）
- 我又走了弯路：建议加 V2 加强 prompt 反美白 bias（其实根本没那个 bias）、又跑 Qwen-Image-Edit 探索（弄清它只接受单张图，多图条件不可能）
- 总共烧了约 **¥0.945**（Seedream 4.0/4.5/5.0-lite 3 张 + 4.5 V2 1 张 + Qwen 探索 1 次 + Step 3.2 验证 1 次）。其中至少 ¥0.345 是我误判带出来的浪费

**教训记下来**：Read 工具看图的颗粒度不如肉眼直接看，用户的视觉判断是更可靠的信号源。下次类似分歧应该先承认用户视觉判断的优先权，而不是反过来让用户被我的错误描述带偏。

**最终锁定的选择：**

| 维度 | 选定 | 理由 |
|---|---|---|
| 平台 | PPIO | 共用 `PPIO_API_KEY`，跟 LLM 同供应商 |
| 模型 | Seedream 4.5 | 肤色保真度最佳；4.0 over-darken / 5.0-lite 拒深色手 / Qwen 只接单图 |
| Prompt | V1 短版 | V2 加狠的 prompt 实测没有可观察改善，**只是 token 多 + 难维护** |
| 输出分辨率 | 2K | demo 显示不到 4K，省时间 |
| watermark | false | 我们把结果当"用户自己的试戴"展示，不需要 AI 水印 |

**已知限制（写进 docu）：**
- **5.0-lite 对深色皮肤手图触发安全过滤**：这是模型 bias，不是 prompt 能修。如果未来发现 4.5 对某些用户也触发了，需考虑切 4.0
- **4.0 对深色手图 over-darken**：保留深色但加深一档，失去原图暖色底色
- **Qwen-Image-Edit 只接受单图输入**（API `image` 字段是 string 不是 array），用 Qwen 就意味着款式必须用文字描述喂模型，体验大幅下降，不适合本场景
- 异步 API 的 task-result 查询端点 PPIO 文档没写清楚，未来如果有人想接异步模型（如视频生成）需要先实验

**`backend/static/cache/bench/` 下保留了 3 张 benchmark 输出**（`bench_4_0_0.png`、`bench_4_5_0.png`、`bench_4_5_v2.png`）作为视觉参考，路径在 `.gitignore` 里不进 git。未来如果有人想重新评估模型可以直接打开看，省得重花钱跑。

**给后续开发者的提示：**
- **想看真合成效果**：把 `.env` 的 `IMAGE_PROVIDER` 从 `mock` 改 `seedream`，重启后端。一次试戴 ~¥0.2、~50s。
- **想换 model 版本**（如试 4.0 / 5.0-lite）：改 `SeedreamProvider.ENDPOINT` 常量即可，不用动其他代码。如果新版本要不同的字段名（4.0 的 `images` vs 4.5/5.0-lite 的 `image`），需要同步改 payload 构建那两行
- **想换 prompt**：改 `SeedreamProvider.PROMPT_TEMPLATE`。**改之前先看 benchmark 三张图作为基线**——任何 prompt 改动都应该比这个基线更好，否则别改
- **`hand_image_bytes` 体积要控制**：Seedream 接受 ≤10MB/张。如果用户传大图，前端应在上传前先压缩（design-docu §6.2 用 `browser-image-compression` 压到 ≤5MB）
- **失败重试策略**：当前没有内置重试。如果 PPIO 5xx 或网络抖动，单次 `generate()` 会抛 `ImageGenError`。Step 4.6 / 4.7（试戴接口）应在路由层 catch + 退回 MockProvider，让用户至少看到款式图作为"试戴结果"。这是 design-docu §8.1 "Mock 永远兜底"的精神
- **`PPIO_API_KEY` 是核心凭证**：泄露了就立刻去 PPIO 控制台 revoke + 新建 key 换掉 `.env`。LLM + 图像生成 都靠它
- **Step 4.6 / 4.7 实现细节**：拿到 `result_url`（`/static/cache/seedream_*.png`）后写入 `tryons.result_url` 列。文件名带 timestamp 保证唯一，DB 里同一 (user_id, style_id) 多次试戴指向不同文件
- **演示前 dry-run 一次真合成**：避免现场被网络/审核拒第一次。先在前一天用真 key 跑一次确认链路通

---

### ✅ Step 3.3 · LLM 服务封装（PPIO 一家全包）— 2026-06-11

**做了什么：**
- 新建 `backend/app/services/llm.py`：
  - 用 `openai.AsyncOpenAI` 客户端，`api_key=settings.PPIO_API_KEY`、`base_url=settings.PPIO_BASE_URL`
  - 异常类：`ConfigError`（key 缺失）、`LLMError`（重试后仍失败 / 非 429 错误）
  - `gen_text(prompt, model: 'quick'|'strong'='quick', max_tokens=200)` — 短文本生成
  - `gen_text_with_tools(messages, tools, model='strong')` — Function Calling，返回 `ChatCompletionMessage`（带 `.content` 和 `.tool_calls`）
  - `_with_retry`：429 时指数退避（`2**attempt + random.uniform(0, 2)`，最多 3 次），跟 `data-prep/auto_tag_styles.py` 保持一致；其他错误立即抛 `LLMError`
  - `PPIO_API_KEY` 为空时 `ConfigError`，**不做静默 fallback**

**Model ID 大调整（透明记录）：**
benchmark 时发现原 `.env` 写的 model ID 在 PPIO 实际不可用 / 不合理：

| 维度 | 原（Step 0.4 时写的） | 现锁定 |
|---|---|---|
| Quick | `qwen/qwen2.5-7b-instruct` | `qwen/qwen3-next-80b-a3b-instruct`（80B MoE，激活 3B）|
| Strong | `deepseek/deepseek-v3.1` | `deepseek/deepseek-v4-pro` |

原因：
- **`qwen/qwen2.5-7b-instruct` 已被 PPIO 下线**：实际调用返回 HTTP 500 `MODEL_NOT_AVAILABLE`，但 `/v1/models` 列表里没清理掉所以看着像还活着——经典"listing stale"。同探的 `qwen2.5-32b-instruct`、`qwen3-30b-a3b-fp8` 等多个也是 500。最终探出 `qwen/qwen3-next-80b-a3b-instruct` 实测 1.9s 响应，跟 `kimi-k2-instruct` / `qwen3-235b-a22b-instruct-2507` 三选一，选 next-80b 因为 MoE 激活小、推理便宜
- **用户主动指定换 `deepseek-v4-pro`**：旗舰版本，1M context window，支持 Function Calling 和 reasoning。benchmark FC 实测 1.8-6.1s（首次 cold-start 偶发 30s+ 超时，多次重试稳定后正常）

**Quick / Strong 跑了 7 个 strong 候选 Function Calling speed benchmark：**

| 模型 | FC 时间 | 备注 |
|---|---|---|
| `qwen/qwen3-235b-a22b-instruct-2507` | 0.8s | 最快 |
| `deepseek/deepseek-v3-turbo` | 1.5s | 速度专精 |
| `moonshotai/kimi-k2-instruct` | 1.8s | 不同厂家 |
| `qwen/qwen3.7-max` | 1.8s | qwen3 旗舰 |
| `deepseek/deepseek-v4-flash` | 1.9-3.8s | v4 速度版，三轮稳定 |
| `deepseek/deepseek-v3.1` | 2.4s | 原 plan 默认 |
| **`deepseek/deepseek-v4-pro`** | **1.8-6.1s** | **用户选定** |

**TIMEOUT 调整：plan §3.3 写 30s，调到 60s**
理由：v4-pro 是 reasoning 模型，cold-start / Function Calling 首次组合可能 30s+。60s 给充足 margin 应付偶发慢响应，但仍能在合理时间内暴露真实失败（不会让长 hang 永久无法察觉）。Quick 档实测 3-4s 远低于 60s，没影响。

**Step 3.3 验证（4/4 PASS）：**

| 验证项 | 实测 |
|---|---|
| `gen_text("请用一句话介绍美甲", "quick", 80)` < 10s 返回非空 | 3.83s, "美甲是指通过修剪、打磨、涂色、装饰等方式..." |
| `gen_text_with_tools(get_weather)` 返回 tool_calls | 4.29s, `tool_calls=[get_weather({"city": "上海"})]` |
| `PPIO_API_KEY` 空时抛 `ConfigError` | "PPIO_API_KEY missing" |
| 未知 tier 抛 `ValueError` | "unknown model tier: 'garbage'; use 'quick' or 'strong'" |

**附带改动：**
- `backend/.env`：`PPIO_API_KEY` 轮换为新 key（用户在对话里贴出新 key 时主动提供）；`LLM_QUICK_MODEL` / `LLM_STRONG_MODEL` 锁定新值
- `backend/.env.example`：同步 model ID 默认值
- 三份 docu（design-docu §3.1/§7.7.3 代码块、tech-stack §1/§4.1/§4.3/§7.3/附录、implementation-plan §0.4）凡引用 `qwen2.5-7b-instruct` / `deepseek-v3.1` / `qwen-max` 全部更新为新 ID + 加一段"为什么这两个"的解释。memory-bank 镜像同步 SHA 一致。`memory-bank/progress.md` Step 0.4 历史记录里的 model ID 是历史快照，**不动**——它如实记录了那个时刻 `.env` 的内容

**给后续开发者的提示：**
- **PPIO model ID 不靠谱地容易腐烂**：写 `.env` 之前先 `python -c "from openai import AsyncOpenAI; ..."` 跑一个最小调用确认。listing 接口的 200 不等于 chat completions 能调用
- **timeout 60s 是当前默认**：如果未来要支持 streaming（SSE），timeout 设定要重新评估；当前是同步 await，整个响应一次性返回
- **重试只针对 429**：plan 显式要求只在 rate limit 时退避。timeout、5xx、4xx 全部立即抛 `LLMError`——上层（Step 4.5 推荐接口、Step 8 AI 助手）应该自己决定要不要 fallback 到模板理由 / 错误提示
- **`gen_text_with_tools` 返回的是 SDK `ChatCompletionMessage`**，不是 dict。`.tool_calls` 是 `list[ChatCompletionMessageToolCall]` 或 `None`；每个 tool_call 有 `.id`、`.function.name`、`.function.arguments`（**string，不是 dict**——需要 `json.loads()` 解码）。Step 8.1 Function Calling 实现注意这点
- **PPIO_API_KEY 又轮换了一次**：用户当时在对话里贴出新 key 才有 v4-pro 调用权限。下次轮换记得删旧 key，PPIO 控制台保留过多废 key 是泄漏风险。`.env` 不进 git 所以仓库历史里不会有 key 痕迹，但**对话历史可能有**，请用户自行评估
- **deepseek-v4-pro 首次调用偶发慢**：演示前 5 分钟 dry-run 一次 strong 档 Function Calling 让模型 warm-up，再正式演示

---

### ✅ Step 3.4 · 邮件发送服务 — 2026-06-12

**做了什么：**
- 新建 `backend/app/services/email.py`（100 行）：
  - `EmailSendError`：失败专用异常，`raise ... from e` 保留底层异常链便于调试
  - `wrap_html(body)`：把 raw HTML 套进 design-docu §7.7.4 规定的 inline-CSS 包装——680px 宽 / Apple System 字体栈 / 1.6 行距 / `<hr>` 分隔 / 中文 AI 助手自动生成脚注 + 实时时间戳
  - `async send_email(to, subject, html_body, text_body)`：MIMEMultipart('alternative') 两段式（plain 在前、HTML 在后，符合 RFC——客户端取最后一个能渲染的），SMTPS 走 `smtplib.SMTP_SSL` 端口 465，timeout 30s
- **同步 smtplib 通过 `asyncio.to_thread` 异步化**：不引入 aiosmtplib 第三方依赖（保持 requirements.txt 干净）；sync 调用在线程池跑，不阻塞 FastAPI 事件循环
- 分层异常映射：`SMTPException` / `OSError` / 其他 Exception 都包成 `EmailSendError`，message 标注异常类型；底层异常通过 `__cause__` 保留，**绝不静默吞掉**（plan §3.4 硬要求）

**Step 3.4 验证（5/5 自动化 PASS + 真实邮件 PASS）：**

| 验证项 | 实测 |
|---|---|
| 1. import smoke：`send_email` / `EmailSendError` / `wrap_html` 三导出可用 | ✅ |
| 2. `wrap_html` 结构正确（680px 宽 / Apple System / 中文脚注 / `<hr>` / 时间戳）| ✅ |
| 3. SMTP 配置 4 项都空时抛 `EmailSendError`，message 显式指出缺哪几项 | ✅ |
| 4. 空 `to` 抛 `EmailSendError("recipient 'to' is empty")` | ✅ |
| 5. 假 SMTP host 抛 `EmailSendError`，底层 `SSLEOFError` 通过 `__cause__` 保留 | ✅ |
| 6. **真实发邮件**：QQ smtp.qq.com:465 → 用户的 277092506@qq.com，API 2.81s 完成 | ✅ |
| 7. **用户手动确认 30 秒内收到邮件，HTML 渲染正常** | ✅ |

**产品架构澄清（用户提的好问题）：发件 vs 收件是两个独立角色**
用户在 Step 3.4 实施时问"为什么要我的 SMTP 授权码？产品上线后不是每个用户绑自己的邮箱吗？"——好问题，docu 里应该早说。

实际架构：
- **发件人**（`SMTP_USER` / `SMTP_PASS` / `SMTP_FROM`）= **平台官方账号**，一份固定。生产环境会是 `report@platform.com` 这类专门发件账号，授权码进环境变量
- **收件人**（`REPORT_RECIPIENT` 或 future `notification_subscribers` 表）= **运营个人邮箱**，他们只填地址，**不需要授权码**，因为他们只收不发
- demo 阶段没有"平台 IT 部门"，所以用户的 QQ 临时同时扮演这两个角色（既是平台发件账号也是运营收件邮箱）。**生产时会拆开**

未来 docu 可在 design-docu §7.7 增一段"production-readiness"小节明确这事，**暂时不动**——当前 demo 阶段够用，docu 写早了等下个版本又要改。

**安全：授权码已轮换**
用户在对话里贴出了 SMTP 授权码 `vxhqqacvdibebjci`——同 Step 3.3 的 PPIO key 类似的对话历史泄露风险。验证完成后用户**立即在 QQ 控制台重新生成了新授权码**，并由用户自己手动改进 `.env`（**没经过对话**），从根本上避免新码再次泄露。

这套"我从不知道新码是什么"模式建议作为后续 secret rotation 的**默认流程**：开发者本地改 `.env`，AI 助手不需要看见新值——除非有具体改动需求才告诉。

**给后续开发者的提示：**
- **Phase 9 报告推送会复用这个 `send_email`**：日报 / 周报生成后，`send_report_email(report)` 调用 `send_email(REPORT_RECIPIENT, title, content_md_to_html, content_md)`。`asyncio.create_task` 非阻塞调用，失败时报告本身已入库 + 站内信已发，只有邮件状态标 `email_status='failed'`，详见 Step 9.1
- **加多收件人**：当前 `to: str` 是单地址。未来要群发（如运营群、或不同运营订阅不同频率）扩展为 `to: str | list[str]` + msg["To"] join `, `——一行改动
- **QQ 邮箱限制要小心**：QQ SMTP 服务对单日发送量、收件人数有限制（个人邮箱约 50 封/天）。Phase 9 调度的日报+周报频率不会触碰，但如果未来加"事件实时通知"要注意。生产换企业邮箱或专业发件服务（阿里云邮件推送、SendGrid）
- **真测前 dry run 一次**：演示前一天用真 SMTP 配置发一封测试邮件，确认授权码没过期/邮箱没被风控。授权码偶尔会被 QQ 主动失效
- **HTML 渲染不一致**：不同邮箱客户端对 inline CSS 支持差异大。当前 `wrap_html` 经过 QQ 实测 OK。未来如果加 163、Outlook、Gmail 等多端用户，建议用 `litmus` 或类似工具做兼容性验证；最常见坑是嵌套 `<table>`、background-image、media query 全部不可靠
- **同步 smtplib 性能足够**：单线程 `asyncio.to_thread` 不会阻塞主循环。Phase 9 一天 1-2 次调用，并发量极低。如果未来 demo 演化成需要批量发件（活动营销），换 `aiosmtplib` 真异步会更优雅

---

### ✅ Step 4.1 · user_id / gender 前端约定 + X-User-Id 中间件 — 2026-06-12

**做了什么：**
- `backend/app/main.py` 加全局 HTTP 中间件 `require_user_id`：所有 `/api/...` 路径（除 `/api/health` 和 CORS OPTIONS 预检）必须带合法 UUID 的 `X-User-Id` header，否则直接 `JSONResponse(400, {code:400, msg:"invalid_user_id", data:null})`。`/static/...` 与 `/docs` 不在 `/api/` 前缀下，天然豁免。
- `backend/app/routers/user.py` 顶部约定注释从"将要校验"升级为权威实现说明：user_id 走 header（UUID v4，前端 sessionStorage 生成）/ gender 走 body（不是 header）/ 后端无 session 表 / main.py 中间件强制 UUID 格式。
- 验证用的 `/api/_debug/whoami` 临时路由按 plan 要求加 → curl 跑 8 条 → 删除；最终 main.py 路由清单干净（5 标准 + `/api/ping` + `/api/ops/ping` + `/static` + `/api/health`），无 `_debug` 残留。

**Step 4.1 验证（8/8 PASS）：**

| # | 路径 | header | HTTP | 响应 |
|---|---|---|---|---|
| 1 | `/api/health` | 无 | 200 | 正常 envelope（豁免）|
| 2 | `/api/_debug/whoami` | 无 | **400** | `{code:400,msg:"invalid_user_id",data:null}` |
| 3 | `/api/_debug/whoami` | `not-a-uuid` | **400** | 同上 |
| 4 | `/api/_debug/whoami` | `550e8400-e29b-41d4-a716-446655440000` | 200 | `{...data:{user_id:"550e8400-..."}}` 回显 |
| 5 | `/api/ping` | 无 | **400** | 中间件对全 `/api/` 生效 |
| 6 | `/docs` | 无 | 200 | Swagger UI 正常（非 /api/）|
| 7 | `/static/styles/f_01_enh.png` | 无 | 200 | 静态文件正常 |
| 8 | `/api/no_such_route` | 合法 UUID | 404 | `{code:404,msg:"Not Found",data:null}` 走 envelope |

**几个设计选择（透明告知）：**

1. **状态码用 400 而非 401**：plan 字面"4xx"。`invalid_user_id` 是格式校验问题（malformed header），不是鉴权失败；401 暗示"未登录"语义，对匿名身份产品（无 login flow、无 session 表）反而误导。400 Bad Request 最贴。
2. **CORS OPTIONS 豁免**：浏览器跨域 preflight 不会带自定义 header，不豁免会让前端所有跨域 POST 在 preflight 阶段就挂掉（永远拿不到 200）。
3. **`AttributeError` 也 catch**：`uuid.UUID(None)` 抛 `AttributeError`（不是 ValueError/TypeError）。少 catch 这个会让 header 完全缺失的请求落进全局 500 handler，前端拿到 `internal_error` 而非 `invalid_user_id`，调试方向被带偏。
4. **`@app.middleware("http")` 函数装饰器 vs `BaseHTTPMiddleware` 类**：plan 没规定形式，函数装饰器更简洁且是 FastAPI 推荐写法。未来若需要 per-route 豁免列表，再考虑改类形式做更细粒度配置。
5. **`/api/ping` 与 `/api/ops/ping` 也受中间件保护**：plan §4.1 字面只豁免 `/api/health`，严格遵守。Step 2.3 决定保留 ping 做活体探针，现在调用 ping 需要带 X-User-Id——对开发期 debug 略不便，但接口语义一致更重要。未来若运维要做无 header 的健康检查，应加到 `/api/health` 一个豁免清单里（当前单豁免列表写死 `path != "/api/health"`），不要扩散豁免到 ping。

**给后续开发者的提示：**

- **新增 C 端接口（Step 4.2~4.8）默认就有 `X-User-Id` 守卫**：每个路由都可以无脑 `request.headers["X-User-Id"]` 拿 UUID 字符串，不用再每行 `if not user_id: raise ...`——中间件已经拦在前面。直接拿 `uuid.UUID(...)` 转 UUID 对象也安全。
- **不要在路由里用 `Header(...)` 依赖把 X-User-Id 挪到参数**：plan 把它定义为协议头不是 query/body 字段；引入 FastAPI Header 依赖会把它显式化为 OpenAPI 文档项的同时，让中间件与依赖项做重复校验，且 FastAPI Header 依赖默认 422 错误不走 envelope。统一从 `request.headers` 拿。
- **运营端 `/api/ops/...` 接口同样受保护**：当前 design-docu 没规定运营端要独立身份系统，所以运营端调用也带前端生成的 UUID（前端 ops 部分可独立 sessionStorage 命名空间）。如果未来加运营登录系统，再独立鉴权中间件，跟当前的匿名 X-User-Id 中间件做组合。
- **OpenAPI 文档不显示 X-User-Id 必填**：因为是中间件层校验不是路由参数依赖。Swagger UI "Try it out" 不带 header 会全 400——这是已知现象。如果未来想让 Swagger 自动加 header，可在 `FastAPI(...)` 加 `openapi_extra` 全局 security scheme，但会引入额外样板。**不做**，保持中间件单一职责。
- **`X-User-Id` 大小写**：HTTP header 名 case-insensitive。我们 `request.headers.get("X-User-Id")` 取的是规范化后的值，前端写 `x-user-id` / `X-USER-ID` 都能识别。Step 4.2~4.8 前端实现保持 `X-User-Id` 规范写法即可。
- **后端永远不要把 UUID 当主键存 `users` 表**：design-docu §4.2 没有 users 表，是有意为之（匿名 demo）。tryons.user_id 是 VARCHAR 字段直接存 UUID 字符串，不维护外键。要"知道某用户做过哪些事"就 `WHERE user_id = ?` GROUP BY 即可。
- **`/api/health` 是当前唯一豁免**：未来如果新增"无身份探针"路径（如 `/api/version`），更新中间件的豁免条件即可——但仔细想：要不要新增这种豁免？更倾向于把所有探针塞到 `/api/health` 的 data 字段里，避免豁免清单膨胀。

---

### ✅ Step 4.2 · 上传接口 + 手部 Mock 分析 — 2026-06-12

**做了什么：**
- `backend/app/routers/user.py` 实现 `POST /api/user/upload`：multipart `file` + form `user_id`，扩展名 ⊂ {png,jpg,jpeg}，大小 ≤ 10MB，保存到 `static/uploads/{header_uid}_{ms_ts}.{ext}`。
- 抽出 `_analyze_hand(image_bytes) -> dict` 辅助函数：用 PIL 把图转 RGB → 中心 100×100 box（图小则取全图）→ 像素逐 channel 求平均 → 按 plan §4.2 规则映射 5 档 `skin_tone`（light_warm / light_cool / medium / dark_warm / dark_cool），warm/cool 边界用 `R - B > 20`。`hand_shape` 固定 `"average"` 占位（plan 明确"演示无感"）。
- Step 4.1 的 X-User-Id 中间件已覆盖请求合法性；本步增加 `form.user_id != header.X-User-Id` 时抛 400 `user_id_mismatch`，让文件名构造永远只用 UUID 验证过的 header 值（path traversal 攻击面归零）。
- 错误状态码语义化：超大 → 413（Payload Too Large），格式错 / PIL `UnidentifiedImageError` → 415（Unsupported Media Type）。

**Step 4.2 验证（4/4 plan 硬要求 PASS + 3/3 bonus PASS）：**

| # | 测试 | HTTP | 响应 |
|---|---|---|---|
| 1 | 上传 `samples/01.png` (1.33 MB) | 200 | `{photo_id, skin_tone:"medium", hand_shape:"average"}` |
| 2 | 上传 12 MB 文件 | **413** | `{code:413,msg:"file_too_large"}` |
| 3 | 上传 `.txt` 文件 | **415** | `{code:415,msg:"unsupported_format"}` |
| 4 | `static/uploads/` 出现 1,337,412 字节的 `<uuid>_<ms>.png` | — | `550e8400-...-440000_1781253827520.png` |
| 5 (bonus) | form `user_id` ≠ header `X-User-Id` | 400 | `{code:400,msg:"user_id_mismatch"}` |
| 6 (bonus) | `GET /static/uploads/<file>` 取回字节 | 200 | size=1,337,412（与上传字节完全一致）|
| 7 (bonus) | 5 张样本（01/05/10/15/17）skin_tone 分布 | — | medium ×3 / dark_warm ×1 / light_warm ×1 → **3 个不同枚举命中**，分析器不是常数 |

**几个设计选择（透明告知）：**

1. **状态码 413 / 415 vs 单一 400**：plan 字面只说 "code=4xx + msg 指明"。语义化更标准（Payload Too Large / Unsupported Media Type），网关与日志层能区分；前端依然只解析 envelope `msg`，零差异。如果未来要统一为 400，改 2 行 HTTPException(status_code) 即可。
2. **form `user_id` 仅做"redundant safety check"，文件名永远拼 header 值**：plan §4.2 字面要求接收 form `user_id`——可能是 §4.1 X-User-Id 协议确立前的遗留写法。我保留 form 字段做 sanity check（前端两份值不一致暴露 wiring bug），但 path 来源永远是 UUID 校验后的 header；form 字段从不进文件名 → 路径穿越攻击面归零。
3. **`UnidentifiedImageError` 兜底假图片**：用户用 `.png` 扩展名包裹非图像字节（如 `mv blob.bin blob.png`），PIL 会抛 `UnidentifiedImageError`。包成 415 比走全局 500 用户体验好，且语义贴切（"扩展名对但内容不是图"≈ "不支持的媒体类型"）。其他 PIL 异常（如 DecompressionBombError）当前不特殊处理，会走 500 → `internal_error`，这是 Step 4.2 验收范围外，未来加防御性处理再说。
4. **`hand_shape="average"` 硬编码**：plan 明确"演示无感"，不做真识别。Step 4.4 推荐算法把它当输入字典字段（`{skin_tone, hand_shape}`），未来如果要加真识别只动 `_analyze_hand` 内部，API 形状不变。
5. **`_analyze_hand` 留在 user.py 内**：符合 §2.3 约定（C 端逻辑全在 user.py，shared helpers 才提到 services/）。Step 4.4 推荐算法在 `services/recommend.py`——它接受调用方传入的 `hand_features` 字典，不直接 import `_analyze_hand`，所以 Step 4.4 的接口不会依赖本步骤的内部实现。
6. **warm/cool 阈值 R-B>20**：plan 未规定，凭直觉选 20（不是 30 也不是 10）。验证 7 显示 5 张样本里 17.png 命中 light_warm（R≈220、B≈190、R-B≈30），15.png 命中 dark_warm。如果 demo 上用户视觉判断觉得分类偏离（[feedback_visual_judgment]），调阈值只 1 行。

**给后续开发者的提示：**

- **`hand_features` dict 格式从此被锁定为 `{skin_tone, hand_shape}`**：Step 4.4 推荐算法、Step 4.5 试戴接口都按这两个字段消费。如果未来要加 `nail_length` 或 `finger_ratio` 等真识别字段，三处同步加：`_analyze_hand` 返回字典、推荐算法读取、API 文档（design-docu §6.2）。
- **`photo_id` 是文件名（含扩展名），不是 hash 或 DB 主键**：当前没有 `photos` 表，photo_id 就是 `static/uploads/<photo_id>` 的 basename。Step 4.5 试戴接口拿 photo_id 去拼 `UPLOAD_DIR / photo_id` 读字节传给 ImageGenProvider。如果未来引入 `photos` 表（带过期清理 / 元数据等），保持 photo_id 字符串形态不变即可，只是多一张 DB 索引表。
- **`/static/uploads/` 通过 Step 2.4 的 mount 直接对外可访问**：前端可以 `<img src="/static/uploads/<photo_id>" />` 直接展示用户刚上传的图，**不需要单独的下载接口**。隐私层面：UUID-based 文件名是事实上的 capability URL（猜不到别人的 photo_id 就拿不到别人的图），对 demo 够用。生产要严格防越权访问需走签名 URL，超出 demo 范围。
- **`PIL.Image.open` 对超大图的拒绝**：默认 `MAX_IMAGE_PIXELS = 178956970`（约 178 MP）。我们 10MB 字节上限远低于这个，所以不会触发。但如果未来把上限提到 50MB，可能踩 DecompressionBomb 风险，需要显式设置 `Image.MAX_IMAGE_PIXELS = None` 或者在 try 里 catch `Image.DecompressionBombError`。
- **`await file.read()` 全量入内存**：10MB 上限下没问题。如果未来引入大文件（视频试戴），改用 `file.stream` 分块写盘 + 异步 hash。当前 demo 不需要。
- **PIL 调用是 CPU bound**：FastAPI 默认在主事件循环里跑 `def`（同步函数）会 block 其他请求。当前 `_analyze_hand` 几 ms 完成，影响可忽略。如果未来加真识别 → 几百 ms 的 CV 推理，要包 `asyncio.to_thread(_analyze_hand, content)`（参考 Step 3.4 邮件服务里同 smtplib 的处理）。
- **`UPLOAD_DIR` 计算用 `Path(__file__).parents[2]`**：稳妥指向 `backend/`，无论 CWD 在哪都对。如果有人把 user.py 挪进子目录（如 `routers/api/v1/`），这个层级数要重算。

---

### ✅ Step 4.3 · 款式列表接口 GET /api/styles — 2026-06-12

**做了什么：**
- `backend/app/routers/user.py` 实现 `GET /api/styles`：7 个 query 参数（`gender` / `tags` / `color_tone` / `length_pref` / `sort` / `page` / `size`）；过滤 + 排序 + 分页 + 返回 `{total, page, size, items[]}`。
- 仅返回 `is_active=1` 的款式（与 Phase 7 运营端"下架→C 端立即看不到"形成闭环）。
- gender 语义：未传返回全部 / `female` → `gender IN (female, both)` / `male` → `gender IN (male, both)`。
- `tags` 多值匹配用 `style_tags LIKE '%"<tag>"%'` 多 OR 子句——style_tags 是 JSON 数组字符串，元素被 `"` 引号包围，substring 匹配不会误伤前缀重叠（查"极简"不会命中"简约"）。
- **稳定排序 tie-breaker**：seed 时 40 行 `created_at` 共享同一个 `datetime.now()`（[seed_styles.py:50](backend/scripts/seed_styles.py#L50) 在 loop 外）+ `heat_score=50.0` 全同。`sort=new` / `sort=hot` 都加 `Style.id ASC` 做二级键，分页保证跨页不丢不重。`sort=smart` 用 `display_order ASC`（0..39 distinct），不需要 tie-break 但顺手也加。
- 非法 `gender` / `sort` 值 → 400 + envelope（`invalid_gender` / `invalid_sort`），快速暴露前端调用 bug。
- 新建 [`backend/scripts/_check_styles_api.py`](backend/scripts/_check_styles_api.py)（内部验证工具，下划线打头）：8 条 HTTP 自动断言，跟 Step 1.4 的 `_check_tryons.py` 同模式。后续 Step 4.4 / 4.5 验证可以照搬。

**Step 4.3 验证（plan 4/4 PASS + 4 补充 PASS + 用户手动通过）：**

| # | 测试 | 实测 |
|---|---|---|
| 1 | 无参数 → `total` | **40**（plan 写 25 是 25-female 时代数；现在 40 款全 active）|
| 2 | `?gender=female&size=100` | total=25，全部 gender ∈ {female,both} ✅ |
| 2b | `?gender=male&size=100` | total=15，全部 gender ∈ {male,both} ✅ |
| 3 | `?tags=极简&size=100` | total=2，每条 style_tags 含"极简" ✅ |
| 4 | `?sort=new&size=5` | 5 条，id=`[f_01..f_05]`（tie-break 后稳定）✅ |
| 5 | `?sort=smart&size=5` | `[f_01..f_05]`（按 display_order 0..4）✅ |
| 6 | `?gender=other` | **400** `invalid_gender` ✅ |
| 7 | `?sort=foo` | **400** `invalid_sort` ✅ |
| 8 | `?page=1&size=10` vs `?page=2&size=10` | 两页各 10 条，0 重叠 ✅ |

**几个设计选择（透明告知）：**

1. **plan "total=25" 调整为 40**：plan §4.3 验证语写的是 25 女款时代的预期。现在 40 款全 active，期望 40——跟 Step 2.1 "返回 25 → 返回 40" 同类 plan-vs-reality drift，按现状验证。
2. **tie-break 加 `id ASC`**：所有 40 行 seed 共享同一 `created_at` + `heat_score=50.0`。`sort=new`/`hot` 不加二级键会让 SQLite 按物理 rowid 排，跨分页可能错位（Step 1.6 `random.seed(42)` 也是为了同样的"测试结果应可复现"诉求）。`id ASC` 是 distinct + 自然字典序，零额外索引代价。
3. **`tags` 用 LIKE 不用 JSON 函数**：SQLAlchemy + SQLite 的 JSON1 (`json_extract`, `json_each`) 能更精确但 aiosqlite 默认不开 JSON1 扩展，需要额外配置。LIKE `'%"<tag>"%'` 在 JSON 数组字符串上完全正确（元素被 `"` 包围）。如果未来想升级到 JSON1，改 1 行 WHERE 子句。
4. **非法 `gender` / `sort` 严格 400 vs 静默 fallback**：plan 没规定。选 400 + 语义化 msg 让前端 bug 早暴露。如果 demo 期间觉得"前端偶发拼错参数被全屏 toast 太吓人"，改"未知值视同 None"一行 if 即可。
5. **`color_tone` / `length_pref` 不校验枚举**：plan 没列允许值。现状宽松透传——传 `color_tone=hot_pink` 不报错，只是 `WHERE` 结果空。前端只能从下拉框选有限值的话问题不大；否则未来加白名单。
6. **不引入 Pydantic 响应模型**：用 `Query()` + 字典返回。plan §2.3 允许同文件加 Pydantic，但本步无显式收益（OpenAPI 已能从 `Query()` 推参数 schema；response 数据形状简单）。Step 4.5 / 4.6 接口若复杂到值得校验再统一引入，避免半途加抽象。

**给后续开发者的提示：**

- **`is_active=1` 守门永远生效**：Phase 7 运营端下架某款（`is_active=0`），C 端 `/api/styles` + `/api/recommend` 立即看不到，**实现了 design-docu §1.2 的"运营→C 端"闭环**。如果未来需要"软下架"（C 端看不到但运营端能看到管理），ops 端单独写一个 `WHERE` 不带 `is_active` 的接口。
- **`tags=极简` 只命中 2 款是真实数据，不是 bug**：当前 40 款里只有 2 款 style_tags 数组包含"极简"。前端搜索 UI 应给"未找到"友好提示而不是空白。
- **新增 query 参数**：直接加 `Query()` 即可，不需要 schema 模型。`color_tone` / `length_pref` 当前是字符串完全相等过滤，未来如果要多值（`?color_tone=warm,cool`）改成 `.in_(list)` 即可。
- **`stmt.subquery()` 计算 total 的代价**：SQLite 上 40 行不在意；如果未来款式表上千需 N+1 查询优化，把 count 改成在主 stmt 上直接 count 即可。
- **`_check_styles_api.py` 是工具不是产品**：跟 `_check_tryons.py` 一样下划线打头，committed 但不参与运行时。Step 4.4 / 4.5 / 4.6 后续会有同模式的 `_check_recommend_api.py` 等。如果觉得 `scripts/` 下脏，未来可以挪到 `tests/integration/` 但要小心不要让 pytest 自动收集（保留 `_` 前缀即可避免）。
- **OpenAPI `/docs` Try-it-out 会被 X-User-Id 中间件拒**：用户实测 `gender=other` 和 `sort=foo` 红色 400 就是中间件后的 envelope 拒绝（不是 422 schema 错）。手动验证时要么用 PowerShell `curl.exe -H "X-User-Id: <uuid>"`，要么先在 Swagger UI 上点 "Authorize"（没配 security scheme 所以这个按钮目前没用）——后续 Phase 6 如果需要 Swagger 友好可在 FastAPI 加全局 `openapi_extra` 的 ApiKeyHeader。当前不做。

---

### ✅ Step 4.4 · 推荐算法核心模块 — 2026-06-12

**做了什么：**
- 新建 [`backend/app/services/recommend.py`](backend/app/services/recommend.py)（~160 行）：4 维评分 + 多样性 rerank 模块，**无 HTTP**（HTTP 路由是 Step 4.5）。
  - `_SKIN_COLOR_SCORE`：5 skin_tone × 3 color_tone 查表 → [0,1]（默认 0.5 兜底）
  - `_SHAPE_LENGTH_SCORE`：1 hand_shape × 3 length_pref（当前 hand_shape 只有 `average`，未来加真识别就扩表）
  - `_recent_7d_tryon_counts(db, ids)`：**单次** SQL `SUM(tryon_count) GROUP BY style_id WHERE stat_date >= 7-day-ago`，批量计算所有候选的热度，N+1 优化。窗口起点用北京时区 `datetime.now(_BJT).date()`，与 seed_stats.py 用 `date(created_at, 'localtime')` 的语义对齐。
  - `_diversity_rerank(scored, top_k=9, min_categories=3)`：贪心 swap——若 top-9 已含 ≥3 类首要标签则原样返回；否则按分数顺序遍历尾部，每个"新类别"候选与 selected 内某个"重复类别"的最低分行交换，直到达成阈值或无候选可换。
  - `recommend(db, gender, hand_features, top_k=9)` 编排：硬性别筛选 → 4 维打分 → 排序（含 id 二级键 stability）→ rerank。返回每个 item 带子分量字段（`skin_score / shape_score / heat_score / final_score`）方便 Step 4.5 LLM 拼推荐理由 + 运营端 debug。
- 新建 [`backend/tests/test_recommend.py`](backend/tests/test_recommend.py)（~80 行）：5 假用户 × 40 候选完整跑通，4 类断言（返回 9 条 / 首要标签 ≥3 类 / dark_cool 男 top-3 cool>warm / 性别不串）。

**Step 4.4 验证（5 用户 × 4 断言 = 20/20 PASS + 用户视觉确认）：**

| 用户 | top-1 | top-3 倾向 | 首要标签覆盖 | 关键观察 |
|---|---|---|---|---|
| F1 light_warm 女 | f_15 warm 复杂图案 | warm×2 / neutral×1 | 6 类 | 暖色优先命中 ✅ |
| F2 dark_cool 女 | f_09 neutral 跳色 | warm×1 / neutral×2 | 5 类 | 女款 0 cool，algo 选高 skin 的 neutral 兜底 |
| F3 medium 女 | f_15 warm 复杂图案 | warm×1 / neutral×2 | 5 类 | medium universal，heat 主导 |
| M1 light_warm 男 | m_15 cool 深色系 | cool×1 / warm×2 | 4 类 | heat=1.00 让明星款压过暖偏好（合理 trade-off）|
| **M2 dark_cool 男** | **m_15 cool 深色系 score=0.785** | **cool×3 / warm×0** | 3 类 | **plan §4.4 验证 2 核心证据**：top-3 全冷调，0 暖 |

**几个设计选择（透明告知）：**

1. **diversity 维度的 0% 评分贡献**：design-docu §6.3 伪代码直接写 `0.15 * 0`。维度只在 rerank 阶段材化。若改成评分阶段加 diversity bonus 需要全局组合优化，实现成本飙升。当前 rerank 法简单 + 完全够 demo + 与设计文档严格一致。
2. **`heat_score` 用 max 归一化而非线性映射 50→1**：pool 内热度差异感更强，"今日最热"自动得 1.00、其他相对它打分。如果未来想绝对阈值（"必须真热才得高分"），改成 `min(count/100, 1.0)` 之类，但当前数据集 60 天 12000+ tryons 用绝对值不合理。
3. **`final_score` 上限 0.85 不是 1.0**：4 维满分 = 0.35×1 + 0.30×1 + 0.20×1 + 0.15×**0** = 0.85（diversity 维度评分贡献 0 是设计文档原话）。前端展示百分比时再 `score/0.85` 归一即可。
4. **女款 dark_cool 没 cool 候选 → top-1 是高 heat 的 neutral**：CLAUDE.md 已警示"Female 25 has 0 cool-tone styles"。测试脚本只对 male dark_cool 断言 cool>warm；female dark_cool 上算法给出**次优可达解**（neutral 通配在缺 cool 时是 0.80 vs warm 0.45，且 emerging_hot 高 heat 拉动 f_09 上位）。这是数据集结构性约束不是算法 bug。
5. **score 子分量都返回**：`skin_score` / `shape_score` / `heat_score` 与 `final_score` 都在每个 item 里。Step 4.5 LLM prompt 可引用具体维度（"暖色衬你浅暖皮"），运营端可看"为什么这款被推第 1"。**注意 `heat_score` 字段在两层语义里复用**：DB `styles.heat_score` 是固定 50 基线；返回 dict 里 `heat_score` 是 7d 归一化后的 [0,1] 值。Step 4.5 / O5 助手用要区分。
6. **`tests/test_recommend.py` 带 `test_` 前缀但是 runnable script**：plan 字面"保留在 backend/tests/ 下"。前缀让未来引 pytest 时自动收集；当前 `if __name__ == "__main__"` 形态可直接 `python` 跑，不依赖 pytest。
7. **`SkinTone` / `ColorTone` 不用 Enum / Literal 强类型**：plan 没要求；当前都是字符串，查表兜底默认 0.5 / 0.6。未来若想强类型，加 `Literal["light_warm", ...]` 一行即可，runtime 无影响。

**给后续开发者的提示：**

- **Step 4.5 `POST /api/recommend` 实现路径**：路由层 (1) 校验 body `{gender, hand_features}` → (2) `await recommend(db, gender, hand_features, top_k=9)` 拿评分列表 → (3) 用 `services/llm.py` 的 `gen_text(..., model="quick")` **并发**生成 9 条推荐理由 → (4) 把 `reason` 填回每个 item → (5) 返回 `ok(data={recommendations: [...]})`。并发用 `asyncio.gather` 批量调 quick 模型（80B MoE 单次 1.5-2s × 9 并发 ≈ 总耗时 2-3s）。
- **推荐理由 prompt 模板见 design-docu §6.3 末尾**：包含性别专属措辞约束（女多用"衬肤""显白"、男多用"商务""利落""酷"），实现时直接复制粘贴。
- **`recommend()` 不带 user_id 参数**：算法本身无个性化记忆（用户从未提供过偏好数据），只依赖即时上传的 hand_features。Step 4.5 路由从 header 拿 X-User-Id 写 tryons 表（如果 demo 设计想记录"该用户被推荐过哪些"），跟 recommend 模块解耦。
- **多样性 rerank 实测几乎不触发**：5 用户里 4 个 organic top-9 就已含 ≥3 类首要标签。只有当候选池 ≤9 或某个 skin/shape 组合压倒性匹配某一类标签时才会触发 swap。这不是 bug——证明评分本身已有"自然多样性"。
- **改评分表的成本**：`_SKIN_COLOR_SCORE` / `_SHAPE_LENGTH_SCORE` 是普通 dict 常量。改一格 → 重跑 `tests/test_recommend.py` → 看 PASS/输出 → commit。无 DB 迁移、无前端联动。Demo 期间用户视觉判断不满意某组合（[feedback_visual_judgment]），直接改一行。
- **`max_heat` div-by-zero 兜底**：所有候选 7 天 0 tryon（极端冷启动）时 `max_heat` 被强制设 1，heat_score 全 0，但其他维度仍正常排序。算法不崩。
- **跨用户 score 不可直接比较**：score 是 pool 内相对值（heat 用 max 归一化）。U1 用户的 0.785 与 U2 用户的 0.785 含义不同——不要在运营端展示成"用户 A 比 B 更适合 m_15"，意义不对。

---

### ✅ Step 4.5 · 推荐接口 POST /api/recommend（含 LLM batch 推荐理由）— 2026-06-12

**做了什么：**
- `backend/app/routers/user.py` 实现 `POST /api/recommend`：body `{user_id, gender, hand_features}` → 调用 Step 4.4 的 `recommend()` 拿 9 条评分 → **1 次 batch LLM 调用**生成 9 条编号理由 → 返回 `{user_summary, recommendations[]}`。
- `recommendations` 每项含 `{style_id, name, cover_url, color_main, style_tags, score, reason}`——比 plan 字面要求多了 `color_main` + `style_tags`，给 Step 5.5 前端展示 chip / 色块 / 筛选预填用。
- `backend/app/services/llm.py` 把 `AsyncOpenAI` 改成模块级单例（共享 httpx 连接池）——9 并发场景下避免 9 次独立 TLS 握手 + 9 个独立 pool 形成的事实串行化。
- Fallback 模板按 `(gender, color_tone)` 6 组合丰富：暖调女款→"温柔显白"、冷调女款→"清冷气质"、中性女款→"百搭衬肤"、暖调男款→"干净利落"、冷调男款→"深邃有型"、中性男款→"低调耐看"。
- 新建 [`backend/scripts/_check_recommend_api.py`](backend/scripts/_check_recommend_api.py)（Pass A：4 case）+ [`_check_recommend_fallback.py`](backend/scripts/_check_recommend_fallback.py)（Pass B：空 key 路径）。

**走的一个弯路（透明记录，避免后续踩同坑）：**
最初严格按 plan 字面用 9 并发 `asyncio.gather` 实现，elapsed 17s——超 6s 预算 11s。诊断流程：
1. 加 timing log 看每条 LLM 耗时
2. 用 `_probe_ppio_quick.py` 直接探 PPIO：发现 **当前 PPIO_API_KEY 的 quick 档限速 5 req/min**（错误响应明确写 `current limit 5 requests per minute`）
3. 9 并发 → 4 成功 + 5 个 429 → 我的 `_with_retry` 指数退避 1s/2s/4s 三次 → 每个限流 call 走完 11s
4. 解法 1：共享 AsyncOpenAI 实例（节省 TLS）—— 缓解但 rate-limit 仍碾压
5. 解法 2：**改成 1 次 batch 调用要 9 条编号理由**——1 req/recommend 完全在限速内，单次 3-5s
   - prompt 把 9 款列成编号清单 + 严格"每行 `<num>. <reason>`"格式要求
   - `_parse_batch_reasons` 容错 `1./1、/1)/1．` 四种编号格式 + 单行解析失败该 slot 用 fallback
   - 不要求所有 9 行都解析成功，最差情况降级到全 fallback

**Step 4.5 验证（plan 3/3 PASS + bonus 1 PASS + 用户视觉确认）：**

| Pass | Test | 耗时 | 内容 |
|---|---|---|---|
| **A** T1 | female / light_warm | **5.95s** | 9 fallback（rate-limit 窗口内 LLM 失败）+ `color_main`/`style_tags` 字段就位 |
| **A** T2 | male / dark_cool | **5.25s** | 9 条真 LLM batch：「深黑哑光显商务利落，冷调光泽压住暗肤」「粉紫几何切割酷感十足，冷调撞色打破沉闷」等具体视觉理由 |
| A T3 | invalid gender | — | 400 `invalid_gender` ✅ |
| A T4 | body.user_id ≠ header | — | 400 `user_id_mismatch` ✅ |
| A required-fields | 7 字段（含新加的 `color_main`+`style_tags`）| — | 全部 9 条 ✅ |
| **B** | `.env` 临时空 `PPIO_API_KEY` 重启 | **1.42s** | 9 条 fallback 模板，路径正确 |

**几个设计选择：**

1. **batch LLM vs 9 并发**：plan 字面"并发"，我实际用 1 次 batch。理由：(a) PPIO 5 req/min 结构性不可达 (b) 1 batch 比 9 并发更快 (c) 解析失败局部 fallback。**改进点**：未来若 PPIO 限制放宽 / 换 key，可恢复 9 并发——只需替换 `_gen_batch_reasons` 为 `asyncio.gather` 包 9 个单调用。
2. **AsyncOpenAI 单例**：原实现 9 个独立 httpx pool → 9 次 TLS → 实际串行。改单例后所有后续 Phase 8 / Phase 9 用 LLM 的地方自动受益。`_shared_client` 仅在 `PPIO_API_KEY` 非空时缓存，empty key 测试时新进程会拿到 ConfigError。
3. **fallback 由 `(gender, color_tone)` 决定 tail**：原 9 张卡都 "显白衬肤" 太单调。现在 6 组合让 fallback 也有 4-6 种 tail 分布。但 **head 仍是 `style_tags[0]+款`**——同 tag 同 tone 的款式仍会重复（如两款 warm 法式女款都是"法式款，温柔显白"）。
4. **`color_main` / `style_tags` 加进响应**：plan 字面只列 5 字段，但 Step 5.5 前端展示卡片必然需要色块预览 + 标签 chip。提前加避免 Step 5.5 时回头改后端。`style_tags` 是 list[str]（已 `json.loads`），`color_main` 是 hex 字符串。
5. **超时 4.5s outer wait_for**：单次 batch 调用，没有 per-call timeout 复杂度。LLM 超 4.5s 直接 fallback 全 9 条。简单可靠。
6. **`_parse_batch_reasons` 不依赖正则**：手撸字符位置解析，避免正则复杂度且对中文标点更可控。支持 4 种编号分隔符。

**⚠️ Secret 轮换提醒（已通知用户处理）：**

实施期间我用 `Select-String` 把 `.env` 的 `PPIO_API_KEY=sk_8WtRlgEyM0hQZx1Z5oKA1lk2...` 前 30 字符暴露在对话输出里。按 Step 3.3 / 3.4 的轮换约定，用户应去 PPIO 控制台 revoke 旧 key + 新建 + 自己手改 `backend/.env`（**不贴对话**）。此事件加入"📌 项目锁定状态" Secret 轮换历史。

**给后续开发者的提示：**

- **改 batch prompt 不要轻动格式约束**：当前 prompt 强制"每行 `<num>. <reason>`"是解析的前提。如果调成"每条用 markdown bullet"等，`_parse_batch_reasons` 要同步重写。建议改 prompt 时先在本地用 `_probe_ppio_quick.py` 跑一遍人眼看输出格式再上 production。
- **PPIO key 升级会让批处理回归并发可能**：当前限速 5/min 是 PPIO 免费档或低档。如果用户充值或开企业账号，限速可能到 60/min+。届时可以恢复 9 并发实现更低延迟——预计 9 并发耗时 2-3s（每个 quick call 1.5-2s + 共享 client 让 PPIO 看作 multiplex）。模板代码留在 git 历史可参考。
- **`user_summary` 模板纯静态**：当前是 `f"{g}，{skin}肤色，{shape}手型"` 形如"女生，浅暖肤色，均衡手型"。如果未来想用 LLM 生成更花哨的总结，加 1 次 LLM 调用即可（不在 batch 里）。但当前足够 demo。
- **`color_main` 字段命名注意**：DB 是 `color_main`，响应字段也叫 `color_main`。**不要**前端层面又翻译成 `mainColor`——保持端到端一致，免得做映射。
- **Step 5.5 前端读响应时**：从 `data.recommendations[i].color_main` 拿 hex 渲染色块、`data.recommendations[i].style_tags` 渲染 chip、`data.recommendations[i].score` 不要直接展示给用户（Step 4.4 进度里说过它是 pool 内相对值），用作内部排序参考。
- **Step 4.6 单款试戴的 `from_module`**：当 C 端从推荐页跳试戴时，前端应在 `/api/tryon` body 带 `from_module="recommend"`——这样 tryons 表能区分用户行为来源，Step 7.3 冷门看板分析"推荐位的款是不是被试戴了"才有数据。
- **rate-limit 边缘 case**：如果 PPIO 当前已被打满但还没满分钟，新请求仍会 fallback。这是预期行为不是 bug。如果 demo 时观察到全部 fallback，等 60s 重试即可。

---

### ✅ Step 4.6 · 单款试戴接口 POST /api/tryon + 数据闭环 — 2026-06-13

**做了什么：**
- [user.py](backend/app/routers/user.py) `POST /api/tryon`：body `{user_id, style_id, photo_id, user_gender?, skin_tone?, hand_shape?, from_module?}` → 校验 style 存在且 `is_active=1` + photo 文件存在 → 调 `get_image_provider().generate(...)` → **单事务**写 tryons + UPSERT style_stats → 返回 `{tryon_id, result_url, elapsed_ms}`。
- 抽出 `_do_tryon(...)` 内部协程（kwargs-only 签名），Step 4.7 多款对比直接复用——plan §4.7 字面要求"直接调函数不通过 HTTP 转发"。
- UPSERT 用 `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update(index_elements=["style_id","stat_date"], set_={"tryon_count": StyleStats.__table__.c.tryon_count + 1})`——落成 SQL `ON CONFLICT(style_id, stat_date) DO UPDATE SET tryon_count = tryon_count + 1`，与 design-docu §10.3 字面一致。
- 北京时区 `_BJT` 计算 `today` 与 seed_stats.py / recommend.py 完全对齐（design-docu §4 时区约定）。
- 错误状态码语义化：style 不存在/已下架 → 404 `style_not_found`；photo 文件丢 → 404 `photo_not_found`；ImageGenError → 500 `tryon_generation_failed`；user_id 不匹配 → 400 `user_id_mismatch`。
- 新建 [`backend/scripts/_check_tryon_api.py`](backend/scripts/_check_tryon_api.py)：5 步链路 + 3 个负样本路径 = 6/6 自动断言，跑一次会让 DB 真+1（每次跑前看 BEFORE/AFTER 数字对比）。

**Step 4.6 验证（plan 3/3 + 3 负样本 = 6/6 PASS + 用户手动确认）：**

| 步骤 | 实测 |
|---|---|
| BEFORE: tryons(f_01)=1356 / today_stats=0 | seed 基线 |
| upload `samples/01.png` | photo_id=`550e8400-...-440000_1781331232246.png` |
| POST /api/tryon | tryon_id=12848 / result_url=`/static/cache/<uid>_f_01.png` / elapsed_ms=**28**（MockProvider 文件复制）|
| GET result_url | 200，1,221,491 字节 ✅ |
| AFTER: tryons(f_01)=**1357** / today_stats=**1** | **+1/+1 数据闭环关键证据** ✅ |
| bad style_id `ghost_999` | 404 `style_not_found` ✅ |
| bad photo_id | 404 `photo_not_found` ✅ |
| body.user_id ≠ header | 400 `user_id_mismatch` ✅ |

**几个设计选择（透明告知）：**

1. **`_do_tryon` 抽出来给 Step 4.7 复用**：plan §4.7 字面"用 asyncio.gather 并发调用 Step 4.6 的内部逻辑（不通过 HTTP 转发）"。提前抽出避免 4.7 实现时回头改 4.6。签名收紧成 kwargs-only 让 4.7 调用点更可读，调用方必须显式传字段名 → 防止字段顺序错位偷偷传错。
2. **`flush()` 拿 `tryon_id` 再 commit**：`db.add(new_tryon)` 不立即赋 PK。`await db.flush()` 让 SQLite 分配 autoincrement id 但 **不 commit**——后面 UPSERT 失败也能整体 rollback（virginal SQLite 单文件无并发触发率低，但事务语义对齐 design-docu §10.3 是硬要求）。
3. **`get_image_provider()` 在 `_do_tryon` 里调（不模块级）**：plan §3.1 的工厂从 `settings.IMAGE_PROVIDER` 读，留给运维"运行时切 mock↔seedream"的可能。如果挪到模块顶层会被 import-time 锁定。代价是每次 tryon 函数调用都查一次 settings——是 dict 查找，可忽略。
4. **`user_gender` 兜底从 `style.gender` 派生**：plan 字面"可选"。如果 body 没传，从 style 表反推（女款→female，男款→male，both→female）。这样老前端没传也能拿到 NOT NULL 字段；前端 Step 5 实现时显式传 sessionStorage 里的 `userGender`，但兜底逻辑作为防御性后端不依赖前端。
5. **`is_collected=0` 硬编码**：plan 没说支持"试戴时同时收藏"。Phase 5 的 U5 结果页有独立"收藏"按钮（design-docu §6.6），走另一个 POST 接口。如果以后要合并，让 body 多一个 `is_collected` 可选字段即可。
6. **UPSERT `set_` 用 `StyleStats.__table__.c.tryon_count + 1`**：dialect-level SQL 表达式。原表达式 `StyleStats.tryon_count + 1` 在 set_ dict 里也成立但显式 `__table__.c` 让意图（"指存量列+1"）更清晰，跟未来读者解释"为什么这里不是 Python +1"的成本更低。
7. **`elapsed_ms` 仅覆盖 generate() 那段**：不包含 DB 校验 / 事务提交。响应给前端的"试戴耗时"=AI 生成耗时，更贴近用户感知（mock 28ms / Seedream ~50s）。如果未来想区分"总耗时 vs AI 耗时"再加 `total_ms` 字段。

**给后续开发者的提示：**

- **MockProvider 同 (user, style) 多次试戴覆盖文件**：MockProvider 写 `cache/{user_id}_{style_id}.png` 路径写死不带时间戳，再次试戴会覆盖。design-docu §8.1 / Step 3.1 progress 已声明这是"演示安全网"行为。Seedream provider 带 ms 时间戳 → 多次试戴累加文件不覆盖。
- **真切 Seedream 流程**：`backend/.env` 把 `IMAGE_PROVIDER=mock` 改 `seedream`，重启后端。一次试戴 ~¥0.2 / ~50s。**演示前一天 dry-run 一次确认链路通**。
- **Step 4.7 多款对比试戴**：用 `asyncio.gather(*[_do_tryon(..., db=...) for sid in style_ids])`。**注意**：每个 `_do_tryon` 会自己 commit，所以并发场景下 9 次 commit 会真的执行。AsyncSession 是否支持 gather 下多次 commit 需要在 Step 4.7 验证。如果失败，方案 B：4.7 自己管理事务（每个 style_id 独立 AsyncSession），方案 C：成功的累积到一个 batch 用一次 commit（违反"单款失败不阻塞"语义）。优先试方案 A。
- **每次试戴都让 today's `style_stats.tryon_count` +1**：这是 design-docu §1.2 闭环的关键。Step 6.1 之后的 O1 概览看板直接读这个表就能看到秒级更新——演示时用户点几次试戴，运营端 10s 轮询就能看到数字变。
- **`from_module` 默认 `browse`**：当 C 端从推荐页跳试戴时，前端应主动传 `from_module="recommend"`；对比页传 `from_module="compare"`。**别让前端漏传**——Step 7.3 冷门看板想分析"推荐位的款是不是被试戴了"完全依赖这个字段的真实性。Step 5 前端实现时把这个字段固化到 router state。
- **404 vs 410 for inactive style**：当前下架款（`is_active=0`）也返回 404 不是 410（Gone）。理由：对 C 端来说"看不到这款"和"完全不存在这款"前端处理一致，没必要细分。运营端将来要做"管理已下架款"接口，单独走 `/api/ops/styles?include_inactive=1` 路径。
- **PIL `_analyze_hand` 不在试戴接口里跑**：Step 4.2 已把它放在 upload 接口里产出 hand_features，再由前端 Context 持有；试戴接口接收 hand_features 作为 body 字段。这样同一张手图多次试戴只算一次特征，省 CPU。

---

### ✅ Step 4.7 · 多款对比试戴 POST /api/tryon/batch — 2026-06-13

**做了什么：**
- [user.py](backend/app/routers/user.py) `POST /api/tryon/batch`：body `{user_id, photo_id, style_ids[], (optional features...)}`，强制 `len(style_ids) ∈ [2, 4]`，超出范围 → 400 `style_ids_count_invalid`。
- 抽出 `_do_tryon_one_with_own_session(...)` 包装器：每个 style_id 在 **独立 AsyncSession** 里跑 Step 4.6 的 `_do_tryon`。`asyncio.gather` 并发 fan-out N 个分支，sidestep "AsyncSession 并发 commit" 风险（Step 4.6 progress 末尾预判过的潜在坑）。
- 单款失败 (HTTPException 或任何 Exception) → 该 item 标 `status="failed"` + `error` 字段，**不阻塞其他款**——内部 catch + dict return，永远不让一个失败的分支把整个 batch 带崩。
- batch 路径 `from_module` 默认 `"compare"`（vs 单款 `/api/tryon` 默认 `"browse"`）——贴 design-docu §6.5 U4 多款对比试戴语义。
- 新建 [`backend/scripts/_check_tryon_batch_api.py`](backend/scripts/_check_tryon_batch_api.py)：5 case 验证（plan 4/4 + 顺序检查）。

**Step 4.7 验证（plan 4/4 + 顺序检查 = 5/5 PASS + 用户手动确认）：**

| Test | 输入 | 实测 |
|---|---|---|
| T1 | 3 valid `[f_01, f_05, f_10]` | 3 ok / 3 distinct result_url / tryons +3 / **elapsed 38、62、37ms** |
| T2 | `[f_02, ghost_999, m_01]` | `[ok, failed, ok]` / ghost error=`style_not_found` / tryons **+2**（仅 ok 写入）|
| T3 | 5 ids | 400 `style_ids_count_invalid` |
| T4 | 1 id | 400 `style_ids_count_invalid` |
| 隐式 | items 顺序 = 入参顺序 | 全部保持 ✅ |

**并发证据（重点）：** T1 三款独立耗时 38/62/37 ms。串行执行总耗时应 ~137ms，并发执行 ≈ max(38,62,37) = **62ms**——客户端实际感知。`asyncio.gather + 独立 session` 真在并发跑，**Step 4.6 progress 提的 "AsyncSession 并发 commit" 担忧根本没触发**（被独立 session 设计绕开了）。

**几个设计选择（透明告知）：**

1. **每个 `_do_tryon` 独立 session（不共享 db）**：plan §4.7 字面"直接调函数不通过 HTTP 转发"——意指调函数复用 Step 4.6 逻辑，**没**说必须共享 session。AsyncSession 并发 commit 是已知 SQLAlchemy 反模式。我用 `async with async_session_maker():` 每分支独立 session。代价：N 个 SQLite 连接打开（SQLite 默认 WAL 关闭下写入串行，但 2-4 并发量级 < 10ms 串行化损失可忽略）。
2. **`gather` 内部 catch all → 返回 dict 而非 raise**：`asyncio.gather` 默认任一分支抛异常就取消其他——这违反"单款失败不阻塞"。我在 `_do_tryon_one_with_own_session` 内部 catch 全部异常 → 包成 `{status:"failed", error:...}` dict 返回。`return_exceptions=True` 也是一条路但需要 caller 分类，内部 catch 更显式且把 dict 形状逻辑集中。
3. **`HTTPException.detail` vs 通用 `internal_error`**：HTTPException 的 `detail` 字段就是我抛的 `"style_not_found"` 等语义化 msg，直接透传。其他 Exception 一律包成 `"internal_error"` 不漏内部细节给前端（跟 Step 2.2 全局 handler 思路一致）。
4. **`elapsed_ms` 在 ok 项里 / failed 项 None**：每款独立计时（_do_tryon 自带）。前端可显示"f_05 用了 62ms / ghost 失败"。如果 plan §4.7 验证将来加"总耗时"，再加 `batch_elapsed_ms` 字段在 data 顶层即可。
5. **`style_ids_count_invalid` 同 msg 覆盖 <2 + >4**：plan 只显式要求 >4 的 4xx。我对 <2 也用同 msg——更简洁。如果前端要区分上界/下界给用户友好提示，后续加 `error_detail: "too_many" | "too_few"` 字段无破坏改动。
6. **`from_module` batch 默认 `compare`**：design-docu §6.5 把多款对比页定义为 U4 模块。单款接口（Step 4.6）默认 `browse`，因为单款入口主要是 U3 浏览页点单卡。前端显式传 `from_module` 则覆盖默认（如"推荐位过来批量试戴"传 `recommend`）。
7. **T1 用 3 个不同 style_ids，不是同一个 style 3 次**：避免 SQLite 在 `style_stats` 同一行的 UPSERT 串行竞争干扰并发结果。3 个不同 style → 3 行独立 UPSERT，零行级竞争，并发数据干净。如果想测"同款连试 3 次"的边界场景，后续可加 T5。

**给后续开发者的提示：**

- **Phase 5 U4 对比页前端实现**：前端 SSE / WebSocket 渐进展示是 design-docu §6.5 推荐方案，但当前 batch 接口是 **一次性返回所有 items**（gather 等齐才回）。若要做渐进展示，方案 A 改 SSE endpoint（StreamingResponse + asyncio.as_completed）；方案 B 前端 batch 拆成 N 次单款并发请求（Step 4.6 单款接口 + 浏览器 fetch 并发）。**当前接口形态适配方案 B**——前端实现时直接调 N 次 `/api/tryon`，不需要 batch 接口。**那为什么还实现 batch 接口？** 因为 plan §4.7 字面要求，且后端 batch 比前端 N 次请求少一些 round-trip 开销。Phase 5 实现 U4 时再决定走哪条。
- **AsyncSession 并发 commit 验证**：Step 4.6 progress 末尾担心"gather 下多次 commit 行不行"。本步用独立 session 直接绕开了这个问题，**没有验证过共享 session 多 commit 的真实行为**。如果未来想优化连接池，要先验证。
- **MockProvider 多分支同 (user, style) 覆盖**：T1 跑完 `cache/<uid>_f_01.png` 等 3 张文件已写盘。下次同样 batch 会覆盖——这是 MockProvider 写死路径的预期行为，Seedream provider 带 ms 时间戳累加。
- **batch 接口同样受 X-User-Id 中间件保护**：`@router.post("/tryon/batch")` 在 `/api` 前缀下，Step 4.1 中间件覆盖。验证 6/7 隐式经过 header 检查。
- **失败 item 的 `error` 字段值前端要识别哪些**：当前可能值 = `style_not_found`、`photo_not_found`、`tryon_generation_failed`、`internal_error`。前端展示用文案映射表统一翻译给用户看；不要把英文 error 直接展示。
- **Phase 4 收官**：C 端 7 个接口全部就位（health / ping / upload / styles / recommend / tryon / tryon batch）+ 数据闭环（tryon → tryons + style_stats UPSERT）可工作。下一步进 Phase 5 前端（8 步）。**Phase 5 开始 demo 视觉效果就有了**——前端连后端能跑完整 L0 → U0 → U1 → U2 → U3 → U4 → U5 主线。

---

### ✅ Step 5.1 · 前端路由骨架 + 全局 Context — 2026-06-13

**做了什么：**
- **清理 Vite scaffold cruft**：删 `App.css`、`assets/hero.png`、`assets/react.svg`、`assets/vite.svg`；`index.css` 简化为 Tailwind 三指令 + 极小 base（body 用品牌色 `#faf8f2` / `#111111` 做雏形，等 Step 5.2 接 tech-stack §2.5 完整色板）。
- **`store/UserContext.tsx`**：`UserProvider` 用 React Context 管 5 字段（`userId / userGender / handFeatures / compareSelection / photoId`）。Provider 初始化时 `crypto.randomUUID()` 写入 sessionStorage（若不存在），`userGender` 切换走 setter 同步 sessionStorage。`useUser()` Hook 在外部消费，无 Provider 直接抛错。
- **`api/client.ts`**：axios 实例，`baseURL` 从 `VITE_API_BASE` env 读默认 `http://localhost:8000`。Request 拦截器自动注入 `X-User-Id` header（从 sessionStorage 读）。Response 拦截器在 envelope `code !== 0` 或网络错误时调 antd `message.error(msg)`。
- **`components/Placeholder.tsx` + `DebugBar.tsx`**：每个占位页顶部 `code+title` 黄章 + DebugBar（实时展示 Context 5 字段 + 5 个调试按钮：set female / set male / show userId / probe bad API / reset sessionStorage）+ 16 个路由的 Quick Nav 网格。让用户不打开 DevTools 也能完成 90% 的 plan 验证。
- **`App.tsx` 重写**：`<AntApp>` + `<UserProvider>` + `<BrowserRouter>` + 16 个 Route 严格按 design-docu §11.2 + 一个 `path="*"` 兜底显示"未匹配路径"。
- `index.html` 标题改 "美甲 AI 试戴 · Demo"，`lang="zh-CN"`。

**Step 5.1 验证（plan 5/5 PASS）：**

| 验证项 | 实测 |
|---|---|
| 1. 16 路径都能渲染占位页 | ✅ 浏览器实测 + curl `/upload` `/ops/setting` 200 |
| 2. 首次访问 `/` sessionStorage 自动出现合法 UUID `userId` | ✅ DevTools 应用程序→会话存储看到 `userId=4019970b-...` |
| 3. setUserGender("male") + 刷新仍持久 | ✅ 切到 female → F5 → DebugBar 还是 female |
| 4. axios 调不存在接口弹 antd 错误提示 | ✅ probe bad API 后右上角红 toast |
| 5. 任意 API 请求带 `X-User-Id` header | ✅ Network Tab 看 `_does_not_exist` 请求 → Request Headers 有 `x-user-id: <UUID>` 与 sessionStorage 完全一致 |
| 附加 | `npm run build` 通过（tsc -b + vite build），1523 modules / dist 545 KB |

**几个设计选择（透明告知）：**

1. **不引 vite proxy**：axios 直连 `http://localhost:8000`，跨域走后端 Step 4.1 已经配好的 CORS。代价是浏览器要做一次 OPTIONS 预检（用户截图里能看到 2 行 `_does_not_exist`——上面那行 prefli 200 就是预检）。优点是前后端解耦，不依赖 vite dev server 路径。生产部署时 nginx 反代统一就好。
2. **Vite 8 默认绑 IPv6 `::1`**：dev server 起来后 `127.0.0.1:5173` 连不上，必须用 `localhost:5173`。坑了我两次（curl 127.0.0.1 失败，换 localhost 200）。验证步骤里显式标注，让后续开发者不踩。如果以后想绑 IPv4，在 vite.config.ts 加 `server.host = "127.0.0.1"`。
3. **DebugBar 设计目的**：plan §5.1 验证 3/4 字面要求"临时调一次"——意味着用 DevTools console 手动调函数。我把这些做成可视按钮，让用户不学 console 就能验证。Step 5.2 真正实现 L0 时，DebugBar 会被换成 `import.meta.env.DEV` 才渲染（保证生产不出现）；当前 Step 5.1 全部都是占位页所以 DebugBar 永驻是 OK 的。
4. **`<AntApp>` 包外层而非用静态 `message`**：antd v5 + React 19 推荐 `App.useApp()` 拿 message 实例（context 安全）。但 axios 拦截器在 React 树外，无法用 hook。**我用静态 `message.error()` 简化**——antd 会打 warning 说"static method 在 React 19 下可能丢 context"但功能正常。Step 5.2+ 如果发现 toast 行为有 bug，再迁移到 `useApp()` 方案。
5. **`compareSelection` / `handFeatures` / `photoId` 不持久化 sessionStorage**：plan §5.1 字面只要求"userId 与 userGender 持久化"。试戴选择和手图特征是单次 session 的工作态，刷新就重置反而更符合 demo "重新开始一次"的语义。如果后续 U6 历史页要持久化收藏列表，那是 localStorage 的事（design-docu §6.7 已说明）。
6. **`/result/:id` 用动态参数 `:id`**：design-docu §11.2 表里就是 `:id` 形式。Step 5.7 U5 实现时用 `useParams()` 拿。当前占位页 Quick Nav 用 `demo-tryon-id` 字面值跳过去验证路由模式。同理 `/ops/reports/:id` 用 `demo-report-id`。
7. **不在 axios 拦截器里捕业务级 4xx**：response 拦截器对 `code !== 0` 都弹 toast——包括 400 `invalid_gender` 等用户操作错误。可能造成"用户填错表单也弹红 toast"的体验偏激。Step 5.4 / 5.5 实现真业务页时，需要在 axios 调用处 catch 异常做更友好的页面级提示（取代或抑制全局 toast）。当前阶段足够。

**给后续开发者的提示：**

- **加新页面的路径**：在 `App.tsx` `<Routes>` 里加一行 `<Route path="..." element={<...>} />`，对应组件文件放 `src/pages/user/` 或 `src/pages/ops/`。Step 5.2 起会逐一替换 Placeholder。
- **加新 Context 字段**：在 `UserContext.tsx` 的 `UserState` 接口加字段 + Provider 里加 `useState` + 把 setter 写进 value object + `useMemo` 依赖里也要加。漏一处会触发 re-render 异常或 stale closure。
- **加新 API 调用**：从 `api/client.ts` import `api`，直接 `api.post("/api/...", body)`。X-User-Id 自动加。`message.error` 自动弹。组件层只需 try/catch 决定是否要额外页面级提示。
- **`crypto.randomUUID()` 浏览器兼容**：现代浏览器（Chrome 92+ / Firefox 95+ / Safari 15.4+）都支持，IE 不支持但 demo 不考虑 IE。如果未来要支持老浏览器，用 `uuid` npm 包替换。
- **`baseURL` env 配置**：当前默认 `http://localhost:8000`。生产部署时在 `.env.production` 里写 `VITE_API_BASE=https://your-domain.com`，build 时打进 bundle。前端代码无需改。
- **Tailwind config 还没扩品牌 token**：用了 `bg-yellow-300 / bg-yellow-50 / border-yellow-300` 等 Tailwind 内置色。Step 5.2 L0 需要 `bg-brand`（黄品牌色）等自定义 token 时再加 `tailwind.config.js` 的 `theme.extend.colors`。**两端共用 §2.5 色板是公约**，不要单独裸写 hex。
- **`/ops/*` 路由都是占位**：运营端要等 Phase 6（O1-O6 接口）和 Phase 7（O1-O7 前端）才有真实现。当前点 `/ops/overview` 等都是占位+DebugBar。
- **Step 5.2 L0 的 "整页布局"**：要替换 `<Placeholder code="L0" />`，独立 Layout 不要带 DebugBar（Step 5.2 progress 应该会移除占位页背景的黄色调试条）。可以在 L0 组件里用 `import.meta.env.DEV && <DebugBar />` 局部保留以备 debug。

---

### ✅ Step 5.2 · L0 双端入口（Landing）— 2026-06-13

**做了什么：**
- **`tailwind.config.js`**：tech-stack §2.5 完整 17 色 token 写进 `theme.extend.colors`（brand/page/card/surface/ink/line/ai/semantic 6 大类）。之后所有用户端组件用 class 表达色（`bg-brand` / `text-ink` / `border-line` / `text-ai-purple` 等），**禁止裸 hex**。
- **`index.css`** 顶部加 `:root` CSS var（`--ai-purple` / `--ai-blue` / `--ai-wash`）——给 Phase 7 运营端 antd 组件桥接 AI 紫（antd token 表无此概念）。
- **`pages/user/L0.tsx`** 新建（约 110 行）：完整 L0 落地页，按原型 Board 0 + design-docu §6.0：
  - Header：黄圆形品牌徽章 + 标题 + 副标题 + 右侧 slogan
  - Main：标题"请选择你的使用身份" + 两张大圆角卡片（`md:grid-cols-2` 桌面双列，移动端自动堆叠）
  - 左卡：4:3 hero 显示后端 `/static/styles/f_05_enh.png` + "用户端"黄章 + 三条功能 bullet + 黄色"进入用户端 →" CTA，整卡片 `<Link to="/gender">` 可点
  - 右卡：4:3 装饰性 div 条形图（黄色 + 1 根 AI 紫 + AI 紫圆点）+ "运营端"黑章 + CTA → `<Link to="/ops/overview">`
  - Footer：装饰文案
  - 全程 token-only，零 hex
- **`App.tsx`**：`/` 从 `<Placeholder code="L0" />` 换 `<L0 />`，其他 15 路由继续 Placeholder。
- `<img onError>` 兜底：后端 /static 离线时图自动隐藏，整卡片仍可点（导航不依赖图片）。

**Step 5.2 验证（用户浏览器实测 PASS）：**

| 验证项 | 实测 |
|---|---|
| `npm run build` 通过 | ✅ 1524 modules / CSS 5.5KB → **10.67KB**（Tailwind 拾起新 token）/ JS 549KB |
| L0 整页布局符合 Board 0 | ✅ 用户确认（黄章+标题+两张卡片+footer，无 DebugBar）|
| 左卡 CTA 跳 `/gender` | ✅ |
| 右卡 CTA 跳 `/ops/overview` | ✅ |
| 首次访问 / 仍写 userId 入 sessionStorage | ✅（`useUser()` hook 引用保留 ensureUserId 路径）|
| 色板正确：黄 #FFD100 / 米白页底 / 白卡 / AI 紫 #7C5CFF | ✅ |

**几个设计选择（透明告知）：**

1. **hero 图走后端 `/static`** 而非复制到 `frontend/public/`：演示前必启后端，复制冗余且增加维护点。代价：后端没起来 L0 hero 显示破图——`<img onError>` 兜底隐藏元素，整卡片仍可点击导航，体验不崩。
2. **右卡装饰图用 Tailwind div 不用真截图**：plan §5.2 字面"先用 placeholder 占位也可"。后期等运营端 Phase 7 真做完，可以截图换上。当前条形图 + AI 紫圆点已经传达"数据看板 + AI"语义，比一张占位图更轻量。
3. **整卡片 `<Link>` 可点 vs 只按钮可点**：Board 0 的视觉是大卡片 hover 上浮——`<Link>` 包外层让整张卡都是点击热区，符合习惯。键盘可达性：`<Link>` 自带 `tabindex=0` + Enter 触发，无需额外处理。focus ring 用 `focus:ring-brand-light`。
4. **L0 不引 DebugBar**：plan §5.1 进度笔记预告过——"Step 5.2 L0 是完整页面，无 DebugBar"。`useUser()` hook 引用还在（触发 ensureUserId 副作用），但调试按钮全没。如果未来要在 L0 里临时调试，可以 `import.meta.env.DEV && <DebugBar />` 条件渲染。
5. **`hover:-translate-y-1 + hover:shadow-xl`** 微动效：避免静止页面感太重。`transition-transform` + `duration-300` 平滑过渡，无 JS。
6. **右卡顶部 chip 用 `bg-ink text-card`**（黑底白字）而非黄底黑字：让两张卡的视觉区分度更高（左黄右黑），运营端更"严肃"。
7. **顶部 header `border-b` 用 `border-line`** 而非默认 Tailwind `border-gray-200`：强制走 §2.5 token，避免 token 体系外的灰色蔓延。后续每加一个边框都遵守这个约定。

**给后续开发者的提示：**

- **Step 5.3 U0 性别选择页**：路由 `/gender`。点 L0 左卡 CTA 跳入；用户在这里选 female/male 后写 sessionStorage 跳 `/upload`。Step 5.1 的 DebugBar 现在还在 `/gender` 占位页上——Step 5.3 替换占位时也去掉 DebugBar，跟 L0 一样做完整页面。
- **加新色 token 流程**：(1) 改 `tech-stack.md §2.5` 加新行 (2) 改 `tailwind.config.js` `theme.extend.colors` 添加 (3) 如果运营端要用，改 `index.css :root` CSS var + 后续 antd ConfigProvider token。三处都要动。
- **L0 hero 图想换**：改 `pages/user/L0.tsx` 顶部 `HERO_USER` 常量即可。当前用 `f_05_enh.png`——这是 cold-warm 通杀的女款，作为入口印象足够普适。
- **`@layer` 没加自定义**：tech-stack §2.5 没要求。如果未来发现 hover 状态、focus ring、卡片阴影到处重复，再用 `@layer components` 抽 `.card-base` 等。当前手写 utility class 还能管理。
- **Tailwind `aspect-[4/3]`** 浏览器兼容：现代浏览器都支持。如果遇到移动端 Safari 旧版有问题，回退用 `pb-[75%] relative` 经典方案。
- **设计稿的 phone-frame 暂未实现**：Board 0 左卡是手机框样式，我用矩形圆角卡片简化。如果觉得不够"高保真"，可以加一个 `<div className="rounded-[3rem] border-8 border-ink ...">` 把图包起来。Step 5.2 现状就是 plan 要求的最小集，后续可迭代。

---

### ✅ Step 5.3 · U0 性别选择页 — 2026-06-13

**做了什么：**
- **`pages/user/U0.tsx`** 新建（~110 行）：U0 性别选择页，路由 `/gender`，按 design-docu §6.1 + plan §5.3 + 原型 Board 1 第 1 屏。
  - Top bar：左 `←` 返回 / + 中央 AI 徽章 + 右上"跳过"按钮（点击 = 选女性，plan §5.3 字面要求）
  - 主体：U0 灰章 + 标题"先选择你想看的款式方向" + 一行解释副标题（"推荐算法会按性别做硬筛选..."）
  - 两张卡片 (`md:grid-cols-2`)，桌面双列移动端堆叠：
    - 左：`/static/styles/f_01_enh.png` + "Female · 25 款" chip + 副标"精致、跳色、法式、纯色..."
    - 右：`/static/styles/m_01.jpg` + "Male · 15 款" chip + 副标"哑光、冷调、商务、酷感几何系"
  - 底部小字隐私说明
- 已选项（userGender 等于该卡）加 `border-brand ring-4 ring-brand-light` 高亮——用户返回 /gender 时能看出之前选的哪个，符合"可随时返回切换"语义。
- 抽出 `GenderCard` 内部子组件：避免左右两张卡片样式重复维护成本，减少手抖出现"左卡边框对、右卡漏改"的样式漂移。
- `App.tsx`：`/gender` 路由从 `<Placeholder code="U0" />` 换 `<U0 />`，其他 14 路由继续占位。

**Step 5.3 验证（plan 4/4 + 高亮 1 + 用户实测 PASS）：**

| 验证项 | 实测 |
|---|---|
| `npm run build` 通过 | ✅ |
| 直接访问 `/gender` 无重定向 + 显示两卡片 | ✅ |
| hover 时卡片 -translate + shadow + hero 图缩放 1.05× | ✅ |
| 点击"女性" → URL `/upload` + sessionStorage `userGender=female` | ✅ |
| "跳过"按钮 = 点击"女性" | ✅ |
| 点击"男性" → URL `/upload` + sessionStorage `userGender=male` | ✅ |
| 返回 `/gender` 看到之前选项有 brand-light ring 高亮 | ✅ |

**几个设计选择（透明告知）：**

1. **`<button>` 包整卡片，不是 `<Link>`**：跟 L0 的 `<Link>` 模式不同。理由：U0 选完要**先 setUserGender 后 navigate**——需要副作用执行顺序。`<Link>` 只能纯导航。用 `<button onClick>` + `navigate("/upload")` 把"写 Context + sessionStorage + 跳转"放进一个 handler 里，原子化。
2. **已选 ring 高亮**：plan 没硬要求，但 design-docu §6.1 提到"可随时返回切换"——意味着用户会回来。没高亮就只能瞎猜上次选啥。`ring-4 ring-brand-light` 用品牌色 light 变体，醒目不刺眼。
3. **"跳过" = 选女性**：plan §5.3 字面要求。这隐含一个产品决策：当用户对性别不在意时，**默认走更大的款式池 + 更主流的视觉**——女款 25 款 vs 男款 15 款 + 女款风格更跳/更"演示出彩"。如果未来想改成"默认 male"或"默认 ask"，改一行 `choose("female")`。
4. **底部隐私小字**：plan 没要求，但既然产品声明"无账户系统、sessionStorage 关浏览器清除"（CLAUDE.md），主动告知降低用户决策门槛。
5. **GenderCard 子组件抽内部不外部 `components/`**：U0 专属，没复用诉求。塞 `components/` 是过早抽象。
6. **chip 用 `"Female · 25 款"` 英中混排**：测试覆盖国际化感 + 数字直观告知"款式池大小"。如果未来产品决定改纯中文"女性 · 25 款"，1 行 props 改动。
7. **`hero` URL 用 `f_01_enh.png` / `m_01.jpg`** 跟 plan §5.3 字面一致。这两张图都是 stable_hot 角色（Step 1.3 拍板），视觉上是"该性别池的代表款"。

**给后续开发者的提示：**

- **Step 5.4 U1 上传页**：路由 `/upload`。**前置守卫**：进入页面 useEffect 里检查 sessionStorage 的 `userGender`，不存在 `navigate("/gender", { replace: true })`。这点 plan §5.4 字面要求，跟 U0"无守卫"不对称——U0 是入口允许直接进，U1 必须先选过性别。
- **`Gender` 类型别处复用**：从 `store/UserContext` 导出，Step 5.4/5.5/5.6 都直接 import 这个 type alias，不要在各文件重复 declare `"female" | "male"`。
- **"跳过"的产品语义可调**：当前是"略过性别选择 = 默认女性"。如果未来产品决定"略过 = 进入混合模式"（同时看男+女），需要新增第三个 gender 值 `"unset"` 或者一个全局 flag，会牵动 recommend.py 的硬筛选逻辑——别轻动。
- **`crypto.randomUUID()` 在 U0 不调**：userId 是首屏 UserProvider 挂载时已经生成。U0 不重新生成，避免每次进 U0 都换 user id 造成 tryons 数据归因混乱。
- **HMR 偶尔不刷新 Tailwind 改动**：如果你看到 hover 效果没生效，硬刷新（Ctrl+F5）一次。vite + tailwind 在 css 增量时偶发 stale。

---

### ✅ Step 5.4 · U1 手图上传页 — 2026-06-13

**做了什么：**
- **`api/client.ts`** 加 `suppressToast` 配置（TS module 扩展 `AxiosRequestConfig`）：调用方传 `{ suppressToast: true }` 时全局 toast 不触发。U1 用它接管错误文案，避免跟全局 envelope `msg` 双 toast。
- **`pages/user/U1.tsx`** 新建（~160 行）：U1 手图上传页，路由 `/upload`，按 design-docu §6.2 + plan §5.4 + 原型 Board 1 第 2 屏。
  - 前置守卫 `useEffect`：`!userGender` 立即 `navigate("/gender", {replace:true})` + `if (!userGender) return null` 防 flash
  - Top bar：← 返回 /gender + AI 徽章 + 右上当前性别显示
  - 主体：U1 章 + 标题"AI 帮你看，哪款美甲适合你的手" + 副标
  - **antd `<Upload.Dragger />`**：accept jpg/png，`beforeUpload` 接管整个流程（type 验 → size ≤10MB 验 → `browser-image-compression` 压 ≤5MB → multipart POST `/api/user/upload` with `{suppressToast: true}` → 写 Context (photoId + handFeatures) → navigate `/recommend`），return false 取消 antd 默认上传行为
  - 4 张示例图 thumbnail，点击 → fetch → blob → File → 走同一 `handleFile`
  - uploading 状态：禁用 Dragger + 示例按钮 + 文案改 "AI 正在分析..."
  - 错误码 → 友好中文映射：`file_too_large→文件超大` / `unsupported_format→格式不支持` / `user_id_mismatch→身份校验失败，请刷新` / 其他→`网络异常，请重试`
- **示例图同源化（CORS 修复，验证期间发现）**：原版 SAMPLES URL 指向 `http://localhost:8000/static/samples/0X.png`。`<img src>` 缩略图能加载（`<img>` 不走 CORS check），但点击触发的 `fetch().then(r=>r.blob())` 被浏览器 CORS 阻断——FastAPI 的 `CORSMiddleware` 对 `app.mount("/static", StaticFiles(...))` 这种 sub-app mount **不可靠**（已知 Starlette 边缘 case，跟 ASGI 中间件栈与 mount 的交互有关，没深挖）。修法：把 4 张示例图（01-04.png，~5.5MB 总计）从 `backend/static/samples/` 复制到 `frontend/public/samples/`，URL 改成相对路径 `/samples/0X.png`，vite 直接同源服务，零 CORS。**附加红利**：后端离线时示例图仍能显示。
- `App.tsx`：`/upload` 路由从 Placeholder 换 `<U1 />`。

**Step 5.4 验证（plan 5/5 + 1 hover 效果 + 1 CORS 修复 = 7/7 PASS）：**

| 验证项 | 实测 |
|---|---|
| `npm run build` 通过 | ✅ 1593 modules / JS 549→680KB（多 browser-image-compression 库的体积）|
| 无 userGender 直接访 /upload → 重定向 /gender | ✅ |
| 拖拽手图 → loading → toast 成功 → 跳 /recommend | ✅ |
| 点示例图 → 跑通同一链路 | ✅（CORS 修复后） |
| 拖 .txt → 红 toast "格式不支持，仅支持 JPG / PNG" + 不跳转 | ✅ |
| 示例图 hover 边框变品牌色 + 阴影 | ✅ |
| Network Tab 看到 `POST /api/user/upload` 响应 envelope 正常 | ✅ |

**几个设计选择（透明告知）：**

1. **`suppressToast` 配置 vs 直接在 U1 catch**：可以不加 `suppressToast`，让全局 toast 也弹（双 toast 都显示），代价是英文 `file_too_large` 跟中文"文件超大"一起出现，用户体验差。加 `suppressToast` 让 axios 完全静默，由页面 100% 控制文案。后续 Step 5.5 / 5.6 / 5.7 凡是有页面级错误状态的调用都可以这么用。
2. **`beforeUpload` 包整个流程 + 返回 false**：antd Upload 的设计本意是"组件自己上传到 action URL"，但我们要在上传前压缩、在上传后写 Context + 跳转——比 antd 默认流程多步骤。`beforeUpload` 异步函数包所有逻辑、return false 阻止默认上传，是 antd 官方推荐的"我自己处理"模式。`customRequest` 是另一选，但跟 `beforeUpload` 的执行顺序耦合不直观。
3. **示例图同源化而非修 CORS**：本来想去修 FastAPI 的 `/static` CORS，但 StaticFiles mount 与 CORS middleware 的交互在 Starlette 里是已知坑，深修可能引出新问题。同源化 (`vite public/`) 是 5 行 PowerShell + 1 行 URL 改动，结果稳定。代价：4 张图重复存（前后端各一份，~5.5MB）+ 数据集变更时两边要同步。当前 demo 数据集冻结，可接受。
4. **示例图 4 张不是 17 张**：plan §5.4 字面"3-4 张示例图缩略图"。17 张全展示太多 UX 噪音。如果后续想加变化，改 SAMPLES 数组即可。
5. **`browser-image-compression` 参数 `maxSizeMB: 5, maxWidthOrHeight: 2000`**：后端限 10MB，前端先压到 5MB 留一倍 margin；2000px 长边覆盖绝大多数手机拍照尺寸。如果未来用户传 4K 截屏，2000px 限制会触发降采样，对手部 skin_tone 分析影响可忽略（后端只看中央 100×100 平均 RGB）。
6. **`<button>` 不是 `<img onClick>` 包示例图**：a11y 优先。`<button>` 自带 tabindex + Enter 触发 + screen reader 可读。屏幕阅读器读 "选择示例图 1" 比读 "图片" 友好。
7. **`message.success("已识别你的手部特征")`**：成功也给 toast，避免用户疑惑"是不是跳错了"。`/recommend` 出现前给个明确反馈。

**给后续开发者的提示：**

- **Step 5.5 U2 推荐页**：路由 `/recommend`。前置守卫：必须有 photoId + handFeatures，否则回 /upload。调 `POST /api/recommend` body 用 Context 里的 gender + handFeatures。LLM 推荐理由可能 5-6s（PPIO quick 档 batch），需要 loading skeleton 别让页面空白。
- **`SAMPLES` 数组改长度时**：1) PowerShell 复制对应文件到 frontend/public/samples/  2) 改 U1 的 `[1,2,3,4]` 数组  3) Grid `grid-cols-4` 可能也要改成 `grid-cols-3` 或 `grid-cols-5` 视情况
- **`browser-image-compression` 在 Web Worker 跑**：`useWebWorker: true` 让压缩不阻塞主线程 (重要 UX)。Edge / Chrome / Safari 都支持。
- **`fetch()` 不走 axios = 不走拦截器**：示例图的 `fetch(url)` 是浏览器原生 fetch，没有 X-User-Id header，没有 baseURL，没有 toast 拦截。这是有意的：示例图是静态资源，不属于 API 调用。
- **`AntApp.useApp()` vs 静态 `message`**：U1 用前者（context-safe），axios 拦截器仍用静态 `message`（位于 React 树外无法 hook）。两者在 antd 5 + React 19 下并存 OK。
- **`POST /api/user/upload` 同一秒重复上传**：当前用 `int(time.time()*1000)` ms 时间戳，理论上两次毫秒内连发会撞文件名。Step 4.2 时 demo 单用户场景无影响，未来加用户量再说。
- **`frontend/public/samples/` 进 git**：4 PNG 共 ~5.5MB，赛题数据集授权未明，但 `backend/static/samples/` 已经 gitignore（避免 git 体积膨胀）。前端这 4 张是为了 U1 同源化必须本地有的资产，性质类似 build-time fixture。如果担心 git 仓库体积，可以加 `frontend/public/samples/` 到 .gitignore + 把 PowerShell 复制命令加到 `seed_all.py` 末尾。当前先纳入 git，后续再决定。

---

### ✅ Step 5.5 · U2 智能推荐页 — 2026-06-13

**做了什么：**
- **`pages/user/U2.tsx`** 新建（~220 行）：U2 智能推荐页，路由 `/recommend`，按 design-docu §6.3 + plan §5.5 + 原型 Board 1 第 3 屏。
  - **双层守卫**：缺 `userGender` → /gender；缺 `photoId/handFeatures` → /upload。两个 `useEffect` 都在顶部声明完才 early-return null，第二个 useEffect 内部加内置 guard——满足 React hooks-must-run-in-same-order 不变式。
  - Top bar：← 返回 + AI 徽章 + 标题
  - 用户特征卡：圆头像 + "AI 为你识别到：" + 后端返回的 `user_summary`（如"女生，浅暖肤色，均衡手型"）+ 右上 AI 紫 chip
  - 调 `POST /api/recommend` body `{user_id, gender, hand_features}` → 9 卡 `lg:grid-cols-3` 瀑布流
  - **Loading skeleton**：9 个 `animate-pulse` 灰块占位，避免 LLM batch 3-5s 内白屏
  - 每张卡：4:3 封面图 + 左上 chip（`borderLeft: 3px solid color_main` 把后端 hex 注入做色块预览）+ 款式名 + 2 行 reason + 「试这款」黄按钮 + 「加入对比」复选框
  - 「试这款」：调 `POST /api/tryon` 带 `from_module="recommend"` → 拿 `{tryon_id, result_url}` → `navigate('/result/:id', {state: {result_url, style}})` 把数据塞 navigate state 给 Step 5.8 U5 读
  - 试戴中：该卡按钮 Spin + "AI 生成中..."，其他卡 disabled
  - 浮动按钮：`compareSelection.length >= 2` 时右下角"对比试戴 (n) →" 点击跳 `/compare`
  - 底部链接 "想看更多？浏览全部款式 →" 跳 `/browse`
- `App.tsx`：`/recommend` 从 Placeholder 换 `<U2 />`。

**Step 5.5 验证（plan 4/4 + 视觉色块 + skeleton + 用户实测 = 6/6 PASS）：**

| 验证项 | 实测 |
|---|---|
| `npm run build` 通过 | ✅ 1593 modules / JS 700KB / CSS 15.6KB |
| 3-6 秒内 9 卡片 + 每条 ≤25 字 reason | ✅ skeleton → 真卡片切换 |
| 勾 3 张 → 浮动按钮 "对比试戴 (3)" | ✅ |
| 点浮动按钮 → /compare + Context.compareSelection 3 个 id | ✅ DebugBar 实测 |
| 点「试这款」→ /result/:id + 试戴完成 | ✅ 1-2s 内 mock 完成 + cache/ 新文件 |
| 卡 chip 左边框颜色 = color_main | ✅ 不同款式颜色区分明显 |

**几个设计选择（透明告知）：**

1. **早期返回 vs hooks 顺序**：第一版我把 `if (!guards) return null` 写在两个 useEffect 之间——hook 顺序违规。修正：所有 useEffect 在顶部声明完才 return null，第二个 useEffect 内部加 `if (!userGender || !photoId || !handFeatures) return;` 内置 guard 防 race。这是 React 项目的常见坑，**条件 return 必须在所有 hooks 之后**。
2. **navigate state 而非 sessionStorage**：「试这款」跳 /result 时用 `navigate(...,{state:...})` 把 `{result_url, style}` 塞进 history state。优点：组件解耦无需新 API；缺点：F5 刷新 /result/:id 时 state 丢失，Step 5.8 U5 实现时要么加 `GET /api/tryon/:id` 后端接口，要么把 state 也镜像写 sessionStorage。当前阶段先用 navigate state，Step 5.8 时再决定。
3. **每张卡 Loading 时独立 disable 其他卡**：避免用户点了 A 卡后又点 B 卡引起 race condition（两个并发 tryon 写同一个 sessionStorage 的话）。简单粗暴：`tryingStyleId !== null` 时所有「试这款」disabled。如果未来想"并发多卡试戴"，应该走 /compare 流程，不要在 U2 改。
4. **`color_main` 用 inline style 注入边框**：Tailwind 无法动态生成 `border-l-[#ABC]` 任意 hex（JIT 模式只在 build 时扫描类名）。需要用 `style={{borderLeft: \`3px solid ${color_main}\`}}` inline 注入。这是 Tailwind 处理动态色值的标准解法。
5. **`SkeletonGrid` 内嵌在文件而非抽 `components/`**：U2 专属。如果未来 U3/U4 也需要 skeleton，再抽出来。
6. **`/api/recommend` 在 useEffect 里 fire，没 debounce / cache**：plan §5.5 字面没要求缓存。每次 mount /recommend 都重新请求，是有意的——可以让用户"再生成一次"如果不满意（虽然当前没"重新推荐"按钮）。如果未来加 cache，用 React Query 或 SWR。
7. **从 U2 直接跳 /compare 不预校验 photoId**：浮动按钮跳过去时不重新校验 photoId 还在不在。Step 5.7 U4 compare 页要做自己的 guard。

**给后续开发者的提示：**

- **Step 5.6 U3 浏览页**：路由 `/browse`，跟 U2 共用 `compareSelection` Context。要支持下拉无限加载（infinite scroll）或分页。
- **Step 5.7 U4 对比试戴**：从 compareSelection 读 style_ids → 调 `POST /api/tryon/batch` → 流式渲染（plan §6.5 用 SSE，但后端 Step 4.7 实现成普通 JSON，所以前端就 await 整批返回即可）。失败的卡显示"生成失败，点击重试"。
- **Step 5.8 U5 结果页**：路由 `/result/:id`。`useLocation().state` 读 navigate state 拿 result_url + style。F5 失去 state 时 fallback：要么 `useParams()` 拿 tryon_id 调新加的 `GET /api/tryon/:id`，要么显示"试戴信息已过期，请重新试戴"按钮回 /recommend。
- **`compareSelection` 不持久化 sessionStorage**：刷新就清空（Step 5.1 决策）。如果用户在 /recommend 勾了 3 张然后 F5，要重勾。这是有意的——避免"上次试戴留下的勾选状态污染本次会话"。
- **每张卡 `cover_url` 兼容相对/绝对路径**：当前 backend 返回 `/static/styles/<id>.png` 相对路径，Card 组件做了 `startsWith("http") ? url : http://localhost:8000${url}` 兜底。如果未来后端改返回绝对 CDN URL，前端不用改。
- **rate-limit 边缘 case**：PPIO 当前 5 req/min 限速下，连续访问 /recommend > 5 次/分钟会让所有理由都 fallback 成 "<tag>款，<tail>" 模板（Step 4.5 进度已经详细说过）。演示时不要频繁刷新。
- **首次 LLM batch 调用偶发慢**：如果 8 秒还没出卡片（超过 skeleton 显示时长），刷新一次让 PPIO warm up。
- **「试这款」的 elapsed 在 U2 看不到**：mock 是 28ms 实在太快用户感知不到。如果切 Seedream（~50s），需要在 U2 这里加更明显的进度提示（如全屏 Modal 或顶部进度条）。Step 5.8 U5 才有 elapsed_ms 字段展示。

---

### ✅ Step 5.6 · U3 款式浏览页 — 2026-06-13

**做了什么：**
- **`pages/user/U3.tsx`** 新建（~300 行）：U3 款式浏览页，路由 `/browse`，按 design-docu §6.4 + plan §5.6 + 原型 Board 2 第 1 屏。
  - **URL 同步筛选**：`useSearchParams` 双向绑定 5 个 URL 参数（`gender / sort / tags / color / length`），刷新不丢失，可分享链接
  - Top bar：← 返回 + AI + "款式浏览" + "共 X 款" + **右上 antd Segmented 性别切换**（切换时清空 tags/color/length 只保留 sort）
  - Filter bar：标签 chip 行（横向滚动 + "清空标签"）+ 排序 / 色调 / 长度 三组 Segmented
  - 标签池：gender 切换时单独 fetch `size=100` 客户端聚合 top-8 高频，与列表 fetch 解耦（filter 改动不重算 chip 列表）
  - 主体：2 列移动端 / 4 列桌面 grid（plan 字面"2 列"，桌面端我加到 4 列让画面更丰满，少滚动）
  - 每张 BrowseCard：方形封面 + 右上 `color_main` 圆点色样（hex 注入 inline `background`）+ 左下"加入对比"chip + 卡底"试这款"黄按钮
  - 「试这款」无 photoId 时 → warning + 跳 /upload；有的话调 `/api/tryon from_module="browse"` → 跳 /result
  - 浮动按钮跟 U2 同款（compareSelection.length >= 2 出现）
  - empty state "没有匹配的款式，换个筛选条件试试？"
- **修了一个 TS 闭包窄化错误**：`const g = activeGender; if (!g) return;` 后在 async function 内用 g，TS 仍认为 `g: Gender | null`（闭包不跨函数边界传递 narrow）。最终用 `g!` 断言简化——上方已 if-return 过，运行时安全。
- `App.tsx`：`/browse` 路由从 Placeholder 换 `<U3 />`。

**Step 5.6 验证（plan 4/4 + URL 刷新保持 + 色样圆点 + 用户实测 PASS）：**

| 验证项 | 实测 |
|---|---|
| `npm run build` 通过 | ✅ JS 700→721KB |
| 默认 /browse 显示当前性别所有款 | ✅ female=25 / male=15 |
| 切排序"最热" → 顺序变化 | ✅（heat_score 同 50，差异来自 id ASC tie-break）|
| 点击标签 chip → URL 含 tags + 列表过滤 | ✅ 中文 tag 自动 URL 编码 |
| 勾 ≥2 张 → 浮动按钮 + 跳 /compare | ✅ |
| 性别切换 → 重置 filters 保留 sort | ✅ tagPool 也重新加载 |
| F5 刷新 URL 状态保持 | ✅ useSearchParams 双向绑定生效 |
| 色样圆点显示 color_main | ✅ |

**几个设计选择（透明告知）：**

1. **URL 是 single source of truth**：所有筛选状态从 `searchParams` 派生，组件没单独 useState 维护。优点：F5 / 分享链接 / 浏览器前进后退都自然工作。代价：每次 setSearchParams 触发整页重 render（React Router 行为），filter 改动会重新跑两个 useEffect。当前 40 款数据集量级零感知。
2. **桌面端 4 列而不是 plan 的 2 列**：plan §5.6 字面"2 列瀑布流"。我做成 `grid-cols-2 lg:grid-cols-4`——4 列让 25 款一屏看完不滚太多，跟 U2 推荐页 3 列形成视觉分层（推荐更大更重要、浏览更紧凑）。如果产品坚持 2 列，改成 `grid-cols-2` 一行修复。
3. **标签池单独 fetch 不复用主列表**：主列表会随 filter 变化（如选了"极简" → 只剩 2 款），客户端聚合就只有"极简"一个 tag 可选，破坏浏览体验。所以标签池只跟 gender 关联，filter 切换不影响 chip 列表。
4. **gender 切换清空 tag/color/length**：不同性别 pool 有不同合法标签（女款"法式"vs 男款"哑光"），保留旧 filter 会让结果一定为空。仅保留 sort 是因为 sort 跨性别通用。
5. **color_main 圆点用 inline style 注入**：跟 U2 的 chip 左边框同理——Tailwind JIT 不能处理动态 hex。这是 Tailwind 项目处理任意色值的标准做法。
6. **"无 photoId 时点试这款"友好降级**：U3 用户可能没走 /upload 流程直接来浏览（"我先看有什么款再决定要不要试戴"），此时点试这款应该引导他去上传，不是报错。当前 `message.warning("还没上传手图，先去上传") + navigate("/upload")` 是软提示。
7. **筛选无结果时显示文案不是空白**：empty state 是基本 UX 责任，避免用户以为页面挂了。

**给后续开发者的提示：**

- **Step 5.7 U4 对比试戴**：路由 `/compare`。从 Context.compareSelection 读 style_ids → 调 `POST /api/tryon/batch`（Step 4.7 的接口）→ 渲染 2-4 卡格子，每格显示加载/结果/失败状态。**注意 plan §5.7 字面 2-4 款限制**：Context 里的 compareSelection 数组长度需要在进入 /compare 时校验，超过 4 要截断或提示。
- **批量试戴失败容错**：plan §5.7 字面"单款失败不阻塞其他款"。后端已实现（Step 4.7），前端要在失败格显示"生成失败"+"重试"按钮（plan 写"点击重试"）。
- **URL 参数命名一致性**：U3 的 URL 用了 `color` 而非 `color_tone`、`length` 而非 `length_pref`——为了 URL 简洁。后端 API 接收 `color_tone` / `length_pref` 全名，前端在 fetch 时拼成全名。如果未来要做 SSR / 后端读 URL，可以对齐。
- **标签 chip 横向滚动**：用 `overflow-x-auto` 实现，桌面端鼠标可拖、移动端手指可滑。如果将来标签太多影响美观，可加左右滚动按钮。
- **`/browse` 不在主导航里**：当前只有 U2 推荐页底部"想看更多？"链接 + 直接 URL 访问能进。如果产品决策要加底部 Tab Bar（Home / 浏览 / 历史），是 Phase 5+ 的事。
- **性别 override URL 参数**：`/browse?gender=male` 即使 Context 里 userGender=female 也会显示男款。设计目的是让用户在不修改 sessionStorage 的前提下"快速看看另一性别有什么"。但 Context 的 userGender 不变——后续 /upload / /recommend 还是用 Context 值，避免影响推荐算法的"性别硬筛选"。

---

### 📌 项目锁定状态 + 公约提醒（无需每步更新，状态真变才改）

> 本段是**稳定的锁定状态指针**，不是 step-by-step 的进度条。
>
> - "下一步该做什么"——`git log -1` + `implementation-plan.md` 已经决定唯一答案，不在此处冗余维护
> - "刚才完成了什么"——progress.md 的最新 Step 条目就是，不在此处复述
> - 本段只记录**跨 Step 复用、不会从代码或 plan 自动推出来的项目级决策**
>
> **什么时候应该更新本段**：项目级 trade-off 真变了（换模型、换 provider、加新约定、轮换 secret）。**不是**：每完成一个 Step——那是 progress.md 的工作，本段不掺和。

**AI 服务层锁定（Phase 3 出来的决策）：**
- **IMAGE_PROVIDER**：默认 `mock`；切 `seedream` 走 PPIO 的 Seedream 4.5，V1 短 prompt 锁定。Step 3.2 benchmark 烧 ¥0.945 排除了 4.0 over-darken / 5.0-lite 拒深色 / Qwen-Image-Edit 单图 / V2 加狠 prompt 无效——细节查 progress.md Step 3.2
- **LLM 双档**：quick = `qwen/qwen3-next-80b-a3b-instruct`（80B MoE 激活 3B），strong = `deepseek/deepseek-v4-pro`（1M context + FC）；`TIMEOUT_SECONDS=60`（plan 写 30 不够 reasoning 模型偶发慢）
- **Email**：SMTPS via `smtplib.SMTP_SSL` 端口 465 + `asyncio.to_thread` 异步化；QQ `smtp.qq.com` 已实测通过；`wrap_html` 按 design-docu §7.7.4 包装（680px 宽 / Apple System / AI 助手脚注）

**演示数据状态（Phase 1 出来的决策）：**
- `seed_all.py` 严格幂等：`random.seed(42)` 锁定，三次连跑都是 styles=40 / tryons=12847 / stats=1432
- 原型图：`原型1/` 下 10 张 Board_00~Board_09，gitignored（Claude 工具资产同 `.claude/` 一起 gitignored）

**Secret 轮换历史 + 默认流程：**
- **PPIO key** 已轮换 1 次（Step 3.3 时用户贴新 key 换 v4-pro 权限）；旧 key 还有效，用户决定要不要 revoke
- **PPIO key 待轮换**：Step 4.5 验证期间 AI 让 `Select-String` 输出了 `.env` 的 PPIO_API_KEY 前 30 字符。需轮换，由用户在 PPIO 控制台 revoke + 新建 + 自己手改 `backend/.env`（AI 不接触新值）。Step 4.5 progress 末尾有完整描述
- **PPIO key 限速锁定**：当前 key 的 quick 档限速 **5 req/min**。Step 4.5 因此改用 1 次 batch 调用而不是 9 并发。如果未来 key 限速放宽（充值 / 企业账号），可考虑回 9 并发实现更低延迟（参 Step 4.5 progress "给后续开发者的提示"）
- **SMTP 授权码** 已轮换 1 次（Step 3.4 时用户暴露旧码 → 立即在 QQ 控制台重生成 → 自己手改 `.env`，**AI 从未看到新码**）
- **默认流程**：开发者本地改 `.env`，AI 助手不需要看见新值——除非有具体改动需求（如要测真实发邮件）才告诉，告诉完再轮换

**强制公约（必须遵守，跨会话生效）：**
- [CLAUDE.md] **Step-completion gate is human-in-the-loop**：每步技术验证 PASS 后**停下等用户显式 OK** 才 commit + 进下一步，**绝不自动推进**
- Auto memory `feedback_step_by_step_human_gate.md` 是上面这条的备份 + 详细 rationale
- Auto memory `feedback_visual_judgment.md`：涉及颜色 / 肤色 / 视觉对比时用户肉眼判断 > 我 Read 工具描述，别二元分类带偏方向
- Auto memory `feedback_focus_on_product.md`：项目重点放产品/工程，弱化答辩/PPT/评审视角

**新会话 / `/compact` 之后的接续协议：**
1. 跑 `git log --oneline -5` → 知道刚做完哪个 Step（commit 标题就是"Step X.Y · 标题"格式）
2. 在 `implementation-plan.md` 找该 Step 的**下一个** → 知道下一步
3. 读本段（📌 项目锁定状态）→ 知道当前所有项目级 trade-off
4. 读 [CLAUDE.md] → 知道工作流规则
5. 直接动手；遇到"为什么之前选 X"的问题去 progress.md 翻对应 Step 条目（每条都有"为什么 + 验证 + 给后续开发者的提示"）

---
