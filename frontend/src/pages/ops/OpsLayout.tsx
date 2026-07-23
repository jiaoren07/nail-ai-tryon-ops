import {
  AppstoreOutlined,
  BarChartOutlined,
  BellOutlined,
  FireOutlined,
  RobotOutlined,
  SettingOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { Badge, Button, Layout, Menu, Tag } from "antd";
import type { MenuProps } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

const { Content, Header, Sider } = Layout;

const NAV_ITEMS: Required<MenuProps>["items"] = [
  { key: "/ops/overview", icon: <BarChartOutlined />, label: "数据概览" },
  { key: "/ops/trending", icon: <FireOutlined />, label: "爆款趋势" },
  { key: "/ops/cold", icon: <WarningOutlined />, label: "冷门预警" },
  { key: "/ops/chat", icon: <RobotOutlined />, label: "AI 助手" },
  { key: "/ops/styles", icon: <AppstoreOutlined />, label: "款式管理" },
  { key: "/ops/setting", icon: <SettingOutlined />, label: "设置中心" },
];

const PAGE_TITLES: Record<string, string> = {
  "/ops/overview": "数据概览",
  "/ops/trending": "爆款趋势",
  "/ops/cold": "冷门预警",
  "/ops/chat": "AI 助手",
  "/ops/styles": "款式管理",
  "/ops/setting": "设置中心",
  "/ops/report": "报告中心",
};

function activeMenuKey(pathname: string): string | undefined {
  return NAV_ITEMS
    .map((item) => String(item?.key))
    .find((key) => pathname === key || pathname.startsWith(`${key}/`));
}

export default function OpsLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const selectedKey = activeMenuKey(location.pathname);
  const pageTitle = PAGE_TITLES[selectedKey ?? location.pathname] ?? "运营工作台";

  return (
    <Layout className="ops-shell min-h-screen">
      <Sider width={232} theme="dark" className="ops-sider">
        <div className="h-20 px-5 flex items-center gap-3 border-b border-white/10">
          <span className="w-10 h-10 rounded-xl bg-brand text-ink flex items-center justify-center font-bold">
            AI
          </span>
          <div className="min-w-0">
            <div className="text-white font-semibold leading-tight">美甲智能运营</div>
            <div className="text-xs text-white/50 mt-1">Operations Console</div>
          </div>
        </div>

        <Menu
          className="ops-menu mt-4"
          theme="dark"
          mode="inline"
          items={NAV_ITEMS}
          selectedKeys={selectedKey ? [selectedKey] : []}
          onClick={({ key }) => navigate(key)}
        />

        <div className="absolute bottom-5 left-5 right-5 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
          <div className="text-xs font-medium text-white/80">实时数据闭环</div>
          <div className="text-[11px] text-white/40 mt-1">用户行为与运营动作即时同步</div>
        </div>
      </Sider>

      <Layout className="min-w-0 bg-surface">
        <Header className="ops-header h-20 px-8 bg-card border-b border-line flex items-center justify-between">
          <div>
            <div className="text-xs text-ink-muted">运营工作台</div>
            <div className="text-lg font-semibold text-ink mt-0.5">{pageTitle}</div>
          </div>

          <div className="flex items-center gap-4">
            <Tag color="purple" bordered={false}>
              AI 驱动
            </Tag>
            <Badge dot offset={[-5, 5]}>
              <Button
                type="text"
                shape="circle"
                size="large"
                icon={<BellOutlined />}
                aria-label="通知"
              />
            </Badge>
          </div>
        </Header>

        <Content className="ops-content min-w-0 p-8">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
