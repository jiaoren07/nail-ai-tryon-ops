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

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func as sqlf
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import OpsAction, Style, StyleStats, Tryon
from app.responses import ok
from app.services import llm
from app.services.assistant_tools import TOOL_SCHEMAS, dispatch

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


# ===== Step 6.4: POST /api/ops/actions =====

_VALID_ACTION_TYPES = {"boost", "demote", "offline", "reorder"}


class ActionBody(BaseModel):
    style_id: str
    action_type: str  # boost | demote | offline | reorder
    reason: str | None = None


async def _target_order_for_action(db: AsyncSession, action_type: str) -> int | None:
    """boost -> min(active display_order)-1; demote -> max+1; else None.

    Shared by the REST action endpoint and the Step 8.1 assistant tool so
    the "top/bottom of the active list" semantics can never drift apart.
    """
    if action_type == "boost":
        current_min = (
            await db.execute(
                select(sqlf.min(Style.display_order)).where(Style.is_active == 1)
            )
        ).scalar_one() or 0
        return current_min - 1
    if action_type == "demote":
        current_max = (
            await db.execute(
                select(sqlf.max(Style.display_order)).where(Style.is_active == 1)
            )
        ).scalar_one() or 0
        return current_max + 1
    return None


async def _apply_action_and_audit(
    db: AsyncSession,
    style: Style,
    *,
    action_type: str,
    reason: str | None,
    display_order: int | None = None,
    is_active: int | None = None,
) -> OpsAction:
    """Apply one style mutation and stage its matching audit row.

    The caller owns the commit so multiple field changes can land atomically.
    """
    if display_order is not None:
        style.display_order = display_order
    if is_active is not None:
        style.is_active = is_active

    audit = OpsAction(
        style_id=style.id,
        action_type=action_type,
        reason=reason,
        operator="ai_assistant",
    )
    db.add(audit)
    await db.flush()
    return audit


@router.post("/actions")
async def perform_action(body: ActionBody, db: AsyncSession = Depends(get_db)):
    """Plan §6.4: unified ops-action entrypoint. Every action (except
    reorder) atomically mutates styles + appends an ops_actions audit row.

    - boost   : styles.display_order := min(active display_order) - 1
    - demote  : styles.display_order := max(active display_order) + 1
    - offline : styles.is_active := 0
    - reorder : returns 501 not_implemented (plan defers)

    Both the styles mutation and the ops_actions insert are in one
    transaction, so an audit row is guaranteed to accompany any state
    change (either both land or both roll back).
    """
    if body.action_type not in _VALID_ACTION_TYPES:
        raise HTTPException(400, "invalid_action_type")
    if body.action_type == "reorder":
        raise HTTPException(501, "not_implemented")

    style = (
        await db.execute(select(Style).where(Style.id == body.style_id))
    ).scalar_one_or_none()
    if style is None:
        raise HTTPException(404, "style_not_found")

    display_order: int | None = await _target_order_for_action(db, body.action_type)
    is_active: int | None = 0 if body.action_type == "offline" else None

    audit = await _apply_action_and_audit(
        db,
        style,
        action_type=body.action_type,
        reason=body.reason,
        display_order=display_order,
        is_active=is_active,
    )
    await db.commit()

    return ok(data={
        "action_id": audit.id,
        "style_id": body.style_id,
        "action_type": body.action_type,
        "display_order": style.display_order,
        "is_active": bool(style.is_active),
        "reason": body.reason,
    })


# ===== Step 6.5: GET/PATCH /api/ops/styles =====

class StylePatchBody(BaseModel):
    is_active: bool | None = None
    display_order: int | None = None
    reason: str | None = None


def _style_to_ops_dict(style: Style) -> dict:
    return {
        "id": style.id,
        "name": style.name,
        "gender": style.gender,
        "cover_url": style.cover_url,
        "style_tags": json.loads(style.style_tags),
        "color_main": style.color_main,
        "color_tone": style.color_tone,
        "length_pref": style.length_pref,
        "complexity": style.complexity,
        "heat_score": style.heat_score,
        "is_active": bool(style.is_active),
        "display_order": style.display_order,
        "created_at": style.created_at.isoformat() if style.created_at else None,
    }


