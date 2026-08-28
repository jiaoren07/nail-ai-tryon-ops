import { App as AntApp } from "antd";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Placeholder from "./components/Placeholder";
import O1Overview from "./pages/ops/O1Overview";
import O2Trending from "./pages/ops/O2Trending";
import O3Cold from "./pages/ops/O3Cold";
import O5Chat from "./pages/ops/O5Chat";
import O7Setting from "./pages/ops/O7Setting";
import RDetail from "./pages/ops/RDetail";
import O6Styles from "./pages/ops/O6Styles";
import OpsLayout from "./pages/ops/OpsLayout";
import L0 from "./pages/user/L0";
import U0 from "./pages/user/U0";
import U1 from "./pages/user/U1";
import U2 from "./pages/user/U2";
import U3 from "./pages/user/U3";
import U4 from "./pages/user/U4";
import U5 from "./pages/user/U5";
import { UserProvider } from "./store/UserContext";

/**
 * Consumer pages are replaced step-by-step from the original route skeleton.
 * Step 7.1 nests every /ops page under one shared operator layout.
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
            <Route path="/result/:id" element={<U5 />} />
            <Route path="/history" element={<Placeholder code="U6" title="试戴历史" />} />
            <Route path="/ops" element={<OpsLayout />}>
              <Route index element={<Navigate to="overview" replace />} />
              <Route
                path="overview"
                element={<O1Overview />}
              />
              <Route path="trending" element={<O2Trending />} />
              <Route path="cold" element={<O3Cold />} />
              {/* 独立报告中心已并入 O7「通知与邮件订阅」tab（design §7.7）；
                  旧路径重定向而非 404，避免历史书签/通知死链 */}
              <Route path="report" element={<Navigate to="/ops/setting" replace />} />
              <Route path="chat" element={<O5Chat />} />
              <Route path="styles" element={<O6Styles />} />
              <Route path="setting" element={<O7Setting />} />
              <Route path="reports/:id" element={<RDetail />} />
            </Route>
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
