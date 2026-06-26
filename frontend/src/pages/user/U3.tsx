import { App as AntApp, Segmented, Spin } from "antd";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "../../api/client";
import { useUser } from "../../store/UserContext";

/**
 * U3 款式浏览页（design-docu §6.4, plan §5.6, 原型 Board 2 第 1 屏）.
 *
 * URL-synced filters (refresh-safe):
 *   ?gender=female|male   (override Context userGender)
 *   ?sort=smart|hot|new
 *   ?tags=极简,法式        (comma-separated)
 *   ?color=warm|cool|neutral
 *   ?length=short|medium|long
 *
 * Data path: single GET /api/styles call per filter combination (size=100
 * fetches the whole matching pool — 40-style dataset doesn't warrant
 * paginated infinite scroll, plan §5.6 said "下拉加载" but verification
 * doesn't require it). Tag chips top-8 are aggregated client-side from a
 * separate unfiltered pool fetch keyed on gender.
 *
 * Compare flow & 试这款 flow mirror U2 exactly.
 */
interface StyleItem {
  id: string;
  name: string;
  cover_url: string;
  gender: string;
  style_tags: string[];
  color_main: string;
  length_pref: string;
}

export default function U3() {
  const {
    userId, userGender, handFeatures, photoId,
    compareSelection, setCompareSelection,
  } = useUser();
  const { message } = AntApp.useApp();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL-derived state (the URL IS the source of truth)
  const sort = searchParams.get("sort") ?? "smart";
  const tagsParam = searchParams.get("tags") ?? "";
  const colorTone = searchParams.get("color") ?? "";
  const lengthPref = searchParams.get("length") ?? "";
  const genderOverride = searchParams.get("gender");
  const activeGender = (genderOverride === "female" || genderOverride === "male")
    ? genderOverride
    : userGender;

  const selectedTags = useMemo(
    () => (tagsParam ? tagsParam.split(",").filter(Boolean) : []),
    [tagsParam],
  );

  const [items, setItems] = useState<StyleItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [tagPool, setTagPool] = useState<string[]>([]);
  const [tryingStyleId, setTryingStyleId] = useState<string | null>(null);

  // Guard: U3 doesn't strictly need photoId/handFeatures (browsing is
  // read-only), but it DOES need userGender (or a ?gender= override).
  useEffect(() => {
    if (!activeGender) navigate("/gender", { replace: true });
  }, [activeGender, navigate]);

  // Tag pool: derive top-8 frequent style_tags per gender (gender-keyed
  // cache; re-fetches only when activeGender changes, not on filter
  // changes). Gives the chip bar a stable list even after filtering.
  useEffect(() => {
    const g = activeGender;
    if (!g) return;
    let cancelled = false;
    async function go() {
      try {
        const r = await api.get(`/api/styles?gender=${g}&size=100`);
        if (!cancelled && r.data?.code === 0) {
          const all = r.data.data.items as StyleItem[];
          const counter: Record<string, number> = {};
          for (const it of all) {
            for (const t of it.style_tags) {
              counter[t] = (counter[t] ?? 0) + 1;
            }
          }
          const top8 = Object.entries(counter)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 8)
            .map(([t]) => t);
          setTagPool(top8);
        }
      } catch {
        /* silently ignore — tag bar is non-critical */
      }
    }
    go();
    return () => { cancelled = true; };
  }, [activeGender]);

  // Filtered list fetch
  useEffect(() => {
    const g = activeGender;
    if (!g) return;
    let cancelled = false;
    async function go() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ gender: g!, sort, size: "100" });
        if (tagsParam) params.set("tags", tagsParam);
        if (colorTone) params.set("color_tone", colorTone);
        if (lengthPref) params.set("length_pref", lengthPref);
        const r = await api.get(`/api/styles?${params}`);
        if (!cancelled && r.data?.code === 0) {
          setItems(r.data.data.items);
          setTotal(r.data.data.total);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    go();
    return () => { cancelled = true; };
  }, [activeGender, sort, tagsParam, colorTone, lengthPref]);

  // URL mutation helper — preserves other params, clears empty values
  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  }

  function toggleTag(tag: string) {
    const next = selectedTags.includes(tag)
      ? selectedTags.filter((t) => t !== tag)
      : [...selectedTags, tag];
    updateParam("tags", next.join(","));
  }

  function switchGender(g: "female" | "male") {
    // Switching gender resets filter context (different style pool has
    // different valid tags/colors). Preserve only sort.
    const next = new URLSearchParams();
    next.set("gender", g);
    next.set("sort", sort);
    setSearchParams(next);
  }

  function toggleCompare(styleId: string) {
    if (compareSelection.includes(styleId)) {
      setCompareSelection(compareSelection.filter((id) => id !== styleId));
    } else {
      setCompareSelection([...compareSelection, styleId]);
    }
  }

  async function tryOne(item: StyleItem) {
    if (!photoId || !handFeatures) {
      message.warning("还没上传手图，先去上传");
      navigate("/upload");
      return;
    }
    if (tryingStyleId) return;
    setTryingStyleId(item.id);
    try {
      const r = await api.post(
        "/api/tryon",
        {
          user_id: userId,
          style_id: item.id,
          photo_id: photoId,
          user_gender: activeGender,
          skin_tone: handFeatures.skin_tone,
          hand_shape: handFeatures.hand_shape,
          from_module: "browse",
        },
        { suppressToast: true },
      );
      if (r.data?.code === 0) {
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

  if (!activeGender) return null;

  return (
    <div className="min-h-screen flex flex-col bg-page pb-32">
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
          <span className="text-sm font-medium text-ink">款式浏览</span>
          <span className="text-xs text-ink-muted ml-2">共 {total} 款</span>
        </div>
        {/* Gender toggle */}
        <Segmented
          size="small"
          value={activeGender}
          onChange={(v) => switchGender(v as "female" | "male")}
          options={[
            { label: "女款", value: "female" },
            { label: "男款", value: "male" },
          ]}
        />
      </header>

      {/* === Filter bar === */}
      <section className="px-6 py-4 border-b border-line bg-card">
        <div className="max-w-6xl mx-auto space-y-3">
          {/* Tag chips */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <span className="text-xs text-ink-muted shrink-0">标签：</span>
            {tagPool.length === 0 && (
              <span className="text-xs text-ink-muted">加载中…</span>
            )}
            {tagPool.map((t) => {
              const on = selectedTags.includes(t);
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() => toggleTag(t)}
                  className={`shrink-0 px-3 py-1 rounded-full text-xs border transition ${
                    on
                      ? "bg-brand text-ink border-brand"
                      : "bg-card text-ink-secondary border-line hover:border-brand hover:text-ink"
                  }`}
                >
                  {t}
                </button>
              );
            })}
            {selectedTags.length > 0 && (
              <button
                type="button"
                onClick={() => updateParam("tags", "")}
                className="shrink-0 text-xs text-ink-muted hover:text-danger ml-2"
              >
                清空标签
              </button>
            )}
          </div>

          {/* Sort + color + length */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-ink-muted">排序：</span>
              <Segmented
                size="small"
                value={sort}
                onChange={(v) => updateParam("sort", v as string)}
                options={[
                  { label: "智能", value: "smart" },
                  { label: "最热", value: "hot" },
                  { label: "最新", value: "new" },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-ink-muted">色调：</span>
              <Segmented
                size="small"
                value={colorTone || "all"}
                onChange={(v) => updateParam("color", v === "all" ? "" : (v as string))}
                options={[
                  { label: "全部", value: "all" },
                  { label: "暖调", value: "warm" },
                  { label: "冷调", value: "cool" },
                  { label: "裸色", value: "neutral" },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-ink-muted">长度：</span>
              <Segmented
                size="small"
                value={lengthPref || "all"}
                onChange={(v) => updateParam("length", v === "all" ? "" : (v as string))}
                options={[
                  { label: "全部", value: "all" },
                  { label: "短", value: "short" },
                  { label: "中", value: "medium" },
                  { label: "长", value: "long" },
                ]}
              />
            </div>
          </div>
        </div>
      </section>

      {/* === Main === */}
      <main className="flex-1 px-6 py-6">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="flex justify-center py-16">
              <Spin size="large" />
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-16 text-ink-muted text-sm">
              没有匹配的款式，换个筛选条件试试？
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {items.map((item) => (
                <BrowseCard
                  key={item.id}
                  item={item}
                  selected={compareSelection.includes(item.id)}
                  trying={tryingStyleId === item.id}
                  disabled={tryingStyleId !== null}
                  onToggleCompare={() => toggleCompare(item.id)}
                  onTry={() => tryOne(item)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* === Floating compare button === */}
      {compareSelection.length >= 2 && (
        <button
          type="button"
          onClick={() => navigate("/compare")}
          className="fixed bottom-8 right-8 z-20 px-6 py-3 rounded-full bg-brand text-ink font-semibold shadow-2xl hover:bg-brand-hover transition flex items-center gap-2"
        >
          对比试戴 ({compareSelection.length})
          <span>→</span>
        </button>
      )}
    </div>
  );
}

interface BrowseCardProps {
  item: StyleItem;
  selected: boolean;
  trying: boolean;
  disabled: boolean;
  onToggleCompare: () => void;
  onTry: () => void;
}

function BrowseCard({ item, selected, trying, disabled, onToggleCompare, onTry }: BrowseCardProps) {
  const coverUrl = item.cover_url.startsWith("http")
    ? item.cover_url
    : `http://localhost:8000${item.cover_url}`;
  return (
    <div className={`group bg-card rounded-2xl border overflow-hidden transition shadow-sm hover:shadow-md ${
      selected ? "border-brand ring-2 ring-brand-light" : "border-line"
    }`}>
      <div className="aspect-square bg-surface relative overflow-hidden">
        <img
          src={coverUrl}
          alt={item.name}
          className="w-full h-full object-cover transition-transform group-hover:scale-105"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
        {/* color swatch dot */}
        <span
          className="absolute top-2 right-2 w-5 h-5 rounded-full border-2 border-white shadow"
          style={{ background: item.color_main }}
          title={item.color_main}
        />
        {/* compare checkbox overlay */}
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); onToggleCompare(); }}
          className={`absolute bottom-2 left-2 px-2 py-0.5 rounded-full text-xs backdrop-blur transition ${
            selected
              ? "bg-brand text-ink"
              : "bg-card/90 text-ink-secondary hover:bg-card"
          }`}
        >
          {selected ? "已加入对比 ✓" : "加入对比"}
        </button>
      </div>
      <div className="p-3">
        <h3 className="text-sm font-medium text-ink mb-2 truncate">{item.name}</h3>
        <button
          type="button"
          onClick={onTry}
          disabled={disabled}
          className="w-full px-3 py-1.5 rounded-full bg-brand text-ink text-xs font-medium hover:bg-brand-hover disabled:opacity-50 flex items-center justify-center gap-1.5"
        >
          {trying ? <Spin size="small" /> : null}
          {trying ? "AI 生成中..." : "试这款"}
        </button>
      </div>
    </div>
  );
}
