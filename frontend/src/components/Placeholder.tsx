import { Link } from "react-router-dom";
import DebugBar from "./DebugBar";

interface PlaceholderProps {
  code: string;
  title: string;
  hint?: string;
}

const ALL_ROUTES: Array<{ code: string; path: string }> = [
  { code: "L0", path: "/" },
  { code: "U0", path: "/gender" },
  { code: "U1", path: "/upload" },
  { code: "U2", path: "/recommend" },
  { code: "U3", path: "/browse" },
  { code: "U4", path: "/compare" },
  { code: "U5", path: "/result/demo-tryon-id" },
  { code: "U6", path: "/history" },
  { code: "O1", path: "/ops/overview" },
  { code: "O2", path: "/ops/trending" },
  { code: "O3", path: "/ops/cold" },
  { code: "O4", path: "/ops/report" },
  { code: "O5", path: "/ops/chat" },
  { code: "O6", path: "/ops/styles" },
  { code: "O7", path: "/ops/setting" },
  { code: "RDET", path: "/ops/reports/demo-report-id" },
];

export default function Placeholder({ code, title, hint }: PlaceholderProps) {
  return (
    <div className="min-h-screen p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <span className="inline-block px-3 py-1 rounded bg-yellow-300 text-black font-semibold">
          {code}
        </span>
        <h1 className="text-2xl mt-3 font-medium">{title}</h1>
        {hint && <p className="text-sm text-gray-500 mt-1">{hint}</p>}
      </div>

      <DebugBar />

      <section className="mt-6">
        <h2 className="text-sm font-semibold text-gray-600 mb-2">
          Quick navigation (16 declared routes)
        </h2>
        <div className="grid grid-cols-4 gap-2">
          {ALL_ROUTES.map((r) => (
            <Link
              key={r.path}
              to={r.path}
              className="px-2 py-1 text-xs rounded border border-gray-300 hover:bg-gray-100 truncate"
              title={r.path}
            >
              <span className="font-semibold">{r.code}</span>{" "}
              <span className="text-gray-500">{r.path}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
