/** Shared email-status tag mapping for O7 list + report detail
 * (own file so component files only export components — react-refresh). */
export type EmailStatus = "pending" | "sent" | "failed";

export const EMAIL_STATUS_TAG: Record<EmailStatus, { color: string; label: string }> = {
  sent: { color: "success", label: "已发送" },
  pending: { color: "processing", label: "发送中" },
  failed: { color: "error", label: "发送失败" },
};
