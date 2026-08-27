import { App as AntApp } from "antd";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Placeholder from "./components/Placeholder";
import O1Overview from "./pages/ops/O1Overview";
import O2Trending from "./pages/ops/O2Trending";
import O3Cold from "./pages/ops/O3Cold";
import OpsLayout from "./pages/ops/OpsLayout";
import OpsPlaceholder from "./pages/ops/OpsPlaceholder";
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
              <Route
                path="report"
                element={
                  <OpsPlaceholder
                    code="O4"
                    title="报告中心"
                    description="查看运营日报、周报及邮件发送状态。"
                  />
                }
              />
              <Route
                path="chat"
                element={
                  <OpsPlaceholder
                    code="O5"
                    title="AI 助手"
                    description="用自然语言查询运营数据并执行经过确认的运营动作。"
                  />
                }
              />
              <Route
                path="styles"
                element={
                  <OpsPlaceholder
                    code="O6"
                    title="款式管理"
                    description="管理全部款式的上下架状态与推荐展示顺序。"
                  />
                }
              />
              <Route
                path="setting"
                element={
                  <OpsPlaceholder
                    code="O7"
                    title="设置中心"
                    description="配置通知、邮件订阅、AI 助手偏好与界面选项。"
                  />
                }
              />
              <Route
                path="reports/:id"
                element={
                  <OpsPlaceholder
                    code="RDET"
                    title="报告详情"
                    description="查看报告正文、生成时间和邮件投递结果。"
                  />
                }
              />
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
