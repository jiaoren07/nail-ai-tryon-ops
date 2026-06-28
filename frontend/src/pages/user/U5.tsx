import { App as AntApp, Spin } from "antd";
import { useEffect, useState } from "react";
import ReactCompareImage from "react-compare-image";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import { useUser } from "../../store/UserContext";

/**
 * U5 单款试戴结果页（design-docu §6.6, plan §5.8, 原型 Board 3 第 1 屏）.
 *
 * Data sources, in order of preference:
 *   1. Nav state from U2/U3/U4 (avoids extra round-trip)
 *   2. GET /api/tryon/:id (F5 fallback, deep-link survival)
 *   3. Error placeholder if both fail
 *
 * Operations bar (5 buttons per plan §5.8):
 *   - 保存:        canvas.toBlob() download of the result image
 *   - 分享:        copy current page URL to clipboard
 *   - 收藏:        POST /api/events/collect (atomic, idempotent)
 *   - 换一款再试:   navigate /recommend
 *   - 找店预约:    placeholder toast
 */
interface TryonDetail {
  tryon_id: number;
  user_id: string;
  style_id: string;
  result_url: string;
  original_url: string | null;
  is_collected: boolean;
  from_module: string;
  style: {
    id: string;
    name: string;
    cover_url: string;
    color_main: string;
    style_tags: string[];
    color_tone: string;
    length_pref: string;
  };
}

function absUrl(u: string | null | undefined): string {
  if (!u) return "";
  return u.startsWith("http") ? u : `http://localhost:8000${u}`;
}

