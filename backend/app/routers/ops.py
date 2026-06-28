"""B-end (operator-side) routes.

CONVENTION (per implementation-plan §2.3):
All B-end routes — overview / trending / cold / actions / styles / chat /
reports / notifications / setting / etc — live in this single file under
prefix `/api/ops`.

DO NOT create separate files per business object. The filename `ops.py`
is shorthand for "B-end router".
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func as sqlf
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Style, StyleStats, Tryon
from app.responses import ok

router = APIRouter(prefix="/api/ops")

_BJT = timezone(timedelta(hours=8))


def _today_bjt() -> date:
    return datetime.now(_BJT).date()


def _now_bjt_seconds_into_day() -> int:
    """Seconds elapsed since midnight Beijing today. Used for "yesterday
    same period" calculations: yesterday's events at time<=current_time."""
    n = datetime.now(_BJT)
    return n.hour * 3600 + n.minute * 60 + n.second


def _pct_diff(curr: float, prev: float) -> float | None:
    """Return (curr-prev)/prev * 100 rounded to 1 decimal; None if prev is 0."""
    if prev == 0:
        return None
    return round((curr - prev) / prev * 100, 1)


@router.get("/ping")
def ping():
    """Liveness probe for the B-end router. Plan §2.3 verification target."""
    return ok(data={"router": "ops"})


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    """Plan §6.1 / design-docu §7.1: one-shot dashboard data.

    Returns:
      kpis: 4 KPIs with current value + ring-comparison percent (today
            full-day vs yesterday's same time window per design-docu §7.1)
      trend_7d:           7-day daily tryon totals (chronological)
      style_distribution: today's top-6 first-tag distribution (percent)
      hourly_heat:        24 ints, today's per-hour tryon counts
    """
    today = _today_bjt()
    yesterday = today - timedelta(days=1)
    elapsed_sec = _now_bjt_seconds_into_day()

    # ---------- KPIs ----------
    # Beijing-date filter via SQLite `date(col, 'localtime')`
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()

    # KPI 1: tryons today (full day so far) vs yesterday's matching window.
    # We use the tryons table directly (rather than style_stats) so the
    # comparison can include sub-day "time(created_at,'localtime') <= now"
    # filtering on yesterday.
    today_tryons = (await db.execute(text(
        "SELECT COUNT(*) FROM tryons "
        "WHERE date(created_at,'localtime') = :d"
    ), {"d": today_str})).scalar_one()

    yest_same_period_tryons = (await db.execute(text(
        "SELECT COUNT(*) FROM tryons "
        "WHERE date(created_at,'localtime') = :d "
        "AND (CAST(strftime('%H', created_at,'localtime') AS INTEGER) * 3600 "
        " + CAST(strftime('%M', created_at,'localtime') AS INTEGER) * 60 "
        " + CAST(strftime('%S', created_at,'localtime') AS INTEGER)) <= :s"
    ), {"d": yesterday_str, "s": elapsed_sec})).scalar_one()

    # KPI 2: conversion (collect / tryon) today vs yesterday-same-period
    today_collected = (await db.execute(text(
        "SELECT COUNT(*) FROM tryons "
        "WHERE date(created_at,'localtime') = :d AND is_collected = 1"
    ), {"d": today_str})).scalar_one()
    today_rate = (today_collected / today_tryons) if today_tryons else 0.0

    yest_collected = (await db.execute(text(
        "SELECT COUNT(*) FROM tryons "
        "WHERE date(created_at,'localtime') = :d AND is_collected = 1 "
        "AND (CAST(strftime('%H', created_at,'localtime') AS INTEGER) * 3600 "
        " + CAST(strftime('%M', created_at,'localtime') AS INTEGER) * 60 "
        " + CAST(strftime('%S', created_at,'localtime') AS INTEGER)) <= :s"
    ), {"d": yesterday_str, "s": elapsed_sec})).scalar_one()
    yest_rate = (yest_collected / yest_same_period_tryons) if yest_same_period_tryons else 0.0

    # KPI 3: active styles snapshot (no ring-compare history available;
    # frontend renders without an arrow)
    active_styles = (await db.execute(
        select(sqlf.count()).select_from(Style).where(Style.is_active == 1)
    )).scalar_one()

    # KPI 4: new trending alerts (Step 6.2 owns the trending detection; here
    # we just expose a sentinel 0 + None diff so the dashboard renders. The
    # ops frontend Phase 7 will likely overlay /api/ops/trending count
    # without re-deriving the rule.)
    new_trending_alerts = 0

    kpis = {
        "tryons_today": {
            "value": today_tryons,
            "diff_percent": _pct_diff(today_tryons, yest_same_period_tryons),
        },
        "conversion_rate": {
            "value": round(today_rate, 4),
            "diff_percent": _pct_diff(today_rate, yest_rate),
        },
        "active_styles": {
            "value": active_styles,
            "diff_percent": None,
        },
        "new_trending_alerts": {
            "value": new_trending_alerts,
            "diff_percent": None,
        },
    }

    # ---------- trend_7d ----------
    # 7 days inclusive of today, oldest first. Backfill missing dates with 0.
    seven_days_ago = today - timedelta(days=6)
    rows = (await db.execute(text(
        "SELECT stat_date, SUM(tryon_count) "
        "FROM style_stats WHERE stat_date >= :start GROUP BY stat_date"
    ), {"start": seven_days_ago.isoformat()})).all()
    counts_by_date: dict[str, int] = {str(r[0]): int(r[1] or 0) for r in rows}
    trend_7d = [
        {
            "date": (seven_days_ago + timedelta(days=i)).isoformat(),
            "tryon_count": counts_by_date.get((seven_days_ago + timedelta(days=i)).isoformat(), 0),
        }
        for i in range(7)
    ]

    # ---------- style_distribution (today's first-tag top-6) ----------
    # JOIN tryons -> styles, take styles.style_tags (JSON), use [0] as
    # primary tag. Aggregate counts client-side because SQLite has no
    # native JSON-array indexing.
    rows = (await db.execute(text(
        "SELECT s.style_tags FROM tryons t "
        "JOIN styles s ON t.style_id = s.id "
        "WHERE date(t.created_at,'localtime') = :d"
    ), {"d": today_str})).all()
    tag_counter: Counter[str] = Counter()
    for (tags_json,) in rows:
        try:
            tags = json.loads(tags_json)
        except (ValueError, TypeError):
            continue
        if tags:
            tag_counter[tags[0]] += 1
    total_tagged = sum(tag_counter.values()) or 1
    top6 = tag_counter.most_common(6)
    style_distribution = [
        {"style_tag": tag, "percent": round(cnt / total_tagged * 100, 1)}
        for tag, cnt in top6
    ]

    # ---------- hourly_heat (today, 24 ints) ----------
    hourly_rows = (await db.execute(text(
        "SELECT CAST(strftime('%H', created_at, 'localtime') AS INTEGER) AS hr, "
        "COUNT(*) FROM tryons WHERE date(created_at,'localtime') = :d "
        "GROUP BY hr"
    ), {"d": today_str})).all()
    hourly: list[int] = [0] * 24
    for hr, cnt in hourly_rows:
        if hr is not None and 0 <= int(hr) < 24:
            hourly[int(hr)] = int(cnt or 0)

    return ok(data={
        "kpis": kpis,
        "trend_7d": trend_7d,
        "style_distribution": style_distribution,
        "hourly_heat": hourly,
    })
