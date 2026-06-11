# 技术栈推荐

> 基于 [design-docu.md](design-docu.md) 的演示 Demo 定位精简版
> 交付目标：可现场体验的 Demo + 用户端/运营端数据实时同步 + AI 助手自主决策

---

## 0. 选型原则

本项目不是生产系统，是**演示型 Demo**，因此技术选型遵循三条铁律：

1. **零部署偏好** — 能本地跑通就不上云，能 SQLite 就不用 PG，能 API 调用就不本地部署模型
2. **抗演示故障** — 关键链路必须有降级方案，宁可简单稳定不要花哨复杂
3. **AI 优先用云端 API** — 不训练任何模型，不微调，不本地推理，全部走商业 API

凡是会让人忍不住"再做完美一点"的技术（K8s、微服务、向量数据库、消息队列、模型微调）一律不引入。

---

## 1. 技术栈一览

| 层 | 选型 | 版本 | 一句话理由 |
|---|---|---|---|
| **前端框架** | React + Vite | React 19.2 / Vite 8.0（npm latest 实装） | 生态最熟，构建最快 |
| **语言** | TypeScript | 6.0.x | 类型安全，前后端接口对得齐 |
| **路由** | React Router | 7.x | SPA 标配，无需多想 |
| **UI 组件** | Ant Design | 5.x | 运营端表格/抽屉/图表一站搞定 |
| **样式** | Tailwind CSS | 3.4.x（**不要升 v4，v4 PostCSS 集成跟 Vite 8 还在打磨**） | 用户端定制化 UI 写得快 |
| **图表** | ECharts (echarts-for-react) | 5.x | 看板所有图一个库覆盖 |
| **HTTP 客户端** | axios | 1.x | 拦截器统一处理错误，比 fetch 省心 |
| **状态管理** | React Context + useReducer | 内置 | 数据量小，无需 Redux/Zustand |
| **后端框架** | FastAPI | 0.110+ | 自动 OpenAPI 文档，async 原生支持 |
| **后端语言** | Python | 3.11+ | AI API 调用生态最好 |
| **ORM** | SQLAlchemy | 2.0 | 异步支持成熟 |
| **数据库** | SQLite | 内置 | 单文件、零运维、演示完打包就能交付 |
| **数据校验** | Pydantic | v2 | FastAPI 原生集成 |
| **HTTP 调用** | httpx | 0.27+ | 异步调用 AI API |
| **定时任务** | APScheduler | 3.10+ | 进程内 cron 调度，无需 Redis/Celery |
| **邮件发送** | smtplib（标准库）+ markdown | - | 零依赖，Markdown 自动转 HTML 邮件 |
| **图像生成** | Seedream 4.5（PPIO） | API | 多图条件输入（手图 + 款式图作两个参考），共用 PPIO key，~¥0.2/张 |
| **LLM 供应商** | PPIO 一家全包 | OpenAI 兼容 API | VLM/LLM 都已验证可用，省一个 dashscope 注册 |
| **LLM (短文本)** | `qwen/qwen3-next-80b-a3b-instruct`（PPIO） | API | 推荐理由生成，9 条/请求，便宜快 |
| **LLM (复杂)** | `deepseek/deepseek-v4-pro`（PPIO） | API | 日报/周报/Function Calling，结构化输出稳 |
| **手部识别** | 手动 mock + 简单色彩分析 | - | 演示不需要真识别，直接预设几套特征 |
| **包管理 (前)** | pnpm | 9.x | 比 npm 快，节省磁盘 |
| **包管理 (后)** | uv 或 pip | uv 0.4+ | uv 安装快 10×，pip 兜底 |

---

## 2. 前端选型详解

### 2.1 为什么是 React + Vite

- Hackathon 场景下 React 招人最容易，三人协作沟通成本低
- Vite 冷启动 < 2 秒，HMR 几乎即时，调试效率高
- TypeScript 让前后端字段对齐零负担（直接复用 Pydantic 生成的类型）

### 2.2 UI 库：Ant Design + Tailwind 混用

| 用在哪 | 用 antd | 用 tailwind |
|---|---|---|
| L0 双端入口 + 用户端（U0–U6） | 少量基础组件（Upload、Modal） | 大部分定制 UI 用 tw 写 |
| 运营端（O1–O7） | 表格、抽屉、卡片、Statistic、Tabs | 仅做布局微调 |