export default function U5() {
  const { id: pathId } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { message } = AntApp.useApp();
  const { photoId: ctxPhotoId } = useUser();

  const [detail, setDetail] = useState<TryonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collected, setCollected] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load: try nav state first, then GET /api/tryon/:id
  useEffect(() => {
    let cancelled = false;
    async function go() {
      setLoading(true);
      setError(null);

      // 1) Nav state (from U2/U3 single-tryon flow)
      const navState = location.state as
        | { result_url?: string; style?: any; original_url?: string }
        | null;

      const idNum = Number(pathId);
      const looksLikeId = !Number.isNaN(idNum) && Number.isInteger(idNum);

      if (navState?.result_url && navState.style && looksLikeId) {
        // Hydrate from nav state (no API call) — fastest path
        const d: TryonDetail = {
          tryon_id: idNum,
          user_id: sessionStorage.getItem("userId") || "",
          style_id: navState.style.id ?? navState.style.style_id ?? "",
          result_url: navState.result_url,
          original_url: navState.original_url ?? null,
          is_collected: false,
          from_module: "recommend",
          style: navState.style,
        };
        if (!cancelled) {
          setDetail(d);
          setCollected(d.is_collected);
          setLoading(false);
        }
        return;
      }

      // 2) GET /api/tryon/:id — F5 / deep-link fallback
      if (!looksLikeId) {
        if (!cancelled) {
          setError("invalid_tryon_id");
          setLoading(false);
        }
        return;
      }
      try {
        const r = await api.get(`/api/tryon/${idNum}`, { suppressToast: true });
        if (cancelled) return;
        if (r.data?.code === 0) {
          const d = r.data.data as TryonDetail;
          setDetail(d);
          setCollected(d.is_collected);
        } else {
          setError(r.data?.msg ?? "load_failed");
        }
      } catch (e: any) {
        if (cancelled) return;
        setError(e?.response?.data?.msg ?? "load_failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    go();
    return () => {
      cancelled = true;
    };
  }, [pathId, location.state]);

  async function onCollect() {
    if (!detail || collecting || collected) return;
    setCollecting(true);
    try {
      const r = await api.post(
        "/api/events/collect",
        { tryon_id: detail.tryon_id },
        { suppressToast: true },
      );
      if (r.data?.code === 0) {
        setCollected(true);
        message.success(r.data.data.changed ? "已收藏，运营端会看到" : "已收藏");
      } else {
        message.error("收藏失败：" + (r.data?.msg ?? "未知错误"));
      }
    } catch (e: any) {
      message.error("收藏失败：" + (e?.response?.data?.msg ?? "网络错误"));
    } finally {
      setCollecting(false);
    }
  }

  async function onShare() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      message.success("链接已复制到剪贴板");
    } catch {
      message.error("复制失败，请手动复制地址栏 URL");
    }
  }

  async function onSave() {
    if (!detail) return;
    setSaving(true);
    try {
      const r = await fetch(absUrl(detail.result_url));
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `nail-tryon-${detail.tryon_id}-${detail.style_id}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      message.success("已下载到本地");
    } catch {
      message.error("下载失败");
    } finally {
      setSaving(false);
    }
  }

  function onFindStore() {
    message.info("即将上线：找店预约功能（demo 占位）");
  }

  function onRetry() {
    navigate("/recommend");
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <div className="flex flex-col items-center gap-3 text-ink-muted">
          <Spin size="large" />
          <p className="text-sm">加载试戴结果...</p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-page px-6">
        <div className="bg-card border border-line rounded-3xl p-8 max-w-md w-full text-center">
          <span className="text-5xl">😕</span>
          <h2 className="text-lg font-semibold text-ink mt-4 mb-2">
            试戴信息未找到
          </h2>
          <p className="text-sm text-ink-secondary mb-6">
            {error === "tryon_not_found"
              ? "这次试戴的记录不存在或已过期，请重新试戴。"
              : error === "tryon_has_no_result"
              ? "这是一条历史数据，没有可展示的试戴图片。"
              : error === "invalid_tryon_id"
              ? "URL 中的试戴 ID 无效。"
              : "加载失败，请重新试戴。"}
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="px-5 py-2 rounded-full bg-brand text-ink font-medium hover:bg-brand-hover transition"
          >
            回到推荐页
          </button>
        </div>
      </div>
    );
  }

  const resultUrl = absUrl(detail.result_url);
  // Three-tier fallback for the "before" image: backend-stored original_url
  // first (F5/deep-link path); Context photoId second (same-session nav
  // state path, since /api/tryon POST response doesn't include the URL);
  // empty as final degraded fallback.
  const fallbackFromCtx = ctxPhotoId ? `/static/uploads/${ctxPhotoId}` : "";
  const originalUrl = absUrl(detail.original_url ?? fallbackFromCtx);
  const coverUrl = absUrl(detail.style?.cover_url);
  // Use original hand as the "before" if available, else the style cover
  // (which mock provider also serves as the "after", so visually no diff).
  const beforeUrl = originalUrl || coverUrl;

  return (
    <div className="min-h-screen flex flex-col bg-page pb-20">
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
          <span className="text-sm font-medium text-ink">试戴结果</span>
          <span className="text-xs text-ink-muted ml-2">#{detail.tryon_id}</span>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">
        <div className="max-w-3xl mx-auto space-y-5">
          {/* Style header */}
          <div className="bg-card border border-line rounded-3xl p-5 flex items-center gap-4">
            <div
              className="w-12 h-12 rounded-2xl border-2 border-white shadow"
              style={{ background: detail.style?.color_main || "#FFD100" }}
            />
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-semibold text-ink truncate">
                {detail.style?.name ?? detail.style_id}
              </h2>
              <p className="text-xs text-ink-muted truncate">
                {(detail.style?.style_tags ?? []).slice(0, 4).join(" · ")}
              </p>
            </div>
            <span className="hidden md:inline-block px-3 py-1 rounded-full bg-brand-light text-ink text-xs">
              U5 · 结果
            </span>
          </div>

          {/* Compare slider */}
          <div className="bg-card border border-line rounded-3xl overflow-hidden">
            <div className="px-5 py-3 border-b border-line flex items-center justify-between">
              <span className="text-sm font-medium text-ink">
                {originalUrl ? "拖动对比" : "试戴效果"}
              </span>
              <span className="text-xs text-ink-muted">
                ← 原图 / 试戴后 →
              </span>
            </div>
            <div className="aspect-square bg-surface">
              {originalUrl ? (
                <ReactCompareImage
                  leftImage={beforeUrl}
                  rightImage={resultUrl}
                  sliderLineColor="#FFD100"
                  sliderLineWidth={2}
                  handleSize={36}
                />
              ) : (
                // No original-hand URL stored; just show the result fullscreen.
                <img
                  src={resultUrl}
                  alt="试戴结果"
                  className="w-full h-full object-cover"
                  onError={(e) => { e.currentTarget.style.display = "none"; }}
                />
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <ActionButton
              onClick={onSave}
              disabled={saving}
              label={saving ? "下载中..." : "保存"}
              hint="下载试戴图"
            />
            <ActionButton
              onClick={onShare}
              label="分享"
              hint="复制链接"
            />
            <ActionButton
              onClick={onCollect}
              disabled={collected || collecting}
              primary={!collected}
              label={collected ? "已收藏 ✓" : collecting ? "处理中..." : "收藏"}
              hint={collected ? "运营端已感知" : "运营端 +1"}
            />
            <ActionButton
              onClick={onRetry}
              label="换一款"
              hint="再试别的"
            />
            <ActionButton
              onClick={onFindStore}
              label="找店预约"
              hint="即将上线"
            />
          </div>
        </div>
      </main>
    </div>
  );
}

interface ActionButtonProps {
  onClick: () => void;
  disabled?: boolean;
  primary?: boolean;
  label: string;
  hint: string;
}

function ActionButton({ onClick, disabled, primary, label, hint }: ActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex flex-col items-center gap-1 px-3 py-3 rounded-2xl border transition disabled:opacity-50 disabled:cursor-not-allowed ${
        primary
          ? "bg-brand text-ink border-brand hover:bg-brand-hover"
          : "bg-card text-ink border-line hover:border-brand"
      }`}
    >
      <span className="text-sm font-medium">{label}</span>
      <span className="text-[10px] text-ink-muted">{hint}</span>
    </button>
  );
}
