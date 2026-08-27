import { Link, useNavigate } from "react-router-dom";
import { type Gender } from "../../store/UserContext";
import { useUser } from "../../store/useUser";

/**
 * U0 性别选择页（design-docu §6.1, plan §5.3, 原型 Board 1 第 1 屏）.
 *
 * - No guard: user can land here directly or from L0.
 * - On select: write userGender (Context + sessionStorage) -> navigate /upload.
 * - "Skip" button equates to selecting "female" (plan §5.3 explicit).
 */
export default function U0() {
  const { setUserGender, userGender } = useUser();
  const navigate = useNavigate();

  const HERO_FEMALE = "http://localhost:8000/static/styles/f_01_enh.png";
  const HERO_MALE = "http://localhost:8000/static/styles/m_01.jpg";

  const choose = (g: Gender) => {
    setUserGender(g);
    navigate("/upload");
  };

  return (
    <div className="min-h-screen flex flex-col bg-page">
      {/* === Top bar === */}
      <header className="px-6 py-4 flex items-center gap-3 border-b border-line bg-card">
        <Link
          to="/"
          className="inline-flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface text-ink-secondary"
          aria-label="返回首页"
        >
          ←
        </Link>
        <div className="flex-1 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-brand text-ink font-bold text-xs">
            AI
          </span>
          <span className="text-sm font-medium text-ink">AI 试戴美甲</span>
        </div>
        <button
          type="button"
          onClick={() => choose("female")}
          className="text-sm text-ink-secondary hover:text-ink underline-offset-4 hover:underline"
        >
          跳过
        </button>
      </header>

      {/* === Main === */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-10">
        <span className="inline-block px-3 py-0.5 rounded-full bg-brand-light text-ink text-xs font-medium mb-4">
          U0 · 性别选择
        </span>
        <h1 className="text-2xl md:text-3xl font-semibold text-ink mb-2 text-center">
          先选择你想看的款式方向
        </h1>
        <p className="text-sm text-ink-secondary mb-10 text-center max-w-md">
          推荐算法会按性别做硬筛选，让你看到的款式都贴合身份。可随时返回切换。
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 w-full max-w-3xl">
          <GenderCard
            label="女性款式"
            sub="精致、跳色、法式、纯色等多种风格"
            tag="Female · 25 款"
            hero={HERO_FEMALE}
            selected={userGender === "female"}
            onClick={() => choose("female")}
          />
          <GenderCard
            label="男性款式"
            sub="哑光、冷调、商务、酷感几何系"
            tag="Male · 15 款"
            hero={HERO_MALE}
            selected={userGender === "male"}
            onClick={() => choose("male")}
          />
        </div>

        <p className="text-xs text-ink-muted mt-10 text-center max-w-md">
          性别仅用于推荐筛选，不会保存到任何账户系统。可在浏览器关闭后自动清除。
        </p>
      </main>
    </div>
  );
}

interface GenderCardProps {
  label: string;
  sub: string;
  tag: string;
  hero: string;
  selected: boolean;
  onClick: () => void;
}

function GenderCard({ label, sub, tag, hero, selected, onClick }: GenderCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group block text-left rounded-3xl border bg-card overflow-hidden transition-transform hover:-translate-y-1 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-brand-light ${
        selected ? "border-brand ring-4 ring-brand-light" : "border-line"
      }`}
    >
      <div className="aspect-[4/3] bg-surface relative overflow-hidden">
        <img
          src={hero}
          alt={label}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
        <span className="absolute top-3 left-3 px-2 py-0.5 rounded-full bg-card/90 text-ink text-xs font-medium backdrop-blur">
          {tag}
        </span>
      </div>
      <div className="p-5">
        <h2 className="text-lg font-semibold text-ink mb-1">{label}</h2>
        <p className="text-sm text-ink-secondary">{sub}</p>
      </div>
    </button>
  );
}