**理由**：运营端需要复杂表格、筛选器、抽屉，自己写 ROI 极低；用户端 UI 视觉化强，antd 默认样式不够灵活，用 tw 自由发挥。

**颜色统一**：两端共用同一套品牌色板（§2.5），用户端通过 Tailwind class 引用、运营端通过 antd ConfigProvider token 引用；同一份十六进制只在 §2.5 一处声明。

### 2.3 状态管理：不用 Redux/Zustand

- 全局只需要 4 个状态：`userGender`、`userId`、`handFeatures`、`selectedStylesForCompare`
- `React.Context` + `useReducer` 完全够用
- 引入 Redux 反而是过度工程

### 2.4 关键第三方库

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "antd": "^5.16.0",
    "@ant-design/icons": "^5.3.0",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.2",
    "axios": "^1.6.0",
    "react-compare-image": "^3.4.0",
    "browser-image-compression": "^2.0.2",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### 2.5 品牌色板与设计变量

> Single source of truth：所有颜色定义集中在此处。`frontend/tailwind.config.js`（用户端）与 antd `ConfigProvider` token（运营端）都从这里 derive，不在其他文档或代码里另定 hex。

**核心记忆点**（5 色 = 一眼能记住的品牌印象）：

| 用途 | Hex | 备注 |
|---|---|---|
| Primary Yellow | `#FFD100` | 品牌主色，CTA 按钮、徽章、高亮 |
| Primary Text | `#111111` | 主文案（不是纯黑色 #000） |
| Page Background | `#FAF8F2` | 页面底色（米白，不是纯白） |
| Card Background | `#FFFFFF` | 卡片浮起色，在米白底上凸出 |
| AI Purple | `#7C5CFF` | AI 相关元素的辨识色（AI 头像、对话气泡、AI 标识徽章） |

**完整色板**：

| 类别 | Token | Hex |
|---|---|---|
| Brand | brand / brand.hover / brand.light | `#FFD100` / `#F6C400` / `#FFF3C4` |
| Surface | page / card / surface | `#FAF8F2` / `#FFFFFF` / `#F6F7F9` |
| Text | ink (DEFAULT) / ink.secondary / ink.muted | `#111111` / `#555555` / `#8A8A8A` |
| Line | line (border) | `#E6E6E6` |
| AI | ai.purple / ai.blue / ai.wash | `#7C5CFF` / `#28A8FF` / `#F4F0FF` |
| Semantic | success / warning / danger / info | `#16A34A` / `#F97316` / `#EF4444` / `#3B82F6` |

**Tailwind config（用户端 + L0 入口）**：

```js
// frontend/tailwind.config.js
theme: { extend: { colors: {
  brand: { DEFAULT:'#FFD100', hover:'#F6C400', light:'#FFF3C4' },
  page: '#FAF8F2', card: '#FFFFFF', surface: '#F6F7F9',
  ink:  { DEFAULT:'#111111', secondary:'#555555', muted:'#8A8A8A' },
  line: '#E6E6E6',
  ai:   { purple:'#7C5CFF', blue:'#28A8FF', wash:'#F4F0FF' },
  success:'#16A34A', warning:'#F97316', danger:'#EF4444', info:'#3B82F6',
}}}
```

**antd ConfigProvider token（运营端）**：

```jsx
<ConfigProvider theme={{
  token: {
    colorPrimary:      '#FFD100',
    colorPrimaryHover: '#F6C400',
    colorBgBase:       '#FAF8F2',
    colorBgContainer:  '#FFFFFF',
    colorBgLayout:     '#F6F7F9',
    colorText:         '#111111',
    colorTextSecondary:'#555555',
    colorTextTertiary: '#8A8A8A',
    colorBorder:       '#E6E6E6',
    colorSuccess:      '#16A34A',
    colorWarning:      '#F97316',
    colorError:        '#EF4444',
    colorInfo:         '#3B82F6',
  },
}}>
```

AI 紫不是 antd 标准 token——在 `frontend/src/index.css` 全局 `:root` 加 CSS var：`--ai-purple: #7C5CFF; --ai-wash: #F4F0FF;`，运营端组件需要时通过 `style={{ color: 'var(--ai-purple)' }}` 引用。

