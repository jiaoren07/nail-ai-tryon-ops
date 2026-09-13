import { SwapOutlined } from "@ant-design/icons";
import { Link } from "react-router-dom";

/** Batch J: consumer-side jump to the ops console — the mirror of the
 * ops sidebar's 「切换到用户端」. A real consumer product wouldn't
 * surface an ops entry, but this is a dual-end showcase: hopping
 * between both sides quickly IS the demo, so every consumer header
 * carries this pill (user request, 2026-09-13). One click, no menu —
 * with only two sides a dropdown would just add a step. */
export default function SideSwitch() {
  return (
    <Link
      to="/ops/overview"
      aria-label="切换到运营端"
      className="inline-flex shrink-0 items-center gap-1 rounded-full border border-line bg-card px-3 py-1 text-xs text-ink-secondary transition hover:border-brand hover:text-ink"
    >
      <SwapOutlined /> 运营端
    </Link>
  );
}
