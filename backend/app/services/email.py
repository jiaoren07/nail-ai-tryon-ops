"""Email service: SMTPS HTML + plain text two-part email via stdlib smtplib.

Per implementation-plan §3.4 + design-docu §7.7.4:
- send_email(to, subject, html_body, text_body) — async, raises EmailSendError on failure
- Connects via SMTPS on port 465 with credentials from .env (SMTP_HOST/PORT/USER/PASS/FROM)
- HTML wrapped in the standardized 680px + Apple System font + AI-generated-footer shell
- No silent exception swallowing — caller (Step 9 report dispatcher) decides how to recover
- Synchronous smtplib call is offloaded to a worker thread via asyncio.to_thread
  so the FastAPI event loop is never blocked
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("nail_demo.email")

SEND_TIMEOUT_SECONDS = 30


class EmailSendError(Exception):
    """Raised when email sending fails (missing config, SMTP auth, network, etc).

    The underlying exception (if any) is preserved via __cause__ so callers
    can introspect: `except EmailSendError as e: log(e, exc_info=e.__cause__)`.
    """


def wrap_html(body: str) -> str:
    """Wrap raw HTML body in the standardized inline-CSS shell.

    Per design-docu §7.7.4: max 680px width centred, Apple System font stack,
    1.6 line-height, divider + "AI 助手自动生成" footer with current timestamp.
    Designed to render correctly in QQ/163 webmail and Outlook clients
    (inline CSS only — no external stylesheets, no <style> blocks).
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\','
        'Arial,sans-serif;max-width:680px;margin:auto;color:#333;line-height:1.6;'
        'padding:24px;">\n'
        f"  {body}\n"
        '  <hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>\n'
        f'  <p style="font-size:12px;color:#999;">本邮件由 AI 助手自动生成于 {now}。</p>\n'
        "</div>"
    )


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> None:
    """Send a multipart text+html email via SMTPS.

    Raises EmailSendError on any failure. Never silently swallows exceptions.
    Returns None on success.

    Args:
        to: recipient email address (single recipient; multi-recipient is
            not currently supported)
        subject: email subject line
        html_body: raw HTML body (will be wrapped via wrap_html)
        text_body: plain-text fallback for clients that don't render HTML
    """
    missing = [
        name for name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "SMTP_FROM")
        if not getattr(settings, name)
    ]
    if missing:
        raise EmailSendError(
            f"SMTP config incomplete; missing in .env: {', '.join(missing)}"
        )
    if not to:
        raise EmailSendError("recipient 'to' is empty")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    # Order matters: text/plain first, text/html second. Mail clients prefer
    # the *last* part that they can render; HTML-capable clients pick HTML,
    # plain-text clients fall back to the first part.
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(wrap_html(html_body), "html", "utf-8"))

    def _send_sync() -> None:
        with smtplib.SMTP_SSL(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=SEND_TIMEOUT_SECONDS,
        ) as srv:
            srv.login(settings.SMTP_USER, settings.SMTP_PASS)
            srv.send_message(msg)

    try:
        await asyncio.to_thread(_send_sync)
    except smtplib.SMTPException as e:
        raise EmailSendError(f"SMTP error: {type(e).__name__}: {e}") from e
    except OSError as e:
        raise EmailSendError(f"network error reaching SMTP: {e}") from e
    except Exception as e:
        raise EmailSendError(f"unexpected error: {type(e).__name__}: {e}") from e
