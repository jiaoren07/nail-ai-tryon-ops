# 美甲 AI 试戴与智能运营 · 实施计划

> 配套文档：[design-docu.md](design-docu.md) · [tech-stack.md](tech-stack.md)
> 目标：把双端 Demo 拆成可由 AI 开发者按顺序执行的最小指令单元，每一步都自带可观测的验证手段

---

## 使用说明

- **每步必须串行执行**，禁止并行抢跑。上一步未通过验证时，不准开始下一步。
- **每步的"验证"是硬门**，未通过即返工，不允许"先放着后面再说"。
- **每步只做指令规定的事**，不顺手加未来需要的代码，不"提前优化"。
- 步骤里只描述"做什么"和"怎么验"，**不规定具体怎么写代码**。语言/库/写法由执行者按 [tech-stack.md](tech-stack.md) 自决。
- 涉及到环境变量、字段名、路径名时**必须严格一致**，因为后续步骤会引用。

---

## 全局约定

- 项目根目录：`d:\github仓库1`
- 项目主目录结构：`backend/`（FastAPI 后端）+ `frontend/`（React 前端）
- 仓库根级还有 `data-prep/`（一次性数据准备工具，已存在；与产品代码隔离，不归 backend/ 管）和 `Meijia/`（早期 Next.js 视觉原型，**不参与本计划的构建**，仅作为视觉风格参考）
- 数据集目录：`d:\美团AI HACKATHON\dataset`（已就绪）：
  - `styles/f_01_enh.png ~ f_25_enh.png` + `f_NN_orig.{png|jpg}` —— 25 张女款（赛题脱敏）
  - `styles/tags_qwen.json` —— 25 个 key 为 `f_NN_enh.png` 的 Qwen2.5-VL 打标结果
  - `styles/male/m_01.jpg ~ m_15.jpg` —— 15 张男款（用户补充）
  - `styles/male/tags_qwen.json` —— 15 个 key 为 `m_NN.jpg` 的 Qwen3-VL 打标结果
  - `hands/01.png ~ 17.png` —— 17 张示例手图，男女共用
- 数据库文件：`backend/nail_demo.db`
- 后端服务端口：`8000`
- 前端开发端口：`5173`
- API 路径前缀：用户端 `/api/...`，运营端 `/api/ops/...`
- 统一响应结构：`{ code, msg, data }`，成功时 `code=0`
- **时区约定**：
  - 后端写入数据库的时间统一是 **UTC**（SQLAlchemy 默认）。
  - 所有 SQL 中涉及"今天 / 今日 / `date('now')` / `datetime('now')`"的地方**必须显式加 `'localtime'` 修饰符**，即 `date('now','localtime')` 与 `datetime('now','localtime')`，让 SQLite 用系统时区（本地 = 北京 UTC+8）解释；否则凌晨 0–8 点之间"今日 KPI"会跨日错位。
  - APScheduler 必须显式 `timezone="Asia/Shanghai"`（详见 Step 9.2）。

---

## Phase 0 · 项目初始化（5 步）

### Step 0.1 · 建立 monorepo 目录骨架

**目标**：搭出 `backend/` 与 `frontend/` 两个子目录，以及后端内部的子结构。

**指令**：
- 在 `d:\github仓库1` 下创建 `backend/` 与 `frontend/` 两个空目录。
- 在 `backend/` 下创建子目录：`app/`、`app/routers/`、`app/services/`、`app/models/`、`scripts/`、`static/styles/`、`static/samples/`、`static/uploads/`、`static/cache/`、`tests/`。
- **不要**在 `backend/` 内再建一个 `data-prep/`——数据准备工具已经在仓库根级 `data-prep/` 下，不要复制。
- 在仓库根目录创建 `.gitignore`，至少忽略：Python 虚拟环境目录、`__pycache__`、Node 模块目录、构建产物、`.env`、SQLite 数据库文件、`static/cache/` 内容。

**验证**：
- 目录树展开后应能看到上述全部目录。
- `.gitignore` 包含至少 6 条忽略规则。

---

### Step 0.2 · 后端 Python 环境与基础依赖

**目标**：建立 Python 虚拟环境并安装 [tech-stack.md §3.4](tech-stack.md) 列出的全部依赖。

**指令**：
- 在 `backend/` 内创建独立的虚拟环境。
- 安装 [tech-stack.md §3.4](tech-stack.md) 中列出的全部 Python 依赖（FastAPI、Uvicorn、SQLAlchemy、aiosqlite、Pydantic、python-multipart、httpx、python-dotenv、Pillow、**openai**（PPIO 用 OpenAI 兼容 API）、APScheduler、markdown）。
- 在 `backend/` 内生成 `requirements.txt`，固定上述全部依赖版本。

**验证**：
- 在虚拟环境内逐个 import 上述包，全部无 `ModuleNotFoundError`。
- `requirements.txt` 行数 ≥ 12 且与已安装版本完全一致。

---

### Step 0.3 · 前端 Vite + TypeScript 工程初始化

**目标**：在 `frontend/` 内生成可启动的 React + TypeScript 工程。

**指令**：
- 在 `frontend/` 内基于 Vite 模板创建 React + TypeScript 工程。
- 安装 [tech-stack.md §2.4](tech-stack.md) 中 dependencies 与 devDependencies 列出的全部依赖（React、React Router、antd、ECharts、axios、react-compare-image 等；Vite、TypeScript、Tailwind 配套等）。
- 按 Tailwind 官方流程初始化 `tailwind.config.js` 与 `postcss.config.js`，并在全局 CSS 内引入 Tailwind 三条指令。

**验证**：
- 启动开发服务器后，浏览器打开 `http://localhost:5173` 能看到 Vite 默认欢迎页。
- 在欢迎页临时加一个使用 Tailwind 类名（如 `bg-red-500`）的元素，刷新后该元素显示为红色背景。验证完后删除该测试元素。

---

### Step 0.4 · 配置后端环境变量模板

**目标**：建立环境变量文件，作为后续模块统一配置来源。

**指令**：
- 在 `backend/` 下创建 `.env`，写入下列变量（值用占位符或真实值，缺失项暂用空字符串）：
  - `DATABASE_URL` — 指向 `backend/nail_demo.db` 的 SQLite aiosqlite URL
  - `IMAGE_PROVIDER` — 默认值 `mock`
  - `JIMENG_API_KEY` — 留空
  - `PPIO_API_KEY` 与 `PPIO_BASE_URL`（值固定为 `https://api.ppio.com/openai`）— **全部 LLM 与 VLM 共用一个供应商**
  - `LLM_QUICK_MODEL` — 短文本生成模型 ID，默认 `qwen/qwen2.5-7b-instruct`
  - `LLM_STRONG_MODEL` — 复杂推理 / Function Calling 模型 ID，默认 `deepseek/deepseek-v3.1`
  - SMTP 五项：`SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`SMTP_FROM`
  - `REPORT_RECIPIENT` — 报告收件邮箱
  - `SCHEDULER_ENABLED` — 默认 `true`
- 在 `backend/` 下创建 `.env.example`，结构与 `.env` 完全一致但所有值替换为占位符，**入库**。
- 确保 `.env` 已被仓库根的 `.gitignore` 覆盖。

**验证**：
- `.env` 与 `.env.example` 字段名一一对应、无遗漏。
- `.env` 在 `git status` 中**不出现**。

---

### Step 0.5 · 后端统一配置加载与启动健康检查

**目标**：建立一个最小可启动的 FastAPI 应用 + 配置加载。

**指令**：
- 用 `pydantic-settings` 实现一个 `Settings` 配置类，字段与 Step 0.4 的 `.env` 一一对应。
- 创建 FastAPI 应用入口 `backend/app/main.py`，在启动时加载 `Settings`。
- 注册一个 `GET /api/health` 路由，返回 `{ code: 0, msg: "ok", data: { service: "nail-demo", env: <从 settings 读取的非敏感字段，如 IMAGE_PROVIDER 与 SCHEDULER_ENABLED> } }`。
- 启用全局 CORS，允许 `http://localhost:5173`。

**验证**：
- 启动后访问 `http://localhost:8000/api/health` 返回 `code=0` 且 `data.env.IMAGE_PROVIDER` 与 `.env` 中一致。
- 浏览器访问 `http://localhost:8000/docs` 可以看到 Swagger UI 且能看到 health 接口。

---

## Phase 1 · 数据层（6 步）

### Step 1.1 · 定义 6 张表的 SQLAlchemy 模型

**目标**：把 [design-docu.md §4.2](design-docu.md) 的全部表结构落地。