@router.get("/styles")
async def list_ops_styles(db: AsyncSession = Depends(get_db)):
    """Return every style, including inactive rows, in display order."""
    styles = (
        await db.execute(
            select(Style).order_by(Style.display_order.asc(), Style.id.asc())
        )
    ).scalars().all()
    return ok(data={
        "items": [_style_to_ops_dict(style) for style in styles],
        "total": len(styles),
    })


@router.patch("/styles/{style_id}")
async def patch_ops_style(
    style_id: str,
    body: StylePatchBody,
    db: AsyncSession = Depends(get_db),
):
    """Update active/order fields and atomically append one audit per change."""
    if body.is_active is None and body.display_order is None:
        raise HTTPException(400, "no_fields_to_update")

    style = (
        await db.execute(select(Style).where(Style.id == style_id))
    ).scalar_one_or_none()
    if style is None:
        raise HTTPException(404, "style_not_found")

    audits: list[OpsAction] = []
    new_is_active = int(body.is_active) if body.is_active is not None else None
    if new_is_active is not None and style.is_active != new_is_active:
        audits.append(await _apply_action_and_audit(
            db,
            style,
            action_type="offline",
            reason=body.reason,
            is_active=new_is_active,
        ))

    if body.display_order is not None and style.display_order != body.display_order:
        audits.append(await _apply_action_and_audit(
            db,
            style,
            action_type="reorder",
            reason=body.reason,
            display_order=body.display_order,
        ))

    if not audits:
        return ok(data={
            "changed": False,
            "style_id": style.id,
            "is_active": bool(style.is_active),
            "display_order": style.display_order,
            "action_ids": [],
        })

    await db.commit()
    return ok(data={
        "changed": True,
        "style_id": style.id,
        "is_active": bool(style.is_active),
        "display_order": style.display_order,
        "action_ids": [audit.id for audit in audits],
    })


# ===== Step 8.2: POST /api/ops/chat =====

_CHAT_MAX_TOOL_ROUNDS = 3   # plan §8.2: at most 3 LLM->tools rounds
_CHAT_HISTORY_LIMIT = 20    # keep prompt bounded; frontend sends full history

# Executed tool -> frontend component name (design-docu §7.5 protocol).
# Only ok=True results become components; error dicts go back to the LLM.
_COMPONENT_BY_TOOL = {
    "query_top_styles": "top_styles_table",
    "find_trending": "trending_list",
    "find_cold": "cold_list",
    "compare_styles": "compare_table",
    "execute_action": "action_result",
}

