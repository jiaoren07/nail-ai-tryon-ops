import { App as AntApp, Checkbox, Spin } from "antd";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { useUser } from "../../store/UserContext";

/**
 * U2 智能推荐页（design-docu §6.3, plan §5.5, 原型 Board 1 第 3 屏）.
 *
 * Guards:
 *  - !userGender -> /gender
 *  - !photoId || !handFeatures -> /upload
 *
 * Flow:
 *  1. POST /api/recommend with (gender, hand_features) -> 9 cards
 *  2. Each card: cover + tags + LLM reason (<=25 chars) + "试这款" + "加入对比"
 *  3. Floating "对比试戴 (n)" bottom-right when >=2 picked
 *  4. "试这款" -> POST /api/tryon -> navigate /result/:id with state
 */
interface RecommendItem {
  style_id: string;
  name: string;
  cover_url: string;
  color_main: string;
  style_tags: string[];
  score: number;
  reason: string;
}

interface RecommendData {
  user_summary: string;
  recommendations: RecommendItem[];
}

export default function U2() {
  const {
    userId, userGender, handFeatures, photoId,
    compareSelection, setCompareSelection,
  } = useUser();
  const { message } = AntApp.useApp();
  const navigate = useNavigate();
  const [data, setData] = useState<RecommendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tryingStyleId, setTryingStyleId] = useState<string | null>(null);

  // Guards — both hooks declared unconditionally at the top so React's
  // call-order invariant holds even when render bails out early below.
  useEffect(() => {
    if (!userGender) { navigate("/gender", { replace: true }); return; }
    if (!photoId || !handFeatures) { navigate("/upload", { replace: true }); return; }
  }, [userGender, photoId, handFeatures, navigate]);

  // Fetch recommendations (internal guard, runs only when all 3 are set)
  useEffect(() => {
    if (!userGender || !photoId || !handFeatures) return;
    let cancelled = false;
    async function go() {
      setLoading(true);
      try {
        const r = await api.post("/api/recommend", {
          user_id: userId,
          gender: userGender,
          hand_features: handFeatures,
        });
        if (!cancelled && r.data?.code === 0) {
          setData(r.data.data);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    go();
    return () => { cancelled = true; };
  }, [userId, userGender, handFeatures, photoId]);

  if (!userGender || !photoId || !handFeatures) return null;

  function toggleCompare(styleId: string) {
    if (compareSelection.includes(styleId)) {
      setCompareSelection(compareSelection.filter((id) => id !== styleId));
    } else {
      setCompareSelection([...compareSelection, styleId]);
    }
  }

  async function tryOne(item: RecommendItem) {
    if (tryingStyleId) return;
    setTryingStyleId(item.style_id);
    try {
      const r = await api.post("/api/tryon", {
        user_id: userId,
        style_id: item.style_id,
        photo_id: photoId,
        user_gender: userGender,
        skin_tone: handFeatures!.skin_tone,
        hand_shape: handFeatures!.hand_shape,
        from_module: "recommend",
      }, { suppressToast: true });
      if (r.data?.code === 0) {
        // Stash result in nav state so U5 can render without a second fetch.
        navigate(`/result/${r.data.data.tryon_id}`, {
          state: { ...r.data.data, style: item },
        });
      } else {
        message.error("试戴失败：" + (r.data?.msg ?? "未知错误"));
      }
    } catch {
      message.error("试戴失败，请重试");
    } finally {
      setTryingStyleId(null);
    }
  }

  function gotoCompare() {
    if (compareSelection.length < 2) return;
    navigate("/compare");
  }

  return (
    <div className="min-h-screen flex flex-col bg-page pb-32">
      {/* === Top bar === */}
      <header className="px-6 py-4 flex items-center gap-3 border-b border-line bg-card sticky top-0 z-10">
        <Link
          to="/upload"
          className="inline-flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface text-ink-secondary"
          aria-label="返回上传"
        >
          ←
        </Link>
        <div className="flex-1 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-brand text-ink font-bold text-xs">
            AI
          </span>
          <span className="text-sm font-medium text-ink">智能推荐</span>
        </div>
      </header>

      {/* === User-summary card === */}
      <section className="px-6 pt-6">
        <div className="max-w-6xl mx-auto bg-card border border-line rounded-3xl p-5 flex items-center gap-4 shadow-sm">
          <div className="w-14 h-14 rounded-full bg-brand-light flex items-center justify-center text-2xl">
            👋
          </div>
          <div className="flex-1">
            <p className="text-xs text-ink-muted mb-0.5">AI 为你识别到：</p>
            <p className="text-base font-semibold text-ink">
              {data?.user_summary ?? "正在分析你的手部特征..."}
            </p>
          </div>
          <span className="hidden md:inline-block px-3 py-1 rounded-full bg-ai-wash text-ai-purple text-xs font-medium">
            U2 · 智能推荐 9 款
          </span>
        </div>
      </section>

      {/* === Recommend grid === */}
      <main className="flex-1 px-6 py-8">
        <div className="max-w-6xl mx-auto">
          {loading ? <SkeletonGrid /> : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {(data?.recommendations ?? []).map((item) => (
                <Card
                  key={item.style_id}
                  item={item}
                  selected={compareSelection.includes(item.style_id)}
                  trying={tryingStyleId === item.style_id}
                  disabled={tryingStyleId !== null}
                  onToggleCompare={() => toggleCompare(item.style_id)}
                  onTry={() => tryOne(item)}
                />
              ))}
            </div>
          )}

          {/* Footer link */}
          <div className="text-center mt-12">
            <Link
              to="/browse"
              className="text-sm text-ink-secondary hover:text-ink underline-offset-4 hover:underline"
            >
              想看更多？浏览全部款式 →
            </Link>
          </div>
        </div>
      </main>

      {/* === Floating compare button === */}
      {compareSelection.length >= 2 && (
        <button
          type="button"
          onClick={gotoCompare}
          className="fixed bottom-8 right-8 z-20 px-6 py-3 rounded-full bg-brand text-ink font-semibold shadow-2xl hover:bg-brand-hover transition flex items-center gap-2"
        >
          对比试戴 ({compareSelection.length})
          <span className="inline-block">→</span>
        </button>
      )}
    </div>
  );
}

interface CardProps {
  item: RecommendItem;
  selected: boolean;
  trying: boolean;
  disabled: boolean;
  onToggleCompare: () => void;
  onTry: () => void;
}

function Card({ item, selected, trying, disabled, onToggleCompare, onTry }: CardProps) {
  const coverUrl = item.cover_url.startsWith("http")
    ? item.cover_url
    : `http://localhost:8000${item.cover_url}`;

  return (
    <div className={`group bg-card rounded-3xl border overflow-hidden transition shadow-sm hover:shadow-lg ${
      selected ? "border-brand ring-2 ring-brand-light" : "border-line"
    }`}>
      <div className="aspect-square bg-surface relative overflow-hidden">
        <img
          src={coverUrl}
          alt={item.name}
          className="w-full h-full object-cover transition-transform group-hover:scale-105"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
        <span
          className="absolute top-3 left-3 px-2 py-0.5 rounded-full bg-card/90 text-ink text-xs font-medium backdrop-blur"
          style={{ borderLeft: `3px solid ${item.color_main}` }}
        >
          {item.style_tags[0] ?? "美甲"}
        </span>
      </div>

      <div className="p-4">
        <h3 className="text-base font-semibold text-ink mb-1 truncate">{item.name}</h3>
        <p className="text-sm text-ink-secondary mb-3 line-clamp-2 min-h-[2.5rem]">
          {item.reason}
        </p>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onTry}
            disabled={disabled}
            className="flex-1 px-3 py-2 rounded-full bg-brand text-ink text-sm font-medium hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {trying ? <Spin size="small" /> : null}
            {trying ? "AI 生成中..." : "试这款"}
          </button>
          <label className="inline-flex items-center gap-1.5 text-xs text-ink-secondary cursor-pointer select-none px-2">
            <Checkbox checked={selected} onChange={onToggleCompare} />
            <span>加入对比</span>
          </label>
        </div>
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="bg-card rounded-3xl border border-line overflow-hidden">
          <div className="aspect-square bg-surface animate-pulse" />
          <div className="p-4 space-y-3">
            <div className="h-4 bg-surface rounded animate-pulse w-2/3" />
            <div className="h-3 bg-surface rounded animate-pulse" />
            <div className="h-3 bg-surface rounded animate-pulse w-4/5" />
            <div className="h-9 bg-surface rounded-full animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}