**统一规则**：
- 用户端组件颜色一律走 Tailwind class（`bg-brand`、`text-ink`、`border-line`）；不写裸 hex
- 运营端组件优先用 antd token；需要 AI 紫时通过 CSS var 引用
- 禁止在组件文件里 hard-code 颜色值——新颜色需求一律先回到 §2.5 加 token，再在两端配置文件里同步
- 设计稿如出现本表外的颜色，先停下来核对，不要默默引入

---

## 3. 后端选型详解

### 3.1 为什么是 FastAPI 而非 Flask/Django

- **自动生成 OpenAPI 文档**：`/docs` 即时调试，省一份接口文档
- **原生 async**：AI API 调用全是 IO 密集，async 必备
- **Pydantic 集成**：前后端类型对齐零成本
- Django 太重；Flask 缺 async 和 Pydantic 默认集成

### 3.2 为什么不用任务队列（Celery / RQ）

原始 PRD 提到"多款并行试戴"，本能反应会想到任务队列。**对演示场景，asyncio.gather 完全够用**：

```python
async def batch_tryon(photo, style_ids):
    return await asyncio.gather(*[
        generate_one(photo, sid) for sid in style_ids
    ])
```

- 单机演示无需横向扩展
- 不需要 Redis broker
- 不需要 worker 进程
- 不需要任务结果持久化

引入 Celery 等于多一个失败点。

**那定时任务呢？** 用 `APScheduler` 即可——它是进程内调度库，跟着 FastAPI 进程一起跑，不需要独立 worker、不需要 Redis、不需要数据库 broker。日报/周报这种每天/每周触发一次的场景完全够用：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()
scheduler.add_job(generate_daily_report,  CronTrigger(hour=9, minute=0), id='daily')
scheduler.add_job(generate_weekly_report, CronTrigger(day_of_week='mon', hour=9), id='weekly')
scheduler.start()
```

### 3.3 为什么不用 SSE/WebSocket 做流式

最初设计文档里提到 SSE 渐进展示。**演示 Demo 用普通 HTTP 多并发请求即可**：

- 前端发起 N 个并发 `POST /api/tryon` 请求
- axios 自带 Promise.all 处理
- 每个请求独立 loading 状态
- 单款失败不影响其他

理由：SSE/WebSocket 在 Demo 现场反而容易因网络抖动出问题。

### 3.4 关键 Python 依赖

```txt
# Py 3.13.2 实际安装版本（Step 0.2 by pip freeze 锁定）
fastapi==0.136.3
uvicorn[standard]==0.48.0
sqlalchemy==2.0.50
aiosqlite==0.22.1
pydantic==2.13.4
pydantic-settings==2.14.1
python-multipart==0.0.29
httpx==0.28.1
python-dotenv==1.2.2
pillow==12.2.0
openai==2.38.0             # PPIO 使用 OpenAI 兼容 API（不是真用 OpenAI）
apscheduler==3.11.2        # 定时任务调度
markdown==3.10.2           # Markdown 转 HTML（邮件正文）
```

> ⚠️ **不要回到 2024 年的旧版本**（pillow 10.x、pydantic 2.6 等）。Py 3.13 上这些版本没有预编译 wheel，会触发 Rust / C 源码编译失败。完整 lockfile 见 `backend/requirements.txt`（含传递依赖共 37 行）。

---

## 4. AI 服务选型详解

### 4.1 完整 AI 调用矩阵

所有 LLM/VLM 通过 **PPIO 派欧云** 一家供应商接入（OpenAI 兼容 API，base URL `https://api.ppio.com/openai`）。

| 用途 | PPIO model ID | API 单价（参考） | 调用频率（演示） |
|---|---|---|---|
| 试戴图像生成 | `seedream-4.5`（PPIO 平台，字节系图像模型） | ~¥0.2/张 | 每次试戴 1 次 |
| 推荐理由生成 | `qwen/qwen3-next-80b-a3b-instruct` | ~¥0.002/千 token | 推荐时批量 9 条 |
| 日报 / 周报生成 | `deepseek/deepseek-v4-pro` | ~¥0.004/千 token | 每日 1 次 + 每周 1 次 |
| AI 助手对话（Function Calling）| `deepseek/deepseek-v4-pro` | ~¥0.004/千 token | 演示时 5–10 次 |
| 款式打标（一次性，已完成）| `qwen/qwen2.5-vl-72b-instruct` / `qwen/qwen3-vl-30b-a3b-instruct` | — | 40 次（一次性） |
| 手部分析 | **不调用任何 AI** | — | mock |

