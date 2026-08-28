import { ArrowLeftOutlined, MailOutlined, ReloadOutlined } from "@ant-design/icons";
import { Alert, App as AntApp, Button, Card, Skeleton, Tag } from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";
import { EMAIL_STATUS_TAG } from "./reportStatus";

interface ReportDetail {
  id: number;
  type: "daily" | "weekly";
  title: string;
  period_start: string;
  period_end: string;
  trigger_source: string;
  email_status: "pending" | "sent" | "failed";
  generated_at: string | null;
  content_md: string;
  email_sent_at: string | null;
  email_error: string | null;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

export default function RDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = AntApp.useApp();
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadDetail = async () => {
      try {
        const response = await api.get<ApiEnvelope<ReportDetail>>(
          `/api/ops/reports/${id}`,
          { suppressToast: true },
        );
        if (response.data.code !== 0) {
          throw new Error(response.data.msg || "report_error");
        }
        if (!cancelled) {
          setDetail(response.data.data);
          setError(null);
        }
      } catch (requestError) {
        if (!cancelled) {
          const msg =
            requestError instanceof Error ? requestError.message : "report_request_failed";
          setError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [id, reloadToken]);

  const refetch = useCallback(() => {
    setLoading(true);
    setReloadToken((k) => k + 1);
  }, []);

  const resend = useCallback(async () => {
    setResending(true);
    try {
      const response = await api.post<ApiEnvelope<{ email_status: string }>>(
        `/api/ops/reports/${id}/resend`,
        undefined,
        { suppressToast: true },
      );
      if (response.data.code !== 0) {
        throw new Error(response.data.msg || "resend_error");
      }
      message.success("已重新触发发送，几秒后刷新查看结果");
      refetch();
    } catch (requestError) {
      const msg =
        requestError instanceof Error ? requestError.message : "resend_request_failed";
      message.error(`重发失败：${msg}`);
    } finally {
      setResending(false);
    }
  }, [id, message, refetch]);

  const statusMeta = detail ? EMAIL_STATUS_TAG[detail.email_status] : null;

  return (
    <section className="mx-auto max-w-[1100px]">
      <Button
        type="text"
        icon={<ArrowLeftOutlined />}
        className="mb-4 -ml-2 text-ink-secondary"
        onClick={() => navigate("/ops/setting")}
      >
        返回设置中心
      </Button>

      {error && (
        <Alert
          type="warning"
          showIcon
          message="报告加载失败"
          description={error}
          action={<Button onClick={refetch}>重试</Button>}
        />
      )}

      {loading && !detail ? (
        <Card className="border-line shadow-sm">
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      ) : (
        detail && (
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start">
            <Card className="min-w-0 flex-1 border-line shadow-sm">
              <h1 className="mb-4 text-xl font-semibold text-ink">{detail.title}</h1>
              <div className="report-md text-sm leading-6 text-ink">
                <ReactMarkdown>{detail.content_md}</ReactMarkdown>
              </div>
            </Card>

            <Card
              className="w-full shrink-0 border-line shadow-sm lg:w-[300px]"
              title={<span className="text-sm font-semibold">报告信息</span>}
            >
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-muted">类型</dt>
                  <dd>
                    <Tag bordered={false} color={detail.type === "daily" ? "blue" : "purple"}>
                      {detail.type === "daily" ? "日报" : "周报"}
                    </Tag>
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">统计周期</dt>
                  <dd className="text-ink">
                    {detail.period_start === detail.period_end
                      ? detail.period_start
                      : `${detail.period_start} ~ ${detail.period_end}`}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">触发方式</dt>
                  <dd className="text-ink">
                    {detail.trigger_source === "scheduled" ? "定时任务" : "手动生成"}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">生成时间</dt>
                  <dd className="text-ink">
                    {detail.generated_at
                      ? dayjs(detail.generated_at).format("MM-DD HH:mm:ss")
                      : "-"}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-ink-muted">邮件状态</dt>
                  <dd className="flex items-center gap-1.5">
                    {statusMeta && (
                      <Tag bordered={false} color={statusMeta.color} className="mr-0">
                        {statusMeta.label}
                      </Tag>
                    )}
                    <Button
                      size="small"
                      type="text"
                      icon={<ReloadOutlined />}
                      onClick={refetch}
                      aria-label="刷新状态"
                    />
                  </dd>
                </div>
                {detail.email_sent_at && (
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">发送时间</dt>
                    <dd className="text-ink">
                      {dayjs(detail.email_sent_at).format("MM-DD HH:mm:ss")}
                    </dd>
                  </div>
                )}
              </dl>

              {detail.email_status === "failed" && (
                <div className="mt-4">
                  <Alert
                    type="error"
                    showIcon
                    message="邮件发送失败"
                    description={
                      <span className="break-all text-xs">{detail.email_error}</span>
                    }
                  />
                  <Button
                    block
                    danger
                    className="mt-3"
                    icon={<MailOutlined />}
                    loading={resending}
                    onClick={() => void resend()}
                  >
                    重新发送
                  </Button>
                </div>
              )}
            </Card>
          </div>
        )
      )}
    </section>
  );
}