**指令**：
- 在 `backend/app/models/` 下定义 6 张表的 SQLAlchemy 模型：`styles`、`tryons`、`style_stats`、`ops_actions`、`reports`、`notifications`。
- 字段名、类型、默认值必须与 [design-docu.md §4.2](design-docu.md) 完全一致。
- 设置 [§4.3](design-docu.md) 列出的全部索引（爆款查询、试戴历史、当日排行榜、报告倒序、未读通知）。
- 提供一个最小的 `init_db()` 函数：连接 SQLite、按当前模型创建所有表（已存在则跳过）。

**验证**：
- 执行 `init_db()` 一次，`backend/nail_demo.db` 文件被创建。
- 使用 `sqlite3` CLI 或脚本查询 `sqlite_master`，能看到全部 6 张表且字段数与设计文档一致。
- 查询 `sqlite_master` 的索引，能看到设计文档列出的 5 个索引名（或等价命名）。

---

### Step 1.2 · 导入款式库的 seed 脚本

**目标**：把 25 女 + 15 男 = **40 张款式** + 17 张示例手图全部入库 / 挂到后端静态目录。

**指令**：
- 创建脚本 `backend/scripts/seed_styles.py`。
- **女款（25 条）**：读 `d:\美团AI HACKATHON\dataset\styles\tags_qwen.json`，key 形如 `f_NN_enh.png`：
  - `id` 直接取去掉 `_enh.png` 的部分，即 `f_01` ~ `f_25`。
  - `cover_url` = `/static/styles/{id}_enh.png`，即 `/static/styles/f_01_enh.png`。
  - 复制 `dataset/styles/f_NN_enh.png` 到 `backend/static/styles/`。
- **男款（15 条）**：读 `d:\美团AI HACKATHON\dataset\styles\male\tags_qwen.json`，key 形如 `m_NN.jpg`：
  - `id` 取去掉 `.jpg` 的部分，即 `m_01` ~ `m_15`。
  - `cover_url` = `/static/styles/{id}.jpg`，即 `/static/styles/m_01.jpg`。
  - 复制 `dataset/styles/male/m_NN.jpg` 到 `backend/static/styles/`。
- **公共字段映射**（每个款式都做）：
  - `name` 由打标的 `style_tags` 拼接生成（如"奶茶杏色极简"或"哑光纯色商务"），允许后续人工覆盖。
  - `gender`、`style_tags`（存 JSON 数组）、`color_main`、`color_tone`、`length_pref`、`complexity` 字段从打标 JSON 直接映射；男款 `gender` 取值 `male` 或 `both`，女款取 `female`。
  - `heat_score` 全部初始化为 `50.0`（后续 seed 行为时再调整）。
  - `is_active=1`，`display_order` 全表按 id 字典序升序填 0–39（女在前、男在后）。
  - `created_at` 取脚本运行时刻。
- **同时复制 17 张示例手图**：把 `d:\美团AI HACKATHON\dataset\hands\01.png` ~ `17.png` 复制到 `backend/static/samples/`（不入数据库，仅作为前端示例图源；男女共用）。
- 脚本可重复执行：清空 `styles` 表再写入，覆盖复制的静态图。

**验证**：
- `SELECT COUNT(*) FROM styles` 返回 **40**。
- `SELECT COUNT(*) FROM styles WHERE gender='female'` 返回 25；`gender='male'` 返回 15（或 male+both 合计 15）。
- `SELECT id FROM styles ORDER BY id` 头几条是 `f_01, f_02, ...`，最后几条是 `m_13, m_14, m_15`。
- `backend/static/styles/` 下存在 25 个 `f_*_enh.png` + 15 个 `m_*.jpg`，合计 40 个文件。
- `backend/static/samples/` 下存在 17 个 `.png` 文件。
- 后端运行时访问 `http://localhost:8000/static/styles/f_01_enh.png`、`http://localhost:8000/static/styles/m_01.jpg`、`http://localhost:8000/static/samples/01.png` 都能下载（先在 Step 2.4 完成静态文件挂载之后再做这条验证）。

---

### Step 1.3 · 人工指定款式角色（爆款/冷门/热门候选）

**目标**：基于 40 款（25 女 + 15 男）的标签，分两个 pool 人工选定演示用的角色分配，写入一个角色配置文件。

**指令**：
- 在 `backend/scripts/` 下创建 `style_roles.json`，结构示例：
  - 顶层是一个对象，分两个 pool：`female` 与 `male`，每个 pool 下有 4 键 `stable_hot`、`emerging_hot`、`cold`、`long_tail`。
  - 每个键对应一个 `style_id` 数组。
  - **女款 25 总数**：`stable_hot=3`、`emerging_hot=2`、`cold=3`、`long_tail=17`。
  - **男款 15 总数**：`stable_hot=2`、`emerging_hot=1`、`cold=2`、`long_tail=10`。
- 选定原则：
  - `emerging_hot` 选视觉辨识度最高、风格鲜明的款（演示时容易让评审记住）。
  - `cold` 选风格相对小众或与主流偏好相反的款。
  - `stable_hot` 选标签里包含"经典""极简""通勤""哑光""纯色"等通用关键字的款。
  - 其余落入 `long_tail`。
- 角色分配的依据写在一份简短的 `style_roles_README.md`（同目录），每个款式一行解释为什么放进这个角色。

**验证**：
- `style_roles.json` 两个 pool 数组的合并集合，女款恰为 `f_01`..`f_25`、男款恰为 `m_01`..`m_15`，无重复无遗漏。
- `style_roles_README.md` 有 40 行解释，每行格式 `f_XX|m_XX: <角色> — <一句话理由>`。

---

### Step 1.4 · 生成 60 天历史试戴行为

**目标**：基于角色分配生成 60 天 `tryons` 表记录。

**指令**：
- 创建脚本 `backend/scripts/seed_tryons.py`。读 `style_roles.json` 的两个 pool。
- 行为规则（每天独立生成，**覆盖范围 `[今天−59, 今天]` 共 60 天（含今天）**，时间倒推；规则对两个 pool **共用**）：
  - `stable_hot` 款：每日试戴 80–150 次，正态分布。
  - `emerging_hot` 款：前 55 天每日 10–30 次，最后 5 天按指数增长（倍率 1.5×、2×、2.5×、3×、3.5×）。
  - `cold` 款：60 天合计试戴次数 ≤ 20，均匀分布。
  - `long_tail` 款：每日 5–40 次，长尾分布。
- **`user_gender` 与款式 `gender` 必须一致**：试戴男款的记录 `user_gender='male'`，试戴女款 `user_gender='female'`，试戴 both 款的 50/50 随机（不要 70/30 全局抽样，否则男款的试戴量看起来全是女性，矛盾）。
- `user_id` 用随机 UUID；`skin_tone`、`hand_shape` 各从 5/3 个枚举中随机抽取；`from_module` 按 50%/30%/20% 概率取 `recommend`/`browse`/`compare`；`is_collected` 按各角色不同概率：stable_hot 25%、emerging_hot 30%、cold 5%、long_tail 12%。
- `created_at` 必须落在该自然日内（小时随机分布在 8:00–23:00）。
- 脚本可重复执行：清空 `tryons` 后重写。

**验证**：
- `SELECT COUNT(*) FROM tryons` 总数应在 [4000, 18000] 区间内（具体取决于随机种子，但不应离谱）。
- `SELECT MIN(created_at), MAX(created_at) FROM tryons` 最早日期 = 今天减 59 天，最新日期 = 今天。
- 对 `emerging_hot` 中任一款，按日分组统计试戴量，最后 5 天应明显高于前 55 天均值（至少 5× 关系）。
- 对 `cold` 中任一款，`SELECT COUNT(*)` 应 ≤ 20。
- 任一男款（如 `m_05`）的所有试戴记录 `user_gender='male'`（除非该款是 `gender='both'`）；任一女款（如 `f_01`）的所有试戴记录 `user_gender='female'`。

---

### Step 1.5 · 生成 style_stats 聚合数据

**目标**：把 `tryons` 表按 `(style_id, stat_date)` 聚合写入 `style_stats`，并补 `exposure_count`、`click_count` 字段。

**指令**：
- 创建脚本 `backend/scripts/seed_stats.py`。
- 按 `style_id + DATE(created_at)` 聚合 `tryons` 表，得到 `tryon_count` 与 `collect_count`（基于 `is_collected=1` 的子集）。
- `exposure_count` 用合理倍数模拟：约等于 `tryon_count × random(8, 20)`。
- `click_count` 约等于 `exposure_count × random(0.05, 0.25)` 且不小于 `tryon_count`。
- 每行写入 `style_stats`，同一 `(style_id, stat_date)` 已存在时覆盖。
- 脚本可重复执行。

