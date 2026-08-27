import {
  CheckOutlined,
  FireOutlined,
  ReloadOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Drawer,
  Empty,
  Table,
  Tag,
  theme,
} from "antd";
import type { TableProps } from "antd";
import dayjs from "dayjs";
import type { EChartsOption } from "echarts";
import { useCallback, useEffect, useMemo, useState } from "react";
import api from "../../api/client";
import EChart from "../../components/EChart";
import { absUrl } from "../../utils/url";

interface TrendingItem {
  style_id: string;
  name: string;
  cover_url: string;
  trend_7d: number[];
  /** null = 前 3 天窗口 0 基数（增长率无穷大，后端以 null 表示"首次爆发"） */
  growth_rate: number | null;
  collect_rate: number;
  last_24h_tryons: number;
  detected_at: string;
  suggested_action: string;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

/** trend_7d 与后端对齐：近 7 个自然日（北京时区），最旧在前。 */
function trendDates(): string[] {
  return Array.from({ length: 7 }, (_, i) =>
    dayjs()
      .subtract(6 - i, "day")
      .format("MM-DD"),
  );
}

function sparklineOption(values: number[], color: string): EChartsOption {
  return {
    animation: false,
    grid: { left: 2, right: 2, top: 4, bottom: 2 },
    xAxis: { type: "category", show: false, boundaryGap: false, data: values.map((_, i) => i) },
    yAxis: { type: "value", show: false },
    series: [
      {
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2, color },
        areaStyle: { opacity: 0.16, color },
        data: values,
      },
    ],
  };
}

function GrowthCell({ value }: { value: number | null }) {
  if (value === null) {
    return <Tag color="volcano">首次爆发</Tag>;
  }
  return (
    <span className="font-semibold text-success">
      +{Math.round(value * 100)}%
    </span>
  );
}

