"""Step 9.1 verification for generate_and_dispatch_report.

Email is MONKEYPATCHED to a stub in every case — no real SMTP traffic
(live-send test is a separate user-approved step). LLM calls are REAL
(strong tier, 3 calls total, 20s spacing for the per-minute rate limit).

  T1 daily + stub-success  -> reports row (type/title/period/source/
     content_md), notifications row (ref_id, summary<=121), email_status
     pending -> sent + email_sent_at set
  T2 daily + stub-failure  -> email_status failed + email_error set,
     report & notification rows still written
  T3 weekly                -> period == last complete Mon..Sun week
  T4 unknown type          -> ReportError, no rows
  T5 LLM failure           -> raises, NO report/notification rows (rollback)

Run from backend/:  .venv\\Scripts\\python.exe -X utf8 scripts\\_check_report_service.py
No HTTP server needed. Reseed first if the day rolled over.
"""
from __future__ import annotations

import asyncio
import sys
import time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

RESULTS: list[tuple[str, bool, str]] = []
LLM_PAUSE = 20


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


async def main() -> None:
    from sqlalchemy import func, select
    from app.db import async_session_maker
    from app.models import Notification, Report
    from app.services import email, llm, report
    from app.services.email import EmailSendError
    from app.services.report import ReportError, generate_and_dispatch_report

    sent_calls: list[dict] = []

    async def stub_ok(to, subject, html_body, text_body):
        sent_calls.append({"to": to, "subject": subject})

    async def stub_fail(to, subject, html_body, text_body):
        raise EmailSendError("stub: simulated SMTP auth failure")

    async def counts():
        async with async_session_maker() as db:
            r = (await db.execute(select(func.count()).select_from(Report))).scalar_one()
            n = (await db.execute(select(func.count()).select_from(Notification))).scalar_one()
            return int(r), int(n)

    async def load_report(report_id):
        async with async_session_maker() as db:
            rep = await db.get(Report, report_id)
            notif = (await db.execute(
                select(Notification).where(Notification.ref_id == report_id)
            )).scalar_one_or_none()
            return rep, notif

    real_send = email.send_email

    # ---- T1: daily, email stub success ---------------------------------
    email.send_email = stub_ok
    r0, n0 = await counts()
    rid1 = await generate_and_dispatch_report("daily", "manual")
    await asyncio.sleep(2)  # let the fire-and-forget email task land
    rep1, notif1 = await load_report(rid1)
    r1, n1 = await counts()
    today = date.today()
    check(
        "T1 daily: report+notification rows, email stub -> sent",
        rep1 is not None
        and rep1.type == "daily"
        and rep1.trigger_source == "manual"
        and rep1.period_start == today and rep1.period_end == today
        and today.isoformat() in rep1.title
        and len(rep1.content_md) > 100 and "##" in rep1.content_md
        and rep1.email_status == "sent" and rep1.email_sent_at is not None
        and notif1 is not None and notif1.type == "report"
        and len(notif1.summary) <= 121
        and (r1, n1) == (r0 + 1, n0 + 1)
        and len(sent_calls) == 1,
        f"id={rid1} md_len={len(rep1.content_md) if rep1 else 0} status={rep1.email_status if rep1 else '-'}",
    )
    time.sleep(LLM_PAUSE)

    # ---- T2: daily, email stub failure ---------------------------------
    email.send_email = stub_fail
    rid2 = await generate_and_dispatch_report("daily", "manual")
    await asyncio.sleep(2)
    rep2, notif2 = await load_report(rid2)
    check(
        "T2 email failure: status=failed + error, rows survive",
        rep2 is not None
        and rep2.email_status == "failed"
        and rep2.email_error and "simulated SMTP" in rep2.email_error
        and rep2.email_sent_at is None
        and notif2 is not None,
        f"id={rid2} error={rep2.email_error[:40] if rep2 else '-'}",
    )
    time.sleep(LLM_PAUSE)

    # ---- T3: weekly period semantics -----------------------------------
    email.send_email = stub_ok
    rid3 = await generate_and_dispatch_report("weekly", "manual")
    await asyncio.sleep(2)
    rep3, _ = await load_report(rid3)
    this_monday = today - timedelta(days=today.weekday())
    expect_start = this_monday - timedelta(days=7)
    expect_end = expect_start + timedelta(days=6)
    check(
        "T3 weekly: period == last complete Mon..Sun",
        rep3 is not None
        and rep3.type == "weekly"
        and rep3.period_start == expect_start
        and rep3.period_end == expect_end
        and "~" in rep3.title
        and rep3.email_status == "sent",
        f"period={rep3.period_start}~{rep3.period_end}" if rep3 else "-",
    )

    # ---- T4: unknown type ----------------------------------------------
    try:
        await generate_and_dispatch_report("monthly", "manual")
        t4 = False
    except ReportError:
        t4 = True
    check("T4 unknown type raises ReportError", t4)

    # ---- T5: LLM failure -> rollback, no rows --------------------------
    real_gen = llm.gen_text

    async def llm_fail(*args, **kwargs):
        raise llm.LLMError("stub: simulated LLM outage")

    llm.gen_text = llm_fail
    r_before, n_before = await counts()
    try:
        await generate_and_dispatch_report("daily", "manual")
        t5_raised = False
    except llm.LLMError:
        t5_raised = True
    r_after, n_after = await counts()
    llm.gen_text = real_gen
    email.send_email = real_send
    check(
        "T5 LLM failure raises, zero rows written",
        t5_raised and (r_after, n_after) == (r_before, n_before),
        f"rows {r_before}/{n_before} -> {r_after}/{n_after}",
    )

    print()
    print("--- T1 report head (first 300 chars) ---")
    print(rep1.content_md[:300] if rep1 else "-")
    print()
    failed = [n for n, okk, _ in RESULTS if not okk]
    if failed:
        print(f"FAILED: {len(failed)}/{len(RESULTS)} -> {failed}")
        sys.exit(1)
    print(f"ALL PASS ({len(RESULTS)}/{len(RESULTS)})")


if __name__ == "__main__":
    asyncio.run(main())
