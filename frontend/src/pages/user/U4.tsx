import { App as AntApp, Spin } from "antd";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { useUser } from "../../store/UserContext";

/**
 * U4 多款对比试戴页（design-docu §6.5, plan §5.7, 原型 Board 2 第 2 屏）.
 *
 * Guards:
 *   !userGender                       -> /gender
 *   !photoId || !handFeatures         -> /upload
 *   compareSelection.length < 2       -> /recommend (with toast)
 *   compareSelection.length > 4       -> truncated to first 4
 *
 * Two parallel fetches on mount:
 *   POST /api/tryon/batch  -> N tryon results (status ok|failed)
 *   GET  /api/styles       -> map of style_id -> {name, cover_url, ...}
 *                             for the "原款式" header thumbnails
 *
 * Per-card 3 states: loading / ok (clickable to /result) / failed (retry).
 */
interface BatchItem {
  style_id: string;
  status: "ok" | "failed";
  tryon_id: number | null;
  result_url: string | null;
  elapsed_ms: number | null;
  error?: string;
}

interface StyleMeta {
  id: string;
  name: string;
  cover_url: string;
  color_main: string;
  style_tags: string[];
}

const MAX_COMPARE = 4;

export default function U4() {
  const {
    userId, userGender, handFeatures, photoId,
    compareSelection, setCompareSelection,
  } = useUser();
  const { message } = AntApp.useApp();
  const navigate = useNavigate();

  const styleIds = useMemo(
    () => compareSelection.slice(0, MAX_COMPARE),
    [compareSelection],
  );

  const [batchItems, setBatchItems] = useState<BatchItem[]>([]);
  const [stylesMap, setStylesMap] = useState<Record<string, StyleMeta>>({});
  const [loading, setLoading] = useState(true);
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());

  // Guard: hooks declared at top, conditional return at bottom.
  useEffect(() => {
    if (!userGender) {
      navigate("/gender", { replace: true });
      return;
    }
    if (!photoId || !handFeatures) {
      navigate("/upload", { replace: true });
      return;
    }
    if (styleIds.length < 2) {
      message.warning("请先在推荐页选 ≥2 款再进入对比");
      navigate("/recommend", { replace: true });
    }
  }, [userGender, photoId, handFeatures, styleIds.length, navigate, message]);

  // Parallel: batch tryon + style metadata
  useEffect(() => {
    if (!userGender || !photoId || !handFeatures || styleIds.length < 2) return;
    let cancelled = false;
    async function go() {
      setLoading(true);
      try {
        const [batchR, stylesR] = await Promise.all([
          api.post(
            "/api/tryon/batch",
            {
              user_id: userId,
              photo_id: photoId,
              style_ids: styleIds,
              user_gender: userGender,
              skin_tone: handFeatures!.skin_tone,
              hand_shape: handFeatures!.hand_shape,
              from_module: "compare",
            },
            { suppressToast: true },
          ),
          api.get(`/api/styles?gender=${userGender}&size=100`),
        ]);
        if (cancelled) return;
        if (batchR.data?.code === 0) {
          setBatchItems(batchR.data.data.items);
        }
        if (stylesR.data?.code === 0) {
          const map: Record<string, StyleMeta> = {};
          for (const s of stylesR.data.data.items) map[s.id] = s;
          setStylesMap(map);
        }
      } catch {
        message.error("批量试戴失败，请重试");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    go();
    return () => {
      cancelled = true;
    };
  }, [userId, userGender, handFeatures, photoId, styleIds.join(","), message]);

  async function retry(styleId: string) {
    if (retryingIds.has(styleId)) return;
    setRetryingIds((prev) => {
      const n = new Set(prev);
      n.add(styleId);
      return n;
    });
    try {
      const r = await api.post(
        "/api/tryon",
        {
          user_id: userId,
          style_id: styleId,
          photo_id: photoId,
          user_gender: userGender,
          skin_tone: handFeatures!.skin_tone,
          hand_shape: handFeatures!.hand_shape,
          from_module: "compare",
        },
        { suppressToast: true },
      );
      if (r.data?.code === 0) {
        setBatchItems((prev) =>
          prev.map((it) =>
            it.style_id === styleId
              ? {
                  style_id: styleId,
                  status: "ok",
                  tryon_id: r.data.data.tryon_id,
                  result_url: r.data.data.result_url,
                  elapsed_ms: r.data.data.elapsed_ms,
                }
              : it,
          ),
        );
      } else {
        message.error("重试失败：" + (r.data?.msg ?? "未知错误"));
      }
    } catch {
      message.error("重试失败，请稍后再试");
    } finally {
      setRetryingIds((prev) => {
        const n = new Set(prev);
        n.delete(styleId);
        return n;
      });
    }
  }

  function clearCompare() {
    setCompareSelection([]);
    navigate("/recommend");
  }

  function viewResult(item: BatchItem, meta: StyleMeta | undefined) {
    if (item.status !== "ok" || !item.result_url || item.tryon_id == null) return;
    // Step 5.8 made batch return real tryon_id; navigate to the canonical
    // /result/:tryon_id path. Nav state is the fast hydration; if missing
    // U5 falls back to GET /api/tryon/:id.
    navigate(`/result/${item.tryon_id}`, {
      state: {
        result_url: item.result_url,
        elapsed_ms: item.elapsed_ms,
        style: meta ?? { id: item.style_id, name: item.style_id, cover_url: "", color_main: "", style_tags: [] },
      },
    });
  }

  if (!userGender || !photoId || !handFeatures || styleIds.length < 2) {
    return null;
  }

  const truncated = compareSelection.length > MAX_COMPARE;

  // Tailwind dynamic col class — N=3 uses 3 cols on lg, others use 2.
  const lgCols = styleIds.length === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2";

  return (
    <div className="min-h-screen flex flex-col bg-page pb-24">
      {/* === Top bar === */}
      <header className="px-6 py-4 flex items-center gap-3 border-b border-line bg-card sticky top-0 z-10">
        <Link
          to="/recommend"
          className="inline-flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface text-ink-secondary"
          aria-label="返回推荐"
        >
          ←
        </Link>
        <div className="flex-1 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-brand text-ink font-bold text-xs">
            AI
          </span>
          <span className="text-sm font-medium text-ink">对比试戴</span>
          <span className="text-xs text-ink-muted ml-2">{styleIds.length} 款并行</span>
        </div>
        <button
          type="button"
          onClick={clearCompare}
          className="px-3 py-1 rounded-full border border-line text-xs text-ink-secondary hover:border-danger hover:text-danger transition"
        >
          清空对比
        </button>
      </header>

      {/* === Truncation notice === */}
      {truncated && (
        <div className="px-6 pt-3">
          <div className="max-w-6xl mx-auto bg-brand-light border border-brand text-ink text-xs rounded-2xl px-4 py-2">
            最多支持 4 款并行对比，已为你取前 4 款；多选的款式可回到推荐页重新选择。
          </div>
        </div>
      )}

      {/* === Grid === */}
      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto">
          <div className={`grid grid-cols-1 sm:grid-cols-2 ${lgCols} gap-5`}>
            {styleIds.map((sid, idx) => {
              const meta = stylesMap[sid];
              const result = batchItems.find((b) => b.style_id === sid);
              const isLoading = loading || !result;
              const isOk = result?.status === "ok";
              const isFailed = result?.status === "failed";
              const isRetrying = retryingIds.has(sid);
              return (
                <CompareCard
                  key={sid}
                  idx={idx + 1}
                  meta={meta}
                  styleId={sid}
                  loading={isLoading}
                  ok={isOk}
                  failed={isFailed && !isRetrying}
                  retrying={isRetrying}
                  resultUrl={result?.result_url ?? null}
                  elapsedMs={result?.elapsed_ms ?? null}
                  error={result?.error}
                  onRetry={() => retry(sid)}
                  onView={() => result && viewResult(result, meta)}
                />
              );
            })}
          </div>
        </div>
      </main>
    </div>
  );
}

interface CompareCardProps {
  idx: number;
  styleId: string;
  meta: StyleMeta | undefined;
  loading: boolean;
  ok: boolean;
  failed: boolean;
  retrying: boolean;
  resultUrl: string | null;
  elapsedMs: number | null;
  error?: string;
  onRetry: () => void;
  onView: () => void;
}

function CompareCard({
  idx, styleId, meta, loading, ok, failed, retrying,
  resultUrl, elapsedMs, error, onRetry, onView,
}: CompareCardProps) {
  const coverUrl = meta?.cover_url?.startsWith("http")
    ? meta.cover_url
    : meta?.cover_url
    ? `http://localhost:8000${meta.cover_url}`
    : "";
  const fullResultUrl = resultUrl?.startsWith("http")
    ? resultUrl
    : resultUrl
    ? `http://localhost:8000${resultUrl}`
    : "";

  return (
    <div className="bg-card border border-line rounded-3xl overflow-hidden shadow-sm flex flex-col">
      {/* Card header: idx badge + name + original cover thumb */}
      <div className="px-4 py-3 flex items-center gap-3 border-b border-line">
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand text-ink text-xs font-bold">
          {idx}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-ink truncate">
            {meta?.name ?? styleId}
          </p>
          <p className="text-xs text-ink-muted truncate">
            {meta?.style_tags?.slice(0, 3).join(" · ") ?? ""}
          </p>
        </div>
        {coverUrl && (
          <div className="w-10 h-10 rounded-lg overflow-hidden border border-line shrink-0 bg-surface">
            <img
              src={coverUrl}
              alt="原款"
              className="w-full h-full object-cover"
              onError={(e) => { e.currentTarget.style.display = "none"; }}
            />
          </div>
        )}
      </div>

      {/* Body: large result area */}
      <div className="aspect-square bg-surface relative flex items-center justify-center">
        {(loading || retrying) && (
          <div className="flex flex-col items-center gap-3 text-ink-muted">
            <Spin size="large" />
            <p className="text-xs">{retrying ? "重试中..." : "AI 合成中..."}</p>
          </div>
        )}
        {ok && fullResultUrl && (
          <img
            src={fullResultUrl}
            alt="试戴结果"
            className="w-full h-full object-cover"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
          />
        )}
        {failed && (
          <div className="flex flex-col items-center gap-3 px-6 text-center">
            <span className="text-4xl">⚠️</span>
            <p className="text-sm text-ink-secondary">生成失败</p>
            {error && (
              <p className="text-xs text-ink-muted break-all">{error}</p>
            )}
            <button
              type="button"
              onClick={onRetry}
              className="px-4 py-1.5 rounded-full bg-brand text-ink text-xs font-medium hover:bg-brand-hover transition"
            >
              点击重试
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 flex items-center justify-between border-t border-line bg-card">
        <span className="text-xs text-ink-muted">
          {ok && elapsedMs !== null ? `${elapsedMs}ms 完成` : ""}
        </span>
        <button
          type="button"
          onClick={onView}
          disabled={!ok}
          className="px-3 py-1.5 rounded-full bg-brand text-ink text-xs font-medium hover:bg-brand-hover disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          查看大图 →
        </button>
      </div>
    </div>
  );
}
