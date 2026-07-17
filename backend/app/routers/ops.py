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


# ===== Step 6.2: GET /api/ops/trending =====

_TRENDING_MIN_GROWTH = 0.5     # +50% recent vs previous 3-day windows
_TRENDING_MIN_24H = 50          # >=50 tryons in last rolling 24 hours
_TRENDING_MIN_COLLECT = 0.20    # >=20% collect rate over recent 3 days


def _suggest_trending_action(growth: float, collect_rate: float, last_24h: int) -> str:
    """Plan §6.2 + design-docu §7.2: rule-based action template, no LLM."""
    if growth >= 2.0:
        return "加入首页推荐位（爆发式增长）"
    if collect_rate >= 0.30:
        return "调高推荐排序权重（高收藏意愿）"
    if last_24h >= 100:
        return "增加曝光，持续监测热度"
    return "纳入候选池，持续观察"


@router.get("/trending")
async def trending(db: AsyncSession = Depends(get_db)):
    """Plan §6.2 / design-docu §7.2: identify trending (emerging-hot) styles.

    All three rules must hold:
      - recent 3d / previous 3d growth_rate >= 50%
      - rolling last 24h tryons >= 50
      - recent 3d collect_rate >= 20%
    """
    # All four group-by queries run against UTC `created_at`. SQLite's
    # `datetime('now', ...)` is UTC too, so the windowing is consistent.
    recent_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*), "
        "SUM(CASE WHEN is_collected=1 THEN 1 ELSE 0 END) "
        "FROM tryons WHERE created_at >= datetime('now','-3 days') "
        "GROUP BY style_id"
    ))).all()
    recent_3d: dict[str, int] = {}
    recent_3d_coll: dict[str, int] = {}
    for sid, cnt, coll in recent_rows:
        recent_3d[sid] = int(cnt)
        recent_3d_coll[sid] = int(coll or 0)

    prev_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now','-6 days') "
        "AND created_at < datetime('now','-3 days') "
        "GROUP BY style_id"
    ))).all()
    prev_3d: dict[str, int] = {sid: int(c) for sid, c in prev_rows}

    last24_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now','-1 day') "
        "GROUP BY style_id"
    ))).all()
    last_24h: dict[str, int] = {sid: int(c) for sid, c in last24_rows}

    # Apply rules
    hits: list[dict] = []
    for sid, recent_cnt in recent_3d.items():
        prev_cnt = prev_3d.get(sid, 0)
        # Growth rate: standard (recent - prev) / prev. If prev is 0 but
        # recent is non-zero treat as infinity (definitely surging); else 0.
        if prev_cnt > 0:
            growth = (recent_cnt - prev_cnt) / prev_cnt
        else:
            growth = float("inf") if recent_cnt > 0 else 0.0
        if growth < _TRENDING_MIN_GROWTH:
            continue
        if last_24h.get(sid, 0) < _TRENDING_MIN_24H:
            continue
        coll_cnt = recent_3d_coll.get(sid, 0)
        coll_rate = (coll_cnt / recent_cnt) if recent_cnt > 0 else 0.0
        if coll_rate < _TRENDING_MIN_COLLECT:
            continue
        hits.append({
            "style_id": sid,
            "growth_rate": growth,
            "collect_rate": coll_rate,
            "last_24h": last_24h.get(sid, 0),
            "recent_3d": recent_cnt,
        })

    if not hits:
        return ok(data={"items": []})

    # Sort by growth_rate desc (Inf naturally sorts to the top)
    hits.sort(key=lambda x: -x["growth_rate"])
    style_ids = [h["style_id"] for h in hits]

    # Pull style metadata
    styles = (
        await db.execute(select(Style).where(Style.id.in_(style_ids)))
    ).scalars().all()
    styles_map = {s.id: s for s in styles}

    # 7-day per-style trend (last 7 Beijing days). Pull raw tryons in window,
    # aggregate client-side: avoids dialect quirks around date(col,'localtime')
    # in GROUP BY + the IN clause.
    seven_days_ago = _today_bjt() - timedelta(days=6)
    raw_trend = (await db.execute(
        select(Tryon.style_id, Tryon.created_at)
        .where(Tryon.created_at >= datetime.now(timezone.utc) - timedelta(days=7))
        .where(Tryon.style_id.in_(style_ids))
    )).all()
    per_style_by_date: dict[str, dict[str, int]] = {sid: {} for sid in style_ids}
    for sid, ct in raw_trend:
        if ct.tzinfo is None:
            ct = ct.replace(tzinfo=timezone.utc)
        bjt_d = ct.astimezone(_BJT).date().isoformat()
        per_style_by_date[sid][bjt_d] = per_style_by_date[sid].get(bjt_d, 0) + 1

    now_iso = datetime.now(_BJT).isoformat()

    items = []
    for h in hits:
        s = styles_map.get(h["style_id"])
        if s is None:
            continue
        sid_trend = [
            per_style_by_date[h["style_id"]].get(
                (seven_days_ago + timedelta(days=i)).isoformat(), 0
            )
            for i in range(7)
        ]
        # Cap growth_rate displayed to avoid Inf bleeding into JSON
        gr = h["growth_rate"]
        gr_out = None if gr == float("inf") else round(gr, 2)
        items.append({
            "style_id": s.id,
            "name": s.name,
            "cover_url": s.cover_url,
            "trend_7d": sid_trend,
            "growth_rate": gr_out,
            "collect_rate": round(h["collect_rate"], 3),
            "last_24h_tryons": h["last_24h"],
            "detected_at": now_iso,
            "suggested_action": _suggest_trending_action(
                gr if gr != float("inf") else 999.0,
                h["collect_rate"],
                h["last_24h"],
            ),
        })

    return ok(data={"items": items})


