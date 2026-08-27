import {
  DownOutlined,
  ReloadOutlined,
  StopOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Drawer,
  Empty,
  Popconfirm,
  Table,
  Tag,
} from "antd";
import type { TableProps } from "antd";
import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../../api/client";
import { absUrl } from "../../utils/url";

interface ColdItem {
  style_id: string;
  name: string;
  cover_url: string;
  recent_7d_tryons: number;
  exposure_click_ratio: number;
  days_since_listed: number;
  cumulative_tryons: number;
  cold_reason: string;
  suggestion: string;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

/** 后端建议文案只有三种模板；含「下架」的建议主操作即下架，
 * 其余（降排序观察 / 优化主图）主操作为降低排序 —— 「优化主图」
 * 没有对应后端 action，不做假按钮，文案保留在建议里。 */
function primaryActionOf(item: ColdItem): "offline" | "demote" {
  return item.suggestion.includes("下架") ? "offline" : "demote";
}

export default function O3Cold() {
  const { message } = AntApp.useApp();
  const [items, setItems] = useState<ColdItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<ColdItem | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [demotedIds, setDemotedIds] = useState<Set<string>>(new Set());
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadCold = async () => {
      try {
        const response = await api.get<ApiEnvelope<{ items: ColdItem[] }>>(
          "/api/ops/cold",
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "cold_error");
        }
        if (!cancelled) {
          setItems(response.data.data.items);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "cold_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadCold();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const runAction = useCallback(
    async (item: ColdItem, actionType: "offline" | "demote") => {
      const key = `${item.style_id}:${actionType}`;
      setBusyKey(key);
      try {
        const response = await api.post<ApiEnvelope<{ display_order: number; is_active: boolean }>>(
          "/api/ops/actions",
          {
            style_id: item.style_id,
            action_type: actionType,
            reason: `冷门预警处理：${item.cold_reason}`,
          },
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "action_error");
        }
        if (actionType === "offline") {
          // 下架后款式不再出现在冷门检测（只扫 is_active=1），本地同步移除
          setItems((prev) => prev.filter((it) => it.style_id !== item.style_id));
          setActive((prev) => (prev?.style_id === item.style_id ? null : prev));
          message.success(`「${item.name}」已下架，用户端立即不可见`);
        } else {
          setDemotedIds((prev) => new Set(prev).add(item.style_id));
          message.success(
            `「${item.name}」已降至推荐末位（display_order=${response.data.data.display_order}）`,
          );
        }
      } catch (requestError) {
        const msg =
          requestError instanceof Error ? requestError.message : "action_request_failed";
        message.error(`操作失败：${msg}`);
      } finally {
        setBusyKey(null);
      }
    },
    [message],
  );

  const renderActions = useCallback(
    (item: ColdItem, size: "small" | "middle") => {
      const primary = primaryActionOf(item);
      const demoted = demotedIds.has(item.style_id);
      const offlineButton = (
        <Popconfirm
          key="offline"
          title="确认下架该款式？"
          description="下架后用户端立即不可见，可在款式管理中重新上架"
          okText="下架"
          cancelText="取消"
          okButtonProps={{ danger: true }}
          onConfirm={() => void runAction(item, "offline")}
          onPopupClick={(event) => event.stopPropagation()}
        >
          <Button
            size={size}
            danger
            type={primary === "offline" ? "primary" : "default"}
            icon={<StopOutlined />}
            loading={busyKey === `${item.style_id}:offline`}
            onClick={(event) => event.stopPropagation()}
          >
            下架
          </Button>
        </Popconfirm>
      );
      const demoteButton = (
        <Button
          key="demote"
          size={size}
          type={primary === "demote" ? "primary" : "default"}
          icon={<DownOutlined />}
          disabled={demoted}
          loading={busyKey === `${item.style_id}:demote`}
          onClick={(event) => {
            event.stopPropagation();
            void runAction(item, "demote");
          }}
        >
          {demoted ? "已降序" : "降低排序"}
        </Button>
      );
      // 主操作排前面
      return (
        <div className="flex items-center gap-2">
          {primary === "offline" ? (
            <>
              {offlineButton}
              {demoteButton}
            </>
          ) : (
            <>
              {demoteButton}
              {offlineButton}
            </>
          )}
        </div>
      );
    },
    [busyKey, demotedIds, runAction],
  );

  const columns = useMemo<TableProps<ColdItem>["columns"]>(
    () => [
      {
        title: "款式",
        key: "style",
        width: 190,
        render: (_, item) => (
          <div className="flex items-center gap-3 min-w-0">
            <img
              src={absUrl(item.cover_url)}
              alt={item.name}
              className="w-12 h-12 rounded-lg object-cover shrink-0 border border-line"
            />
            <div className="min-w-0">
              <div className="font-medium text-ink truncate">{item.name}</div>
              <div className="text-xs text-ink-muted">{item.style_id}</div>
            </div>
          </div>
        ),
      },
      {
        title: "近 7 天",
        dataIndex: "recent_7d_tryons",
        key: "recent7d",
        width: 84,
        render: (value: number) => (
          <span className={value <= 2 ? "font-semibold text-danger" : "text-ink"}>{value}</span>
        ),
      },
      {
        title: "点击曝光比",
        key: "ratio",
        width: 96,
        render: (_, item) => `${(item.exposure_click_ratio * 100).toFixed(1)}%`,
      },
      {
        title: "上架天数",
        dataIndex: "days_since_listed",
        key: "days",
        width: 80,
      },
      {
        title: "冷门原因",
        key: "reason",
        width: 170,
        render: (_, item) => (
          <Tag color="orange" bordered={false} className="whitespace-normal leading-5">
            {item.cold_reason}
          </Tag>
        ),
      },
      {
        title: "建议",
        dataIndex: "suggestion",
        key: "suggestion",
        width: 200,
        className: "text-ink-secondary",
      },
      {
        title: "操作",
        key: "action",
        width: 186,
        render: (_, item) => renderActions(item, "small"),
      },
    ],
    [renderActions],
  );

  return (
    <section className="max-w-[1500px] mx-auto">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
            <WarningOutlined /> O3 · 冷门预警
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-ink">冷门款式预警</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            命中任一规则即预警：近 7 天试戴 ≤5 次 / 点击曝光比 ≤2% / 上架超 30 天累计 ≤20 次
          </p>
        </div>
        <Button
          icon={<ReloadOutlined />}
          loading={loading}
          onClick={() => {
            setLoading(true);
            setReloadToken((k) => k + 1);
          }}
        >
          刷新
        </Button>
      </div>

      {error && (
        <Alert
          className="mb-5"
          type="warning"
          showIcon
          message="数据暂时不可用"
          description={`请确认后端 8000 端口已启动：${error}`}
        />
      )}

      <Card className="border-line shadow-sm" styles={{ body: { padding: 0 } }}>
        <Table<ColdItem>
          rowKey="style_id"
          columns={columns}
          dataSource={items}
          loading={loading}
          pagination={false}
          scroll={{ x: 1006 }}
          locale={{
            emptyText: <Empty description="当前没有命中冷门规则的在架款式" />,
          }}
          onRow={(item) => ({
            onClick: () => setActive(item),
            style: { cursor: "pointer" },
          })}
        />
      </Card>

      <Drawer
        open={active !== null}
        onClose={() => setActive(null)}
        width={520}
        title={
          active ? (
            <div className="flex items-center gap-2">
              <span>{active.name}</span>
              <Tag color="orange" bordered={false}>
                冷门预警
              </Tag>
            </div>
          ) : null
        }
      >
        {active && (
          <div>
            <img
              src={absUrl(active.cover_url)}
              alt={active.name}
              className="w-full h-52 object-cover rounded-xl border border-line"
            />

            <div className="mt-5 grid grid-cols-4 gap-3 text-center">
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">近 7 天</div>
                <div className="mt-1 font-semibold text-danger">{active.recent_7d_tryons}</div>
              </div>
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">点击曝光比</div>
                <div className="mt-1 font-semibold text-ink">
                  {(active.exposure_click_ratio * 100).toFixed(1)}%
                </div>
              </div>
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">上架天数</div>
                <div className="mt-1 font-semibold text-ink">{active.days_since_listed}</div>
              </div>
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">累计试戴</div>
                <div className="mt-1 font-semibold text-ink">{active.cumulative_tryons}</div>
              </div>
            </div>

            <Alert
              className="mt-6"
              type="warning"
              showIcon
              message="冷门原因"
              description={active.cold_reason}
            />

            <div className="mt-4 rounded-xl bg-brand-light px-4 py-3.5">
              <div className="text-xs font-semibold text-ink-secondary">AI 运营建议</div>
              <div className="mt-1 text-sm text-ink">{active.suggestion}</div>
            </div>

            <div className="mt-5">{renderActions(active, "middle")}</div>
          </div>
        )}
      </Drawer>
    </section>
  );
}