### 4.2 关键决策：手部分析直接 Mock

PRD 里的"肤色识别、手型分类"听起来很 AI，**演示场景完全可以 mock**：

**简化方案**：
- 用户上传图片 → 后端用 PIL 取一小块手部区域的平均 RGB → 按阈值映射到 5 种肤色枚举
- 手型分类直接根据上传图的"示例 ID"返回预设值（示例图是固定的）
- 用户自己上传的图，统一返回 `("medium", "average")`

**理由**：
- 真做手部关键点检测需引入 MediaPipe 或 OpenCV，增加部署复杂度
- 演示场景用户感知不到识别准确度，只要"看起来在分析"就够
- 节省 2 天开发时间

### 4.3 AI 厂商选型理由

**为什么 LLM 全走 PPIO 而非 dashscope（通义千问官方 SDK）？**
- PPIO 已经在用（VLM 打标链路已验证），无需再注册第二个供应商
- PPIO 模型库覆盖通义全家桶 + DeepSeek + GLM + Kimi 等，按需挑选
- OpenAI 兼容 API（base URL `https://api.ppio.com/openai`），与 OpenAI SDK 直接对接，无需厂商专用 SDK
- 单 key 走完所有 LLM/VLM 调用，配置最简

**为什么短文本用 qwen3-next-80b、复杂任务用 deepseek-v4-pro？**
- qwen3-next-80b-a3b-instruct 是 MoE 架构（80B 总参数，激活 3B），benchmark 实测 ~1.9-3.8s 响应，"推荐理由 9 条/请求"这种短输出场景跑得稳定
- deepseek-v4-pro 是 DeepSeek 旗舰，Function Calling 1.8-6.1s 实测稳定（早期 cold-start 时偶尔 30s+ 超时是 PPIO 瞬时问题）；1M token context 对未来"周报拼一周数据让 AI 写综述"有天然优势
- 模型 ID 通过 `.env` 中的 `LLM_QUICK_MODEL` 和 `LLM_STRONG_MODEL` 暴露，必要时可热切换。早期 plan 写过 `qwen/qwen2.5-7b-instruct` + `deepseek/deepseek-v3.1`，benchmark 发现 7b 已被 PPIO 下线、v3.1 仍可用但 v4-pro 更接近未来方向，故升级
- 两个 model ID 都通过 `.env` 中的 `LLM_QUICK_MODEL` 和 `LLM_STRONG_MODEL` 暴露，必要时可热切换

**为什么图像生成走 PPIO 的 Seedream 而非火山方舟即梦或其他？**
- PPIO 提供 Seedream 4.0 / 4.5 / 5.0-lite，**和 LLM 共用同一个 `PPIO_API_KEY`**，省去单独注册火山方舟实名认证
- Seedream 系列**支持多图条件输入**（手图 + 款式图同时喂进去作两个参考），其他文生图模型（即梦文生图 3.0/3.1、Qwen-Image 文生图）只能接受文字提示
- benchmark 实测 Seedream 4.5 在肤色保真度上优于 4.0（4.0 over-darken）和 5.0-lite（对深色手图触发安全过滤拒绝）；同时优于 Qwen-Image-Edit（只接受单张输入图，无法把款式作为视觉参考）
- 详细对比依据见 progress.md Step 3.2

**降级最终保底**：所有 AI 调用都包一层 `MockProvider`，无网络/无 key 时返回款式封面复制图作为试戴结果，演示链路不中断。

### 4.4 抽象层代码骨架

