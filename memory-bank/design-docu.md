# 美甲 AI 试戴与智能运营 · 产品设计文档

> 基于 PRD v2.0 的工程级实现设计 + 答辩要点说明
> 文档版本：design v1.0 / 适用赛事：美团 AI Hackathon

---

## 目录

1. [项目摘要](#1-项目摘要)
2. [系统架构](#2-系统架构)
3. [技术选型与理由](#3-技术选型与理由)
4. [数据库设计](#4-数据库设计)
5. [API 接口设计](#5-api-接口设计)
6. [用户端模块实现](#6-用户端模块实现)
7. [运营端模块实现](#7-运营端模块实现)
8. [AI 服务设计](#8-ai-服务设计)
9. [Mock 数据构造方案](#9-mock-数据构造方案)
10. [数据闭环与同步机制](#10-数据闭环与同步机制)
11. [前端工程规范](#11-前端工程规范)
12. [团队分工与里程碑](#12-团队分工与里程碑)
13. [创新点与差异化](#13-创新点与差异化)
14. [商业价值论证](#14-商业价值论证)
15. [风险与降级预案](#15-风险与降级预案)

---

## 1. 项目摘要

### 1.1 一句话定位

用 AI 把"用户试戴决策"和"平台运营决策"串起来的双端 Web 系统。

### 1.2 核心差异化（vs 美团问小团）

| 差异点 | 价值 |
|---|---|
| 性别维度入口分流 | 男女款式池物理隔离，男性用户不再被淹没在法式甜美款里 |
| 肤色 + 手型智能推荐 | 每款附 25 字内的具体推荐理由，不模板化 |
| 多款并排对比试戴 | 一次生成 2–4 款，符合"比较型决策"用户实际行为 |
| 完整可交互运营看板 | 问小团对外完全未展示的能力，全力打造 |
| 双端数据闭环 | 用户端试戴行为实时反哺运营端爆款/冷门识别 |

### 1.3 演示故事主线（8 分钟答辩）

```
[用户端] 男性用户进入 → 选"男性" → 看到极简哑光款而非法式甜美款
       ↓
       上传手部照片 → AI 识别"深肤色 / 修长手型"
       ↓
       推荐 9 款 + 推荐理由「哑光黑配你的修长手型，商务场合不出错」
       ↓
       勾选 3 款 → 对比试戴 → 选定一款
       ↓
[运营端] 切换到运营视图 → 总览看板出现新爆款预警
       ↓
       点开爆款详情 → 该款式正是用户刚刚选的那款
       ↓
       AI 日报建议「加入首页推荐位」→ 一键采纳
       ↓
       回到用户端刷新 → 首页推荐顺序变化，闭环完成
```

---

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────┐
│  展现层 (React SPA)                                 │
│  ├── 用户端视图：U0–U6                              │
│  └── 运营端视图：O1–O7                              │
│       共享顶部导航切换（同一域名 /user, /ops）      │
└─────────────────────────────────────────────────────┘
                        │ HTTPS / JSON
┌─────────────────────────────────────────────────────┐
│  应用层 (FastAPI)                                   │
│  ├── 路由层：user_router / ops_router               │
│  ├── 业务逻辑层：recommend / tryon / stats / report │
│  ├── 调度层：APScheduler（日报 09:00 / 周报周一 09:00）│
│  └── 事件总线：试戴事件 → 统计聚合                  │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
┌──────────────┐ ┌────────────────┐ ┌─────────────────┐
│ AI 服务层    │ │ 数据层         │ │ 静态资源        │
│ ├ ImageGen   │ │ SQLite         │ │ ├ 款式图        │
│ ├ LLM        │ │ ├ styles       │ │ ├ 示例手部图    │
│ ├ HandAnalyze│ │ ├ tryons       │ │ └ 试戴结果缓存  │
│ └ Email/SMTP │ │ ├ style_stats  │ └─────────────────┘
└──────────────┘ │ ├ ops_actions  │
                 │ ├ reports      │
                 │ └ notifications│
                 └────────────────┘
```

### 2.2 关键设计决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 单仓 vs 双仓 | 单仓 monorepo (`frontend/` + `backend/`) | Hackathon 协作成本低，前后端类型可共享 |
| SPA vs MPA | React SPA（顶部导航切换两端） | 评审现场切换成本低，故事链路连续 |
| 同步 vs 异步生成 | 异步并行 + WebSocket/轮询 | 多款对比试戴需要并行，单款也走异步队列保持一致性 |
| 状态管理 | React Context + URL State | 性别字段放 sessionStorage，避免刷新丢失 |
| 鉴权 | 演示阶段无登录，匿名 user_id (UUID) | Hackathon 不做账号体系，匿名 ID 足以串数据闭环 |

---

## 3. 技术选型与理由

### 3.1 技术栈总览

| 层 | 技术 | 版本建议 | 选型理由 |
|---|---|---|---|
| 前端框架 | React 18 + Vite | 18.x | 生态成熟，Vite 构建快，Hackathon 友好 |
| 路由 | React Router | 6.x | SPA 标配 |
| UI 组件 | Ant Design + Tailwind | antd 5 + tw 3 | antd 提供运营端表格/图表/抽屉，tw 写用户端定制 UI |
| 图表 | ECharts (echarts-for-react) | 5.x | 运营端折线/饼图/热力图统一一个库 |
| 后端框架 | FastAPI | 0.110+ | 自动生成 OpenAPI 文档，类型注解友好，async 原生 |
| ORM | SQLAlchemy 2.0 + SQLite | - | 零部署，演示场景足够；生产可平滑迁 PostgreSQL |
| 异步任务 | asyncio + asyncio.gather | - | 多款并行试戴用 gather 即可，无需引入 Celery |
| 图像生成 | 即梦 AI（字节）+ Replicate 备选 | API | 国内访问稳定；Replicate 提供 ControlNet 备选保细节 |
| LLM 推荐理由 | 通义千问 qwen-turbo | API | 短文本生成成本低、速度快 |
| LLM 日报/对话 | 通义千问 qwen-max | API | 复杂推理与 Function Calling 用更强模型 |
| 手部识别 | MediaPipe Hands (JS or Python) | - | 浏览器侧/服务端均可跑，无需 GPU，关键点准确 |

### 3.2 为什么是云端 API 而非本地模型

- **零部署成本**：评审现场不依赖本地 GPU
- **生成质量稳定**：商业 API 已针对人手场景优化
- **接口可替换**：通过 `ImageGenProvider` 抽象层屏蔽底层 API，可一键切换备选

### 3.3 为什么 SQLite

- 单文件、零运维、Python 内置
- 40 款款式 + 模拟 60 天试戴行为 ≈ 万行级记录，SQLite 性能完全够
- 演示完打包源码即可复现，无需额外数据库实例

---

## 4. 数据库设计

### 4.1 ER 关系

```
styles 1───* tryons *───1 (匿名用户 user_id 不建表，UUID 字符串)
   │
   └──1───* style_stats（按天聚合）
   └──1───* ops_actions（运营动作日志）

reports（日报/周报归档，独立时序数据，无强外键）
   └──1───* notifications（ref_id 软关联 reports.id）
```

### 4.2 表结构

#### `styles` — 款式库

| 字段 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 款式 ID，如 `f_001`/`m_001` |
| name | TEXT | 款式名，如「奶茶杏色法式」 |
| gender | TEXT | `female` / `male` |
| cover_url | TEXT | 款式封面图 URL |
| style_tags | TEXT (JSON array) | 如 `["法式","渐变","显白"]` |
| color_main | TEXT | 主色调英文 token，如 `#E8C9A0` |
| color_tone | TEXT | `warm` / `cool` / `neutral` |
| length_pref | TEXT | `short` / `medium` / `long` |
| complexity | INT | 1–5 复杂度 |
| heat_score | REAL | 平台基础热度（初始化时构造） |
| is_active | INT | 1 上架 / 0 下架 |
| display_order | INT | 推荐位排序权重，运营端可调 |
| created_at | DATETIME | 上架时间 |

#### `tryons` — 试戴行为表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK AUTO | |
| user_id | TEXT | 匿名用户 UUID |
| user_gender | TEXT | 用户性别 |
| style_id | TEXT FK | 关联 styles.id |
| skin_tone | TEXT | `light_warm`/`light_cool`/`medium`/`dark_warm`/`dark_cool` |
| hand_shape | TEXT | `slim_long`/`short_round`/`average` |
| from_module | TEXT | `recommend`/`browse`/`compare` 来源 |
| is_collected | INT | 试戴后是否收藏 |
| created_at | DATETIME | |

#### `style_stats` — 款式日度聚合表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK AUTO | |
| style_id | TEXT FK | |
| stat_date | DATE | 统计日期 |
| tryon_count | INT | 当日试戴次数 |
| collect_count | INT | 当日收藏数 |
| exposure_count | INT | 当日曝光次数 |
| click_count | INT | 当日点击次数 |

唯一索引：`(style_id, stat_date)`

#### `ops_actions` — 运营动作日志

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | |
| style_id | TEXT FK | |
| action_type | TEXT | `boost`/`demote`/`offline`/`reorder` |
| reason | TEXT | AI 给出的理由（用于回放） |
| operator | TEXT | 演示场景固定 `ai_assistant` |
| created_at | DATETIME | |

#### `reports` — 报告归档表（日报 / 周报）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK AUTO | |
| type | TEXT | `daily` / `weekly` |
| title | TEXT | 如「美甲品类日报 2026-05-26」 |
| content_md | TEXT | LLM 生成的 Markdown 正文 |
| period_start | DATE | 统计起始日（含） |
| period_end | DATE | 统计结束日（含） |
| trigger_source | TEXT | `scheduled` / `manual` |
| email_status | TEXT | `pending` / `sent` / `failed` |
| email_sent_at | DATETIME | 邮件发送时间，可空 |
| email_error | TEXT | 发送失败的错误信息，可空 |
| generated_at | DATETIME | 默认 `CURRENT_TIMESTAMP` |

#### `notifications` — 站内信表

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK AUTO | |
| type | TEXT | 当前仅 `report`，预留扩展（`trending_alert` 等） |
| ref_id | INTEGER | 关联资源 ID（如 reports.id） |
| title | TEXT | 通知标题 |
| summary | TEXT | 摘要，120 字以内 |
| is_read | INT | 0 未读 / 1 已读 |
| created_at | DATETIME | 默认 `CURRENT_TIMESTAMP` |
| read_at | DATETIME | 标记已读的时间，可空 |

### 4.3 索引建议

- `tryons (style_id, created_at)` — 爆款增长率计算高频查询
- `tryons (user_id, created_at)` — 试戴历史
- `style_stats (stat_date, tryon_count DESC)` — 当日排行榜
- `reports (type, period_end DESC)` — 报告中心按类型 + 时间倒序
- `notifications (is_read, created_at DESC)` — 未读数与下拉列表

---

## 5. API 接口设计

所有接口遵循 RESTful 风格，统一返回结构：

```json
{ "code": 0, "msg": "ok", "data": { ... } }
```

### 5.1 用户端接口

| 方法 | 路径 | 说明 |
|---|---|---|
| ~~POST~~ | ~~`/api/user/session`~~ | 已废弃——前端本地生成 UUID v4 作为 `user_id`，所有请求带在 header，后端不维护会话表 |
| POST | `/api/user/upload` | 上传手部照片，返回特征 JSON |
| GET | `/api/styles` | 款式列表，支持 `?gender=&tags=&color=&sort=` |
| GET | `/api/styles/{id}` | 款式详情 |
| POST | `/api/recommend` | 智能推荐，body: `{user_id, gender, hand_features}` |
| POST | `/api/tryon` | 单款试戴，body: `{user_id, style_id, photo_id}` |
| POST | `/api/tryon/batch` | 多款对比试戴，body: `{user_id, style_ids:[], photo_id}` |
| POST | `/api/events/collect` | 收藏事件埋点 |

### 5.2 运营端接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/ops/overview` | 当日 KPI + 趋势图数据 |
| GET | `/api/ops/trending` | 爆款列表 + 详情 |
| GET | `/api/ops/cold` | 冷门款列表 + 处理建议 |
| POST | `/api/ops/chat` | AI 助手对话，Function Calling |
| POST | `/api/ops/actions` | 执行运营动作，body: `{style_id, action_type}` |
| GET | `/api/ops/styles` | 款式管理列表 |
| PATCH | `/api/ops/styles/{id}` | 上下架、调整顺序 |
| GET | `/api/ops/reports` | 报告列表，支持 `?type=&start_date=&end_date=&page=&size=` |
| GET | `/api/ops/reports/{id}` | 报告详情（含 Markdown 正文与发送状态） |
| POST | `/api/ops/reports/generate` | 立即生成一次，body: `{type:"daily"\|"weekly"}` |
| GET | `/api/ops/notifications` | 站内信列表，支持 `?unread_only=&limit=` |
| GET | `/api/ops/notifications/unread-count` | 未读数（铃铛红点轮询用） |
| POST | `/api/ops/notifications/{id}/read` | 标记单条已读 |
| POST | `/api/ops/notifications/read-all` | 全部已读 |

### 5.3 关键接口详细规约

#### POST `/api/recommend`

**请求**

```json
{
  "user_id": "uuid-string",
  "gender": "male",
  "hand_features": {
    "skin_tone": "medium",
    "hand_shape": "slim_long",
    "keypoints": [...]
  }
}
```

**响应**

```json
{
  "code": 0,
  "data": {
    "user_summary": "你是男性，手型偏修长、肤色偏冷调",
    "recommendations": [
      {
        "style_id": "m_003",
        "name": "深邃哑光黑",
        "cover_url": "/static/styles/m_003.jpg",
        "score": 0.92,
        "reason": "哑光黑配你的修长手型，商务场合不出错"
      }
    ]
  }
}
```

#### POST `/api/tryon/batch`

**请求**

```json
{
  "user_id": "uuid",
  "photo_id": "upload-123",
  "style_ids": ["m_003","m_007","m_012"]
}
```

**响应**（流式渐进，每款式生成完即推送一条 SSE 消息）

```
event: tryon_done
data: {"style_id":"m_003","result_url":"/cache/xxx.jpg","status":"success"}

event: tryon_done
data: {"style_id":"m_007","result_url":"/cache/yyy.jpg","status":"success"}
```

#### POST `/api/ops/chat`

支持 Function Calling，可调用的函数清单：

| 函数名 | 入参 | 用途 |
|---|---|---|
| `query_top_styles` | `{date_range, top_n, gender?}` | 试戴 TopN |
| `compare_styles` | `{style_ids[], date_range}` | 两/多款对比 |
| `find_trending` | `{growth_threshold, min_volume}` | 爆款发现 |
| `find_cold` | `{days_no_activity}` | 冷门发现 |
| `execute_action` | `{style_id, action_type}` | 执行运营动作 |

LLM 决策流程：用户问题 → 选择函数 + 参数 → 后端执行 → 返回 JSON → LLM 组织自然语言回答 + 附结构化展示组件标识（前端据此渲染表格/卡片/图表）。

#### GET `/api/ops/reports`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | `daily`/`weekly`/空 | 否 | 不传则返回全部 |
| `start_date` | YYYY-MM-DD | 否 | 按 `period_end` 过滤起始 |
| `end_date` | YYYY-MM-DD | 否 | 按 `period_end` 过滤结束 |
| `page` | int | 否 | 默认 1 |
| `size` | int | 否 | 默认 20，最大 100 |

**响应**

```json
{
  "code": 0,
  "data": {
    "total": 42,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": 88,
        "type": "weekly",
        "title": "美甲品类周报 2026-05-19 ~ 2026-05-25",
        "period_start": "2026-05-19",
        "period_end": "2026-05-25",
        "trigger_source": "scheduled",
        "email_status": "sent",
        "generated_at": "2026-05-26T09:00:12"
      }
    ]
  }
}
```

#### POST `/api/ops/reports/generate`

**请求**

```json
{ "type": "daily" }
```

**响应**

```json
{
  "code": 0,
  "data": {
    "report_id": 89,
    "title": "美甲品类日报 2026-05-27",
    "email_status": "sent",
    "elapsed_ms": 4820
  }
}
```

幂等性：同一自然日（或同一周）多次调用允许，每次产生独立记录、独立站内信、独立邮件；前端 UI 在按钮上做防抖（30 秒内不可重复点击）。

#### GET `/api/ops/notifications/unread-count`

**响应**

```json
{ "code": 0, "data": { "unread": 3 } }
```

被前端铃铛组件以 5 秒间隔轮询。

---

## 6. 用户端模块实现

### 6.1 U0 手图入口页（用户进入产品看到的第一页）

- **路由**：`/` 默认重定向至 `/upload`
- **职责**：让用户给系统一张"代表自己手"的图，作为后续推荐和试戴的输入
- **两种方式**（都走 `POST /api/user/upload`）：
  - 自拍/上传：拖拽或点击上传组件，基于 antd `<Upload.Dragger />`，限制 jpg/png ≤10MB
  - 点示例图：3–4 张示例手图，懒得自拍的用户直接点（前端 fetch 该图为 blob 再走上传接口）
- **客户端压缩**：使用 `browser-image-compression` 压到 ≤5MB 再传
- **示例图来源**：17 张手图（`dataset/hands/01.png` ~ `17.png`，13 张赛题 + 4 张补充），seed 时复制到 `backend/static/samples/`。**不按性别区分**（手的视觉性别特征弱），男女用户共用
- **跳转**：成功上传/选定后，前端把 `photoId` 与 `handFeatures` 写入 Context，跳转 `/gender`
- **session 处理**：进入本页时若 `sessionStorage.userId` 不存在则前端本地生成 UUID v4 并写入，后续所有请求均携带；**不需要 `POST /api/user/session` 接口**

### 6.2 U1 性别选择页

- **路由**：`/gender`
- **前置条件**：必须已经过 U0 拿到 `photoId`，否则重定向回 `/upload`
- **职责**：让用户选女/男，决定推荐时看到哪个款式池
- **存储**：`sessionStorage.setItem('userGender', value)`
- **跳过策略**：右上角"跳过"按钮等同选择 `female`（覆盖大多数用户）
- **关键组件**：`<GenderCard />`，左右并排，hover 放大动效
- **视觉**：女性卡片背景渐变粉/奶茶色，男性卡片背景渐变深灰/墨蓝
- **跳转**：选定后跳 `/recommend`

### 6.3 U2 智能推荐（核心）

**推荐算法（伪代码）**

```python
def recommend(gender, hand_features, top_k=9):
    # 1. 性别硬筛选
    candidates = styles.filter(gender=gender, is_active=1)

    # 2. 多维打分
    for style in candidates:
        skin_score = match_skin(style.color_tone, hand_features.skin_tone)  # 0–1
        shape_score = match_shape(style.length_pref, hand_features.hand_shape)
        heat_score = normalize(style.heat_score + recent_7d_tryons(style.id))
        style.final_score = (
            0.35 * skin_score +
            0.30 * shape_score +
            0.20 * heat_score +
            0.15 * 0  # 多样性在后续 rerank 中体现
        )

    # 3. 排序 + 多样性 rerank（确保前 9 款至少覆盖 3 种风格 tag）
    sorted_list = sorted(candidates, key=lambda s: -s.final_score)
    final = diversity_rerank(sorted_list, top_k=9, min_style_categories=3)

    # 4. LLM 生成推荐理由（批量并发）
    for s in final:
        s.reason = llm_gen_reason(s, gender, hand_features)

    return final
```

**LLM 推荐理由 Prompt 模板**

```
你是美甲推荐专家。请用一句话（≤25字）说明为什么这款适合用户。
用户：{gender}，肤色{skin_tone}，手型{hand_shape}
款式：{style_name}，标签{tags}，主色{color}
要求：
- 必须包含具体视觉理由
- {gender==女: 多用"衬肤""显白""精致" | gender==男: 多用"商务""干净""利落""酷"}
- 不要说"适合您""精选好物"等空话
```

### 6.4 U3 款式浏览

- **瀑布流**：使用 CSS Grid + `grid-auto-flow: dense`
- **筛选器**：URL 同步参数 `?tags=&color=&length=`，刷新不丢失
- **性别切换**：顶部小按钮，演示用，切换后请求新数据

### 6.5 U4 多款对比试戴（核心）

**关键实现：并行 + 渐进展示**

```python
async def batch_tryon(photo, style_ids):
    tasks = [generate_one(photo, sid) for sid in style_ids]
    for coro in asyncio.as_completed(tasks):  # 谁先完成谁先返回
        result = await coro
        yield {"style_id": result.style_id, "url": result.url}
```

前端用 `EventSource` 接 SSE，每收到一条立刻填入对应格子。

**容错**：单款失败时该格子显示「生成失败，点击重试」，不阻塞其他款。

### 6.6 U5 试戴结果展示

- **对比滑块**：使用 `react-compare-image`，左右拖动原图/生成图
- **操作栏**：保存（canvas toBlob 下载）/ 分享（复制链接）/ 收藏（埋点）/ 找店预约（占位跳转）

### 6.7 U6 试戴历史（P2）

`sessionStorage` 存最近 10 条试戴记录，刷新清空。设计上预留 `localStorage` 接口，未来接账号可平滑迁移。

---

## 7. 运营端模块实现

### 7.1 O1 数据概览看板

- **布局**：顶部 4 张 KPI 卡 + 下方 3 个图表（折线/饼/热力）
- **数据源**：`/api/ops/overview` 一次拉全
- **KPI 卡组件**：`<KpiCard title value diff diffType />`，红绿环比箭头
- **环比计算**：当日 0:00–now 数据 vs 昨日同时段

### 7.2 O2 爆款趋势识别（核心）

**识别 SQL（核心逻辑）**

```sql
WITH recent_3d AS (
  SELECT style_id, SUM(tryon_count) AS cnt
  FROM style_stats
  WHERE stat_date >= date('now','-3 days')
  GROUP BY style_id
),
prev_3d AS (
  SELECT style_id, SUM(tryon_count) AS cnt
  FROM style_stats
  WHERE stat_date BETWEEN date('now','-6 days') AND date('now','-4 days')
  GROUP BY style_id
)
SELECT r.style_id,
       (r.cnt - p.cnt) * 1.0 / NULLIF(p.cnt,0) AS growth_rate,
       r.cnt AS recent_volume
FROM recent_3d r LEFT JOIN prev_3d p USING(style_id)
WHERE r.cnt >= 50
  AND (r.cnt - p.cnt) * 1.0 / NULLIF(p.cnt,1) >= 0.5
ORDER BY growth_rate DESC;
```

再叠加收藏率筛选 ≥20%，得到爆款清单。

**处理建议生成**：基于规则映射到固定动作模板，无需 LLM。

### 7.3 O3 冷门款式预警

规则查询同上反向，额外按"冷门原因"分类输出对应建议。

### 7.4 O4 AI 运营日报（核心）

> O4 是报告生成的**业务逻辑层**，O7 是其**调度 + 推送 + 归档**的载体。日报生成的代码路径被 O7 的定时任务和手动触发共用。

**生成流程**

```
当日数据快照 → 结构化 JSON → LLM 模板填充 → Markdown 日报 → 入库 reports → 站内信 + 邮件
```

**日报 Prompt 模板**

```
你是平台美甲品类的运营助手。基于以下数据，生成一份结构化日报。
数据：{today_stats_json}
要求章节：
1. 数据概览：3 句话总结 KPI 与环比
2. 重点亮点：列出 TOP3 试戴款、TOP3 增长款、转化率最高款
3. 风险预警：冷门款数量、转化下降款、库存紧张款
4. 运营建议：3–5 条可执行建议，每条须引用具体数据
5. 关键问题：1–2 个需运营拍板的开放问题
语言风格：简洁专业，避免空话。
```

**周报 Prompt 模板**

```
你是平台美甲品类的运营助手。基于以下本周与上周对比数据，生成一份周报。
本周数据：{this_week_stats_json}
上周数据：{last_week_stats_json}
要求章节：
1. 本周总览：试戴总量、转化率、活跃款式数（含周环比）
2. 趋势亮点：连续上升 ≥ 3 天的款式、本周首次进入 TOP10 的款式
3. 持续冷门：本周和上周都进入冷门预警的款式
4. 性别分布：女性/男性用户试戴行为差异（如有显著变化）
5. 运营建议：3–5 条针对下周的具体动作
6. 待决问题：1–2 个需要拍板的运营决策
语言风格：简洁专业，引用具体数字，体现"周"的时间维度。
```

### 7.5 O5 AI 助手对话

**前端实现**

- 右下角悬浮按钮 → 展开聊天面板
- 消息体支持 markdown + 自定义组件（表格/迷你图/卡片）
- 自定义组件通过约定协议返回：`{"component":"top_styles_table","data":[...]}`

**后端实现**

```python
TOOLS = [
    {"name":"query_top_styles", "schema": {...}},
    {"name":"compare_styles", "schema": {...}},
    {"name":"execute_action", "schema": {...}},
    # ...
]

async def chat(user_msg, history):
    resp = await llm.chat(messages=history+[user_msg], tools=TOOLS)
    if resp.tool_calls:
        results = await asyncio.gather(*[
            dispatch_tool(tc) for tc in resp.tool_calls
        ])
        final = await llm.chat(messages=history+[..., results])
        return final
    return resp
```

### 7.6 O6 款式列表管理（P2）

基础表格 + 上下架开关 + 拖拽排序。点击保存后立即影响用户端 `/api/styles` 返回顺序，体现"运营调整即时生效"的闭环。

### 7.7 O7 报告中心（核心）

> O7 把 O4 的"按需触发"升级为**定时任务 + 双通道推送 + 历史归档**，是 AI 自主运营叙事的关键载体。

#### 7.7.1 功能描述

运营无需主动进入系统，AI 助手会在每天/每周固定时间自动：
1. 聚合数据 → LLM 生成报告（复用 O4 的生成代码）
2. 写入 `reports` 表，归档可查
3. 投递到站内信通知中心（铃铛红点）
4. HTML 邮件发送到指定运营邮箱

运营进入"报告中心"页面可按 **类型（日报/周报）** 和 **日期范围** 双维筛选历史归档。

#### 7.7.2 定时调度

使用 `APScheduler` 进程内调度，跟 FastAPI 同进程：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    if settings.SCHEDULER_ENABLED:
        scheduler.add_job(
            lambda: generate_and_dispatch_report("daily"),
            CronTrigger(hour=9, minute=0),
            id="daily_report"
        )
        scheduler.add_job(
            lambda: generate_and_dispatch_report("weekly"),
            CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_report"
        )
        scheduler.start()
```

| 任务 | 触发时机 |
|---|---|
| 日报 | 每天 09:00 |
| 周报 | 每周一 09:00（覆盖上周一至上周日） |

#### 7.7.3 统一生成 + 推送链路

定时触发和手动触发走**同一个函数**，仅 `trigger_source` 不同：

```python
async def generate_and_dispatch_report(report_type: str, source: str = "scheduled"):
    # 1. 数据聚合
    period_start, period_end = compute_period(report_type)
    stats = await aggregate_stats(period_start, period_end)

    # 2. LLM 生成 Markdown
    prompt = build_daily_prompt(stats) if report_type == "daily" else build_weekly_prompt(stats)
    content_md = await llm.chat(prompt, model="qwen-max")
    title = build_title(report_type, period_start, period_end)

    # 3. 入库
    report = await db.insert_report(
        type=report_type, title=title, content_md=content_md,
        period_start=period_start, period_end=period_end,
        trigger_source=source, email_status="pending"
    )

    # 4. 站内信
    await db.insert_notification(
        type="report", ref_id=report.id,
        title=title, summary=truncate(content_md, 120)
    )

    # 5. 邮件（异步发送，失败不阻塞前面流程）
    asyncio.create_task(send_report_email(report))
    return report
```

#### 7.7.4 邮件发送

```python
import smtplib, markdown
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

async def send_report_email(report):
    try:
        html = markdown.markdown(report.content_md, extensions=['tables','fenced_code'])
        msg = MIMEMultipart('alternative')
        msg['Subject'] = report.title
        msg['From'] = settings.SMTP_FROM
        msg['To'] = settings.REPORT_RECIPIENT
        msg.attach(MIMEText(report.content_md, 'plain', 'utf-8'))
        msg.attach(MIMEText(wrap_html(html), 'html', 'utf-8'))

        with smtplib.SMTP_SSL(settings.SMTP_HOST, 465) as srv:
            srv.login(settings.SMTP_USER, settings.SMTP_PASS)
            srv.send_message(msg)

        await db.update_report(report.id, email_status="sent", email_sent_at=now())
    except Exception as e:
        await db.update_report(report.id, email_status="failed", email_error=str(e))
```

**HTML 包装函数**（避免 QQ/163 客户端排版错乱）：

```python
def wrap_html(body: str) -> str:
    return f"""
    <div style="font-family:-apple-system,sans-serif;max-width:680px;margin:auto;color:#333;line-height:1.6;padding:24px;">
      {body}
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>
      <p style="font-size:12px;color:#999;">本邮件由 AI 助手自动生成于 {now():%Y-%m-%d %H:%M}。</p>
    </div>"""
```

#### 7.7.5 站内信铃铛

顶部导航右侧固定铃铛组件，所有运营页面共享：

```typescript
function NotificationBell() {
  const [unread, setUnread] = useState(0)
  const [open, setOpen] = useState(false)

  useInterval(async () => {
    const { count } = await api.getUnreadCount()
    setUnread(count)
  }, 5000)

  return (
    <Badge count={unread} onClick={() => setOpen(true)}>
      <BellOutlined />
    </Badge>
    // 抽屉/下拉：最近 10 条 + "全部已读" + 点击跳转 /ops/reports/{id}
  )
}
```

#### 7.7.6 报告中心页面（双筛选）

布局：

```
┌─ 报告中心 ───────────────────────────── [立即生成日报][立即生成周报] ─┐
│                                                                       │
│ 类型: ◉全部 ○日报 ○周报     日期范围: [2026-05-01] ~ [2026-05-26]   │

│                                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 标题                          类型  日期范围      生成时间  邮件 │ │
│ │ 美甲品类日报 2026-05-26       日报  05-26         09:00    已发 │ │
│ │ 美甲品类周报 05-19~05-25      周报  05-19~05-25   09:00    已发 │ │
│ │ ...                                                              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

- 类型筛选用 antd `<Radio.Group>`，日期范围用 `<DatePicker.RangePicker>`，两者并列不分前后
- 点击行进入详情页：左侧渲染 Markdown 正文（用 `react-markdown`），右侧显示元信息卡（生成方式、邮件状态、错误信息）
- 右上角两个按钮触发 `POST /api/ops/reports/generate?type=daily|weekly`，调试用

#### 7.7.7 失败处理与重试

- **LLM 调用失败**：记录 `email_status="failed"`，但报告本身入库失败时，整个任务回滚（事务 + 异常抛出），调度器下一次自然触发会重试
- **邮件发送失败**：报告已入库且站内信已发出，仅邮件失败。在报告详情页显示「邮件发送失败：<error>」+ 「重新发送」按钮，调用 `POST /api/ops/reports/{id}/resend`
- **调度漏触发**（如服务器宕机跨过 09:00）：APScheduler 配置 `misfire_grace_time=3600`，1 小时内补跑；超出后由人工点"立即生成"补救
- **同一周期重复生成**：允许，按时间倒序排列；UI 上同一日期的多条用折叠形式显示，避免列表噪音

---

## 8. AI 服务设计

### 8.1 抽象层设计

```python
class ImageGenProvider(ABC):
    @abstractmethod
    async def generate(self, hand_img: bytes, style_ref: bytes, prompt: str) -> bytes: ...

class JimengProvider(ImageGenProvider): ...
class ReplicateProvider(ImageGenProvider): ...
class MockProvider(ImageGenProvider):
    """降级方案：返回预生成图 + 简单叠加"""
```

通过环境变量 `IMAGE_PROVIDER=jimeng|replicate|mock` 切换。Mock 在 API 不可用或开发联调时启用。

### 8.2 推荐场景的 API 选择

| 场景 | 选用 API | 理由 |
|---|---|---|
| 试戴图像生成 | 即梦 AI（字节）API | 国内访问稳定、中文 prompt 友好、按次计费 |
| 试戴备选 | Replicate `lucataco/sdxl-controlnet` | 海外网络可用，ControlNet 保手部细节 |
| 推荐理由（短文本，9×次/请求） | 通义千问 `qwen-turbo` | 便宜、快，单次几十 token 足够 |
| AI 日报 / 周报（长结构化） | 通义千问 `qwen-max` | 复杂指令遵循、结构化输出更稳 |
| AI 助手 Function Calling | 通义千问 `qwen-max` | 工具调用能力成熟 |
| 手部检测/关键点 | MediaPipe Hands（本地） | 浏览器即可跑，零调用成本 |
| 邮件推送 | Python `smtplib`（标准库）+ `markdown` | 零外部依赖，QQ/163 SMTPS 465 端口稳定 |
| 站内信 | 本地 DB + 5 秒前端轮询 | 演示场景轮询足够，无需 WebSocket |
| 定时调度 | APScheduler（进程内） | 无需 Celery beat / 系统 cron / Redis |

### 8.3 试戴生成 Prompt 工程

```
prompt = (
  "Realistic close-up of a {gender} hand, {hand_shape} fingers, {skin_tone} skin, "
  "wearing nail polish in style: {style_description}, "
  "natural lighting, palm facing down, photographic, high detail nail texture"
)
negative = "blurry hand, deformed fingers, extra fingers, low quality, cartoon"
```

配合 ControlNet 时，将用户上传图作为 `canny` 或 `depth` 控制图，保持手部姿态与位置。

### 8.4 性能与成本估算

| 项目 | 单次耗时 | 单次成本（约） |
|---|---|---|
| 单款试戴生成 | 3–8 秒 | ¥0.05–0.15 |
| 4 款并行对比 | 5–10 秒（并行） | ¥0.20–0.60 |
| 推荐理由（9 款批量） | 2–4 秒 | ¥0.01 |
| 日报生成（含邮件发送） | 5–10 秒 | ¥0.05 |
| 周报生成（含邮件发送） | 8–15 秒 | ¥0.08 |
| AI 助手单轮（含工具调用） | 3–8 秒 | ¥0.02–0.05 |

演示阶段总成本可控在 ¥20 内。

---

## 9. Mock 数据构造方案

### 9.1 款式库（40 款 = 25 女 + 15 男）

| 来源 | 数量 | 文件路径 | 打标 JSON |
|---|---|---|---|
| 赛题脱敏数据集（增强版） | 25 女 | `dataset/styles/f_01_enh.png` ~ `f_25_enh.png` | `dataset/styles/tags_qwen.json`（25 个 `f_NN_enh.png` 键） |
| 用户补充的男款图 | 15 男 | `dataset/styles/male/m_01.jpg` ~ `m_15.jpg` | `dataset/styles/male/tags_qwen.json`（15 个 `m_NN.jpg` 键） |

**为什么这样分**：
- 赛题只给了女款，男款是为支持 U1 性别维度差异化由用户从外部补充
- 女款 25 张白底干净、构图统一，是赛题清洗过的标准图，质量足以直接入库
- 试戴生成阶段女款的款式参考与赛题评测输入一致，模型表现的可比性最高
- 男款的风格分布与女款互补（女偏跳色/镶钻/法式，男偏哑光/酷炫/几何/朋克），共同覆盖完整推荐池

**两组的打标分布**（实测）：

| 维度 | 25 女 | 15 男 | 合计 40 |
|---|---|---|---|
| `gender` | 25 female | 15 male（含部分 both） | 25 F + 15 M |
| `color_tone` | 0 cool / 21 neutral / 4 warm | 7 cool / 6 neutral / 2 warm | 7 / 27 / 6 |
| `length_pref` | 1 short / 16 medium / 8 long | 9 short / 6 medium / 0 long | 10 / 22 / 8 |
| 风格热词 | 跳色、镶钻、闪光、法式、复杂图案 | 个性、哑光、纯色、酷炫、几何、商务 | 互补无重叠 |

**关键洞察**：男款的加入让 cool 调与 short 长度从"近零"变成"有量"，推荐算法（§6.3）的肤色/手型适配维度对全谱用户都成立。

**标签生成路径**：
- 女款用 `data-prep/auto_tag_styles.py` 调 PPIO **Qwen2.5-VL-72B-Instruct** 打标（25 次 ≈ ¥0.15）
- 男款用 `data-prep/tag_male_styles.py` 调 PPIO **qwen3-vl-30b-a3b-instruct** 打标（72B 因平台限流降级到 MoE-30B；15 次 ≈ ¥0.05）
- 两份 JSON 由 `backend/scripts/seed_styles.py` 在 seed 时读取，统一写入 `styles` 表

### 9.2 行为数据构造（30 天）

构造 30 天试戴行为时刻意制造爆款/冷门分布，让运营端模块有内容可分析：

| 款式角色 | 数量 | 行为模式 |
|---|---|---|
| 稳定热门款 | 3 款 | 每日试戴 80–150，波动小 |
| 萌芽爆款 | 2 款 | 前 25 天平稳，最后 5 天指数上升（触发爆款识别规则） |
| 冷门款 | 3 款 | 30 天累计试戴 ≤ 20 次（触发冷门预警规则） |
| 长尾普通款 | 17 款 | 试戴量符合长尾分布 |

具体哪几款扮演哪个角色，等打标完成后根据风格分布人工指定（让"萌芽爆款"是视觉上有记忆点的款式，演示更直观）。

**构造脚本** `scripts/seed_mock_data.py`：

```python
def seed():
    import_styles_from_dataset()  # 读 dataset/styles/*_enh.png + auto_tag 输出 JSON → styles 表
    for day in range(30, 0, -1):
        for style in styles:
            count = simulate_count(style, day_offset=day)  # 按角色生成日试戴量
            for _ in range(count):
                user_id = uuid4().hex
                tryons.insert(style.id, user_id, ...)
        aggregate_style_stats(day)  # 写入聚合表
```

### 9.3 实时同步逻辑

用户的真实试戴行为会写入 `tryons` 表，并实时累加到当日 `style_stats`，因此**用户在 C 端选某款 → B 端总览数字+1 → 若触发阈值即出现爆款预警**，构成完整的数据闭环。

---

## 10. 数据闭环与同步机制

### 10.1 闭环路径

```
[U2/U4 试戴行为] → POST /api/tryon → 写 tryons 表
                                     ↓
                              触发器/事件总线
                                     ↓
                         更新 style_stats 当日聚合
                                     ↓
                  [O1 看板] [O2 爆款规则扫描] [O4 日报]
                                     ↓
                         运营执行 reorder/boost
                                     ↓
                       更新 styles.display_order
                                     ↓
                     回到 [U2/U3] 用户看到新顺序
```

### 10.2 实时性保证

- **写时同步**：每次 `tryon` 接口里同步 `UPDATE style_stats SET tryon_count = tryon_count + 1 WHERE style_id=? AND stat_date=today`
- **看板拉取**：运营端首页轮询 `/api/ops/overview`（每 10 秒），现场操作立即可见
- **演示优化**：演示前手动 reset 一遍 mock 数据，确保萌芽爆款的阈值临界，用户随便点几次即可触发预警

### 10.3 写时同步的事务一致性

```python
async def record_tryon(user_id, style_id, ...):
    async with db.transaction():
        await db.execute("INSERT INTO tryons ...")
        await db.execute("""
            INSERT INTO style_stats(style_id, stat_date, tryon_count)
            VALUES(?, date('now','localtime'), 1)
            ON CONFLICT(style_id, stat_date)
            DO UPDATE SET tryon_count = tryon_count + 1
        """)
```

---

## 11. 前端工程规范

### 11.1 目录结构

```
frontend/
├── src/
│   ├── api/              # 接口封装
│   ├── components/       # 通用组件
│   ├── pages/
│   │   ├── user/         # U0–U6
│   │   └── ops/          # O1–O6
│   ├── hooks/
│   ├── store/            # Context + reducers
│   ├── utils/
│   └── App.tsx
├── public/
│   └── samples/          # 示例手部图、款式封面
└── vite.config.ts
```

### 11.2 路由设计

| 路径 | 页面 |
|---|---|
| `/` | 重定向至 `/upload` |
| `/upload` | U0 手图入口 |
| `/gender` | U1 性别选择 |
| `/recommend` | U2 推荐 |
| `/browse` | U3 浏览 |
| `/compare` | U4 对比试戴 |
| `/result/:id` | U5 结果展示 |
| `/history` | U6 历史 |
| `/ops/overview` | O1 |
| `/ops/trending` | O2 |
| `/ops/cold` | O3 |
| `/ops/report` | O4 |
| `/ops/chat` | O5（悬浮，所有 ops 页面共享） |
| `/ops/styles` | O6 |
| `/ops/reports` | O7 报告中心列表 |
| `/ops/reports/:id` | O7 报告详情 |

### 11.3 响应式断点

- 移动端 ≤ 768px：用户端单列布局
- 平板 768–1024px：用户端两列
- 桌面 ≥ 1024px：用户端三列瀑布流，运营端启用完整看板

---

## 12. 团队分工与里程碑

### 12.1 三人分工

| 角色 | 主要负责 | 关键交付 |
|---|---|---|
| PM | 需求/演示/PPT/Mock 数据构造 | seed 脚本 + 演示脚本 + 答辩 PPT |
| 前端 | 用户端 + 运营端所有页面 | React SPA，对接所有接口 |
| 后端/AI | FastAPI + 数据库 + AI 服务对接 | API、推荐算法、AI 接入、Mock seed 配合 |

### 12.2 里程碑（按 5 天 Hackathon 估算）

| Day | 里程碑 | 验收 |
|---|---|---|
| D1 | 技术栈搭起、款式素材 40 张（25 女赛题 + 15 男补充）入库 + 双批 VLM 打标完成、数据库 ER 落地、Mock seed 跑通（60 天数据，含周对比维度） | 数据库可查到 40 款带标签的款式 + 60 天聚合数据，启动接口能返回 styles 列表 |
| D2 | 用户端 U0/U1/U2 跑通（含真实推荐算法 + LLM 理由） | 浏览器可完成"上传手图→选性别→看推荐"完整链路 |
| D3 | U4 多款对比试戴跑通（核心差异化）+ U3/U5 | 单设备可完成完整 C 端流程 |
| D4 | 运营端 O1/O2/O3/O4 全部跑通 + AI 助手 O5 + O7 报告中心（含 APScheduler 定时 + 邮件 + 站内信） | 点"立即生成"后铃铛 5 秒内出现红点 + 邮箱真实收到 HTML 邮件 + reports 表新增一条 |
| D5 | 全链路联调、Mock/Real 切换开关、边界与异常路径走查 | 用户/运营双端完整路径无 bug，关键异常路径有清晰提示 |

### 12.3 P0/P1/P2 取舍

- **D3 结束前必须完成所有 P0**，否则砍 P1
- **U6 / O6 在 D5 仍未完成则改静态展示**
- **O7 邮件发送若被网络封端口**：降级为站内信单通道，报告详情页显示"邮件发送失败"+ 重试按钮（不阻塞核心闭环）

---

## 13. 创新点与差异化

### 13.1 三大创新点（答辩话术）

1. **性别维度的硬隔离推荐**
   行业内首个把性别作为款式池物理分流维度的美甲产品。男性用户不再被淹没在法式甜美款里，从入口即体验差异化。

2. **可解释的多维推荐 + LLM 个性化理由**
   推荐不再是"猜你喜欢"，而是"基于你的肤色冷调 + 修长手型，这款显白且衬肤"。用户每一次推荐都能看到 AI 的判断逻辑，建立信任。

3. **市面首个多款对比试戴**
   解决"比较型决策"用户的真实行为。问小团/Glamlab 等头部产品都不支持，是显著差异点。

### 13.2 双端数据闭环（最大亮点）

不是两个独立系统拼贴，而是**真正的数据闭环**：

- 用户每次试戴 → 实时进入运营统计
- 现场答辩时可邀请评委亲自试戴 → 切换运营端立即看到该款式数据+1
- 这种"看得见的闭环"是评审现场最有说服力的演示设计

### 13.3 AI 自主运营（O7 报告中心叙事）

运营不再是"主动查数据的工具用户"，而是"被动接收 AI 洞察的决策者"：

- **早上 9 点运营还没上班** → AI 已经把昨日数据整理好发到邮箱
- **登录系统** → 通知中心同步显示日报，未读铃铛红点
- **每周一 9 点** → 自动到达包含趋势对比的周报
- **想看历史** → 报告中心按类型 + 日期范围筛选

这套机制把"AI Coding 辅助开发"提升到"AI 自主运营业务"——不只是一个分析工具，而是一个能持续输出洞察、主动推送决策建议的虚拟运营助手。答辩时这是和"自主决策"赛题命题最贴合的应答。

---

## 14. 商业价值论证

### 14.1 量化模型

**假设**：平台美甲品类日活 50 万 UV，当前下单转化率 3%。

| 指标 | 当前 | 引入后预估 | 增量 |
|---|---|---|---|
| 试戴使用率 | 0%（未上线） | 30% | +15 万试戴 UV/日 |
| 试戴用户下单率 | — | 4.5%（高于均值 50%） | — |
| 整体下单转化率 | 3.0% | 3.45% | +15% |
| 日新增订单（按 50 万 UV） | 15,000 | 17,250 | +2,250 单 |

按客单价 ¥80 估算，**日 GMV 增量约 ¥18 万**，年化超 ¥6500 万。

### 14.2 运营效率

- **运营响应时效**：爆款识别从「人工拉数据 3 天」降到「实时 1 小时内」
- **运营人力成本**：日报生成从 2 小时降到 15 分钟，单人节约 87%
- **冷门处理成本**：自动建议每周可识别约 20 款滞销款，减少人工排查

### 14.3 男性市场增量

男性美甲是被严重忽视的增量市场。粗估目前男性消费占比 <5%，性别分流后预计可拉到 10–15%，即 **2–3 倍增量**。

---

## 15. 风险与降级预案

### 15.1 技术风险矩阵

| 风险 | 影响 | 降级预案 |
|---|---|---|
| 图像生成 API 超时/限流 | 高 | 切换 `MockProvider` 返回预生成图 + 款式贴图叠加 |
| 现场网络不稳定 | 高 | 关键演示路径全程录屏备份，关键截图离线 |
| 多款并行生成耗时长 | 中 | 渐进展示 + Loading 骨架屏 + 提前缓存示例用户的结果 |
| LLM 理由偶尔失败 | 中 | fallback 到模板理由「显白显气色」「商务百搭」 |
| SQLite 并发写冲突 | 低 | 加 `BEGIN IMMEDIATE` 事务，演示场景无高并发 |

### 15.2 演示降级方案

提前为 3 个典型用户（女浅肤短指 / 女深肤长指 / 男深肤修长）预生成全套结果，以"示例用户"路径展示时直接走缓存，确保 100% 演示成功率。

### 15.3 进度风险

- **若 D3 未完成 U4**：砍掉 U6，集中火力
- **若 D4 未完成 O5 AI 助手**：改为静态截图 + 视频展示
- **若 D5 仍有 P0 bug**：演示走"安全路径"（即提前彩排好的固定用户路径）

---

## 附录 A · 关键文件清单

```
backend/
├── app/
│   ├── main.py
│   ├── routers/
│   │   ├── user.py        # U0–U6 接口
│   │   └── ops.py         # O1–O7 接口（含报告中心、站内信）
│   ├── services/
│   │   ├── recommend.py   # 推荐算法
│   │   ├── image_gen.py   # ImageGenProvider 抽象 + 实现
│   │   ├── llm.py         # LLM 封装
│   │   ├── stats.py       # 聚合与爆款识别
│   │   ├── report.py      # 日报 / 周报 生成 + 推送链路
│   │   ├── mailer.py      # smtplib + Markdown→HTML 邮件
│   │   ├── notification.py # 站内信写入与读取
│   │   └── scheduler.py   # APScheduler 配置（日报 09:00 / 周报周一 09:00）
│   ├── models.py          # SQLAlchemy 模型
│   └── db.py
├── scripts/                # 产品代码：数据库 seed
│   ├── seed_styles.py      # 40 款入库（女 25 + 男 15，分别从 dataset/styles 与 dataset/styles/male 复制）
│   ├── seed_tryons.py      # 60 天试戴行为模拟（按角色 + 性别 pool 分别生成）
│   ├── seed_stats.py       # 聚合写入 style_stats
│   └── seed_all.py         # 一键入口：建表 + 全部 seed
├── static/
│   ├── styles/             # 40 张款式图（女 f_*_enh.png + 男 m_*.jpg）
│   ├── samples/            # 17 张示例手图（seed 时从 dataset/hands 复制）
│   ├── uploads/            # 用户上传图（运行时生成）
│   └── cache/              # 试戴结果缓存（运行时生成）
└── requirements.txt

frontend/
├── src/
│   ├── pages/user/{Onboarding,Home,Recommend,Browse,Compare,Result,History}.tsx
│   ├── pages/ops/{Overview,Trending,Cold,Report,Chat,Styles,Reports,ReportDetail}.tsx
│   ├── components/{GenderCard,StyleCard,KpiCard,CompareSlider,NotificationBell,...}.tsx
│   └── api/index.ts
└── public/                # 仅放图标 / favicon，示例图由后端 /static/samples 提供

data-prep/                  # 仓库根级，一次性数据准备工具（与产品代码隔离）
├── download_dataset.py     # 从赛题 xlsx 下载 63 张图到 d:\美团AI HACKATHON\dataset\
├── auto_tag_styles.py      # 调 PPIO Qwen2.5-VL-72B 给 25 女款打标 → styles/tags_qwen.json
├── tag_male_styles.py      # 调 PPIO Qwen3-VL-30B-MoE 给 15 男款打标 → styles/male/tags_qwen.json
└── probe_*.py              # PPIO API 连通性 / 模型 ID 探测
```

## 附录 B · 演示话术提纲（8 分钟）

| 时长 | 内容 |
|---|---|
| 0:00–1:00 | 痛点 + 一句话定位 + 竞品对比表 |
| 1:00–4:00 | 用户端完整 Live Demo（性别→上传→推荐→对比→选定） |
| 4:00–6:00 | 运营端 Live Demo（看板→爆款→日报→AI 助手） |
| 6:00–6:30 | 数据闭环演示（用户刚才的选择实时反映到运营端） |
| 6:30–7:30 | 技术亮点 + 商业价值 |
| 7:30–8:00 | 总结 + Q&A |

---

> 文档结束。如需进一步细化任何模块（如完整 OpenAPI yaml、推荐算法权重调参、Mock seed 完整代码），可基于此文档单独展开。
