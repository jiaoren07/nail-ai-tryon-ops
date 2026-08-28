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
              children: (
                <div className="py-10 text-center text-sm text-ink-muted">
                  账号信息、API 用量与版本信息（本期占位）
                </div>
              ),
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
