import { ArrowLeftOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Skeleton, Tag } from "antd";
import dayjs from "dayjs";
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useNavigate, useParams } from "react-router-dom";
import api from "../../api/client";

interface ReportDetail {
  id: number;
  type: "daily" | "weekly";
  title: string;
  period_start: string;
  period_end: string;
  trigger_source: string;
  generated_at: string | null;
  content_md: string;
}

interface ApiEnvelope<T> {
  code: number;
  msg: string;
  data: T;
}

export default function RDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
                    <Tag variant="filled" color={detail.type === "daily" ? "blue" : "purple"}>
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
              </dl>
            </Card>
          </div>
        )
      )}
    </section>
  );
}
