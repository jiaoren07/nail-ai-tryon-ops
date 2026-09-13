"""Step 9.1 verification for generate_and_dispatch_report.

Batch H: the email leg was removed product-wide — reports are in-app
only, so this script now verifies the reports+notifications pipeline.
LLM calls are REAL (strong tier, 2 calls total, 20s spacing for the
per-minute rate limit).

  T1 daily        -> reports row (type/title/period/source/content_md),
     notifications row (ref_id, summary<=121)
  T2 weekly       -> period == last complete Mon..Sun week
  T3 unknown type -> ReportError, no rows
  T4 LLM failure  -> raises, NO report/notification rows (rollback)

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
    from app.services import llm
    from app.services.report import ReportError, generate_and_dispatch_report

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

    # ---- T1: daily -----------------------------------------------------
    r0, n0 = await counts()
    rid1 = await generate_and_dispatch_report("daily", "manual")
    rep1, notif1 = await load_report(rid1)
    r1, n1 = await counts()
    today = date.today()
    check(
        "T1 daily: report+notification rows written",
        rep1 is not None
        and rep1.type == "daily"
        and rep1.trigger_source == "manual"
        and rep1.period_start == today and rep1.period_end == today
        and today.isoformat() in rep1.title
        and len(rep1.content_md) > 100 and "##" in rep1.content_md
        and notif1 is not None and notif1.type == "report"
        and len(notif1.summary) <= 121
        and (r1, n1) == (r0 + 1, n0 + 1),
        f"id={rid1} md_len={len(rep1.content_md) if rep1 else 0}",
    )
    time.sleep(LLM_PAUSE)

    # ---- T2: weekly period semantics -----------------------------------
    rid2 = await generate_and_dispatch_report("weekly", "manual")
    rep2, _ = await load_report(rid2)
    this_monday = today - timedelta(days=today.weekday())
    expect_start = this_monday - timedelta(days=7)
    expect_end = expect_start + timedelta(days=6)
    check(
        "T2 weekly: period == last complete Mon..Sun",
        rep2 is not None
        and rep2.type == "weekly"
        and rep2.period_start == expect_start
        and rep2.period_end == expect_end
        and "~" in rep2.title,
        f"period={rep2.period_start}~{rep2.period_end}" if rep2 else "-",
    )

    # ---- T3: unknown type ----------------------------------------------
    try:
        await generate_and_dispatch_report("monthly", "manual")
        t3 = False
    except ReportError:
        t3 = True
    check("T3 unknown type raises ReportError", t3)

    # ---- T4: LLM failure -> rollback, no rows --------------------------
    real_gen = llm.gen_text

    async def llm_fail(*args, **kwargs):
        raise llm.LLMError("stub: simulated LLM outage")

    llm.gen_text = llm_fail
    r_before, n_before = await counts()
    try:
        await generate_and_dispatch_report("daily", "manual")
        t4_raised = False
    except llm.LLMError:
        t4_raised = True
    r_after, n_after = await counts()
    llm.gen_text = real_gen
    check(
        "T4 LLM failure raises, zero rows written",
        t4_raised and (r_after, n_after) == (r_before, n_before),
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
