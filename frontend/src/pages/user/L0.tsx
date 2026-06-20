import { Link } from "react-router-dom";
import { useUser } from "../../store/UserContext";

/**
 * L0 双端入口（design-docu §6.0, 原型 Board 0）.
 *
 * Layout:
 *   ┌── Header (brand badge + slogan) ──┐
 *   │  请选择你的使用身份                  │
 *   │  ┌─用户端─┐  ┌─运营端─┐              │
 *   │  └────────┘  └────────┘              │
 *   │  Footer (decorative tag line)       │
 *   └────────────────────────────────────┘
 *
 * Both cards are entire-card <Link>s. The user card hero image comes from
 * the backend /static mount (f_05_enh.png — a representative female style).
 * If the backend isn't running the image fails gracefully (broken-image
 * icon) but navigation still works.
 */
export default function L0() {
  // Side-effect: instantiating the context guarantees ensureUserId() ran
  // and userId is in sessionStorage before the user clicks either CTA.
  useUser();

  const HERO_USER = "http://localhost:8000/static/styles/f_05_enh.png";

  return (
    <div className="min-h-screen flex flex-col bg-page">
      {/* === Header === */}
      <header className="px-8 py-5 flex items-center gap-3 border-b border-line bg-card">
        <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-brand text-ink font-bold text-sm shadow-sm">
          AI
        </span>
        <div className="flex-1">
          <h1 className="text-base font-semibold text-ink leading-tight">
            AI 试戴美甲与智能运营助手
          </h1>
          <p className="text-xs text-ink-secondary leading-tight">
            高保真原型设计 · Board 0 · 入口页
          </p>
        </div>
        <span className="hidden md:inline-block text-xs text-ink-muted">
          让美甲更懂你
        </span>
      </header>

      {/* === Main === */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-10">
        <h2 className="text-2xl md:text-3xl font-semibold text-ink mb-2">
          请选择你的使用身份
        </h2>
        <p className="text-sm text-ink-secondary mb-10">
          进入用户端体验，或转向运营端 · AI 试戴与智能运营
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl">
          {/* Card: User-side */}
          <Link
            to="/gender"
            className="group block rounded-3xl border border-line bg-card overflow-hidden transition-transform hover:-translate-y-1 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-brand-light"
          >
            <div className="aspect-[4/3] bg-surface relative overflow-hidden">
              <img
                src={HERO_USER}
                alt="美甲试戴示意"
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                onError={(e) => {
                  // Fallback if backend /static is offline
                  e.currentTarget.style.display = "none";
                }}
              />
              <span className="absolute top-4 left-4 px-2 py-0.5 rounded-full bg-brand text-ink text-xs font-medium">
                用户端
              </span>
            </div>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-ink mb-1">
                AI 试戴美甲
              </h3>
              <p className="text-sm text-ink-secondary mb-4">
                上传一张手图，AI 推荐 9 款最适合你的美甲，并提供真实合成预览。
              </p>
              <ul className="text-xs text-ink-muted space-y-1 mb-5">
                <li>· 个性化推荐（肤色 + 手型 + 风格）</li>
                <li>· 多款对比试戴</li>
                <li>· LLM 生成的一句话理由</li>
              </ul>
              <span className="inline-block px-5 py-2 rounded-full bg-brand text-ink font-medium text-sm transition-colors group-hover:bg-brand-hover">
                进入用户端 →
              </span>
            </div>
          </Link>

          {/* Card: Ops-side */}
          <Link
            to="/ops/overview"
            className="group block rounded-3xl border border-line bg-card overflow-hidden transition-transform hover:-translate-y-1 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-brand-light"
          >
            <div className="aspect-[4/3] bg-surface relative overflow-hidden flex items-end justify-center p-8">
              <span className="absolute top-4 left-4 px-2 py-0.5 rounded-full bg-ink text-card text-xs font-medium">
                运营端
              </span>
              {/* Decorative dashboard mock: bar chart + AI purple indicator */}
              <div className="w-full flex items-end gap-2 h-3/5">
                {[40, 65, 30, 80, 55, 90, 70].map((h, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-t ${
                      i === 5 ? "bg-ai-purple" : "bg-brand"
                    } opacity-90`}
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
              <div className="absolute top-1/3 right-8 w-12 h-12 rounded-full bg-ai-wash flex items-center justify-center">
                <span className="text-ai-purple text-xs font-bold">AI</span>
              </div>
            </div>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-ink mb-1">
                智能运营助手
              </h3>
              <p className="text-sm text-ink-secondary mb-4">
                数据闭环看板 + 爆款/冷门趋势 + AI 周报与建议，运营动作一键生效。
              </p>
              <ul className="text-xs text-ink-muted space-y-1 mb-5">
                <li>· 实时试戴/收藏数据看板</li>
                <li>· 爆款萌芽 & 冷门预警</li>
                <li>· AI 助手对话式运营操作</li>
              </ul>
              <span className="inline-block px-5 py-2 rounded-full bg-brand text-ink font-medium text-sm transition-colors group-hover:bg-brand-hover">
                进入运营端 →
              </span>
            </div>
          </Link>
        </div>
      </main>

      {/* === Footer === */}
      <footer className="px-8 py-4 text-center text-xs text-ink-muted border-t border-line bg-card">
        风格选择 · 轻松搭配 · 产品策略设计支持
      </footer>
    </div>
  );
}
