import {
  ArrowDownOutlined,
  ArrowUpOutlined,
  FireOutlined,
  ReloadOutlined,
  TableOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Empty,
  Switch,
  Table,
  Tag,
  Tooltip,
} from "antd";
import type { TableProps } from "antd";
import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../../api/client";
import { absUrl } from "../../utils/url";

interface OpsStyle {
  id: string;
  name: string;
  gender: "female" | "male" | "both";
  cover_url: string;
  style_tags: string[];
  color_main: string;
  color_tone: string;
  length_pref: string;
  complexity: number;
  heat_score: number;
  is_active: boolean;
  display_order: number;
  created_at: string | null;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

interface PatchResult {
  changed: boolean;
  style_id: string;
  is_active: boolean;
  display_order: number;
  action_ids: number[];
}

const GENDER_TAG: Record<OpsStyle["gender"], { color: string; label: string }> = {
  female: { color: "magenta", label: "女生" },
  male: { color: "geekblue", label: "男生" },
  both: { color: "default", label: "通用" },
};

/** 列表顺序与后端 GET /api/ops/styles 一致：display_order ASC, id ASC。 */
function sortStyles(list: OpsStyle[]): OpsStyle[] {
  return [...list].sort(
    (a, b) => a.display_order - b.display_order || a.id.localeCompare(b.id),
  );
}

export default function O6Styles() {
  const { message } = AntApp.useApp();
  const [items, setItems] = useState<OpsStyle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadStyles = async () => {
      try {
        const response = await api.get<ApiEnvelope<{ items: OpsStyle[]; total: number }>>(
          "/api/ops/styles",
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "styles_error");
        }
        if (!cancelled) {
          setItems(response.data.data.items);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "styles_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadStyles();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const refetch = useCallback(() => {
    setLoading(true);
    setReloadToken((k) => k + 1);
  }, []);

  const patchStyle = useCallback(
    async (
      styleId: string,
      body: { is_active?: boolean; display_order?: number; reason?: string },
    ): Promise<PatchResult> => {
      const response = await api.patch<ApiEnvelope<PatchResult>>(
        `/api/ops/styles/${styleId}`,
        body,
        { suppressToast: true },
      );
      if (response.data.code !== 0) {
        throw new Error(response.data.msg || "patch_error");
      }
      return response.data.data;
    },
    [],
  );

  const toggleActive = useCallback(
    async (item: OpsStyle, next: boolean) => {
      setBusyKey(`${item.id}:active`);
      try {
        const result = await patchStyle(item.id, {
          is_active: next,
          reason: next ? "款式管理：重新上架" : "款式管理：手动下架",
        });
        setItems((prev) =>
          prev.map((it) => (it.id === item.id ? { ...it, is_active: result.is_active } : it)),
        );
        message.success(
          next
            ? `「${item.name}」已上架，用户端立即可见`
            : `「${item.name}」已下架，用户端立即不可见`,
        );
      } catch (requestError) {
        const msg =
          requestError instanceof Error ? requestError.message : "patch_request_failed";
        message.error(`操作失败：${msg}`);
      } finally {
        setBusyKey(null);
      }
    },
    [message, patchStyle],
  );

  /** 上移/下移 = 与相邻行交换 display_order（两次 PATCH，各写一条 reorder
   * audit）。若相邻值相等（人工制造的重复值），退化为自己 ±1 保证有效移动。
   * 第二次 PATCH 失败时 refetch 恢复服务端真实状态。 */
  const move = useCallback(
    async (item: OpsStyle, direction: "up" | "down") => {
      const index = items.findIndex((it) => it.id === item.id);
      const neighborIndex = direction === "up" ? index - 1 : index + 1;
      if (neighborIndex < 0 || neighborIndex >= items.length) return;
      const neighbor = items[neighborIndex];

      setBusyKey(`${item.id}:${direction}`);
      try {
        const selfTarget =
          neighbor.display_order === item.display_order
            ? item.display_order + (direction === "up" ? -1 : 1)
            : neighbor.display_order;
        const reason = `款式管理：${direction === "up" ? "上移" : "下移"}（与 ${neighbor.id} 交换）`;

        await patchStyle(item.id, { display_order: selfTarget, reason });
        if (neighbor.display_order !== item.display_order) {
          await patchStyle(neighbor.id, { display_order: item.display_order, reason });
        }

        setItems((prev) =>
          sortStyles(
            prev.map((it) => {
              if (it.id === item.id) return { ...it, display_order: selfTarget };
              if (
                it.id === neighbor.id &&
                neighbor.display_order !== item.display_order
              ) {
                return { ...it, display_order: item.display_order };
              }
              return it;
            }),
          ),
        );
        message.success(`「${item.name}」已${direction === "up" ? "上移" : "下移"}`);
      } catch (requestError) {
        const msg =
          requestError instanceof Error ? requestError.message : "patch_request_failed";
        message.error(`排序失败，已刷新真实状态：${msg}`);
        refetch();
      } finally {
        setBusyKey(null);
      }
    },
    [items, message, patchStyle, refetch],
  );

  const columns = useMemo<TableProps<OpsStyle>["columns"]>(
    () => [
      {
        title: "款式",
        key: "style",
        width: 250,
        render: (_, item) => (
          <div
            className={`flex items-center gap-3 min-w-0 ${item.is_active ? "" : "opacity-50"}`}
          >
            <img
              src={absUrl(item.cover_url)}
              alt={item.name}
              className="w-12 h-12 rounded-lg object-cover shrink-0 border border-line"
            />
            <div className="min-w-0">
              <div className="font-medium text-ink truncate">{item.name}</div>
              <div className="text-xs text-ink-muted">{item.id}</div>
            </div>
          </div>
        ),
      },
      {
        title: "性别",
        key: "gender",
        width: 84,
        filters: [
          { text: "女生", value: "female" },
          { text: "男生", value: "male" },
          { text: "通用", value: "both" },
        ],
        onFilter: (value, item) => item.gender === value,
        render: (_, item) => {
          const meta = GENDER_TAG[item.gender] ?? GENDER_TAG.both;
          return (
            <Tag color={meta.color} bordered={false}>
              {meta.label}
            </Tag>
          );
        },
      },
      {
        title: "标签",
        key: "tags",
        width: 250,
        render: (_, item) => (
          <div className="flex flex-wrap gap-1">
            {item.style_tags.slice(0, 3).map((tag) => (
              <Tag key={tag} bordered={false} className="mr-0">
                {tag}
              </Tag>
            ))}
            {item.style_tags.length > 3 && (
              <Tooltip title={item.style_tags.slice(3).join(" / ")}>
                <Tag bordered={false} className="mr-0">
                  +{item.style_tags.length - 3}
                </Tag>
              </Tooltip>
            )}
          </div>
        ),
      },
      {
        title: "热度",
        dataIndex: "heat_score",
        key: "heat",
        width: 96,
        sorter: (a, b) => a.heat_score - b.heat_score,
        render: (value: number) => (
          <span className="inline-flex items-center gap-1 text-ink">
            <FireOutlined className="text-warning" />
            {value}
          </span>
        ),
      },
      {
        title: "上下架",
        key: "active",
        width: 96,
        filters: [
          { text: "在架", value: true },
          { text: "已下架", value: false },
        ],
        onFilter: (value, item) => item.is_active === value,
        render: (_, item) => (
          <Switch
            checked={item.is_active}
            loading={busyKey === `${item.id}:active`}
            onChange={(next) => void toggleActive(item, next)}
          />
        ),
      },
      {
        title: "排序值",
        dataIndex: "display_order",
        key: "order",
        width: 90,
        render: (value: number) => <span className="font-mono text-ink-secondary">{value}</span>,
      },
      {
        title: "排序操作",
        key: "move",
        width: 120,
        render: (_, item, index) => (
          <div className="flex items-center gap-1.5">
            <Tooltip title="上移">
              <Button
                size="small"
                icon={<ArrowUpOutlined />}
                disabled={index === 0}
                loading={busyKey === `${item.id}:up`}
                onClick={() => void move(item, "up")}
              />
            </Tooltip>
            <Tooltip title="下移">
              <Button
                size="small"
                icon={<ArrowDownOutlined />}
                disabled={index === items.length - 1}
                loading={busyKey === `${item.id}:down`}
                onClick={() => void move(item, "down")}
              />
            </Tooltip>
          </div>
        ),
      },
    ],
    [busyKey, items.length, move, toggleActive],
  );

  const inactiveCount = items.filter((item) => !item.is_active).length;

  return (
    <section className="max-w-[1500px] mx-auto">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
            <TableOutlined /> O6 · 款式管理
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-ink">款式管理</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            共 {items.length} 款（在架 {items.length - inactiveCount} / 下架 {inactiveCount}
            ）；开关与排序即时生效，用户端下一次请求立即可见
          </p>
        </div>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={refetch}>
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
        <Table<OpsStyle>
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          pagination={false}
          locale={{ emptyText: <Empty description="款式库为空，请先运行 seed_all.py" /> }}
        />
      </Card>
    </section>
  );
}
