import { ArrowLeftOutlined, HeartFilled, HistoryOutlined } from "@ant-design/icons";
import { Empty, Segmented, Skeleton } from "antd";
import dayjs from "dayjs";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { absUrl } from "../../utils/url";

/**
 * U6 「我的试戴」 (Batch E): the user's own try-on history + collected
 * looks. Replaces the dev Placeholder (which leaked a debug bar with
 * route navigation on a public route). Data: GET /api/tryons scoped to
 * the X-User-Id the api client already sends.
 */

interface MyTryon {
  tryon_id: number;
  style_id: string;
  style_name: string;
  cover_url: string;
  result_url: string;
  is_collected: boolean;
  from_module: string;
  created_at: string | null;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

export default function U6() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<"all" | "collected">("all");
  const [items, setItems] = useState<MyTryon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadTryons = async () => {
      try {
        const response = await api.get<ApiEnvelope<{ items: MyTryon[] }>>(
          "/api/tryons",
          {
            params: { collected_only: filter === "collected", limit: 60 },
            suppressToast: true,
          },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "tryons_error");
        }
        if (!cancelled) {
          setItems(response.data.data.items);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "tryons_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadTryons();
    return () => {
      cancelled = true;
    };
  }, [filter]);

  return (
    <main className="min-h-screen bg-page">
      <div className="mx-auto max-w-[1100px] px-5 py-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="返回"
              onClick={() => navigate(-1)}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-line bg-card text-ink hover:border-brand"
            >
              <ArrowLeftOutlined />
            </button>
            <div>
              <div className="inline-flex items-center gap-1.5 rounded-full bg-brand-light px-3 py-1 text-xs font-semibold text-ink">
                <HistoryOutlined /> U6 · 我的试戴
              </div>
              <h1 className="mt-1.5 text-xl font-semibold text-ink">试戴历史与收藏</h1>
            </div>
          </div>
          <Segmented
            value={filter}
            onChange={(value) => {
              setLoading(true);
              setFilter(value as "all" | "collected");
            }}
            options={[
              { label: "全部", value: "all" },
              { label: "已收藏", value: "collected" },
            ]}
          />
        </div>

        {error && (
          <p className="mb-4 text-sm text-danger">加载失败：{error}（请确认后端已启动）</p>
        )}

        {loading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="overflow-hidden rounded-2xl border border-line bg-card">
                <div className="aspect-square animate-pulse bg-surface" />
                <div className="space-y-2 p-3">
                  <Skeleton.Input active size="small" block />
                </div>
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-3xl border border-line bg-card py-16">
            <Empty
              description={
                filter === "collected" ? "还没有收藏的试戴" : "还没有试戴记录"
              }
            >
              <Link
                to="/recommend"
                className="inline-block rounded-full bg-brand px-5 py-2 text-sm font-medium text-ink hover:bg-brand-hover"
              >
                去试戴 →
              </Link>
            </Empty>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {items.map((item) => (
              <button
                key={item.tryon_id}
                type="button"
                onClick={() => navigate(`/result/${item.tryon_id}`)}
                className="group overflow-hidden rounded-2xl border border-line bg-card text-left transition hover:shadow-lg"
              >
                <div className="relative aspect-square overflow-hidden bg-surface">
                  <img
                    src={absUrl(item.result_url)}
                    alt={item.style_name}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform group-hover:scale-105"
                  />
                  {item.is_collected && (
                    <span className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-card/90 text-danger backdrop-blur">
                      <HeartFilled />
                    </span>
                  )}
                </div>
                <div className="p-3">
                  <div className="truncate text-sm font-medium text-ink">{item.style_name}</div>
                  <div className="mt-0.5 text-xs text-ink-muted">
                    {item.created_at ? dayjs(item.created_at).format("MM-DD HH:mm") : ""}
                    <span className="mx-1">·</span>#{item.tryon_id}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
