import { App as AntApp } from "antd";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Placeholder from "./components/Placeholder";
import L0 from "./pages/user/L0";
import U0 from "./pages/user/U0";
import U1 from "./pages/user/U1";
import U2 from "./pages/user/U2";
import U3 from "./pages/user/U3";
import U4 from "./pages/user/U4";
import { UserProvider } from "./store/UserContext";

/**
 * Step 5.1 plumbing: every page is a Placeholder + DebugBar.
 * Step 5.2 onward replaces them one by one (L0 first).
 *
 * Route table mirrors design-docu.md §11.2 verbatim.
 */
export default function App() {
  return (
    <AntApp>
      <UserProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<L0 />} />
            <Route path="/gender" element={<U0 />} />
            <Route path="/upload" element={<U1 />} />
            <Route path="/recommend" element={<U2 />} />
            <Route path="/browse" element={<U3 />} />
            <Route path="/compare" element={<U4 />} />
            <Route path="/result/:id" element={<Placeholder code="U5" title="试戴结果" />} />
            <Route path="/history" element={<Placeholder code="U6" title="试戴历史" />} />
            <Route path="/ops/overview" element={<Placeholder code="O1" title="运营 · 数据概览" />} />
            <Route path="/ops/trending" element={<Placeholder code="O2" title="运营 · 爆款看板" />} />
            <Route path="/ops/cold" element={<Placeholder code="O3" title="运营 · 冷门看板" />} />
            <Route path="/ops/report" element={<Placeholder code="O4" title="运营 · 报告中心" />} />
            <Route path="/ops/chat" element={<Placeholder code="O5" title="运营 · AI 助手" />} />
            <Route path="/ops/styles" element={<Placeholder code="O6" title="运营 · 款式管理" />} />
            <Route path="/ops/setting" element={<Placeholder code="O7" title="运营 · 设置中心" />} />
            <Route
              path="/ops/reports/:id"
              element={<Placeholder code="RDET" title="运营 · 报告详情" />}
            />
            <Route
              path="*"
              element={<Placeholder code="404" title="未匹配路径" hint="检查 App.tsx 路由表" />}
            />
          </Routes>
        </BrowserRouter>
      </UserProvider>
    </AntApp>
  );
}