# ===== Step 6.3: GET /api/ops/cold =====

_COLD_MAX_7D_TRYONS = 5           # rule 1: recent 7d <= 5 tryons
_COLD_MAX_CLICK_RATE = 0.02       # rule 2: recent 7d click/exposure <= 2%
_COLD_LISTED_DAYS = 30            # rule 3: listed > 30 days
_COLD_CUMULATIVE_MAX = 20         # rule 3: cumulative tryons <= 20


@router.get("/cold")
async def cold(db: AsyncSession = Depends(get_db)):
    """Plan §6.3 / design-docu §7.3: identify cold-warning styles.

    Any single rule hit -> style is cold. Priority for reason/suggestion:
      rule 3 (long-dead) > rule 1 (recent slump) > rule 2 (viz problem)
    """
    # Rule 1: recent 7-day tryons per style
    r1 = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now','-7 days') "
        "GROUP BY style_id"
    ))).all()
    recent_7d: dict[str, int] = {sid: int(c) for sid, c in r1}

    # Rule 2: recent 7-day click/exposure ratio per style (from style_stats)
    r2 = (await db.execute(text(
        "SELECT style_id, SUM(click_count), SUM(exposure_count) "
        "FROM style_stats "
        "WHERE stat_date >= date('now','-7 days','localtime') "
        "GROUP BY style_id"
    ))).all()
    ratio_by_style: dict[str, tuple[int, int]] = {
        sid: (int(ck or 0), int(ex or 0)) for sid, ck, ex in r2
    }

    # Rule 3: cumulative tryons per style (all-time)
    r3 = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons GROUP BY style_id"
    ))).all()
    cumulative: dict[str, int] = {sid: int(c) for sid, c in r3}

    # All active styles + created_at for days_since_listed
    styles = (
        await db.execute(select(Style).where(Style.is_active == 1))
    ).scalars().all()

    now_utc = datetime.now(timezone.utc)
    items: list[dict] = []

    for s in styles:
        r7 = recent_7d.get(s.id, 0)
        ck, ex = ratio_by_style.get(s.id, (0, 0))
        cex_ratio = (ck / ex) if ex > 0 else 0.0
        cum = cumulative.get(s.id, 0)

        created = s.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days_listed = (now_utc - created).days

        # Priority evaluation — first matching rule wins for reason/suggestion.
        # Rule 2 requires ex > 0 to avoid false-positive on brand-new styles
        # with zero exposure data (ratio computes to 0 which trivially <= 2%).
        reason: str | None = None
        suggestion: str | None = None

        rule3_hit = days_listed > _COLD_LISTED_DAYS and cum <= _COLD_CUMULATIVE_MAX
        rule1_hit = r7 <= _COLD_MAX_7D_TRYONS
        rule2_hit = ex > 0 and cex_ratio <= _COLD_MAX_CLICK_RATE

        if rule3_hit:
            reason = f"上架 {days_listed} 天累计仅 {cum} 次试戴"
            suggestion = "建议下架或替换为新款设计"
        elif rule1_hit:
            reason = f"近 7 天试戴极少（{r7} 次）"
            suggestion = "降低推荐位排名，或临时替换封面主图观察"
        elif rule2_hit:
            reason = f"曝光高但点击寥寥（点击曝光比 {cex_ratio:.2%}）"
            suggestion = "优化封面视觉或替换主图，提升点击意愿"

        if reason is None:
            continue

        items.append({
            "style_id": s.id,
            "name": s.name,
            "cover_url": s.cover_url,
            "recent_7d_tryons": r7,
            "exposure_click_ratio": round(cex_ratio, 4),
            "days_since_listed": days_listed,
            "cumulative_tryons": cum,
            "cold_reason": reason,
            "suggestion": suggestion,
        })

    # Order: coldest first (fewest recent 7d, ties broken by lowest cumulative)
    items.sort(key=lambda h: (h["recent_7d_tryons"], h["cumulative_tryons"]))
    return ok(data={"items": items})