**验证**：
- `SELECT COUNT(*) FROM style_stats` 大致等于 `25 × 实际有数据的天数`，应在 [1000, 1500] 区间。
- 任取 5 条记录，验证 `click_count >= tryon_count` 且 `exposure_count >= click_count`。
- `SELECT SUM(tryon_count) FROM style_stats` 必须等于 `SELECT COUNT(*) FROM tryons`。

---

### Step 1.6 · 统一 seed 入口

**目标**：用一条命令完成全部 seed（建表 + 40 款 + 60 天行为 + 聚合）。

**指令**：
- 创建脚本 `backend/scripts/seed_all.py`。
- 顺序调用：`init_db()` → `seed_styles` → `seed_tryons` → `seed_stats`。
- 每步打印开始/结束时间与受影响行数。
- 全脚本必须在 60 秒内完成。

**验证**：
- 删除 `nail_demo.db` 后运行 `seed_all.py`，结束打印形如 `styles=25 tryons=XXXX stats=YYYY`，且实际数据库内数据条数与打印一致。
- 第二次连续运行 `seed_all.py`，结果数据条数应与第一次完全相同（幂等）。

---

## Phase 2 · 后端基础设施（4 步）

### Step 2.1 · 数据库依赖注入

**目标**：建立 FastAPI 路由可用的异步 SQLAlchemy session 依赖。

**指令**：
- 在 `backend/app/db.py` 定义异步 `engine`、`async_session_maker`、`get_db` 依赖（异步生成器，yield session 后自动关闭）。
- 在 `main.py` 启动事件中调用 `init_db()` 确保表存在。

**验证**：
- 临时新增一个 `GET /api/_debug/count_styles` 路由（用 `get_db` 依赖）返回 `SELECT COUNT(*) FROM styles`。
- 访问该路由返回 `25`。
- 验证完成后删除该调试路由。

---

### Step 2.2 · 统一响应包装与异常处理

**目标**：所有成功响应自动包成 `{code, msg, data}`，所有异常自动转标准错误结构。

**指令**：
- 定义统一的成功响应辅助函数与错误响应模型（`code` 非 0 表示错误，`msg` 为提示，`data=null`）。
- 注册一个全局异常处理器：捕获 `HTTPException` 返回 `{code: status_code, msg: detail, data: null}`；捕获其他未处理异常返回 `{code: 500, msg: "internal_error", data: null}` 并打 ERROR 日志。
- 改造 `/api/health` 让其响应符合统一结构（之前已经是了，再确认）。

**验证**：
- `/api/health` 仍然返回 `code=0`。
- 临时新增一个 `/api/_debug/raise` 路由抛 `HTTPException(404, "not found")`，请求应返回 `{code: 404, msg: "not found", data: null}` 且 HTTP 状态码为 404。
- 临时新增一个 `/api/_debug/boom` 路由抛 `ZeroDivisionError`，请求应返回 `{code: 500, msg: "internal_error", data: null}`。
- 两个调试路由验证完成后删除。

---

### Step 2.3 · 路由分组骨架

**目标**：建立 `user_router`、`ops_router` 两个 APIRouter 并挂到主应用。

**指令**：
- 在 `backend/app/routers/user.py` 与 `backend/app/routers/ops.py` 分别创建空的 `APIRouter`，前者前缀 `/api`，后者前缀 `/api/ops`。
- 在 `main.py` 注册这两个路由。
- 暂时各放一个 `GET /ping` 返回 `{code:0, msg:"ok", data:{router:"user"|"ops"}}`。
- **强约定（防止后续 Phase 4 误拆文件）**：
  - `routers/user.py` **统一收纳所有 C 端（消费者端）路由**，不论 URL 二级路径是什么。包括但不限于 `/api/user/upload`、`/api/styles`、`/api/recommend`、`/api/tryon`、`/api/tryon/batch`、`/api/events/collect`、`/api/tryon/:id`。每个新接口都直接在 user.py 中加 `@router.<method>("<二级路径>")`，**禁止**新建 `styles.py` / `recommend.py` / `tryon.py` / `events.py` 等独立文件。
  - `routers/ops.py` 同理，统一收纳所有 B 端（运营端）路由，前缀 `/api/ops`。包括 overview / trending / cold / actions / styles / chat / reports / notifications 等等。**禁止**为各业务对象拆独立文件。
  - 文件名 `user.py` 是"C 端"的代称，不是"只放 `/api/user/*` 的接口"。后续读到 Phase 4 / Phase 6 任何"实现 `POST /api/xxx`"指令时，无需思考归属：C 端 → user.py，B 端 → ops.py。

**验证**：
- `/api/ping` 返回 `data.router == "user"`。
- `/api/ops/ping` 返回 `data.router == "ops"`。
- 两个 ping 验证后删除（或保留也行，开发期无害）。

---

### Step 2.4 · 静态文件服务

**目标**：让 `backend/static/` 在 `/static/` 路径下可直接访问。

**指令**：
- 在 FastAPI 主应用挂载 `backend/static/` 为 `/static/` 路径。

**验证**：
- 访问 `http://localhost:8000/static/styles/01_enh.png` 能直接看到款式图。
- 在 25 个款式中随机抽 5 个序号都能拿到图。

---

## Phase 3 · AI 服务层（4 步）

### Step 3.1 · ImageGenProvider 抽象 + MockProvider

**目标**：建立可切换的图像生成服务抽象层，默认走 Mock。

**指令**：
- 在 `backend/app/services/image_gen.py` 定义抽象基类，规定异步方法签名：输入「手图 bytes、款式 id、可选的提示词参数」，输出「生成结果图的相对 URL 字符串」。
- 实现 `MockProvider`：直接复制款式封面 `static/styles/{id}_enh.png` 到 `static/cache/{user_id}_{style_id}.png`（演示阶段把"原款式图"当成"试戴结果图"作为兜底），返回该 cache 路径。
- 实现工厂函数 `get_image_provider()`，根据 `IMAGE_PROVIDER` 环境变量返回对应实现。

**验证**：
- 写一次性测试脚本：传一张任意 PNG 字节 + `style_id=f_01`，调用 MockProvider，返回的字符串以 `/static/cache/` 开头。
- 在 `backend/static/cache/` 下能看到对应文件。
- 删除该测试脚本。

---

### Step 3.2 · 即梦 AI Provider 接入（可选 P1）

**目标**：实现真实的 `JimengProvider`，作为 MockProvider 之外的可选实现。

**指令**：
- 实现 `JimengProvider` 类，按即梦 AI 官方 API 文档（火山方舟）调用图生图接口。
- 输入用户手图 + 款式参考图（从 `static/styles/{id}_enh.png` 读取作为 reference）+ 固定 prompt（参考 [design-docu.md §8.3](design-docu.md)）。
- 返回结果保存到 `backend/static/cache/jimeng_{uuid}.png`。
- 超时设置 60 秒，超时或异常抛 `ImageGenError`（自定义异常）。
- 通过 `.env` 中的 `JIMENG_API_KEY` 鉴权；key 为空时直接抛配置错误。

**验证**：
- 在 `.env` 临时设 `IMAGE_PROVIDER=jimeng` 且填入有效 key，写一次性测试：传任一示例手图 + `style_id=f_01`，应在 60 秒内返回 URL 且文件存在。
- 测试完成后把 `IMAGE_PROVIDER` 改回 `mock`。
- 如果 key 暂未拿到，本步可跳过，但需要在 `image_gen.py` 中**保留 `JimengProvider` 占位类**抛"未实现"错误。

---

### Step 3.3 · LLM 服务封装（PPIO 一家全包）

**目标**：建立统一的 LLM 调用模块，通过 PPIO 的 OpenAI 兼容接口同时支撑短文本与复杂推理两档。

**指令**：
- 在 `backend/app/services/llm.py` 用 `openai.AsyncOpenAI` 创建客户端，`api_key=settings.PPIO_API_KEY`、`base_url=settings.PPIO_BASE_URL`。
- 提供异步函数：
  - `gen_text(prompt: str, model: "quick" | "strong", max_tokens: int) -> str` — 通用文本生成。`model="quick"` 映射到 `settings.LLM_QUICK_MODEL`，`"strong"` 映射到 `settings.LLM_STRONG_MODEL`。
  - `gen_text_with_tools(messages, tools, model="strong") -> tool_calls_or_text` — 支持 Function Calling 的对话调用，默认走 strong。