```python
# backend/app/services/image_gen.py
from abc import ABC, abstractmethod
from app.config import settings

class ImageGenProvider(ABC):
    @abstractmethod
    async def generate(
        self, user_id: str, style_id: str,
        hand_image_bytes: bytes, prompt_extra: str | None = None,
    ) -> str: ...

class SeedreamProvider(ImageGenProvider):
    """走 PPIO 的 Seedream 4.5：用户手图 + 款式封面作两个 reference，
    生成结果存到 /static/cache/seedream_<...>.png，返回相对 URL。"""

class MockProvider(ImageGenProvider):
    """降级：把款式封面直接复制到 /static/cache/ 当试戴结果。
    永远能跑，不依赖任何外部 API。"""

def get_image_provider() -> ImageGenProvider:
    name = settings.IMAGE_PROVIDER.lower()
    if name == "mock": return MockProvider()
    if name == "seedream": return SeedreamProvider()
    raise ImageGenError(f"unknown IMAGE_PROVIDER: {name!r}")
```

通过环境变量切换：`IMAGE_PROVIDER=mock`（默认）/ `IMAGE_PROVIDER=seedream`（真合成）。Mock 是兜底，永远可用。

---

## 5. 数据库与存储

### 5.1 为什么 SQLite

- 单文件，演示完直接 `nail_demo.db` 打包交付
- Python 内置 `aiosqlite`，无需独立进程
- 三人开发不会有并发冲突
- 表结构变化用 `alembic` 管理，或者更简单：drop 重建 + seed 脚本

### 5.2 数据同步机制（核心）

用户端 → 运营端数据同步采用**写时同步 + 轮询查询**，无需消息队列：

```python
# 用户每次试戴时，事务内同时更新两张表
async def record_tryon(user_id, style_id, ...):
    async with db.begin():
        await db.execute(insert_tryons(...))
        await db.execute("""
            INSERT INTO style_stats(style_id, stat_date, tryon_count)
            VALUES(:sid, date('now','localtime'), 1)
            ON CONFLICT(style_id, stat_date)
            DO UPDATE SET tryon_count = tryon_count + 1
        """)
```

运营端轮询：

```typescript
// 每 5 秒拉一次总览数据，演示现场实时性足够
useInterval(() => fetchOpsOverview(), 5000)
```

### 5.3 静态资源存储

- 款式封面图：`backend/static/styles/*.png`（seed 时从 `dataset/styles/*_enh.png` 复制）
- 示例手部图：`backend/static/samples/*.png`（seed 时从 `dataset/hands/*.png` 复制；前端通过 `http://localhost:8000/static/samples/01.png` 访问，不在 `frontend/public/` 放二份）
- 用户上传图：`backend/static/uploads/{user_id}_{时间戳}.{ext}`
- 试戴结果缓存：`backend/static/cache/{user_id}_{style_id}.png`

无需 OSS/S3，本地文件系统足够。

---

## 6. AI 助手自主决策的实现

> 这是用户特别强调的能力，单独列出实现方案

### 6.1 自主决策的两种触发方式

| 类型 | 触发方式 | 实现 |
|---|---|---|
| **规则触发** | 数据满足阈值即触发 | 后端定时扫描 + 规则匹配 |
| **LLM 触发** | 运营点击"生成日报"等操作 | LLM Function Calling |

### 6.2 规则触发（无需 LLM，零成本）

```python
# backend/app/services/auto_decision.py
async def auto_rerank_styles():
    """根据近 7 天试戴量自动重排款式 display_order"""
    rows = await db.fetch_all("""
        SELECT style_id, SUM(tryon_count) AS recent_count
        FROM style_stats
        WHERE stat_date >= date('now','-7 days')
        GROUP BY style_id
        ORDER BY recent_count DESC
    """)
    for rank, row in enumerate(rows):
        await db.execute(
            "UPDATE styles SET display_order = :r WHERE id = :sid",
            {"r": rank, "sid": row["style_id"]}
        )

async def detect_trending():
    """爆款识别 + 自动写入运营动作日志"""
    trending = await find_trending_styles()
    for style in trending:
        await db.execute(insert_ops_action(
            style_id=style.id,
            action_type="boost",
            reason=f"近 3 天增长率 {style.growth_rate:.0%}，自动提升推荐位"
        ))
```

**触发时机**：
- 每次用户试戴后异步触发一次（轻量，无需定时器）
- 或者运营端访问"看板"时同步触发一次（保证数据新鲜）

### 6.3 LLM 触发（用 Function Calling）

