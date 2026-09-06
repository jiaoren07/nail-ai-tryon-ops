import {
  FileTextOutlined,
  MailOutlined,
  ReloadOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Checkbox,
  Empty,
  Input,
  Switch,
  Table,
  Tabs,
  Tag,
} from "antd";
import type { TableProps } from "antd";
import { isAxiosError } from "axios";
import dayjs from "dayjs";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api/client";
import { EMAIL_STATUS_TAG } from "./reportStatus";

interface ReportItem {
  id: number;
  type: "daily" | "weekly";
  title: string;
  period_start: string;
  period_end: string;
  trigger_source: string;
  email_status: "pending" | "sent" | "failed";
  generated_at: string | null;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

/** Subscription prefs are front-end only per design-docu §7.7.6 —
 * localStorage, NOT the backend REPORT_RECIPIENT (that's the fallback). */
const SUBSCRIPTION_KEY = "ops_email_subscription";

interface Subscription {
  enabled: boolean;
  email: string;
  frequencies: string[];
}

function loadSubscription(): Subscription {
  try {
    const raw = localStorage.getItem(SUBSCRIPTION_KEY);
    if (raw) return JSON.parse(raw) as Subscription;
  } catch {
    // corrupted storage -> defaults
  }
  return { enabled: true, email: "", frequencies: ["daily", "weekly"] };
}

interface HealthService {
  ok: number;
  fail: number;
  last_ok_at: string | null;
  last_fail_at: string | null;
  last_fail_reason: string | null;
}

interface HealthStats {
  started_at: string;
  uptime_seconds: number;
  services: Record<string, HealthService>;
  degradations: Array<{ at: string; source: string; reason: string }>;
  image_provider: string;
  scheduler_enabled: boolean;
  scheduler_running: boolean;
  llm_quick_model: string;
  llm_strong_model: string;
}

const SERVICE_LABEL: Record<string, string> = {
  llm_quick: "LLM 轻量档",
  llm_strong: "LLM 强推理档",
  image_gen: "图像生成",
  email: "邮件发送",
};

const DEGRADATION_LABEL: Record<string, string> = {
  recommend_reasons: "推荐理由 → 模板降级",
  ops_chat: "AI 助手 → 数据摘要降级",
};

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h} 小时 ${m} 分` : `${m} 分 ${seconds % 60} 秒`;
}

/** Batch E: real content for the 账号工作台 tab — the degradation
 * visibility panel. Every fallback in this product used to be silent
 * (which once hid a 100%-template regression for days); this makes the
 * safety net observable. Window = since backend process start. */
function AccountHealthSection() {
  const [stats, setStats] = useState<HealthStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadStats = async () => {
      try {
        const response = await api.get<ApiEnvelope<HealthStats>>(
          "/api/ops/health-stats",
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "health_error");
        }
        if (!cancelled) {
          setStats(response.data.data);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "health_request_failed";
          setError(msg);
        }
      }
    };

    void loadStats();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  if (error) {
    return <Alert type="warning" showIcon message="服务状态暂不可用" description={error} />;
  }
  if (!stats) {
    return <div className="py-8 text-center text-sm text-ink-muted">加载服务状态…</div>;
  }

  const serviceKeys = Object.keys(SERVICE_LABEL).filter(
    (key) => stats.services[key] || key.startsWith("llm"),
  );

  return (
    <div className="max-w-[760px]">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-ink">运行状态（自后端启动起）</div>
        <Button size="small" icon={<ReloadOutlined />} onClick={() => setReloadToken((k) => k + 1)} />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-xl bg-surface px-3 py-2.5">
          <div className="text-xs text-ink-muted">运行时长</div>
          <div className="mt-0.5 text-sm font-medium text-ink">
            {formatUptime(stats.uptime_seconds)}
          </div>
        </div>
        <div className="rounded-xl bg-surface px-3 py-2.5">
          <div className="text-xs text-ink-muted">图像生成模式</div>
          <div className="mt-0.5">
            <Tag
              bordered={false}
              color={stats.image_provider === "seedream" ? "purple" : "default"}
            >
              {stats.image_provider === "seedream" ? "Seedream 真实生成" : "Mock 快速预览"}
            </Tag>
          </div>
        </div>
        <div className="rounded-xl bg-surface px-3 py-2.5">
          <div className="text-xs text-ink-muted">定时报告调度</div>
          <div className="mt-0.5">
            <Tag bordered={false} color={stats.scheduler_running ? "success" : "warning"}>
              {stats.scheduler_running ? "运行中" : "未启动"}
            </Tag>
          </div>
        </div>
        <div className="rounded-xl bg-surface px-3 py-2.5">
          <div className="text-xs text-ink-muted">模型档位</div>
          <div className="mt-0.5 truncate text-xs text-ink-secondary" title={`${stats.llm_quick_model} / ${stats.llm_strong_model}`}>
            {stats.llm_quick_model.split("/").pop()}
            <br />
            {stats.llm_strong_model.split("/").pop()}
          </div>
        </div>
      </div>

      <div className="mt-6 text-sm font-semibold text-ink">AI / 外部服务调用</div>
      <div className="mt-2 overflow-hidden rounded-xl border border-line">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-surface text-ink-secondary">
              <th className="px-3 py-2 text-left font-medium">服务</th>
              <th className="px-3 py-2 text-right font-medium">成功</th>
              <th className="px-3 py-2 text-right font-medium">失败</th>
              <th className="px-3 py-2 text-left font-medium">最近失败</th>
            </tr>
          </thead>
          <tbody>
            {serviceKeys.map((key) => {
              const s = stats.services[key];
              return (
                <tr key={key} className="border-t border-line">
                  <td className="px-3 py-2 text-ink">{SERVICE_LABEL[key]}</td>
                  <td className="px-3 py-2 text-right font-medium text-success">{s?.ok ?? 0}</td>
                  <td className={`px-3 py-2 text-right font-medium ${s?.fail ? "text-danger" : "text-ink-muted"}`}>
                    {s?.fail ?? 0}
                  </td>
                  <td className="max-w-[280px] truncate px-3 py-2 text-ink-muted" title={s?.last_fail_reason ?? ""}>
                    {s?.last_fail_at
                      ? `${dayjs(s.last_fail_at).format("MM-DD HH:mm")} ${s.last_fail_reason ?? ""}`
                      : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 text-sm font-semibold text-ink">最近降级事件</div>
      {stats.degradations.length === 0 ? (
        <p className="mt-2 text-xs text-ink-muted">
          无降级发生 —— 所有 AI 文案均为模型实时生成
        </p>
      ) : (
        <div className="mt-2 space-y-1.5">
          {stats.degradations.slice(0, 8).map((d, i) => (
            <div key={i} className="flex items-start gap-2 rounded-lg bg-surface px-3 py-2 text-xs">
              <Tag bordered={false} color="orange" className="mr-0 shrink-0">
                {DEGRADATION_LABEL[d.source] ?? d.source}
              </Tag>
              <span className="text-ink-muted">{dayjs(d.at).format("MM-DD HH:mm")}</span>
              <span className="min-w-0 truncate text-ink-secondary" title={d.reason}>
                {d.reason}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SubscriptionSection() {
  const { message } = AntApp.useApp();
  const [sub, setSub] = useState<Subscription>(() => loadSubscription());

  const save = () => {
    try {
      localStorage.setItem(SUBSCRIPTION_KEY, JSON.stringify(sub));
      message.success("订阅设置已保存（本地）");
    } catch {
      message.error("保存失败：浏览器存储不可用");
    }
  };

  return (
    <div className="max-w-[560px]">
      <div className="flex items-center gap-3">
        <Switch
          checked={sub.enabled}
          onChange={(enabled) => setSub((s) => ({ ...s, enabled }))}
        />
        <span className="text-sm font-medium text-ink">启用邮件订阅</span>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <div className="mb-1 text-xs text-ink-secondary">收件邮箱</div>
          <Input
            placeholder="user@example.com"
            value={sub.email}
            disabled={!sub.enabled}
            onChange={(e) => setSub((s) => ({ ...s, email: e.target.value }))}
          />
        </div>
        <div>
          <div className="mb-1 text-xs text-ink-secondary">订阅频率</div>
          <Checkbox.Group
            value={sub.frequencies}
            disabled={!sub.enabled}
            options={[
              { label: "日报", value: "daily" },
              { label: "周报", value: "weekly" },
              { label: "关键事件实时", value: "events" },
            ]}
            onChange={(frequencies) =>
              setSub((s) => ({ ...s, frequencies: frequencies as string[] }))
            }
          />
        </div>
        <Button type="primary" onClick={save}>
          保存
        </Button>
      </div>
    </div>
  );
}

function ReportsSection() {
  const { message } = AntApp.useApp();
  const navigate = useNavigate();
  const [items, setItems] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<"daily" | "weekly" | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadReports = async () => {
      try {
        const response = await api.get<
          ApiEnvelope<{ items: ReportItem[]; total: number }>
        >("/api/ops/reports", { params: { size: 10 }, suppressToast: true });
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "reports_error");
        }
        if (!cancelled) {
          setItems(response.data.data.items);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "reports_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadReports();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const generate = useCallback(
    async (type: "daily" | "weekly") => {
      setGenerating(type);
      try {
        const response = await api.post<ApiEnvelope<{ report_id: number }>>(
          "/api/ops/reports/generate",
          { type },
          { suppressToast: true, timeout: 120_000 },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "generate_error");
        }
        message.success(
          `${type === "daily" ? "日报" : "周报"}已生成（#${response.data.data.report_id}），邮件投递中`,
        );
        setLoading(true);
        setReloadToken((k) => k + 1);
      } catch (requestError) {
        if (isAxiosError<{ msg?: string }>(requestError)) {
          const code = requestError.response?.status;
          const msg = requestError.response?.data?.msg;
          if (code === 429) {
            message.warning("30 秒内已生成过该类型报告，稍后再试");
          } else if (code === 503) {
            message.error("AI 服务暂时繁忙，请稍后重试");
          } else {
            message.error(`生成失败：${msg ?? code ?? "网络错误"}`);
          }
        } else {
          message.error("生成失败：网络错误");
        }
      } finally {
        setGenerating(null);
      }
    },
    [message],
  );

  const columns = useMemo<TableProps<ReportItem>["columns"]>(
    () => [
      {
        title: "标题",
        dataIndex: "title",
        key: "title",
        render: (title: string) => (
          <span className="font-medium text-ink">{title}</span>
        ),
      },
      {
        title: "类型",
        key: "type",
        width: 90,
        render: (_, item) => (
          <Tag bordered={false} color={item.type === "daily" ? "blue" : "purple"}>
            {item.type === "daily" ? "日报" : "周报"}
          </Tag>
        ),
      },
      {
        title: "触发",
        key: "source",
        width: 90,
        render: (_, item) =>
          item.trigger_source === "scheduled" ? "定时" : "手动",
      },
      {
        title: "生成时间",
        key: "generated",
        width: 150,
        render: (_, item) =>
          item.generated_at ? dayjs(item.generated_at).format("MM-DD HH:mm") : "-",
      },
      {
        title: "邮件状态",
        key: "email",
        width: 110,
        render: (_, item) => {
          const meta = EMAIL_STATUS_TAG[item.email_status];
          return (
            <Tag bordered={false} color={meta.color}>
              {meta.label}
            </Tag>
          );
        },
      },
    ],
    [],
  );

  return (
    <div className="mt-8 border-t border-line pt-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="text-base font-semibold text-ink">
          <FileTextOutlined className="mr-2" />
          最近 10 份报告
        </div>
        <div className="flex items-center gap-2">
          <Button
            icon={<ReloadOutlined />}
            loading={loading}
            onClick={() => {
              setLoading(true);
              setReloadToken((k) => k + 1);
            }}
          />
          <Button
            type="primary"
            loading={generating === "daily"}
            disabled={generating !== null}
            onClick={() => void generate("daily")}
          >
            立即生成日报
          </Button>
          <Button
            loading={generating === "weekly"}
            disabled={generating !== null}
            onClick={() => void generate("weekly")}
          >
            立即生成周报
          </Button>
        </div>
      </div>

      {error && (
        <Alert
          className="mb-4"
          type="warning"
          showIcon
          message="报告列表暂时不可用"
          description={`请确认后端 8000 端口已启动：${error}`}
        />
      )}

      <Table<ReportItem>
        rowKey="id"
        size="middle"
        columns={columns}
        dataSource={items}
        loading={loading}
        pagination={false}
        locale={{ emptyText: <Empty description="暂无报告，点击右上角立即生成" /> }}
        onRow={(item) => ({
          onClick: () => navigate(`/ops/reports/${item.id}`),
          style: { cursor: "pointer" },
        })}
      />
    </div>
  );
}