- `PPIO_API_KEY` 为空时调用即抛配置错误（`ConfigError("PPIO_API_KEY missing")`），**不要静默 fallback**。
- 超时 30 秒；429 限流时指数退避重试最多 3 次（与 [data-prep/auto_tag_styles.py](data-prep/auto_tag_styles.py) 的重试策略保持一致）。

**验证**：
- 写一次性测试脚本调用 `gen_text("请用一句话介绍美甲", "quick", 80)`，应在 10 秒内返回非空字符串。
- 再调一次 `gen_text_with_tools` 用一个简单工具（如 `get_weather(city)`），返回应含 `tool_calls`。
- 删除该测试脚本。
- 如果 PPIO_API_KEY 尚未拿到（不太可能，本仓库 `.env` 已就绪），本步只完成代码骨架与错误抛出，验证延后到 key 到位后补做。

---

### Step 3.4 · 邮件发送服务

**目标**：用 smtplib 实现 HTML + 纯文本两段式邮件发送。

**指令**：
- 在 `backend/app/services/email.py` 提供异步函数 `send_email(to, subject, html_body, text_body)`。
- 使用 SMTPS（465 端口）登录 `.env` 的 SMTP 账户。
- HTML 正文用 [design-docu.md §7.7.4 wrap_html](design-docu.md) 描述的 inline-CSS 包装规则（680px 宽、Apple System 字体、底部带"AI 助手自动生成"说明）。
- 失败时抛 `EmailSendError`，**不要**在内部静默吞掉异常。

**验证**：
- 在 `.env` 内填好真实 SMTP 配置（QQ/163 授权码），写一次性测试发送 `subject="冒烟测试"、html_body="<h2>Hello</h2>"、text_body="Hello"`。
- 收件邮箱在 30 秒内收到该邮件，HTML 渲染正常（标题居中或加粗均可）。
- 删除该测试脚本。
- 如果 SMTP 配置未就绪，跳过验证，但代码骨架需完成。

---

## Phase 4 · 用户端接口（7 步）

### Step 4.1 · user_id / gender 的前端约定（**不实现任何后端接口**）

**目标**：明确"匿名身份"与"性别字段"的产生路径与传递协议，无需任何后端接口。

**约定**：
- **`user_id` 由前端本地生成**：用户首次进入 `/upload` 时，若 `sessionStorage.userId` 不存在则生成一个 UUID v4 并写入；后续所有 API 请求必须在 HTTP header `X-User-Id` 携带该值。
- **`gender` 由前端本地存储**：用户在 `/gender` 页选择后写入 `sessionStorage.userGender`（取值 `female`/`male`），后续涉及推荐/试戴的请求显式带在 body 里。
- **后端只在收到请求时校验 header `X-User-Id` 必须为合法 UUID 字符串**（不存在或非法直接返回 `code=4xx`，`msg="invalid_user_id"`），不维护任何 session 表。
- 把这一约定写入 `backend/app/routers/user.py` 模块顶部作为一段注释（或独立 `docs/AUTH.md` 文件），以便后续接口实现者直接引用。

**验证**：
- 在 `backend/app/main.py` 加一个全局中间件：所有 `/api/...` 路径（除 `/api/health`、`/docs`）必须带 `X-User-Id` 且为合法 UUID，否则拒绝。
- 临时写一次性脚本：用 `curl` 调用 `/api/health`（不带 header）→ 200；调用某个保护接口（如新增的 `GET /api/_debug/whoami` 返回 `data.user_id`）不带 header → `code=4xx`，带合法 UUID → 返回该 UUID。
- 验证完删除 `_debug/whoami` 路由。

---

### Step 4.2 · 上传接口 + 手部 Mock 分析

**目标**：让前端能上传一张手图，服务端返回 mock 手部特征。

**指令**：
- 实现 `POST /api/user/upload`，接收 multipart 文件（字段名 `file`）+ 表单字段 `user_id`。
- 服务端把文件保存到 `backend/static/uploads/{user_id}_{时间戳}.{扩展名}`，仅允许 png/jpg/jpeg、大小 ≤ 10MB。
- 调用 mock 手部分析函数：用 PIL 读图，取中央 100×100 像素的平均 RGB，按下列规则映射 `skin_tone`：
  - R 平均值 > 200 → `light_warm` 或 `light_cool`（依 R-B 差值决定 warm/cool）
  - 150–200 → `medium`
  - < 150 → `dark_warm` 或 `dark_cool`
- `hand_shape` 直接返回固定值 `average`（演示无感）。
- 响应 `data` 含 `photo_id`（保存路径的 basename）、`hand_features: {skin_tone, hand_shape}`。

**验证**：
- 上传任意示例手图（`dataset/hands/01.png`），返回 `code=0`，`data.photo_id` 非空，`data.hand_features.skin_tone` ∈ 5 个枚举之一。
- 上传 12MB 的文件 → 返回 `code=4xx`，`msg` 指明超过大小限制。
- 上传 `.txt` 文件 → 返回 `code=4xx`，`msg` 指明格式不支持。
- `backend/static/uploads/` 下能看到成功上传的文件。

---

### Step 4.3 · 款式列表接口

**目标**：实现带筛选与排序的款式列表。

**指令**：
- 实现 `GET /api/styles`，查询参数：`gender`（可空）、`tags`（逗号分隔多个）、`color_tone`（可空）、`length_pref`（可空）、`sort`（`smart`/`hot`/`new`，默认 `smart`）、`page`（默认 1）、`size`（默认 24，最大 100）。
- 仅返回 `is_active=1` 的款式。
- `gender` 不传时返回全部；传 `female` 时返回 `gender ∈ {"female","both"}`；传 `male` 时返回 `gender ∈ {"male","both"}`。
- `tags` 命中策略：款式的 `style_tags` 数组与查询 tags 有交集。
- `sort=hot` 按 `heat_score` 倒序；`sort=new` 按 `created_at` 倒序；`sort=smart` 按 `display_order` 升序。
- 响应 `data` 含 `total`、`page`、`size`、`items[]`，`items` 每条至少 `{id, name, cover_url, gender, style_tags, color_main, length_pref}`。

**验证**：
- 不带任何参数 → `total=25`。
- `?gender=female` → `total` ≤ 25 且每条 `gender` ∈ `{female, both}`。
- `?tags=极简` → 每条 `style_tags` 至少包含"极简"。
- `?sort=new&size=5` → 返回 5 条，且 `items` 顺序与按 `created_at desc` 一致。

---

### Step 4.4 · 推荐算法核心模块

**目标**：实现 [design-docu.md §6.3](design-docu.md) 的多维打分推荐。

**指令**：
- 在 `backend/app/services/recommend.py` 实现函数：输入 `gender`、`hand_features`、候选款式列表，输出按综合分倒序的列表（含分数）。
- 评分公式严格按设计文档 4 维：肤色适配 35% + 手型适配 30% + 热度 20% + 多样性 15%（多样性在排序后做 rerank 实现）。
- 肤色适配：定义一个 `(skin_tone, color_tone) → score [0,1]` 的查表函数，深肤适配冷调/裸色得高分、浅肤适配暖色得高分，等等。
- 手型适配：`(hand_shape, length_pref) → score`，短手适配 short/medium 得高分等。
- 热度：取该款式过去 7 天的 `tryon_count` 总和归一化到 [0,1]。
- 多样性 rerank：保证前 9 款的 `style_tags` 至少覆盖 3 种不同的首要标签。
- 提供单测脚本：构造 5 个假用户特征（含男女各若干）× 候选 40 款 → 验证排序结果合理。

**验证**：
- 用 `(skin_tone=light_warm, hand_shape=average)` 调用，返回 9 款；列表中至少 3 个不同的首要 `style_tags`。
- 用 `(skin_tone=dark_cool, ...)`，列表前 3 款的 `color_tone` 偏冷的比例显著高于偏暖。
- 单测脚本运行无错。
- 单测脚本保留在 `backend/tests/` 下以便后续回归。

---

### Step 4.5 · 推荐接口（含 LLM 推荐理由）

**目标**：把推荐算法暴露成 HTTP 接口，并为每款配 LLM 生成的一句话理由。

