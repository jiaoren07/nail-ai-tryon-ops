import {
  AppstoreOutlined,
  ArrowDownOutlined,
  ArrowUpOutlined,
  FireOutlined,
  MinusOutlined,
  PercentageOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { Alert, Card, Col, Row, Segmented, Skeleton, Statistic, theme } from "antd";
import type { EChartsOption } from "echarts";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import api from "../../api/client";
import EChart from "../../components/EChart";

interface KpiValue {
  value: number;
  diff_percent: number | null;
}

interface OverviewData {
  kpis: {
    tryons_today: KpiValue;
    conversion_rate: KpiValue;
    active_styles: KpiValue;
    new_trending_alerts: KpiValue;
  };
  trend_7d: Array<{ date: string; tryon_count: number }>;
  style_distribution: Array<{ style_tag: string; percent: number }>;
  hourly_heat: number[];
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

interface KpiCardProps {
  title: string;
  value: number;
  diff: number | null;
  icon: ReactNode;
  precision?: number;
  suffix?: string;
}

function KpiCard({
  title,
  value,
  diff,
  icon,
  precision,
  suffix,
}: KpiCardProps) {
  const isUp = diff !== null && diff > 0;
  const isDown = diff !== null && diff < 0;
  const trendClass = isUp
    ? "text-success"
    : isDown
      ? "text-danger"
      : "text-ink-muted";
  const TrendIcon = isUp ? ArrowUpOutlined : isDown ? ArrowDownOutlined : MinusOutlined;
  const trendText =
    diff === null ? "暂无同期数据" : `${Math.abs(diff).toFixed(1)}% 较昨日同期`;

  return (
    <Card className="h-full border-line shadow-sm" styles={{ body: { padding: 22 } }}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="text-sm text-ink-secondary">{title}</div>
          <Statistic
            className="mt-2"
            value={value}
            precision={precision}
            suffix={suffix}
            valueStyle={{ fontSize: 30, fontWeight: 650, color: "inherit" }}
          />
        </div>
        <div className="w-11 h-11 shrink-0 rounded-xl bg-brand-light text-ink flex items-center justify-center text-lg">
          {icon}
        </div>
      </div>
      <div className={`mt-4 flex items-center gap-1.5 text-xs ${trendClass}`}>
        <TrendIcon />
        <span>{trendText}</span>
      </div>
    </Card>
  );
}

function ChartCard({
  title,
  extra,
  children,
}: {
  title: string;
  extra?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Card
      className="h-full border-line shadow-sm"
      title={<span className="text-base font-semibold text-ink">{title}</span>}
      extra={extra}
    >
      {children}
    </Card>
  );
}

export default function O1Overview() {
  const { token } = theme.useToken();
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadOverview = async () => {
      try {
        const response = await api.get<ApiEnvelope<OverviewData>>("/api/ops/overview", {
          suppressToast: true,
        });
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "overview_error");
        }
        if (!cancelled) {
          setOverview(response.data.data);
          setUpdatedAt(new Date());
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const message =
            requestError instanceof Error ? requestError.message : "overview_request_failed";
          setError(message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadOverview();
    const timer = window.setInterval(() => void loadOverview(), 10_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const trendOption = useMemo<EChartsOption>(
    () => ({
      animationDuration: 500,
      color: [token.colorPrimary],
      grid: { left: 48, right: 22, top: 24, bottom: 42 },
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: overview?.trend_7d.map((item) => item.date.slice(5)) ?? [],
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
          symbolSize: 8,
          lineStyle: { width: 3 },
          areaStyle: { opacity: 0.12 },
          data: overview?.trend_7d.map((item) => item.tryon_count) ?? [],
        },
      ],
    }),
    [overview, token],
  );

  const distributionOption = useMemo<EChartsOption>(
    () => ({
      // NOTE: not colorInfo — antd defaults colorInfo === colorPrimary, which
      // made slice 1 and slice 5 the same blue. token.purple keeps us on
      // preset tokens (no hard-coded hex per tailwind.config.js rule).
      color: [
        token.colorPrimary,
        token.colorSuccess,
        token.colorWarning,
        token.colorError,
        token.purple,
        token.colorTextSecondary,
      ],
      tooltip: { trigger: "item", formatter: "{b}: {c}%" },
      legend: {
        bottom: 0,
        left: "center",
        textStyle: { color: token.colorTextSecondary },
      },
      series: [
        {
          name: "标签占比",
          type: "pie",
          radius: ["38%", "62%"],
          center: ["50%", "42%"],
          avoidLabelOverlap: true,
          itemStyle: {
            borderColor: token.colorBgContainer,
            borderWidth: 3,
            borderRadius: 6,
          },
          // 单行短标签（百分比取整）+ 收短引导线，避免左右边缘被画布裁剪；
          // 精确到 0.1% 的值保留在 tooltip 里
          label: {
            formatter: (params: { name: string; percent?: number }) =>
              `${params.name} ${Math.round(params.percent ?? 0)}%`,
            fontSize: 11,
          },
          labelLine: { length: 12, length2: 8 },
          data:
            overview?.style_distribution.map((item) => ({
              name: item.style_tag,
              value: item.percent,
            })) ?? [],
        },
      ],
    }),
    [overview, token],
  );

  const heatOption = useMemo<EChartsOption>(() => {
    const values = overview?.hourly_heat ?? [];
    const maxValue = Math.max(...values, 1);
    return {
      tooltip: {
        position: "top",
        formatter: (params: unknown) => {
          const value = (params as { value: [number, number, number] }).value;
          return `${String(value[0]).padStart(2, "0")}:00 · ${value[2]} 次试戴`;
        },
      },
      grid: { left: 18, right: 18, top: 34, bottom: 72 },
      xAxis: {
        type: "category",
        data: Array.from({ length: 24 }, (_, hour) => `${String(hour).padStart(2, "0")}:00`),
        splitArea: { show: true },
        axisLabel: { interval: 2, color: token.colorTextSecondary },
        axisLine: { lineStyle: { color: token.colorBorderSecondary } },
      },
      yAxis: {
        type: "category",
        data: ["今日热度"],
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitArea: { show: true },
      },
      visualMap: {
        min: 0,
        max: maxValue,
        calculable: false,
        orient: "horizontal",
        left: "center",
        bottom: 4,
        text: ["高", "低"],
        textStyle: { color: token.colorTextSecondary },
        inRange: {
          color: [token.colorFillSecondary, token.colorPrimary, token.colorWarning],
        },
      },
      series: [
        {
          name: "时段热度",
          type: "heatmap",
          data: values.map((value, hour) => [hour, 0, value]),
          label: { show: false },
          emphasis: {
            itemStyle: {
              shadowBlur: 8,
              shadowColor: token.colorTextQuaternary,
            },
          },
        },
      ],
    };
  }, [overview, token]);

  const kpis = overview?.kpis;

  return (
    <section className="max-w-[1500px] mx-auto">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="inline-flex items-center rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
            O1 · 实时看板
          </div>
          <h1 className="mt-3 text-2xl font-semibold text-ink">业务数据概览</h1>
          <p className="mt-1 text-sm text-ink-secondary">
            用户试戴与运营动作同步汇总，每 10 秒自动刷新
          </p>
        </div>
        <div className="text-xs text-ink-muted">
          {updatedAt ? `最近更新 ${updatedAt.toLocaleTimeString("zh-CN")}` : "正在连接数据…"}
        </div>
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

      {loading && !overview ? (
        <Card className="border-line shadow-sm">
          <Skeleton active />
        </Card>
      ) : (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} xl={6}>
              <KpiCard
                title="今日试戴次数"
                value={kpis?.tryons_today.value ?? 0}
                diff={kpis?.tryons_today.diff_percent ?? null}
                icon={<ThunderboltOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} xl={6}>
              <KpiCard
                title="收藏转化率"
                value={(kpis?.conversion_rate.value ?? 0) * 100}
                diff={kpis?.conversion_rate.diff_percent ?? null}
                precision={1}
                suffix="%"
                icon={<PercentageOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} xl={6}>
              <KpiCard
                title="在架款式"
                value={kpis?.active_styles.value ?? 0}
                diff={kpis?.active_styles.diff_percent ?? null}
                icon={<AppstoreOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} xl={6}>
              <KpiCard
                title="新增爆款预警"
                value={kpis?.new_trending_alerts.value ?? 0}
                diff={kpis?.new_trending_alerts.diff_percent ?? null}
                icon={<FireOutlined />}
              />
            </Col>
          </Row>

          <div className="mt-5">
            <ChartCard
              title="试戴趋势"
              extra={
                <Segmented
                  size="small"
                  value="7d"
                  options={[
                    { label: "近 7 日", value: "7d" },
                    { label: "近 30 日", value: "30d", disabled: true },
                  ]}
                />
              }
            >
              <EChart option={trendOption} height={300} />
            </ChartCard>
          </div>

          <Row className="mt-5" gutter={[16, 16]}>
            <Col xs={24} xl={10}>
              <ChartCard title="款式标签分布">
                <EChart option={distributionOption} height={310} />
              </ChartCard>
            </Col>
            <Col xs={24} xl={14}>
              <ChartCard title="24 小时时段热力">
                <EChart option={heatOption} height={310} />
              </ChartCard>
            </Col>
          </Row>
        </>
      )}
    </section>
  );
}