export default function O7Setting() {
  return (
    <section className="mx-auto max-w-[1100px]">
      <div className="mb-6">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
          <SettingOutlined /> O7 · 设置中心
        </div>
        <h1 className="mt-3 text-2xl font-semibold text-ink">设置中心</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          报告订阅、通知偏好与工作台配置；独立报告中心已并入「通知与邮件订阅」
        </p>
      </div>

      <Card className="border-line shadow-sm">
        <Tabs
          defaultActiveKey="notify"
          items={[
            {
              key: "account",
              label: "账号工作台",
              children: <AccountHealthSection />,
            },
            {
              key: "notify",
              label: (
                <span>
                  <MailOutlined className="mr-1" />
                  通知与邮件订阅
                </span>
              ),
              children: (
                <div>
                  <SubscriptionSection />
                  <ReportsSection />
                </div>
              ),
            },
            {
              key: "ai",
              label: "AI 助手偏好",
              children: (
                <div className="py-10 text-center text-sm text-ink-muted">
                  模型档位、Function Calling 开关与生成温度（本期占位）
                </div>
              ),
            },
            {
              key: "display",
              label: "显示与界面",
              children: (
                <div className="py-10 text-center text-sm text-ink-muted">
                  主题切换、紧凑模式与图表偏好（本期占位）
                </div>
              ),
            },
          ]}
        />
      </Card>
    </section>
  );
}
