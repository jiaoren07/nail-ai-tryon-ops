# 公开部署手册（云主机单机版）

目标：一台便宜的国内轻量云主机，跑出一个任何人可访问的 `http://<服务器IP>` 链接。
代码侧的部署改造（单一来源、每日自愈 reseed、生图额度护栏）已经完成，
本文只剩服务器上的操作。

## 0. 买什么

- 腾讯云/阿里云 **轻量应用服务器**：2 核 2G、3–5Mbps 即可，选国内区域（上海/广州），
  学生/新用户活动价通常每月几十元
- 系统镜像选 **Ubuntu 22.04 LTS**（下文命令以它为准）
- 无需域名：裸 IP 直接访问，不涉及备案。若日后想要域名+HTTPS，选**香港区域**的机器
  可绑域名免备案（大陆访问稍慢），或走大陆域名备案流程
- 买好后在控制台防火墙放行 **80 端口**（TCP）

## 1. 服务器初始化（SSH 登录后逐段执行）

```bash
# 基础依赖：Python 3.11+、Node 20（构建前端用）、git
sudo apt update && sudo apt install -y python3-venv python3-pip git curl
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 拉代码
git clone https://github.com/jiaoren07/nail-ai-tryon-ops.git /opt/nail
cd /opt/nail
```

## 2. 配置与构建

```bash
# 后端环境
cd /opt/nail/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# .env（把 <> 换成真实值；SMTP 五项可留空 = 邮件仅标记失败）
cp .env.example .env
nano .env
#   PPIO_API_KEY=<你的 key>
#   IMAGE_PROVIDER=seedream        # 想让访客看真实生成就开；纯免费演示就保持 mock
#   SEEDREAM_DAILY_QUOTA=30        # 每天最多真实生成张数（约 ¥6/天封顶）
#   DAILY_RESEED=true              # 公开站必开：每晚 04:30 自愈
#   SCHEDULER_ENABLED=true

# 种子数据（图片随仓库自带）
.venv/bin/python -X utf8 scripts/seed_all.py

# 前端构建（构建产物由后端直接托管，单端口无跨域）
cd /opt/nail/frontend
npm install && npm run build
```

## 3. 以服务方式常驻（80 端口）

```bash
sudo tee /etc/systemd/system/nail.service > /dev/null <<'EOF'
[Unit]
Description=nail-ai-tryon-ops
After=network.target

[Service]
WorkingDirectory=/opt/nail/backend
ExecStart=/opt/nail/backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 80
Restart=always
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now nail
sudo systemctl status nail --no-pager   # 应显示 active (running)
```

## 4. 验收

浏览器打开 `http://<服务器IP>`：

1. 首页双端入口正常，走一次上传→推荐→试戴
2. 直接访问 `http://<IP>/ops/overview` （深链刷新不 404 = SPA 托管正常）
3. 次日再看：数据被夜间 reseed 重置为新鲜状态

## 5. 日常运维

```bash
sudo systemctl restart nail        # 改配置后重启
sudo journalctl -u nail -f         # 看实时日志
cd /opt/nail && git pull && cd frontend && npm run build && sudo systemctl restart nail   # 升级版本
```

## 风险与护栏（已内置）

| 风险 | 护栏 |
|---|---|
| 访客乱按运营端（下架/排序） | 每晚 04:30 自动 reseed 复原（DAILY_RESEED=true） |
| 访客狂刷真实生图烧钱 | SEEDREAM_DAILY_QUOTA 封顶，超出静默降级 mock 并记入 O7 健康面板 |
| 访客刷爆 LLM | PPIO 每分钟限速天然节流 + 所有调用点自带降级文案 |
| 运营端无登录 | demo 定位接受；数据每晚自愈，无持久损害面 |
