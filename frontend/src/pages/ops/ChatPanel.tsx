import { RobotOutlined, SendOutlined, UserOutlined } from "@ant-design/icons";
import { Avatar, Button, Input, Spin, Tag } from "antd";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "../../api/client";
import EChart from "../../components/EChart";

/**
 * O5 chat panel (design-docu §7.5 / plan §8.3). Used twice:
 *   - OpsLayout floating button -> Drawer (primary entry)
 *   - /ops/chat route page (menu entry, full-page variant)
 * Each mount keeps its own message history; the backend is stateless and
 * receives the full {role, content} history every turn.
 */

interface ChatComponent {
  component: string;
  data: unknown;
}

interface ChatMsg {
  role: "user" | "assistant";
  content: string;
  components?: ChatComponent[];
  failed?: boolean;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

interface ChatReply {
  reply: string;
  components: ChatComponent[];
  session_id: string | null;
  tool_rounds: number;
}

const SUGGESTIONS = [
  "今天哪款式试戴最多？",
  "这周哪些款式涨得最快？",
  "哪些款式一周完全没人试？",
];

interface TopStyleRow {
  style_id: string;
  name: string;
  tryon_count: number;
  collect_count: number;
  collect_rate: number;
}

interface TrendingRow {
  style_id: string;
  name: string;
  growth_rate: number | null;
  recent_3d: number;
  last_24h_tryons: number;
  collect_rate: number;
}

interface ActionResult {
  ok: boolean;
  style_id: string;
  name?: string;
  action_type: string;
  display_order: number;
  is_active: boolean;
  action_id: number;
}

function TopStylesTable({ rows }: { rows: TopStyleRow[] }) {
  return (
    <div className="mt-2 overflow-hidden rounded-lg border border-line bg-card">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-surface text-ink-secondary">
            <th className="px-3 py-1.5 text-left font-medium">款式</th>
            <th className="px-3 py-1.5 text-right font-medium">试戴</th>
            <th className="px-3 py-1.5 text-right font-medium">收藏率</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.style_id} className="border-t border-line">
              <td className="px-3 py-1.5 text-ink">
                {row.name}
                <span className="ml-1 text-ink-muted">{row.style_id}</span>
              </td>
              <td className="px-3 py-1.5 text-right font-medium text-ink">{row.tryon_count}</td>
              <td className="px-3 py-1.5 text-right text-ink-secondary">
                {(row.collect_rate * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TrendingList({ rows }: { rows: TrendingRow[] }) {
  return (
    <div className="mt-2 space-y-1.5">
      {rows.map((row) => (
        <div
          key={row.style_id}
          className="flex items-center justify-between rounded-lg border border-line bg-card px-3 py-2 text-xs"
        >
          <span className="min-w-0 truncate text-ink">
            {row.name}
            <span className="ml-1 text-ink-muted">{row.style_id}</span>
          </span>
          <span className="ml-3 shrink-0">
            <Tag color="volcano" bordered={false} className="mr-1">
              {row.growth_rate === null ? "首次爆发" : `+${Math.round(row.growth_rate * 100)}%`}
            </Tag>
            <span className="text-ink-secondary">24h {row.last_24h_tryons}</span>
          </span>
        </div>
      ))}
    </div>
  );
}

function MiniTrend({ values }: { values: number[] }) {
  return (
    <div className="mt-2 rounded-lg border border-line bg-card px-2 py-1">
      <EChart
        height={56}
        option={{
          animation: false,
          grid: { left: 2, right: 2, top: 6, bottom: 2 },
          xAxis: { type: "category", show: false, data: values.map((_, i) => i) },
          yAxis: { type: "value", show: false },
          series: [
            {
              type: "line",
              smooth: true,
              symbol: "none",
              lineStyle: { width: 2 },
              areaStyle: { opacity: 0.15 },
              data: values,
            },
          ],
        }}
      />
    </div>
  );
}

function ActionResultCard({ result }: { result: ActionResult }) {
  const label =
    result.action_type === "boost"
      ? "已置顶推荐位"
      : result.action_type === "demote"
        ? "已降至末位"
        : "已下架";
  return (
    <div className="mt-2 rounded-lg border border-line bg-brand-light px-3 py-2 text-xs text-ink">
      ✅ {label}：「{result.name ?? result.style_id}」 display_order={result.display_order}
      {result.is_active ? "" : "（用户端已不可见）"}
      <span className="ml-1 text-ink-muted">audit #{result.action_id}</span>
    </div>
  );
}

function ComponentBlock({ comp }: { comp: ChatComponent }) {
  // plan §8.3: render top_styles_table / trending_list / mini_trend,
  // everything else falls back to compact JSON.
  if (comp.component === "top_styles_table" && Array.isArray(comp.data)) {
    return <TopStylesTable rows={comp.data as TopStyleRow[]} />;
  }
  if (comp.component === "trending_list" && Array.isArray(comp.data)) {
    return <TrendingList rows={comp.data as TrendingRow[]} />;
  }
  if (comp.component === "mini_trend" && Array.isArray(comp.data)) {
    return <MiniTrend values={comp.data as number[]} />;
  }
  if (comp.component === "action_result") {
    return <ActionResultCard result={comp.data as ActionResult} />;
  }
  return (
    <pre className="mt-2 max-h-48 overflow-auto rounded-lg border border-line bg-surface px-3 py-2 text-[11px] leading-4 text-ink-secondary">
      {JSON.stringify(comp.data, null, 2)}
    </pre>
  );
}

function Bubble({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar
        size={30}
        className={isUser ? "shrink-0 bg-ink" : "shrink-0 bg-brand text-ink"}
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
      />
      <div className={`min-w-0 max-w-[85%] ${isUser ? "text-right" : ""}`}>
        <div
          className={
            isUser
              ? "inline-block rounded-2xl rounded-tr-sm bg-ink px-3.5 py-2 text-left text-sm text-white"
              : msg.failed
                ? "inline-block rounded-2xl rounded-tl-sm border border-danger/40 bg-card px-3.5 py-2 text-sm text-danger"
                : "chat-md inline-block rounded-2xl rounded-tl-sm border border-line bg-card px-3.5 py-2 text-sm text-ink"
          }
        >
          {isUser || msg.failed ? msg.content : <ReactMarkdown>{msg.content}</ReactMarkdown>}
        </div>
        {msg.components?.map((comp, i) => (
          <ComponentBlock key={i} comp={comp} />
        ))}
      </div>
    </div>
  );
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  // Lazily minted on first send — render must stay pure (react-hooks/purity).
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const send = useCallback(
    async (text: string) => {
      const question = text.trim();
      if (!question || sending) return;
      if (!sessionIdRef.current) {
        sessionIdRef.current = `ops_${crypto.randomUUID().slice(0, 8)}`;
      }
      const nextMessages: ChatMsg[] = [...messages, { role: "user", content: question }];
      setMessages(nextMessages);
      setDraft("");
      setSending(true);
      try {
        const response = await api.post<ApiEnvelope<ChatReply>>(
          "/api/ops/chat",
          {
            messages: nextMessages.map((m) => ({ role: m.role, content: m.content })),
            session_id: sessionIdRef.current,
          },
          { suppressToast: true, timeout: 120_000 },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "chat_error");
        }
        const { reply, components } = response.data.data;
        setMessages((prev) => [...prev, { role: "assistant", content: reply, components }]);
      } catch (requestError) {
        const msg =
          requestError instanceof Error ? requestError.message : "chat_request_failed";
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `请求失败（${msg}），请稍后重试`, failed: true },
        ]);
      } finally {
        setSending(false);
      }
    },
    [messages, sending],
  );

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="rounded-xl border border-line bg-surface px-4 py-4">
            <div className="text-sm font-semibold text-ink">你好，我是运营 AI 助手</div>
            <p className="mt-1 text-xs leading-5 text-ink-secondary">
              可以用自然语言查询试戴数据、发现爆款与冷门，或直接让我执行推荐位调整、下架等动作
              （动作即时生效并写入审计）。
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <Tag
                  key={s}
                  className="cursor-pointer select-none"
                  onClick={() => void send(s)}
                >
                  {s}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <Bubble key={i} msg={msg} />
        ))}

        {sending && (
          <div className="flex items-center gap-2.5">
            <Avatar size={30} className="shrink-0 bg-brand text-ink" icon={<RobotOutlined />} />
            <div className="rounded-2xl rounded-tl-sm border border-line bg-card px-3.5 py-2">
              <Spin size="small" />
              <span className="ml-2 text-xs text-ink-muted">正在查询数据…</span>
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 flex items-end gap-2 border-t border-line pt-3">
        <Input.TextArea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoSize={{ minRows: 1, maxRows: 4 }}
          placeholder="输入问题，回车发送，Shift+回车换行"
          disabled={sending}
          onPressEnter={(e) => {
            if (e.shiftKey) return; // Shift+Enter = newline
            e.preventDefault();
            void send(draft);
          }}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          loading={sending}
          disabled={!draft.trim()}
          onClick={() => void send(draft)}
        >
          发送
        </Button>
      </div>
    </div>
  );
}