**指令**：
- 实现 `POST /api/recommend`，请求体含 `user_id`、`gender`、`hand_features`。
- 内部调用 Step 4.4 的推荐函数得到前 9 款。
- 并发调用 `llm.gen_text(..., model="quick")` 为每款生成 ≤25 字的推荐理由，prompt 模板参考 [design-docu.md §6.3](design-docu.md)（女性话术 vs 男性话术）。
- 响应 `data` 含 `user_summary`（一句话总结用户特征）、`recommendations[]`（含 `style_id, name, cover_url, score, reason`）。
- 若 LLM 调用失败，回退到模板理由如"显白显气色"/"商务百搭"。

**验证**：
- 调用一次，`recommendations.length == 9`，每条 `reason` 长度 ≤ 25 字符。
- PPIO_API_KEY 为空时仍能返回 9 条结果，每条 `reason` 是模板理由之一（回退路径）。
- 整个接口响应时间 < 6 秒（在 LLM 正常情况下）。

---

### Step 4.6 · 单款试戴接口 + 数据同步触发

**目标**：单款试戴生成 + 同步写入 `tryons` 与 `style_stats`。

**指令**：
- 实现 `POST /api/tryon`，请求体含 `user_id`、`style_id`、`photo_id`、可选 `user_gender`/`skin_tone`/`hand_shape`/`from_module`。
- 流程：
  1. 校验 `style_id` 存在；
  2. 读取上传的手图字节；
  3. 调用 `image_gen.get_provider().generate(...)` 得到结果 URL；
  4. 在同一个数据库事务内：向 `tryons` 插入一行；对 `style_stats` 用 UPSERT 把当日 `tryon_count` +1（参考 [design-docu.md §10.3](design-docu.md)）。
- 响应 `data` 含 `tryon_id`、`result_url`、`elapsed_ms`。

**验证**：
- 上传手图 + 调用试戴 → 返回 `result_url`，访问该 URL 能下载到图。
- 试戴前后比较：`SELECT tryon_count FROM style_stats WHERE style_id=? AND stat_date=date('now','localtime')` 数字 +1。
- 试戴前后 `SELECT COUNT(*) FROM tryons WHERE style_id=?` +1。

---

### Step 4.7 · 多款对比试戴接口

**目标**：并发生成 2–4 款试戴结果。

**指令**：
- 实现 `POST /api/tryon/batch`，请求体含 `user_id`、`photo_id`、`style_ids[]`（2–4 个）。
- 用 `asyncio.gather` 并发调用 Step 4.6 的内部逻辑（不通过 HTTP 转发，直接调函数）。
- 单款失败不阻塞其他款：失败项在返回数组中标 `status="failed"` + `error` 字段。
- 响应 `data` 含 `items[]`，每项 `{style_id, status, result_url, elapsed_ms, error?}`。

**验证**：
- 传 3 个有效 `style_ids` → 全部 `status="ok"`，3 个 `result_url` 各自不同。
- 传 2 个有效 + 1 个不存在的 → 2 个 `ok` + 1 个 `failed`。
- 传 5 个 ids → 返回 `code=4xx`，`msg` 指明数量超过上限。
- 调用一次后 `tryons` 表新增 ≥2 行（只 `ok` 的写入）。

---

## Phase 5 · 用户端前端（6 步）

### Step 5.1 · 路由骨架 + 全局 Context

**目标**：搭出路由表，建立 React Context 管理用户全局状态。

**指令**：
- 按 [design-docu.md §11.2](design-docu.md) 的路径表配置 React Router 路由（U0–U6 与 O1–O7 路径全部声明，页面用占位组件先填空）。
- 创建一个 `UserContext`：管理 `userId`、`userGender`、`handFeatures`、`compareSelection`、`photoId` 五个字段。
- **`userId` 与 `userGender` 持久化到 `sessionStorage`**：进入应用时若 `userId` 不存在则生成 UUID v4 写入，刷新页面不丢失。
- 提供一个 axios 实例：自动给所有请求带 `X-User-Id` header；统一拦截响应、`code != 0` 时弹 antd `message.error`。

**验证**：
- 浏览器手动访问每个声明的路径（共约 13 个），都能渲染出占位页面（不报 404）。
- 首次访问 `/upload` 后 sessionStorage 中 `userId` 自动出现且为合法 UUID。
- 在 `/gender` 占位页里临时调一次 `setUserGender("male")` → 刷新页面后从 `sessionStorage` 仍能读到 `male`。
- 用 axios 调用一个故意不存在的接口，能在右上角看到 antd 错误提示。
- 浏览器 DevTools 看任意 API 请求的 header 必带 `X-User-Id` 字段。

---

### Step 5.2 · U0 手图入口页

**目标**：完成 [design-docu.md §6.1](design-docu.md) 描述的入口页。

**指令**：
- 路由 `/upload`；`/` 默认重定向至此页。
- 页面布局：顶部 Banner（"AI 帮你看，哪款美甲适合你的手"），中部上传区域（antd `<Upload.Dragger />`），下方 3–4 张示例图缩略图。
- 示例图：前端通过后端 URL 访问 `http://localhost:8000/static/samples/01.png` ~ `04.png`，这 4 张在 Step 1.2 已由 seed 脚本复制到 `backend/static/samples/`，**男女用户共用同一组示例**。
- 上传组件：限制 jpg/png ≤10MB，前端调用 `browser-image-compression` 压到 ≤5MB 再传。
- 上传成功后调用 `POST /api/user/upload`，把 `photoId` 与 `handFeatures` 写入 Context，跳转 `/gender`。
- 点击示例图也走同一流程（先 fetch 该示例图为 blob，再走上传接口）。
- 异常文案严格按 [design-docu.md §4.2.5](design-docu.md)（格式不支持、文件超大、网络异常）。

**验证**：
- 首次访问 `/`，被重定向到 `/upload`。
- 拖拽一张本地手图上传 → 显示 loading → 跳转到 `/gender`，Context 中 `photoId` 与 `handFeatures.skin_tone` 已填。
- 点击任一示例图 → 同样进入 `/gender`。
- 拖拽一个 `.txt` 文件 → 显示错误文案"格式不支持"，**不**跳转。

---

### Step 5.3 · U1 性别选择页

**目标**：完成 [design-docu.md §6.2](design-docu.md)。

**指令**：
- 路由 `/gender`。
- **前置守卫**：进入页面时检查 Context 中 `photoId` 是否存在，不存在则重定向回 `/upload`。
- 页面布局：顶部标题"再告诉我们一些信息"，下方两张并排卡片（左"女性"右"男性"），底部小字说明、右上角"跳过"按钮。
- 两张卡片用 Tailwind 实现 hover 放大动效；卡片内放代表性款式图（女性卡用 `f_01_enh.png`，男性卡用一张男款代表图，等 Step 1.2 男款 seed 后用 `m_01.png`）。
- 点击卡片：把 `gender` 写入 Context + `sessionStorage`，跳转 `/recommend`。
- 点击"跳过"：等同点击"女性"。

**验证**：
- 未先经过上传时直接访问 `/gender`，应被重定向回 `/upload`。
- 完成上传后跳到 `/gender`，看到两张卡片并排显示，hover 时有放大效果。
- 点击"女性"后 URL 变为 `/recommend`，sessionStorage 中 `userGender=female`。
- 重置 sessionStorage 的 `userGender` 字段后刷新 `/recommend`，应被重定向回 `/gender`（即未选性别时无法进入推荐）。

---

### Step 5.4 · U2 智能推荐页

**目标**：完成 [design-docu.md §4.3](design-docu.md)。

**指令**：
- 顶部用户特征卡（显示"你是{gender}，肤色偏{cool/warm/neutral}…"）。
- 主体 3 列瀑布流的推荐卡片（数据从 `POST /api/recommend` 拉）。
- 每张卡片：款式封面、款式名、推荐理由、「试这款」按钮、「加入对比」复选框。
- 右下角浮动按钮：勾选 ≥2 时显示「对比试戴 (n)」，点击跳转 `/compare`。
- 底部「想看更多？浏览全部款式」跳转 `/browse`。

**验证**：
- 浏览器打开 `/recommend`，3–6 秒内显示 9 张推荐卡片，每张有 ≤25 字理由。
- 勾选 3 张 → 右下角浮动按钮显示「对比试戴 (3)」。
- 点击浮动按钮 → URL 变为 `/compare`，Context 中 `compareSelection` 含 3 个 id。
- 点击「试这款」 → 进入单款试戴流程并跳转到结果页（结果页可暂用占位）。

---

### Step 5.5 · U3 款式浏览页

**目标**：完成 [design-docu.md §4.4](design-docu.md)。

