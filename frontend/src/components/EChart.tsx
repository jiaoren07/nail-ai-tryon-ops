import * as echarts from "echarts";
import type { EChartsOption } from "echarts";
import { useEffect, useRef } from "react";

/**
 * Thin ECharts wrapper shared by ops dashboard pages (extracted from
 * Step 7.2 O1Overview so O2 sparklines / drawer charts reuse one impl).
 * Instance lifecycle is owned here: init on mount, resize via
 * ResizeObserver, dispose on unmount. Options are applied notMerge so
 * a page can swap whole option objects without stale series lingering.
 */
export default function EChart({
  option,
  height,
}: {
  option: EChartsOption;
  height: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = echarts.init(containerRef.current);
    chartRef.current = chart;
    const resizeObserver = new ResizeObserver(() => chart.resize());
    resizeObserver.observe(containerRef.current);
    return () => {
      resizeObserver.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  return <div ref={containerRef} style={{ height }} />;
}