export default function O2Trending() {
  const { token } = theme.useToken();
  const { message } = AntApp.useApp();
  const [items, setItems] = useState<TrendingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<TrendingItem | null>(null);
  const [adoptingId, setAdoptingId] = useState<string | null>(null);
  const [adoptedIds, setAdoptedIds] = useState<Set<string>>(new Set());

  // Refresh trigger: bumping the token re-runs the fetch effect. Fetch
  // lives inside the effect (same pattern as O1Overview) so no setState
  // runs synchronously in the effect body, and `cancelled` guards
  // against setState after unmount.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadTrending = async () => {
      try {
        const response = await api.get<ApiEnvelope<{ items: TrendingItem[] }>>(
          "/api/ops/trending",
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "trending_error");
        }
        if (!cancelled) {
          setItems(response.data.data.items);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "trending_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadTrending();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const adopt = useCallback(
    async (item: TrendingItem) => {
      setAdoptingId(item.style_id);
      try {
        const response = await api.post<ApiEnvelope<{ display_order: number }>>(
          "/api/ops/actions",
          {
            style_id: item.style_id,
            action_type: "boost",
            reason: `采纳爆款建议：${item.suggested_action}`,
          },
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "action_error");
        }
        setAdoptedIds((prev) => new Set(prev).add(item.style_id));
        message.success(
          `已采纳：「${item.name}」提升至推荐首位（display_order=${response.data.data.display_order}）`,
        );
      } catch (requestError) {
        const msg =
          requestError instanceof Error ? requestError.message : "action_request_failed";
        message.error(`采纳失败：${msg}`);
      } finally {
        setAdoptingId(null);
      }
    },
    [message],
  );

  const columns = useMemo<TableProps<TrendingItem>["columns"]>(
    () => [
      {
        title: "款式",
        key: "style",
        width: 240,
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
        title: "近 7 日趋势",
        key: "trend",
        width: 160,
        render: (_, item) => (
          <div style={{ width: 140 }}>
            <EChart option={sparklineOption(item.trend_7d, token.colorPrimary)} height={42} />
          </div>
        ),
      },
      {
        title: "增长率",
        key: "growth",
        width: 110,
        render: (_, item) => <GrowthCell value={item.growth_rate} />,
      },
      {
        title: "收藏率",
        key: "collect",
        width: 100,
        render: (_, item) => `${(item.collect_rate * 100).toFixed(1)}%`,
      },
      {
        title: "24h 试戴",
        dataIndex: "last_24h_tryons",
        key: "last24",
        width: 100,
      },
      {
        title: "发现时间",
        key: "detected",
        width: 110,
        render: (_, item) => dayjs(item.detected_at).format("HH:mm"),
      },
      {
        title: "操作",
        key: "action",
        width: 130,
        render: (_, item) => {
          const adopted = adoptedIds.has(item.style_id);
          return (
            <Button
              size="small"
              type={adopted ? "default" : "primary"}
              disabled={adopted}
              loading={adoptingId === item.style_id}
              icon={adopted ? <CheckOutlined /> : <RiseOutlined />}
              onClick={(event) => {
                event.stopPropagation();
                void adopt(item);
              }}
            >
              {adopted ? "已采纳" : "采纳建议"}
            </Button>
          );
        },
      },
    ],
    [adopt, adoptedIds, adoptingId, token.colorPrimary],
  );

  const drawerChartOption = useMemo<EChartsOption>(() => {
    if (!active) return {};
    return {
      color: [token.colorPrimary],
      grid: { left: 44, right: 18, top: 30, bottom: 36 },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: trendDates(),
        axisLine: { lineStyle: { color: token.colorBorderSecondary } },
        axisLabel: { color: token.colorTextSecondary },
      },
      yAxis: {
        type: "value",
        minInterval: 1,
        axisLabel: { color: token.colorTextSecondary },
        splitLine: { lineStyle: { color: token.colorBorderSecondary } },
      },
      series: [
        {
          name: "试戴次数",
          type: "line",
          smooth: true,
          symbolSize: 7,
          lineStyle: { width: 3 },
          areaStyle: { opacity: 0.12 },
          data: active.trend_7d,
        },
      ],
    };
  }, [active, token]);

  const activeAdopted = active !== null && adoptedIds.has(active.style_id);

  return (
    <section className="max-w-[1500px] mx-auto">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
            <FireOutlined /> O2 · 爆款识别
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-ink">爆款趋势</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            规则：近 3 日增长 ≥50% 且 24h 试戴 ≥50 次 且 收藏率 ≥20%，全部满足即入选
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
        <Table<TrendingItem>
          rowKey="style_id"
          columns={columns}
          dataSource={items}
          loading={loading}
          pagination={false}
          locale={{
            emptyText: (
              <Empty
                description="当前没有满足全部规则的爆款；若为演示环境，请先重跑 seed_all.py 刷新时间窗口"
              />
            ),
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
              <Tag color="volcano" bordered={false}>
                爆款候选
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

            <div className="mt-5 grid grid-cols-3 gap-3 text-center">
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">3 日增长</div>
                <div className="mt-1 font-semibold text-success">
                  {active.growth_rate === null
                    ? "首次爆发"
                    : `+${Math.round(active.growth_rate * 100)}%`}
                </div>
              </div>
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">收藏率</div>
                <div className="mt-1 font-semibold text-ink">
                  {(active.collect_rate * 100).toFixed(1)}%
                </div>
              </div>
              <div className="rounded-xl bg-surface px-2 py-3">
                <div className="text-xs text-ink-muted">24h 试戴</div>
                <div className="mt-1 font-semibold text-ink">{active.last_24h_tryons}</div>
              </div>
            </div>

            <div className="mt-6">
              <div className="text-sm font-semibold text-ink mb-2">近 7 日试戴趋势</div>
              <EChart option={drawerChartOption} height={240} />
            </div>

            <div className="mt-6 rounded-xl bg-brand-light px-4 py-3.5">
              <div className="text-xs font-semibold text-ink-secondary">AI 运营建议</div>
              <div className="mt-1 text-sm text-ink">{active.suggested_action}</div>
            </div>

            <Button
              className="mt-5"
              block
              type="primary"
              size="large"
              disabled={activeAdopted}
              loading={adoptingId === active.style_id}
              icon={activeAdopted ? <CheckOutlined /> : <RiseOutlined />}
              onClick={() => void adopt(active)}
            >
              {activeAdopted ? "已采纳该建议" : "采纳建议（提升推荐位）"}
            </Button>
          </div>
        )}
      </Drawer>
    </section>
  );
}