运营在 AI 助手里说"把本周爆款提到首页"：

```
用户: "把本周爆款全部提到首页推荐"
  ↓
LLM 决定调用: find_trending(growth_threshold=0.5, min_volume=50)
  ↓
后端返回: [{style_id:"f_007", growth:0.8}, ...]
  ↓
LLM 决定调用: execute_action(style_id="f_007", action_type="boost")
  ↓
后端执行: UPDATE styles SET display_order = 0 WHERE id="f_007"
       + INSERT ops_actions(...)
  ↓
LLM 返回: "已将 3 款爆款提至首页推荐位顶部，新的排序已生效。"
```

效果：用户端立即刷新就能看到调整。

### 6.4 日报 / 周报：定时生成 + 邮件 + 站内信

日报/周报由 **APScheduler 定时触发**，生成后同时：
1. 写入 `reports` 表（产品内 O7 设置中心的「通知与邮件订阅」tab 可查看历史，详见 [design-docu.md §7.7.6](design-docu.md)）
2. 写入 `notifications` 表（前端铃铛红点提醒）
3. 通过 SMTP 发送 HTML 邮件到指定运营邮箱

**完整流程**

```python
async def generate_and_dispatch_report(report_type: str):
    # 1. 数据聚合
    if report_type == "daily":
        data = await aggregate_stats(start=today(), end=today())
        prompt = build_daily_prompt(data)
        title = f"美甲品类日报 {today():%Y-%m-%d}"
    else:  # weekly
        data = await aggregate_stats(start=last_monday(), end=last_sunday())
        prompt = build_weekly_prompt(data)
        title = f"美甲品类周报 {last_monday():%Y-%m-%d} ~ {last_sunday():%Y-%m-%d}"

    # 2. LLM 生成 Markdown
    content_md = await llm.chat(prompt, model=settings.LLM_STRONG_MODEL)

    # 3. 持久化
    report = await db.insert_report(
        type=report_type, title=title, content_md=content_md,
        period_start=data.start, period_end=data.end,
        trigger_source="scheduled"
    )

    # 4. 站内信
    await db.insert_notification(
        type="report", ref_id=report.id, title=title,
        summary=content_md[:120]
    )

    # 5. 邮件
    await send_email(
        to=settings.REPORT_RECIPIENT,
        subject=title,
        html_body=markdown.markdown(content_md, extensions=['tables']),
        text_body=content_md  # 纯文本兜底
    )
```

**调度配置**

| 任务 | 触发时机 | Cron 表达式 |
|---|---|---|
| 日报 | 每天 09:00 | `hour=9, minute=0` |
| 周报 | 每周一 09:00 | `day_of_week='mon', hour=9, minute=0` |

**演示兜底：手动立即触发**

```
POST /api/ops/reports/generate?type=daily   # 立即执行一次
POST /api/ops/reports/generate?type=weekly
```

UI 在 O7 设置中心 →「通知与邮件订阅」tab 下半区放两个按钮：「立即生成日报」「立即生成周报」。点击后走的是和定时任务**完全相同的代码路径**——生成 → 入库 → 站内信 → 邮件，只是 `trigger_source` 字段标记为 `"manual"`。

> 这条手动触发链路的存在是为了让"定时器跑出来的内容"可以被实时验证：日报/周报实际是定时任务在 09:00 自动跑的，开发与排错时不可能等到第二天 9 点，所以提供一个走相同代码路径的手动入口。

### 6.5 邮件发送实现

用 Python 标准库，零额外依赖：

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

async def send_email(to: str, subject: str, html_body: str, text_body: str):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = settings.SMTP_FROM
    msg['To'] = to
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(wrap_html(html_body), 'html', 'utf-8'))  # 加 inline CSS

    with smtplib.SMTP_SSL(settings.SMTP_HOST, 465) as srv:
        srv.login(settings.SMTP_USER, settings.SMTP_PASS)
        srv.send_message(msg)