**指令**：
- 顶部横向滚动标签（取当前性别 pool 内的款式标签去重，前 8 个高频）。
- 颜色 / 风格 / 长度三组筛选器，排序选项「智能/最热/最新」。
- 主体 2 列瀑布流卡片，每张含「加入对比」复选框。
- 性别切换小按钮放右上角。
- 数据从 `GET /api/styles?...` 拉，分页支持下拉加载。

**验证**：
- 打开 `/browse`，默认显示该性别下全部款式。
- 切换排序「最热」→ 列表顺序明显变化（与「智能」不同）。
- 点击任一标签 → URL 中带上 `tags=xxx`，列表刷新只显示含该标签的款式。
- 勾选 ≥2 张 → 右下角浮动按钮出现，跳 `/compare` 正常。

---

### Step 5.6 · U4 多款对比试戴页

**目标**：完成 [design-docu.md §4.5](design-docu.md)。

**指令**：
- 顶部已选区：展示 2–4 张缩略图，支持移除（移除后剩 1 张则禁用「开始」按钮）。
- 「开始对比试戴」按钮：点击调用 `POST /api/tryon/batch`。
- 结果展示区按数量自适应：2 款左右、3 款 1+2 或并排 3 列、4 款 2×2。
- 渐进展示：先用骨架屏占位，每款回包后即时填入对应格子。
- 单款失败时该格显示「生成失败，重试」按钮，点击重试单款。

**验证**：
- 选 3 款 → 点开始 → 看到 3 个骨架 → 5–15 秒内全部填充 3 张图。
- 选 4 款 → 渲染 2×2 网格。
- Mock provider 模式下生成应几乎瞬间完成。

---

### Step 5.7 · U5 结果展示页

**目标**：完成 [design-docu.md §4.6](design-docu.md)。

**指令**：
- 路由 `/result/:tryon_id`，从 URL 读取试戴 id，请求一个新增的 `GET /api/tryon/:id` 接口（顺便补做该后端接口：返回 `result_url`、`style` 信息、原图 URL）。补做的接口写在 `routers/user.py`（按 Step 2.3 单文件约定）。
- 主图区用 `react-compare-image` 实现原图与试戴图左右滑动对比。
- 操作栏：保存（canvas toBlob 下载）、分享（复制当前 URL）、收藏（调用 `POST /api/events/collect`）、换一款再试（回 `/recommend`）、找店预约（占位）。
- **`POST /api/events/collect` 后端实现关键**：
  - 请求体 `{tryon_id: int}`。
  - 在同一事务内做两件事：
    1. `UPDATE tryons SET is_collected=1 WHERE id=:tid AND is_collected=0` —— 用条件防止重复触发；
    2. 若上一步 affected_rows > 0（说明此前未收藏），则 UPSERT `style_stats`：找到该 tryon 对应的 `style_id` 与 `DATE(created_at, 'localtime')`，把当日 `collect_count` 加 1。
  - 如果 tryon 不存在 → 返回 `code=404, msg="tryon_not_found"`；如果已经是 collected=1 → 返回 `code=0` 但 `data.changed=false`（前端 UI 可以原样置灰）。

**验证**：
- 完成单款试戴后跳到 `/result/:id`，能看到主图与对比滑块。
- 点击「收藏」 → 按钮变灰且文案改为「已收藏」；后端 `SELECT is_collected FROM tryons WHERE id=?` 为 1。
- **同时** `SELECT collect_count FROM style_stats WHERE style_id=? AND stat_date=date('now','localtime')` 数字相比收藏前 +1。
- 再点一次「收藏」（同一 tryon_id）→ `collect_count` 不再增加（幂等）。
- 点击「分享」 → 系统剪贴板里有当前 URL（手动粘贴验证）。

---

## Phase 6 · 运营端接口（5 步）

### Step 6.1 · 数据概览接口

**目标**：实现 [design-docu.md §7.1](design-docu.md) 看板需要的全部数据。

**指令**：
- 实现 `GET /api/ops/overview`，响应 `data` 含：
  - `kpis: { tryons_today, conversion_rate, active_styles, new_trending_alerts }` 含每项的当前值与环比百分数；
  - `trend_7d: [{date, tryon_count}]`（7 天，按日）；
  - `style_distribution: [{style_tag, percent}]`（今日试戴的标签分布饼图，取前 6）；
  - `hourly_heat: [count×24]`（今日 24 小时各小时试戴量）。
- 全部数据从 `style_stats` 与 `tryons` 聚合得出，不接受查询参数。

**验证**：
- 请求一次，所有四个键都有数据；`trend_7d.length == 7`；`hourly_heat.length == 24`。
- `kpis.tryons_today` 与 `SELECT SUM(tryon_count) FROM style_stats WHERE stat_date=date('now','localtime')` 一致。

---

### Step 6.2 · 爆款识别接口

**目标**：实现 [design-docu.md §7.2](design-docu.md) 的爆款规则与详情。

**指令**：
- 实现 `GET /api/ops/trending`，响应 `data.items[]` 含每个爆款的：`style_id`、`name`、`cover_url`、`trend_7d:[]`（迷你折线数据）、`growth_rate`、`collect_rate`、`detected_at`、`suggested_action`。
- 爆款规则严格按设计文档 §7.2.2：近 3 天复合增长率 ≥ 50% + 近 24 小时试戴 ≥ 50 + 收藏率 ≥ 20%。
- `suggested_action` 是字符串如「加入首页推荐位」或「调高推荐排序权重」，按规则模板生成。

**验证**：
- 用 Step 1.4 选定的 2 个 `emerging_hot` 款式，调用 `/api/ops/trending` 应至少返回这 2 个的 `style_id`。
- 其他款式不应误报为爆款。

---

### Step 6.3 · 冷门预警接口

**目标**：实现 [design-docu.md §7.3](design-docu.md) 的冷门识别与建议。

**指令**：
- 实现 `GET /api/ops/cold`，响应 `data.items[]` 含 `style_id`、`name`、`cover_url`、`recent_7d_tryons`、`exposure_click_ratio`、`days_since_listed`、`cold_reason`、`suggestion`。
- 三条触发规则任一命中即视为冷门：近 7 天试戴 ≤ 5；近 7 天点击曝光比 ≤ 2%；上架超 30 天但累计试戴 ≤ 20。
- `cold_reason` 与 `suggestion` 按设计文档 §7.3.3 的映射表生成。

**验证**：
- Step 1.4 选定的 3 个 `cold` 款式应全部出现。
- 任意 `stable_hot` 款式不应出现。

---

### Step 6.4 · 运营动作接口

**目标**：实现执行运营动作的统一入口。

**指令**：
- 实现 `POST /api/ops/actions`，请求体含 `style_id`、`action_type ∈ {boost, demote, offline, reorder}`、可选 `reason` 字符串。
- `boost`：把该款式 `display_order` 设为当前所有 `is_active=1` 款式中最小值再 -1。
- `demote`：设为当前最大值 +1。
- `offline`：`is_active=0`。
- `reorder`：暂不实现（返回 not implemented）。
- 每次操作同步插入 `ops_actions` 表一行，`operator="ai_assistant"`。

**验证**：
- 调用 `boost` on `f_15` → `SELECT display_order FROM styles WHERE id='f_15'` 应为当前最小。
- 调用 `offline` on `f_25` → 再 `GET /api/styles` 不再包含 `f_25`。
- `SELECT COUNT(*) FROM ops_actions WHERE style_id='f_15' AND action_type='boost'` ≥ 1。

---

### Step 6.5 · 款式管理 CRUD

**目标**：实现 [design-docu.md §7.6 O6](design-docu.md)。

**指令**：
- 实现 `GET /api/ops/styles`：全量返回 40 款（含 `is_active=0` 的），按 `display_order` 升序。
- 实现 `PATCH /api/ops/styles/{id}`：可选字段 `is_active`、`display_order`。
- 改动必须同步写入 `ops_actions`（动作类型分别用 `offline`/`reorder`）。

**验证**：
- `GET` 返回 25 条（包含离线的）。
- `PATCH` 切换 `is_active` 后再次 `GET /api/styles` 列表数变化。

---

## Phase 7 · 运营端前端（5 步）

### Step 7.1 · 运营端布局与共享导航

**目标**：建立运营端共享的 Layout（左侧菜单 + 顶部含铃铛 + 主体）。

**指令**：
- 在 `/ops/*` 路径下使用统一 Layout：左侧 antd Menu（包含 O1 总览、O2 爆款、O3 冷门、O5 AI 助手悬浮、O6 款式管理、O7 报告中心 6 个菜单项）。
- 顶部右侧放铃铛组件（先用静态红点占位，Step 9.5 接真实数据）。
- 切换菜单时主体路由跳转。

