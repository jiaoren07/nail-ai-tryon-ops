# 美甲 AI 试戴与智能运营 Demo

双端 Web 产品：用户端 AI 试戴流程（上传手图 → 智能推荐 → 试戴/对比 → 收藏）+
运营端智能工作台（实时看板 / 爆款冷门识别 / AI 助手 Function Calling / 自动日报周报），
共享同一条实时数据闭环。设计与构建计划见 `design-docu.md` / `tech-stack.md` / `implementation-plan.md`。

## 启动步骤

**0. 配置 `.env`**（首次）

```
cd backend
copy .env.example .env
```

按注释填入 `PPIO_API_KEY`（必填，LLM/生图共用）与 SMTP 五项 + `REPORT_RECIPIENT`
（可留空：报告仍生成入库，仅邮件标记发送失败）。`IMAGE_PROVIDER=mock` 为默认安全网，
切 `seedream` 走真实生图（约 ¥0.2/张）。

**1. 初始化数据库（seed，可重复执行）**

```
cd backend
.venv\Scripts\python.exe -X utf8 scripts\seed_all.py
```

依赖首次安装：`python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`。
输出 `styles=40 tryons=12847 stats=1432` 即成功。演示数据的时间窗口锚定在 seed 时刻，
隔天演示前请重新执行。

**2. 启动后端（端口 8000）**

```
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

**3. 启动前端（端口 5173）**

```
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`：`/` 为双端入口，用户端从性别选择开始，
运营端在 `/ops/overview`。

## 备注

- LLM/VLM/生图统一走 PPIO（OpenAI 兼容 API）；当前 key 双档均约 5 次/分钟限速，
  AI 助手连续提问建议间隔 30 秒（超限时接口自动降级为数据摘要回复，不会空白）。
- 定时报告（每日 09:00 / 周一 09:00，北京时间）随后端进程运行；`SCHEDULER_ENABLED=false`
  可关闭，O7 设置中心的手动生成按钮不受影响。
- `data-prep/` 为一次性数据集准备脚本，`Meijia/` 为已弃用的早期原型，均非产品代码。
