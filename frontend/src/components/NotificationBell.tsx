import { BellOutlined, CheckOutlined } from "@ant-design/icons";
import { App as AntApp, Badge, Button, Drawer, Empty, Tag } from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

/**
 * Step 9.5 (design-docu §7.7.5): the bell is the single entry point for
 * AI-initiated activity. Polls unread-count every 5s; the drawer lists
 * the latest 10 notifications; clicking one marks it read and jumps to
 * the referenced report detail.
 */

interface NotificationItem {
  id: number;
  type: string;
  ref_id: number | null;
  title: string;
  summary: string;
  is_read: boolean;
  created_at: string | null;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

const POLL_INTERVAL_MS = 5_000;

export default function NotificationBell() {
  const navigate = useNavigate();
  const { message } = AntApp.useApp();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [listLoading, setListLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const response = await api.get<ApiEnvelope<{ unread: number }>>(
          "/api/ops/notifications/unread-count",
          { suppressToast: true },
        );
        if (!cancelled && response.data.code === 0) {
          setUnread(response.data.data.unread);
        }
      } catch {
        // Backend offline — keep the last known badge, polling continues.
      }
    };

    void poll();
    const timer = window.setInterval(() => void poll(), POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const loadList = useCallback(async () => {
    setListLoading(true);
    try {
      const response = await api.get<ApiEnvelope<{ items: NotificationItem[] }>>(
        "/api/ops/notifications",
        { params: { limit: 10 }, suppressToast: true },
      );
      if (response.data.code === 0) {
        setItems(response.data.data.items);
      }
    } catch {
      message.error("通知列表加载失败");
    } finally {
      setListLoading(false);
    }
  }, [message]);

  const openDrawer = useCallback(() => {
    setOpen(true);
    void loadList();
  }, [loadList]);

  const clickItem = useCallback(
    async (item: NotificationItem) => {
      if (!item.is_read) {
        try {
          await api.post(`/api/ops/notifications/${item.id}/read`, undefined, {
            suppressToast: true,
          });
          setUnread((u) => Math.max(0, u - 1));
        } catch {
          // Non-fatal: navigation still proceeds; badge corrects on next poll.
        }
      }
      setOpen(false);
      if (item.ref_id != null) {
        navigate(`/ops/reports/${item.ref_id}`);
      }
    },
    [navigate],
  );

  const readAll = useCallback(async () => {
    try {
      const response = await api.post<ApiEnvelope<{ marked: number }>>(
        "/api/ops/notifications/read-all",
        undefined,
        { suppressToast: true },
      );
      if (response.data.code !== 0) {
        throw new Error(response.data.msg);
      }
      setUnread(0);
      setItems((prev) => prev.map((it) => ({ ...it, is_read: true })));
      message.success("已全部标记为已读");
    } catch {
      message.error("操作失败，请重试");
    }
  }, [message]);

  return (
    <>
      <Badge count={unread} size="small" offset={[-4, 4]}>
        <Button
          type="text"
          shape="circle"
          size="large"
          icon={<BellOutlined />}
          aria-label="通知"
          onClick={openDrawer}
        />
      </Badge>

      <Drawer
        title="通知"
        width={400}
        open={open}
        onClose={() => setOpen(false)}
        extra={
          <Button size="small" icon={<CheckOutlined />} onClick={() => void readAll()}>
            全部已读
          </Button>
        }
        styles={{ body: { padding: 12 } }}
        loading={listLoading}
      >
        {items.length === 0 ? (
          <Empty className="mt-10" description="暂无通知" />
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`block w-full rounded-xl border px-4 py-3 text-left transition-colors hover:border-brand ${
                  item.is_read ? "border-line bg-card opacity-60" : "border-line bg-surface"
                }`}
                onClick={() => void clickItem(item)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="min-w-0 truncate text-sm font-medium text-ink">
                    {!item.is_read && (
                      <span className="mr-1.5 inline-block h-2 w-2 rounded-full bg-danger align-middle" />
                    )}
                    {item.title}
                  </span>
                  <Tag bordered={false} className="mr-0 shrink-0">
                    {item.type === "report" ? "报告" : item.type}
                  </Tag>
                </div>
                <div className="mt-1 line-clamp-2 text-xs leading-5 text-ink-secondary">
                  {item.summary}
                </div>
                <div className="mt-1 text-[11px] text-ink-muted">
                  {item.created_at ? dayjs(item.created_at).format("MM-DD HH:mm") : ""}
                </div>
              </button>
            ))}
          </div>
        )}
      </Drawer>
    </>
  );
}