_CHAT_SYSTEM_PROMPT = (
    "你是美甲品类运营工作台的 AI 助手，帮运营人员查数据、做判断、执行动作。\n"
    "规则：\n"
    "1. 涉及数据的问题必须先调用工具查询，严禁编造数字；回答要引用工具返回的具体款式名和数字。\n"
    "2. 用户未指定参数时的默认值：query_top_styles 用 date_range=today、top_n=3；"
    "find_trending 用 growth_threshold=0.5、min_volume=50（与爆款页同口径）；"
    "find_cold 用 days_no_activity=7。\n"
    "3. 只有当用户明确要求执行动作（推荐位/降序/下架）时才调用 execute_action，"
    "执行后清楚说明做了什么动作、生效结果。\n"
    "4. 用简体中文回复，简洁专业，不超过 150 字。明细数据由界面组件展示，"
    "文字里点出关键结论即可，不要罗列全表。"
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatBody(BaseModel):
    messages: list[ChatMessage]
    session_id: str | None = None


def _chat_fallback_reply(components: list[dict]) -> str:
    """Template reply used when the LLM cannot produce final text (rate
    limit / timeout / rounds exhausted) but tools already ran — the demo
    must degrade to something informative, never a blank bubble."""
    if not components:
        return "AI 服务暂时繁忙，请稍后重试。"
    parts: list[str] = []
    for comp in components:
        name, data = comp["component"], comp["data"]
        if name == "top_styles_table" and data:
            parts.append(f"试戴 TOP{len(data)}：{data[0]['name']} 以 {data[0]['tryon_count']} 次居首")
        elif name == "trending_list":
            if data:
                names = "、".join(f"「{d['name']}」" for d in data[:3])
                parts.append(f"发现 {len(data)} 款增长中的爆款候选：{names}")
            else:
                parts.append("当前没有满足阈值的爆款候选")
        elif name == "cold_list":
            if data:
                names = "、".join(f"「{d['name']}」" for d in data[:3])
                parts.append(f"发现 {len(data)} 款连续无试戴的冷门款：{names}")
            else:
                parts.append("没有完全无活动的款式")
        elif name == "compare_table" and data:
            found = [d for d in data if d.get("found")]
            names = "、".join(f"「{d['name']}」" for d in found[:3])
            parts.append(f"已对比 {names} 的试戴与收藏数据")
        elif name == "action_result" and data.get("ok"):
            parts.append(f"已对「{data.get('name', data.get('style_id'))}」执行 {data['action_type']}")
    joined = "；".join(parts) if parts else "查询已完成"
    return f"{joined}。详细数据见下方组件。（AI 文案生成繁忙，以上为系统摘要）"


@router.post("/chat")
async def ops_chat(body: ChatBody, db: AsyncSession = Depends(get_db)):
    """Plan §8.2: assistant chat with a bounded Function-Calling loop.

    messages -> LLM(strong, tools) -> [execute tool_calls -> feed back]*
    up to _CHAT_MAX_TOOL_ROUNDS, then the last text (or a template
    summary) is returned together with `components` derived from every
    successfully executed tool.

    Tool calls run SEQUENTIALLY, not asyncio.gather (design-docu §7.5
    pseudo-code) — one AsyncSession must not be shared across concurrent
    tasks, and execute_action commits mid-loop.
    """
    if not body.messages:
        raise HTTPException(400, "empty_messages")
    for m in body.messages:
        if m.role not in {"user", "assistant"}:
            raise HTTPException(400, "invalid_role")
        if not m.content.strip():
            raise HTTPException(400, "empty_content")
    if body.messages[-1].role != "user":
        raise HTTPException(400, "last_message_must_be_user")

    history = body.messages[-_CHAT_HISTORY_LIMIT:]
    llm_messages: list[dict] = [
        {"role": "system", "content": _CHAT_SYSTEM_PROMPT},
        *({"role": m.role, "content": m.content} for m in history),
    ]

    components: list[dict] = []
    tool_rounds = 0
    reply: str | None = None

    try:
        for _ in range(_CHAT_MAX_TOOL_ROUNDS):
            msg = await llm.gen_text_with_tools(llm_messages, TOOL_SCHEMAS)
            if not msg.tool_calls:
                reply = (msg.content or "").strip()
                break

            tool_rounds += 1
            llm_messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                result = await dispatch(db, tc.function.name, tc.function.arguments)
                if result.get("ok") and tc.function.name in _COMPONENT_BY_TOOL:
                    data = result if tc.function.name == "execute_action" else result.get("items", [])
                    components.append({
                        "component": _COMPONENT_BY_TOOL[tc.function.name],
                        "data": data,
                    })
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        else:
            # Rounds exhausted while the model still wants tools: one last
            # text-only call so the reply reflects gathered data.
            final = await llm.gen_text_with_tools(llm_messages, tools=[])
            reply = (final.content or "").strip()
    except (llm.LLMError, llm.ConfigError):
        reply = None  # degrade below; components (if any) still ship

    if not reply:
        reply = _chat_fallback_reply(components)

    return ok(data={
        "reply": reply,
        "components": components,
        "session_id": body.session_id,
        "tool_rounds": tool_rounds,
    })