```

**推荐用 QQ/163 邮箱的 465 端口**（SMTPS）：
- 端口被会场 wifi 封的概率低
- 不需要 STARTTLS 协商
- 授权码在邮箱网页设置里申请，**不是登录密码**

**HTML 邮件排版**：用 inline CSS 简单包装，避免 QQ/163 客户端渲染错乱：

```python
def wrap_html(body_html: str) -> str:
    return f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 680px; margin: auto; color: #333; line-height: 1.6;">
      {body_html}
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;"/>
      <p style="font-size: 12px; color: #999;">本邮件由 AI 助手自动生成。</p>
    </div>
    """
```

### 6.6 站内信实现

不用 WebSocket，**前端 5 秒轮询未读数**即可：

```typescript
// 顶部铃铛组件
useInterval(async () => {
  const { unread } = await api.getUnreadCount()
  setUnreadCount(unread)
}, 5000)
```

后端只需 3 个接口：
- `GET /api/ops/notifications/unread-count` — 红点数字
- `GET /api/ops/notifications?limit=10` — 下拉列表
- `POST /api/ops/notifications/{id}/read` — 标记已读

演示效果：手动触发"立即生成" → 5 秒内铃铛出现红点 → 点击下拉 → 跳转报告详情。

---

## 7. 演示部署方案

### 7.1 最简部署：本地运行

```bash
# 后端（终端 1）
cd backend
uv pip install -r requirements.txt
python scripts/seed_all.py         # 一键 seed：建表 + 40 款入库（25 女 + 15 男）+ 60 天行为 + 聚合
uvicorn app.main:app --reload --port 8000

# 前端（终端 2）
cd frontend
pnpm install
pnpm dev                            # 默认 5173 端口
```

浏览器打开 `http://localhost:5173` 即可演示。

### 7.2 可选：云端备份部署

防止现场网络问题，准备一份云端备份：

| 服务 | 平台 | 免费额度 |
|---|---|---|
| 前端 | Vercel / Cloudflare Pages | 充足 |
| 后端 | Railway / Render | 500 小时/月 |
| 数据库 | 直接打包 sqlite 文件部署 | 0 |

部署只需 30 分钟，作为现场网络故障兜底。

### 7.3 必备的环境变量

```bash
# backend/.env
IMAGE_PROVIDER=mock                                # mock（默认，复制款式封面）/ seedream（PPIO 真合成）
PPIO_API_KEY=sk_xxx                                # 全部 LLM/VLM/图像生成 共用
PPIO_BASE_URL=https://api.ppio.com/openai
LLM_QUICK_MODEL=qwen/qwen3-next-80b-a3b-instruct   # 短文本（推荐理由）
LLM_STRONG_MODEL=deepseek/deepseek-v4-pro          # 复杂（日报、Function Calling）
DATABASE_URL=sqlite+aiosqlite:///./nail_demo.db

# 邮件（用 QQ/163 都行）
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_account@qq.com
SMTP_PASS=xxxxxxxxxxxxxxxx                  # 邮箱授权码，不是登录密码
SMTP_FROM=your_account@qq.com
REPORT_RECIPIENT=operator@example.com       # 演示用接收邮箱

# 调度开关（演示时可关闭定时，只保留手动触发）
SCHEDULER_ENABLED=true
```

> ⚠️ **邮箱授权码获取**：QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 开启 → 生成授权码（16 位）。163 流程类似。Gmail 需开两步验证后生成应用专用密码。

---

## 8. 明确不引入的技术（对比清单）

| 不引入 | 原因 |
|---|---|
| Redux / Zustand / MobX | 4 个全局状态用 Context 够了 |
| Celery / RQ / Redis | 并行用 asyncio.gather，定时用 APScheduler 进程内调度，都不需要外部 broker |
| WebSocket / SSE | 普通 HTTP 多并发请求更稳；站内信用 5 秒轮询代替 |
| Nginx | 演示场景不需要反向代理 |
| Docker | 本地 venv + pnpm install 5 分钟搞定 |
| MediaPipe / OpenCV | 手部识别 mock 化，演示场景无感 |
| 向量数据库（Pinecone/Milvus） | 推荐是规则打分，不需要 embedding |
| 模型微调 / LoRA | 全部用现成 API |
| 本地部署 Stable Diffusion | 不需要 GPU 服务器 |
| Kubernetes / Docker Compose | 单机 Demo 不存在编排 |
| 用户认证 (OAuth/JWT) | 匿名 UUID 足够 |
| Sentry / Datadog | Demo 不需要监控 |
| ESLint 严格配置 | 时间不够，能跑就行 |
| 单元测试 (Jest/pytest) | Demo 用人工冒烟测试代替 |
| Storybook | UI 组件少，无需独立调试 |

---

## 9. 推荐的开发节奏

| 时间 | 后端 | 前端 |
|---|---|---|
| D1 上午 | 项目骨架 + 数据库表 + seed 脚本 | 项目骨架 + 路由 + UI 库接入 |
| D1 下午 | 用户端基础接口（styles、recommend、tryon） | L0 双端入口 + U0 性别 + U1 上传页面 |
| D2 | AI 服务接入（Seedream 图像 + PPIO LLM） | U2 智能推荐页（核心差异化） |
| D3 | 运营端接口（overview、trending、cold） | U4 多款对比试戴（核心差异化） |
| D4 | AI 日报 + Function Calling 助手 | 运营端 O1–O4 看板 |
| D5 | 联调 + 降级开关 + 演示数据微调 | 联调 + 走查 + 演示彩排 |

---

## 10. 立即可用的初始化命令

```bash
# 创建仓库结构
mkdir -p nail-ai-demo/{backend,frontend}
cd nail-ai-demo

# 后端
cd backend
uv venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
uv pip install fastapi uvicorn[standard] sqlalchemy aiosqlite \
  pydantic pydantic-settings python-multipart httpx \
  python-dotenv pillow openai apscheduler markdown

# 前端
cd ../frontend
pnpm create vite@latest . -- --template react-ts
pnpm install
pnpm add antd @ant-design/icons echarts echarts-for-react \
  react-router-dom axios react-compare-image \
  browser-image-compression dayjs
pnpm add -D tailwindcss postcss autoprefixer
pnpm dlx tailwindcss init -p
```

---

## 附录 · 选型决策对照表

| 问题 | 备选方案 | 选定 | 理由 |
|---|---|---|---|
| 前端框架 | React / Vue / Next.js | **React + Vite** | 团队最熟，生态最大 |
| UI 库 | antd / Material-UI / 自写 | **antd + Tailwind 混用** | 运营端用 antd 省力，用户端用 tw 灵活 |
| 后端语言 | Python / Node.js / Go | **Python** | AI API SDK 最全 |
| 后端框架 | FastAPI / Flask / Django | **FastAPI** | async + 自动文档 |
| 数据库 | SQLite / MySQL / PostgreSQL | **SQLite** | 零部署 |
| 图像生成 | Seedream 4.0/4.5/5.0-lite / 即梦文生图 / Qwen-Image-Edit / 火山方舟即梦 | **Seedream 4.5（PPIO）+ Mock（降级）** | 多图条件输入 + 肤色保真 + 共用 PPIO key（实测对比详情见 progress.md Step 3.2）|
| LLM 供应商 | dashscope / PPIO / 直连各厂 | **PPIO 一家全包** | OpenAI 兼容、模型库全、单 key 跑完整链路 |
| LLM 模型选 | qwen / DeepSeek / GLM / Claude | **qwen3-next-80b-a3b-instruct（短）+ deepseek-v4-pro（强）** | benchmark 实测 1-6s 响应稳定，FC 支持成熟 |
| 手部分析 | MediaPipe / OpenCV / 云端 API / Mock | **Mock** | 演示无感，省 2 天 |
| 并发任务 | Celery / asyncio / 同步 | **asyncio** | 演示足够 |
| 定时任务 | Celery beat / 系统 cron / APScheduler | **APScheduler** | 进程内调度，零外部依赖 |
| 邮件推送 | 三方 SDK / smtplib / Webhook | **smtplib + markdown** | Python 标准库，零依赖 |
| 消息提醒 | WebSocket / SSE / 轮询 | **5 秒轮询** | 演示场景轮询足够，更稳 |
| 部署 | Docker / 直接运行 / 云函数 | **本地 + 云备份** | 现场网络风险可控 |

---

> 文档结束。本技术栈针对"演示 Demo"目标做了大量减法，砍掉了所有生产级冗余设计。如果项目后续要走向生产化，可参考 design-docu.md 中的扩展路径，但 Hackathon 阶段坚持精简。
