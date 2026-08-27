import { InboxOutlined } from "@ant-design/icons";
import { App as AntApp, Upload } from "antd";
import imageCompression from "browser-image-compression";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { useUser } from "../../store/useUser";

/**
 * U1 手图上传页（design-docu §6.2, plan §5.4, 原型 Board 1 第 2 屏）.
 *
 * Guards: userGender must exist in sessionStorage (set in U0); otherwise
 * redirect to /gender. First C-end page that actually talks to the backend.
 *
 * Two entry paths into POST /api/user/upload:
 *  - Dragger / click-pick a file
 *  - Click one of 4 sample thumbnails -> fetch as blob -> same flow
 */
export default function U1() {
  const { userId, userGender, setHandFeatures, setPhotoId } = useUser();
  const { message } = AntApp.useApp();
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);

  // Plan §5.4 hard guard: missing userGender -> bounce to /gender.
  useEffect(() => {
    if (!userGender) navigate("/gender", { replace: true });
  }, [userGender, navigate]);
  if (!userGender) return null;

  // Samples live in frontend/public/samples/, served same-origin by vite,
  // so the click->fetch->blob->File pipeline avoids the CORS check that
  // would block the cross-origin /static/* mount on the backend.
  const SAMPLES = [1, 2, 3, 4].map((n) => `/samples/0${n}.png`);

  function friendlyError(msg: string | undefined) {
    if (msg === "file_too_large") return "文件超大";
    if (msg === "unsupported_format") return "格式不支持";
    if (msg === "user_id_mismatch") return "身份校验失败，请刷新页面";
    return "网络异常，请重试";
  }

  async function handleFile(file: File) {
    // 1. Type guard. Plan: jpg/png only.
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      message.error("格式不支持，仅支持 JPG / PNG");
      return;
    }
    // 2. Size guard (matches backend Step 4.2's 10MB cap).
    if (file.size > 10 * 1024 * 1024) {
      message.error("文件超大，请选择 10MB 以内的图片");
      return;
    }
    setUploading(true);
    try {
      // 3. Client-side compression to <=5MB before posting (plan §5.4).
      const compressed = await imageCompression(file, {
        maxSizeMB: 5,
        maxWidthOrHeight: 2000,
        useWebWorker: true,
      });
      // 4. Multipart POST. suppressToast keeps the global interceptor
      //    quiet so we can show our own friendlier Chinese message.
      const fd = new FormData();
      fd.append("file", compressed, file.name || "hand.png");
      fd.append("user_id", userId);
      const r = await api.post("/api/user/upload", fd, { suppressToast: true });
      if (r.data?.code !== 0) {
        message.error(friendlyError(r.data?.msg));
        return;
      }
      // 5. Write Context then navigate.
      setPhotoId(r.data.data.photo_id);
      setHandFeatures(r.data.data.hand_features);
      message.success("已识别你的手部特征");
      navigate("/recommend");
    } catch (e: unknown) {
      const errObj = e as { response?: { data?: { msg?: string } }; message?: string };
      message.error(friendlyError(errObj.response?.data?.msg ?? errObj.message));
    } finally {
      setUploading(false);
    }
  }

  async function handleSampleClick(url: string) {
    try {
      const resp = await fetch(url);
      if (!resp.ok) throw new Error("fetch_sample_failed");
      const blob = await resp.blob();
      const filename = url.split("/").pop() ?? "sample.png";
      const file = new File([blob], filename, { type: blob.type || "image/png" });
      await handleFile(file);
    } catch {
      message.error("示例图加载失败，请检查后端");
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-page">
      {/* === Top bar === */}
      <header className="px-6 py-4 flex items-center gap-3 border-b border-line bg-card">
        <Link
          to="/gender"
          className="inline-flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface text-ink-secondary"
          aria-label="返回性别选择"
        >
          ←
        </Link>
        <div className="flex-1 flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-brand text-ink font-bold text-xs">
            AI
          </span>
          <span className="text-sm font-medium text-ink">AI 试戴美甲</span>
        </div>
        <span className="text-xs text-ink-muted">
          当前性别：{userGender === "female" ? "女性" : "男性"}
        </span>
      </header>

      {/* === Main === */}
      <main className="flex-1 flex flex-col items-center px-6 py-10">
        <span className="inline-block px-3 py-0.5 rounded-full bg-brand-light text-ink text-xs font-medium mb-4">
          U1 · 手图上传
        </span>
        <h1 className="text-2xl md:text-3xl font-semibold text-ink mb-2 text-center">
          AI 帮你看，哪款美甲适合你的手
        </h1>
        <p className="text-sm text-ink-secondary mb-8 text-center max-w-md">
          上传一张你手部的照片，AI 会分析肤色 + 手型，再为你推荐 9 款最合适的美甲。
        </p>

        {/* Upload zone */}
        <div className="w-full max-w-2xl">
          <Upload.Dragger
            name="file"
            accept="image/jpeg,image/png"
            multiple={false}
            showUploadList={false}
            disabled={uploading}
            beforeUpload={async (file) => {
              await handleFile(file as unknown as File);
              return false; // we handle upload ourselves
            }}
            className="!bg-card !border-line"
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: "#FFD100", fontSize: 56 }} />
            </p>
            <p className="ant-upload-text" style={{ fontSize: 16, color: "#111111" }}>
              {uploading ? "AI 正在分析你的手部特征..." : "拖拽手图到此处，或点击选择"}
            </p>
            <p className="ant-upload-hint" style={{ color: "#8A8A8A" }}>
              支持 JPG / PNG，≤10MB；上传前自动压缩，不会保存你的隐私
            </p>
          </Upload.Dragger>
        </div>

        {/* Samples */}
        <div className="w-full max-w-2xl mt-10">
          <p className="text-sm text-ink-secondary mb-3">
            或者，挑一张示例图快速体验：
          </p>
          <div className="grid grid-cols-4 gap-3">
            {SAMPLES.map((url, idx) => (
              <button
                type="button"
                key={url}
                disabled={uploading}
                onClick={() => handleSampleClick(url)}
                className="aspect-square rounded-2xl overflow-hidden border border-line bg-card hover:border-brand hover:shadow-md transition disabled:opacity-50"
                aria-label={`选择示例图 ${idx + 1}`}
              >
                <img
                  src={url}
                  alt={`示例 ${idx + 1}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </button>
            ))}
          </div>
        </div>

        <p className="text-xs text-ink-muted mt-10 text-center max-w-md">
          上传图仅保存在本次会话中用于推荐与试戴，关闭浏览器后自动清除。
        </p>
      </main>
    </div>
  );
}