**验证**：
- 访问 `/ops/overview`，左侧菜单 6 项可见，「数据概览」高亮。
- 点击「爆款趋势」→ URL 变成 `/ops/trending`，菜单高亮切换。

---

### Step 7.2 · O1 数据概览看板

**目标**：完成 [design-docu.md §7.1](design-docu.md)。

**指令**：
- 顶部 4 张 antd Statistic 卡片显示 KPI；每张显示当前值与环比箭头（涨绿、跌红）。
- 中部 ECharts 折线图展示 7 天趋势；切换按钮支持 7d/30d（30d 暂可不实现）。
- 下方两栏：左侧饼图（标签分布），右侧热力条（24 小时）。
- 数据从 `GET /api/ops/overview` 拉，每 10 秒自动刷新。

**验证**：
- 打开 `/ops/overview`，所有图表 5 秒内渲染完成。
- 在用户端用真实账户做一次试戴 → 10 秒内 KPI 中「今日试戴次数」+1。
- 4 张卡片的环比箭头方向与数字符号一致。

---

### Step 7.3 · O2 爆款趋势页

**目标**：完成 [design-docu.md §7.2](design-docu.md) 的表格 + 详情抽屉。

**指令**：
- 主体 antd Table：列含款式封面、名称、迷你折线（7 天 sparkline 用 ECharts）、增长率、收藏率、发现时间、操作按钮「采纳建议」。
- 点击行打开右侧 antd Drawer：展示详细 7 天趋势大图、建议文案、「采纳」按钮（点击调用 `POST /api/ops/actions` 执行对应动作并 toast 成功）。
- 数据从 `GET /api/ops/trending` 拉。

**验证**：
- 打开 `/ops/trending`，表格显示至少 2 行（emerging_hot 款式）。
- 点击某行 → 右侧抽屉展开，趋势图渲染正常。
- 点击「采纳建议」→ toast「已采纳」，刷新页面后 `display_order` 变化（在 O6 页面或用户端推荐里可看到该款式位置上移）。

---

### Step 7.4 · O3 冷门预警页

**目标**：完成 [design-docu.md §7.3](design-docu.md)。

**指令**：
- 与 O2 同样的 Table + Drawer 模式。
- 表格列：封面、名称、近 7 天试戴量、点击曝光比、上架天数、冷门原因、建议、操作。
- 操作按钮按建议类型显示，如「优化主图」「下架」等；点击下架直接调 actions 接口的 `offline`。

**验证**：
- 至少看到 3 个冷门款式（来自 seed 设定）。
- 点击某行下架 → 该款式从 `/api/styles` 默认列表消失，从用户端推荐列表也消失。

---

### Step 7.5 · O6 款式管理页（P2）

**目标**：完成 [design-docu.md §7.6](design-docu.md)。

**指令**：
- antd Table 列出全部 40 款式：封面、名称、性别、标签、热度、上下架开关、排序值。
- 上下架开关切换调 `PATCH /api/ops/styles/{id}`。
- 拖拽排序：每行支持上下移按钮（拖拽可省略），点击后调接口更新 `display_order`。

**验证**：
- 切换某款式开关 → 用户端 `/browse` 立刻看不到/看到它。
- 点击「上移」→ 该款式 `display_order` 减小，用户端 `/recommend` 列表中位置上调。

---

## Phase 8 · AI 助手（3 步）

### Step 8.1 · Function Calling 工具集定义

**目标**：定义供 LLM 调用的 5 个工具，及其后端实现。

**指令**：
- 在 `backend/app/services/assistant_tools.py` 定义 5 个工具的 JSON Schema（OpenAI tools 格式），按 [design-docu.md §5.3](design-docu.md) 表格：
  - `query_top_styles(date_range, top_n, gender?)`
  - `compare_styles(style_ids[], date_range)`
  - `find_trending(growth_threshold, min_volume)`
  - `find_cold(days_no_activity)`
  - `execute_action(style_id, action_type)`
- 为每个工具实现纯函数（同步或异步皆可），返回 dict（不是 HTTP 响应）。
- 提供一个 dispatcher：根据工具名调用对应函数。

**验证**：
- 写一次性测试：直接调 `query_top_styles({"date_range":"today","top_n":3})` → 返回 3 条 styles。
- 直接调 `execute_action({"style_id":"f_01","action_type":"boost"})` → 数据库 `display_order` 变化、`ops_actions` 新增一行。
- 删除该测试脚本。

---

### Step 8.2 · AI 助手对话接口

**目标**：实现 `POST /api/ops/chat`，包含 Function Calling 循环。

**指令**：
- 请求体 `{messages: [{role, content}], session_id?}`。
- 内部循环：
  1. 调用 `llm.gen_text_with_tools(messages, tools)`；
  2. 若返回 tool_calls，执行 dispatcher → 把结果作为 `tool` 消息追加 → 再次调用 LLM；
  3. 最多循环 3 次，超出强制取最后文本。
- 响应 `data` 含 `reply`（最终文本）、`components[]`（数组，每项 `{component, data}` 描述前端要渲染的可视化组件名如 `top_styles_table`、`mini_trend`）。

**验证**：
- 发消息「今天哪款式试戴最多？」→ 返回的 `reply` 含具体款式名，`components` 含 `top_styles_table`。
- 发消息「把 f_15 加入首页推荐」→ 数据库的 `f_15` `display_order` 变最小、`ops_actions` 新增一行。
- 发消息「这周哪些款式涨得最快？」→ `reply` 含 2 个款式名，`components` 含 `trending_list`。

---

### Step 8.3 · O5 前端聊天面板

**目标**：完成 [design-docu.md §7.5](design-docu.md)。

**指令**：
- 在运营端 Layout 右下角放悬浮按钮，点击展开抽屉式聊天面板。
- 消息体支持 markdown 渲染。
- 收到响应中的 `components` 数组时，按组件名渲染对应小组件（先支持 `top_styles_table`、`trending_list`、`mini_trend` 三种即可，其余兜底为 JSON 文本）。
- 用户输入框：回车发送、Shift+回车换行。

**验证**：
- 点击悬浮按钮 → 抽屉打开。
- 输入「今天哪款式试戴最多？」回车 → 5–10 秒内出现回复，回复下方渲染出 3 行款式表格。
- 输入「把 f_15 加入首页推荐」→ 回复确认成功执行；再到 O6 页面看到 `f_15` 排序上移。

---

## Phase 9 · 报告中心（5 步）

### Step 9.1 · 报告与通知的服务函数

**目标**：先实现"生成 + 入库 + 站内信 + 邮件"的统一函数，再挂调度。

**指令**：
- 在 `backend/app/services/report.py` 实现 `generate_and_dispatch_report(report_type, trigger_source) -> report_id`。
- 流程严格按 [design-docu.md §7.7.3](design-docu.md)：聚合数据 → LLM 生成 Markdown（按 §7.4 的 prompt 模板，区分日报/周报）→ 入库 `reports` → 入库 `notifications` → 异步发邮件 → 更新 `email_status`。
- 邮件发送用 `asyncio.create_task` 异步触发，不阻塞函数返回。
- 失败处理按 §7.7.7：LLM 失败抛异常回滚；邮件失败只更新 email_status="failed" + email_error。

**验证**：
- 直接调用 `generate_and_dispatch_report("daily", "manual")` → 函数返回 `report_id`，`reports` 表新增一行（`email_status="pending"`，几秒后变为 `sent` 或 `failed`），`notifications` 表新增一行。
- 检查收件箱（若 SMTP 已配置）能收到邮件。
- 把 SMTP 密码故意改错重新调一次 → `reports.email_status="failed"` 且 `email_error` 非空，但 `reports` 与 `notifications` 仍正常写入。

---

### Step 9.2 · APScheduler 集成

**目标**：把 Step 9.1 挂到定时调度。

**指令**：
- 在 `main.py` 的 startup 事件里启动 `AsyncIOScheduler`，**显式指定 `timezone="Asia/Shanghai"`**（无论部署在哪台机器，"9:00" 都按北京时间触发；千万不要用默认时区，云端默认 UTC 会让任务延迟 8 小时）。
- 当 `SCHEDULER_ENABLED=true` 时注册两个 job：
  - 日报：`CronTrigger(hour=9, minute=0, timezone="Asia/Shanghai")`，每天北京时间 09:00。
  - 周报：`CronTrigger(day_of_week="mon", hour=9, minute=0, timezone="Asia/Shanghai")`，每周一北京时间 09:00。
