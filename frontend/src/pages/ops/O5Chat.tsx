import { RobotOutlined } from "@ant-design/icons";
import { Card } from "antd";
import ChatPanel from "./ChatPanel";

/** Full-page variant of the O5 assistant for the /ops/chat menu entry.
 * The floating Drawer entry (OpsLayout) is the primary UX per design-docu
 * §7.5; this page keeps the sidebar menu item meaningful. Histories are
 * per-mount — the two entries hold independent conversations. */
export default function O5Chat() {
  return (
    <section className="mx-auto flex h-[calc(100vh-224px)] min-h-[420px] max-w-[900px] flex-col">
      <div className="mb-5">
        <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
          <RobotOutlined /> O5 · AI 助手
        </div>
        <h1 className="mt-3 text-2xl font-semibold text-ink">AI 运营助手</h1>
        <p className="mt-1 text-sm text-ink-secondary">
          自然语言查数据、发现爆款冷门、执行运营动作（Function Calling · 全程审计）
        </p>
      </div>
      <Card
        className="min-h-0 flex-1 border-line shadow-sm"
        styles={{
          body: { height: "100%", display: "flex", flexDirection: "column", padding: 16 },
        }}
      >
        <ChatPanel />
      </Card>
    </section>
  );
}
