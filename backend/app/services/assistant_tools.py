"""Step 8.1: Function Calling tool set for the ops AI assistant.

Five tools per design-docu §5.3 / plan §8.1, exposed two ways:
  - TOOL_SCHEMAS: OpenAI `tools` array (Step 8.2 passes it to the LLM)
  - dispatch():   name + arguments dict -> awaited tool result dict

Conventions:
  - Every tool is an async pure-ish function `tool(db, **kwargs) -> dict`
    returning JSON-serializable data (NOT an HTTP envelope).
  - Tools never raise on bad LLM-supplied input; they return
    {"ok": False, "error": "..."} so the FC loop can feed the error back
    to the model for self-correction. Programming errors still raise.
  - Date windows use Beijing calendar days via SQLite `localtime`,
    matching the ops REST endpoints.
  - execute_action reuses ops.py's `_apply_action_and_audit` +
    `_target_order_for_action` so every mutation lands with the same
    audit trail as `POST /api/ops/actions` (operator: ai_assistant).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Style

_BJT = timezone(timedelta(hours=8))

# date_range enum -> (days_back_from_today, include_today)
# Window is a closed range of Beijing calendar dates [start, end].
_DATE_RANGES = {
    "today": 0,
    "yesterday": None,  # special-cased: single day, yesterday
    "last_3d": 2,
    "last_7d": 6,
    "last_30d": 29,
}


def _range_bounds(date_range: str) -> tuple[str, str] | None:
    """Return (start_iso, end_iso) Beijing dates for a date_range enum."""
    if date_range not in _DATE_RANGES:
        return None
    today = datetime.now(_BJT).date()
    if date_range == "yesterday":
        d = today - timedelta(days=1)
        return d.isoformat(), d.isoformat()
    back = _DATE_RANGES[date_range]
    return (today - timedelta(days=back)).isoformat(), today.isoformat()


def _err(message: str) -> dict:
    return {"ok": False, "error": message}


# ---------------------------------------------------------------- tool 1
async def query_top_styles(
    db: AsyncSession,
    date_range: str = "today",
    top_n: int = 5,
    gender: str | None = None,
) -> dict:
    """Top-N styles by tryon count inside a date window (+ collect rate)."""
    bounds = _range_bounds(date_range)
    if bounds is None:
        return _err(f"invalid date_range '{date_range}', use one of {sorted(_DATE_RANGES)}")
    if not 1 <= int(top_n) <= 20:
        return _err("top_n must be between 1 and 20")
    if gender is not None and gender not in {"female", "male"}:
        return _err("gender must be 'female' or 'male' (or omitted)")

    gender_clause = ""
    params: dict = {"s": bounds[0], "e": bounds[1], "n": int(top_n)}
    if gender is not None:
        gender_clause = "AND s.gender IN (:g, 'both') "
        params["g"] = gender

    rows = (await db.execute(text(
        "SELECT t.style_id, s.name, COUNT(*) AS cnt, "
        "SUM(CASE WHEN t.is_collected=1 THEN 1 ELSE 0 END) AS coll "
        "FROM tryons t JOIN styles s ON t.style_id = s.id "
        "WHERE date(t.created_at,'localtime') BETWEEN :s AND :e "
        f"{gender_clause}"
        "GROUP BY t.style_id ORDER BY cnt DESC, t.style_id ASC LIMIT :n"
    ), params)).all()

    items = [
        {
            "style_id": sid,
            "name": name,
            "tryon_count": int(cnt),
            "collect_count": int(coll or 0),
            "collect_rate": round((coll or 0) / cnt, 3) if cnt else 0.0,
        }
        for sid, name, cnt, coll in rows
    ]
    return {"ok": True, "date_range": date_range, "items": items}


# ---------------------------------------------------------------- tool 2
async def compare_styles(
    db: AsyncSession,
    style_ids: list[str],
    date_range: str = "last_7d",
) -> dict:
    """Side-by-side tryon/collect stats for 2..6 named styles."""
    bounds = _range_bounds(date_range)
    if bounds is None:
        return _err(f"invalid date_range '{date_range}', use one of {sorted(_DATE_RANGES)}")
    if not isinstance(style_ids, list) or not 2 <= len(style_ids) <= 6:
        return _err("style_ids must be a list of 2 to 6 style ids")

    styles = (
        await db.execute(select(Style).where(Style.id.in_(style_ids)))
    ).scalars().all()
    styles_map = {s.id: s for s in styles}

    known_ids = [sid for sid in style_ids if sid in styles_map]
    counts: dict[str, tuple[int, int]] = {}
    if known_ids:
        placeholders = ",".join(f":id{i}" for i in range(len(known_ids)))
        params = {f"id{i}": sid for i, sid in enumerate(known_ids)}
        params.update({"s": bounds[0], "e": bounds[1]})
        rows = (await db.execute(text(
            "SELECT style_id, COUNT(*), "
            "SUM(CASE WHEN is_collected=1 THEN 1 ELSE 0 END) "
            "FROM tryons "
            "WHERE date(created_at,'localtime') BETWEEN :s AND :e "
            f"AND style_id IN ({placeholders}) GROUP BY style_id"
        ), params)).all()
        counts = {sid: (int(c), int(coll or 0)) for sid, c, coll in rows}

    items = []
    for sid in style_ids:  # preserve caller order
        s = styles_map.get(sid)
        if s is None:
            items.append({"style_id": sid, "found": False})
            continue
        cnt, coll = counts.get(sid, (0, 0))
        items.append({
            "style_id": sid,
            "found": True,
            "name": s.name,
            "is_active": bool(s.is_active),
            "tryon_count": cnt,
            "collect_count": coll,
            "collect_rate": round(coll / cnt, 3) if cnt else 0.0,
        })
    return {"ok": True, "date_range": date_range, "items": items}


# ---------------------------------------------------------------- tool 3
async def find_trending(
    db: AsyncSession,
    growth_threshold: float = 0.5,
    min_volume: int = 50,
) -> dict:
    """Styles whose recent-3d tryons grew >= threshold vs previous 3d AND
    whose rolling last-24h volume >= min_volume.

    NOTE: parameterized variant of GET /api/ops/trending. The REST rule
    set additionally requires collect_rate >= 20%; this tool exposes the
    two tunable rules from its signature and RETURNS collect_rate so the
    LLM (or caller) can apply its own collection cutoff. Tool output is
    therefore a superset of the O2 page when called with defaults.
    """
    try:
        growth_threshold = float(growth_threshold)
        min_volume = int(min_volume)
    except (TypeError, ValueError):
        return _err("growth_threshold must be a number and min_volume an integer")
    if growth_threshold < 0 or min_volume < 0:
        return _err("growth_threshold and min_volume must be >= 0")

    recent_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*), "
        "SUM(CASE WHEN is_collected=1 THEN 1 ELSE 0 END) "
        "FROM tryons WHERE created_at >= datetime('now','-3 days') "
        "GROUP BY style_id"
    ))).all()
    prev_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now','-6 days') "
        "AND created_at < datetime('now','-3 days') GROUP BY style_id"
    ))).all()
    last24_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now','-1 day') GROUP BY style_id"
    ))).all()

    prev_3d = {sid: int(c) for sid, c in prev_rows}
    last_24h = {sid: int(c) for sid, c in last24_rows}

    hits = []
    for sid, cnt, coll in recent_rows:
        recent = int(cnt)
        prev = prev_3d.get(sid, 0)
        growth: float | None
        if prev > 0:
            growth = (recent - prev) / prev
            if growth < growth_threshold:
                continue
        else:
            growth = None  # 0-base surge: treat as passing any threshold
            if recent == 0:
                continue
        vol24 = last_24h.get(sid, 0)
        if vol24 < min_volume:
            continue
        hits.append({
            "style_id": sid,
            "growth_rate": round(growth, 2) if growth is not None else None,
            "recent_3d": recent,
            "last_24h_tryons": vol24,
            "collect_rate": round((coll or 0) / recent, 3) if recent else 0.0,
        })

    hits.sort(key=lambda h: (h["growth_rate"] is not None, -(h["growth_rate"] or 0)))
    style_ids = [h["style_id"] for h in hits]
    names = {}
    if style_ids:
        names = {
            s.id: s.name
            for s in (
                await db.execute(select(Style).where(Style.id.in_(style_ids)))
            ).scalars()
        }
    for h in hits:
        h["name"] = names.get(h["style_id"], h["style_id"])
    return {
        "ok": True,
        "growth_threshold": growth_threshold,
        "min_volume": min_volume,
        "items": hits,
    }


# ---------------------------------------------------------------- tool 4
async def find_cold(db: AsyncSession, days_no_activity: int = 7) -> dict:
    """Active styles with ZERO tryons in the last N days (literal
    "no activity"), plus listing age and lifetime volume for context.

    NOTE: narrower than GET /api/ops/cold (whose rule 1 is <=5 tryons /
    7d and which adds click-ratio + long-dead rules); this tool answers
    the specific "which styles had no activity for N days" question the
    signature encodes.
    """
    try:
        days = int(days_no_activity)
    except (TypeError, ValueError):
        return _err("days_no_activity must be an integer")
    if not 1 <= days <= 90:
        return _err("days_no_activity must be between 1 and 90")

    recent_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons "
        "WHERE created_at >= datetime('now', :win) GROUP BY style_id"
    ), {"win": f"-{days} days"})).all()
    recent = {sid: int(c) for sid, c in recent_rows}

    cumulative_rows = (await db.execute(text(
        "SELECT style_id, COUNT(*) FROM tryons GROUP BY style_id"
    ))).all()
    cumulative = {sid: int(c) for sid, c in cumulative_rows}

    styles = (
        await db.execute(select(Style).where(Style.is_active == 1))
    ).scalars().all()

    now_utc = datetime.now(timezone.utc)
    items = []
    for s in styles:
        if recent.get(s.id, 0) > 0:
            continue
        created = s.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        items.append({
            "style_id": s.id,
            "name": s.name,
            "days_checked": days,
            "cumulative_tryons": cumulative.get(s.id, 0),
            "days_since_listed": (now_utc - created).days,
        })
    items.sort(key=lambda h: h["cumulative_tryons"])
    return {"ok": True, "days_no_activity": days, "items": items}


# ---------------------------------------------------------------- tool 5
async def execute_action(db: AsyncSession, style_id: str, action_type: str) -> dict:
    """Apply boost / demote / offline through the shared mutation+audit
    path (`_apply_action_and_audit`), committing atomically. Audit rows
    carry operator='ai_assistant' (model default) and a fixed reason."""
    # Imported here (not at module top) to keep services -> routers
    # coupling explicit and avoid import cycles at app startup.
    from app.routers.ops import _apply_action_and_audit, _target_order_for_action

    if action_type not in {"boost", "demote", "offline"}:
        return _err(
            f"unsupported action_type '{action_type}', use boost | demote | offline"
        )

    style = (
        await db.execute(select(Style).where(Style.id == style_id))
    ).scalar_one_or_none()
    if style is None:
        return _err(f"style '{style_id}' not found")

    display_order = await _target_order_for_action(db, action_type)
    is_active = 0 if action_type == "offline" else None

    audit = await _apply_action_and_audit(
        db,
        style,
        action_type=action_type,
        reason="AI 助手 Function Calling 执行",
        display_order=display_order,
        is_active=is_active,
    )
    await db.commit()
    return {
        "ok": True,
        "style_id": style.id,
        "name": style.name,
        "action_type": action_type,
        "display_order": style.display_order,
        "is_active": bool(style.is_active),
        "action_id": audit.id,
    }


# ------------------------------------------------------------ dispatcher
_TOOL_FUNCS = {
    "query_top_styles": query_top_styles,
    "compare_styles": compare_styles,
    "find_trending": find_trending,
    "find_cold": find_cold,
    "execute_action": execute_action,
}

_DATE_RANGE_SCHEMA = {
    "type": "string",
    "enum": ["today", "yesterday", "last_3d", "last_7d", "last_30d"],
    "description": "统计窗口（北京时区自然日，含今天）",
}

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "query_top_styles",
            "description": "查询某时间窗口内试戴次数最多的 TopN 款式（含收藏率），可按性别过滤",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_range": _DATE_RANGE_SCHEMA,
                    "top_n": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": "返回条数，默认 5",
                    },
                    "gender": {
                        "type": "string",
                        "enum": ["female", "male"],
                        "description": "可选：只看该性别可见的款式（含通用款）",
                    },
                },
                "required": ["date_range", "top_n"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_styles",
            "description": "对比 2-6 个指定款式在同一时间窗口内的试戴量与收藏率",
            "parameters": {
                "type": "object",
                "properties": {
                    "style_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 6,
                        "description": "款式 id 列表，如 [\"f_15\",\"f_09\"]",
                    },
                    "date_range": _DATE_RANGE_SCHEMA,
                },
                "required": ["style_ids", "date_range"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_trending",
            "description": (
                "发现增长中的爆款候选：近 3 天试戴较前 3 天增长率 >= growth_threshold，"
                "且最近 24 小时试戴量 >= min_volume。结果附收藏率供进一步筛选"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "growth_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "description": "增长率阈值，0.5 表示 +50%（O2 页面同款默认）",
                    },
                    "min_volume": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "最近 24 小时最低试戴量，O2 页面默认 50",
                    },
                },
                "required": ["growth_threshold", "min_volume"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_cold",
            "description": "发现连续 N 天完全无试戴的在架款式（含上架天数与累计试戴量）",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_no_activity": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 90,
                        "description": "连续无活动天数，常用 7",
                    },
                },
                "required": ["days_no_activity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_action",
            "description": (
                "执行真实运营动作并写入审计：boost=置顶推荐位，demote=降至末位，"
                "offline=下架（用户端立即不可见）。动作立刻生效，谨慎调用"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "style_id": {"type": "string", "description": "款式 id，如 f_15"},
                    "action_type": {
                        "type": "string",
                        "enum": ["boost", "demote", "offline"],
                    },
                },
                "required": ["style_id", "action_type"],
            },
        },
    },
]


async def dispatch(db: AsyncSession, name: str, arguments: dict | str) -> dict:
    """Route one LLM tool call to its implementation.

    `arguments` accepts a dict or the raw JSON string the OpenAI API
    returns. Unknown tools / broken JSON come back as error dicts, never
    exceptions, so Step 8.2's FC loop can hand them to the model.
    """
    func = _TOOL_FUNCS.get(name)
    if func is None:
        return _err(f"unknown tool '{name}', available: {sorted(_TOOL_FUNCS)}")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments.strip() else {}
        except ValueError:
            return _err("arguments is not valid JSON")
    if not isinstance(arguments, dict):
        return _err("arguments must be a JSON object")
    try:
        return await func(db, **arguments)
    except TypeError as e:
        # e.g. unexpected/missing kwargs from the model
        return _err(f"bad arguments for '{name}': {e}")