- `misfire_grace_time=3600`（允许漏触发 1 小时内补跑）。
- 在 shutdown 事件里关闭 scheduler。

**验证**：
- 启动服务，日志能看到「Scheduler started」或类似输出。
- 调用一个临时 `GET /api/ops/_debug/scheduler` 路由（自行加），返回当前注册的 job 名列表与下次触发时间。**下次触发时间应该是北京时间下一个 09:00**（如果当前时刻 < 09:00 北京时间则今天 09:00，否则明天 09:00）；不能是 UTC 09:00。验证完后删除该调试路由。
- 把 `SCHEDULER_ENABLED=false` 重启，调度不启动。

---

### Step 9.3 · 报告中心后端接口

**目标**：实现 [design-docu.md §5.3](design-docu.md) 报告 + 通知相关的全部接口。

**指令**：
- 实现 `GET /api/ops/reports`：支持 `type`、`start_date`、`end_date`、`page`、`size` 查询参数，按 `period_end DESC` 倒序，分页响应。
- 实现 `GET /api/ops/reports/{id}`：返回 `content_md` 在内的全字段。
- 实现 `POST /api/ops/reports/generate`：请求体 `{type:"daily"|"weekly"}`，调 Step 9.1 函数，30 秒内防抖（同一 type 30 秒内重复请求直接返回 `code=4xx`）。
- 实现 `POST /api/ops/reports/{id}/resend`：仅当 `email_status="failed"` 时允许，重新触发邮件发送。
- 实现 `GET /api/ops/notifications`：参数 `unread_only`、`limit`；按 `created_at DESC`。
- 实现 `GET /api/ops/notifications/unread-count`：仅返回 `{unread: <int>}`。
- 实现 `POST /api/ops/notifications/{id}/read` 与 `POST /api/ops/notifications/read-all`。

**验证**：
- 调用 `POST /api/ops/reports/generate {type:"daily"}` → 返回 `report_id`。
- 5 秒内调用 `GET /api/ops/notifications/unread-count` → `unread >= 1`。
- 调用 `GET /api/ops/reports?type=daily&start_date=2026-01-01&end_date=2026-12-31` → 至少返回上一步生成的报告。
- 30 秒内再次调用 `generate` 同 type → 返回 4xx 防抖错误。
- 调用 `POST /api/ops/notifications/{id}/read` → 该通知 `is_read=1`、`read_at` 非空。

---

### Step 9.4 · O7 前端：报告中心列表 + 详情

**目标**：完成 [design-docu.md §7.7.6](design-docu.md)。

**指令**：
- 路由 `/ops/reports`：顶部 antd Radio.Group 类型筛选（全部/日报/周报）+ DatePicker.RangePicker 日期筛选 + 右上角两个按钮「立即生成日报」「立即生成周报」。
- 表格列：标题、类型、日期范围、生成时间、邮件状态（带图标），点击行跳转 `/ops/reports/:id`。
- 路由 `/ops/reports/:id`：左侧 react-markdown 渲染 `content_md`，右侧元信息卡（生成方式、邮件状态、错误信息、若失败显示「重新发送」按钮）。
- 筛选变化时调接口刷新；筛选条件写入 URL query 便于分享。

**验证**：
- 打开 `/ops/reports`，能看到至少 1 条记录（来自 Step 9.3 触发的那条）。
- 点击「立即生成周报」→ 10 秒内列表新增 1 条周报。
- 类型筛选切换到「仅日报」→ 列表只显示日报。
- 日期范围筛选缩到今天 → 只显示今天生成的。
- 点击行 → 详情页 markdown 正常渲染、元信息卡显示状态。

---

### Step 9.5 · 站内信铃铛组件接通真实数据

**目标**：完成 [design-docu.md §7.7.5](design-docu.md)。

**指令**：
- 把 Step 7.1 的铃铛占位组件改造为真实数据：
  - 每 5 秒轮询 `GET /api/ops/notifications/unread-count`，更新红点数字。
  - 点击铃铛打开下拉/抽屉：展示最近 10 条 + 「全部已读」按钮。
  - 点击某条 → 调 `POST /api/ops/notifications/{id}/read` → 跳转 `/ops/reports/:ref_id`。

**验证**：
- 打开运营端任意页面，触发一次「立即生成日报」→ 5 秒内铃铛红点出现/+1。
- 点击铃铛 → 下拉列表显示该通知。
- 点击该通知 → URL 跳转到对应报告详情，红点数减 1。
- 点击「全部已读」→ 红点消失。

---

## Phase 10 · 端到端联调与冒烟（4 步）

### Step 10.1 · 数据闭环验证

**目标**：验证用户端试戴→运营端看板实时同步。

**指令**：
- 在用户端完成一次完整流程：上传 hands/01.png（或点示例图）→ 选女 → 推荐 → 选 3 款对比试戴 → 在 U5 收藏其中一款。
- 切换到运营端 O1 概览页（不刷新页面，等轮询）。
- 观察 O1 的 KPI 卡 / 趋势图变化。
- 用同一款式重复试戴 60 次（脚本批量调 `POST /api/tryon` 即可），观察 O2 是否出现该款式爆款预警。

**验证**：
- O1 的 `今日试戴次数` 在 10 秒内增加 ≥3。
- O1 的 `style_distribution` 中该款式标签占比上升。
- 批量试戴后 5 分钟内（或直接调一次 trending 接口），O2 列表新增该款式条目。

---

### Step 10.2 · IMAGE_PROVIDER 切换验证

**目标**：验证降级路径无副作用。

**指令**：
- 把 `.env` 的 `IMAGE_PROVIDER` 从 `mock` 改成 `jimeng`（若 JIMENG_API_KEY 有），重启后端。
- 完成一次试戴。
- 把 `.env` 改回 `mock`，重启后端。
- 完成一次试戴。

**验证**：
- 两种模式下 `POST /api/tryon` 都能成功返回 `result_url`。
- `static/cache/` 下分别有真生成图与 mock 复制图，两者文件大小差异显著（真生成的应在几百 KB 以上）。

---

### Step 10.3 · 报告全链路实测

**目标**：从触发到收信全链路无遗漏。

**指令**：
- 在运营端报告中心点击「立即生成日报」。
- 同时打开邮箱、铃铛、报告列表三个面板。

**验证**：
- 铃铛 5 秒内红点出现。
- 报告列表 10 秒内新增条目，`email_status` 列由 `pending` 在 1 分钟内变为 `sent`。
- 邮箱在 1 分钟内收到 HTML 邮件，正文渲染正常（标题、列表、表格至少一种格式存在）。
- 点击通知跳转报告详情，markdown 渲染与邮件正文一致。

---

### Step 10.4 · 完整故事链路冒烟

**目标**：以"评审脚本"的顺序跑一遍，确认无报错节点。

**指令**：
- 浏览器无痕模式打开 `/`（应被重定向到 `/upload`）。
- 依次完成：上传 → 选男 → 推荐 → 看到 9 款 → 加入对比 3 款 → 对比试戴 → 选定 1 款 → 收藏。
- 切换到运营端：O1 看板 → O2 爆款 → 点开某爆款 → 「采纳建议」→ O7 报告中心 → 「立即生成日报」→ 等铃铛 → 点开通知 → 看到报告详情。
- 用 AI 助手对话 3 轮：查 TopN、对比两款、把某款加入首页推荐。

**验证**：
- 全流程无报错（浏览器 Console / 后端日志均无 ERROR 级别输出）。
- 每个跳转/接口响应时间符合用户感知：推荐 < 8 秒、对比试戴 < 15 秒、看板加载 < 3 秒、报告生成 < 30 秒。
- 用户端"收藏"动作在 1 分钟内反映到运营端 O1 的 `转化率` KPI 上。

---

## 收尾清单

完成 Phase 10 后，做一次工程化检查：

1. **依赖清单**：`backend/requirements.txt` 与 `frontend/package.json` 锁定版本，能在干净环境复现。
2. **环境样板**：`backend/.env.example` 包含所有 key 占位且与代码读取的字段名完全对齐。
3. **seed 幂等性**：删除 `nail_demo.db` → 跑 `seed_all.py` → 启动 → 全链路可用。
4. **README 最小化**：根目录写一个 `README.md`，仅含"如何启动后端 / 启动前端 / 跑 seed / 修改 .env"四步操作。
5. **调试路由清理**：搜索代码中所有 `_debug` 路径，确认在交付前移除或加密。

完成上述五条后，项目达到可交付的最小完整状态。
