"""Recommendation engine: 4-dim scoring + diversity rerank.

Per design-docu §6.3 + implementation-plan Step 4.4:
- Hard gender pre-filter (no cross-pollination)
- 4-dim weighted score: skin 35% / shape 30% / heat 20% / diversity 15%
- Diversity in scoring is `0`; it materializes in the post-sort rerank
- Module returns scored + reranked candidates; LLM reasons are added by
  the HTTP route layer (Step 4.5), not here.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func as sqlf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Style, StyleStats

# Beijing timezone for the 7-day window (matches stat_date semantics in
# seed_stats.py, which buckets by `date(created_at, 'localtime')`).
_BJT = timezone(timedelta(hours=8))


# ---------- Score tables ----------

# (skin_tone, color_tone) -> score in [0, 1]. Rationale: warm tones flatter
# warm undertones; cool tones flatter cool undertones; neutral/nude flatters
# everything but especially deeper skin tones.
_SKIN_COLOR_SCORE: dict[tuple[str, str], float] = {
    ("light_warm", "warm"): 0.90,
    ("light_warm", "cool"): 0.55,
    ("light_warm", "neutral"): 0.75,
    ("light_cool", "warm"): 0.55,
    ("light_cool", "cool"): 0.90,
    ("light_cool", "neutral"): 0.75,
    ("medium", "warm"): 0.75,
    ("medium", "cool"): 0.75,
    ("medium", "neutral"): 0.85,
    ("dark_warm", "warm"): 0.60,
    ("dark_warm", "cool"): 0.70,
    ("dark_warm", "neutral"): 0.90,
    ("dark_cool", "warm"): 0.45,
    ("dark_cool", "cool"): 0.90,
    ("dark_cool", "neutral"): 0.80,
}
_DEFAULT_SKIN_SCORE = 0.5

# (hand_shape, length_pref) -> score. Currently only `average` hand_shape
# is produced by Step 4.2's mock analyzer; extend the table when real
# hand-shape detection lands.
_SHAPE_LENGTH_SCORE: dict[tuple[str, str], float] = {
    ("average", "short"): 0.80,
    ("average", "medium"): 0.90,
    ("average", "long"): 0.70,
}
_DEFAULT_SHAPE_SCORE = 0.6


def match_skin(skin_tone: str, color_tone: str) -> float:
    return _SKIN_COLOR_SCORE.get((skin_tone, color_tone), _DEFAULT_SKIN_SCORE)


def match_shape(hand_shape: str, length_pref: str) -> float:
    return _SHAPE_LENGTH_SCORE.get((hand_shape, length_pref), _DEFAULT_SHAPE_SCORE)


# ---------- Heat (recent 7-day tryon sum) ----------

async def _recent_7d_tryon_counts(
    db: AsyncSession, style_ids: list[str]
) -> dict[str, int]:
    """Sum tryon_count over the last 7 Beijing days per style_id (batched)."""
    if not style_ids:
        return {}
    today_bjt = datetime.now(_BJT).date()
    window_start = today_bjt - timedelta(days=6)
    stmt = (
        select(StyleStats.style_id, sqlf.sum(StyleStats.tryon_count))
        .where(StyleStats.style_id.in_(style_ids))
        .where(StyleStats.stat_date >= window_start)
        .group_by(StyleStats.style_id)
    )
    result = await db.execute(stmt)
    return {sid: int(total or 0) for sid, total in result.all()}


# ---------- Diversity rerank ----------

def _first_tag(item: dict) -> str:
    tags = item.get("style_tags") or []
    return tags[0] if tags else "_"


def _diversity_rerank(
    scored: list[dict], top_k: int = 9, min_categories: int = 3
) -> list[dict]:
    """Ensure the top-k window covers at least `min_categories` distinct first-tags.

    Greedy: take top_k by score. If categories < min_categories, walk the
    remaining list; for each "new-category" candidate, swap out the
    lowest-ranked selected item whose category is duplicated. Repeat until
    the threshold is met or no improvement is possible.
    """
    if len(scored) <= top_k:
        return list(scored)

    selected = list(scored[:top_k])
    seen_cats = {_first_tag(s) for s in selected}
    if len(seen_cats) >= min_categories:
        return selected

    remaining = scored[top_k:]
    for candidate in remaining:
        cat = _first_tag(candidate)
        if cat in seen_cats:
            continue
        cat_counts: dict[str, int] = {}
        for s in selected:
            c = _first_tag(s)
            cat_counts[c] = cat_counts.get(c, 0) + 1
        for i in range(len(selected) - 1, -1, -1):
            c = _first_tag(selected[i])
            if cat_counts[c] > 1:
                # category c had >=2 occurrences in selected; swapping one
                # out still leaves it represented, so seen_cats unchanged
                selected[i] = candidate
                seen_cats.add(cat)
                break
        if len(seen_cats) >= min_categories:
            break
    return selected


# ---------- Orchestration ----------

def _row_to_dict(row: Style) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "cover_url": row.cover_url,
        "gender": row.gender,
        "style_tags": json.loads(row.style_tags),
        "color_main": row.color_main,
        "color_tone": row.color_tone,
        "length_pref": row.length_pref,
    }


async def recommend(
    db: AsyncSession,
    gender: str,
    hand_features: dict,
    top_k: int = 9,
) -> list[dict]:
    """Per design-docu §6.3 / plan §4.4.

    Returns up to `top_k` styles ordered by score desc (with diversity
    rerank applied to the top-k window). Each item carries score breakdown
    fields for transparency: `skin_score`, `shape_score`, `heat_score`,
    `final_score`. LLM reasons are NOT added here (Step 4.5 route layer).
    """
    if gender not in {"female", "male"}:
        raise ValueError(f"unknown gender: {gender!r}")

    gender_set = ["female", "both"] if gender == "female" else ["male", "both"]
    stmt = (
        select(Style)
        .where(Style.is_active == 1)
        .where(Style.gender.in_(gender_set))
    )
    candidates = (await db.execute(stmt)).scalars().all()
    if not candidates:
        return []

    heat_raw = await _recent_7d_tryon_counts(db, [c.id for c in candidates])
    max_heat = max(heat_raw.values()) if heat_raw else 0
    if max_heat <= 0:
        max_heat = 1  # avoid div-by-zero; all rows then score 0 on heat dim

    skin_tone = hand_features.get("skin_tone", "medium")
    hand_shape = hand_features.get("hand_shape", "average")

    scored: list[dict] = []
    for c in candidates:
        skin_s = match_skin(skin_tone, c.color_tone)
        shape_s = match_shape(hand_shape, c.length_pref)
        heat_s = heat_raw.get(c.id, 0) / max_heat
        # 15% diversity is materialized in rerank, scoring contribution = 0.
        final = 0.35 * skin_s + 0.30 * shape_s + 0.20 * heat_s
        item = _row_to_dict(c)
        item.update(
            skin_score=round(skin_s, 3),
            shape_score=round(shape_s, 3),
            heat_score=round(heat_s, 3),
            final_score=round(final, 4),
        )
        scored.append(item)

    # tie-break by id ASC for stable ordering (mirrors Step 4.3 rationale)
    scored.sort(key=lambda x: (-x["final_score"], x["id"]))

    return _diversity_rerank(scored, top_k=top_k, min_categories=3)
