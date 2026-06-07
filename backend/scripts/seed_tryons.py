"""Seed script: 60 days of synthetic tryon events driven by style_roles.json.

Coverage: [today_local - 59 days, today_local], 60 days inclusive.
Each event's created_at is stored as naive-UTC datetime; SQL queries should
use `date(created_at, 'localtime')` to bucket by Beijing date.

Rule interpretation (implementation-plan §1.4) — mixed by bucket, each
to satisfy both the total-count window [4000, 18000] and the per-style
verifications:
- stable_hot "每日 80-150 次": bucket-global daily quota (5 stable_hot
  styles across both pools share one 80-150 quota). Per-style would
  blow past the 18000 total cap.
- long_tail "每日 5-40 次": bucket-global daily quota (27 long_tail
  styles share). Same reason.
- emerging_hot "前 55 天每日 10-30 次": per-STYLE daily count, so the
  per-style 5× peak ratio (verification line 3) holds reliably without
  bucket-share dilution. Spike base widened to [30, 40] so even the
  lowest spike-day count beats pre-55 avg by ≥ 5×.
- cold "60 天合计 ≤ 20": per-style total cap (matches verification:
  "对 cold 中任一款 SELECT COUNT(*) 应 ≤ 20").
- user_gender always derived from style.gender (never global 70/30
  sampling, per spec warning).

Idempotent: DELETE FROM tryons then INSERT.

Run from anywhere:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_tryons.py
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
import uuid
from datetime import date as date_t, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Style, Tryon  # noqa: E402

ROLES_FILE = HERE / "style_roles.json"
BJ = timezone(timedelta(hours=8))

SKIN_TONES = ["light_warm", "light_cool", "medium", "dark_warm", "dark_cool"]
HAND_SHAPES = ["slim_long", "short_round", "average"]
FROM_MODULES_BAG = ["recommend"] * 50 + ["browse"] * 30 + ["compare"] * 20
COLLECT_PROB_BY_ROLE = {
    "stable_hot": 0.25,
    "emerging_hot": 0.30,
    "cold": 0.05,
    "long_tail": 0.12,
}


def _daily_bucket_count(role: str, day_offset: int) -> int:
    """Bucket-global daily quota for stable_hot / long_tail."""
    if role == "stable_hot":
        c = int(random.gauss(115, 15))
        return max(80, min(150, c))
    if role == "long_tail":
        return random.randint(5, 40)
    raise ValueError(f"_daily_bucket_count called with non-bucket role: {role}")


def _daily_per_style_emerging_count(day_offset: int) -> int:
    """Per-style daily count for emerging_hot. day_offset: 0 = today, 59 = oldest."""
    if day_offset <= 4:
        mults = [3.5, 3.0, 2.5, 2.0, 1.5]  # offset 0 = today = 3.5x peak
        base = random.randint(30, 40)  # > pre-spike upper bound so peak/avg >= 5x reliably
        return int(base * mults[day_offset])
    return random.randint(10, 30)


def _resolve_user_gender(style_gender: str) -> str:
    if style_gender == "both":
        return random.choice(["female", "male"])
    return style_gender


def _random_utc_in_local_day(local_d: date_t) -> datetime:
    """Pick a random datetime within [08:00, 23:59] local Beijing on local_d, return naive UTC."""
    hour = random.randint(8, 23)
    minute = random.randint(0, 59)
    sec = random.randint(0, 59)
    local_dt = datetime(local_d.year, local_d.month, local_d.day, hour, minute, sec, tzinfo=BJ)
    return local_dt.astimezone(timezone.utc).replace(tzinfo=None)


def _make_event(style: Style, when_utc: datetime, role: str) -> Tryon:
    return Tryon(
        user_id=str(uuid.uuid4()),
        user_gender=_resolve_user_gender(style.gender),
        style_id=style.id,
        skin_tone=random.choice(SKIN_TONES),
        hand_shape=random.choice(HAND_SHAPES),
        from_module=random.choice(FROM_MODULES_BAG),
        is_collected=1 if random.random() < COLLECT_PROB_BY_ROLE[role] else 0,
        created_at=when_utc,
    )


def _build_events(styles_by_id: dict[str, Style], roles: dict) -> list[Tryon]:
    today_local = datetime.now(BJ).date()
    events: list[Tryon] = []

    # Bucket-global: merge female + male into one bucket per role
    global_buckets: dict[str, list[Style]] = {
        role: [styles_by_id[sid] for sid in roles["female"][role] + roles["male"][role]]
        for role in ("stable_hot", "emerging_hot", "cold", "long_tail")
    }

    # stable_hot / long_tail: bucket-global daily quota, distributed via random.choice
    for role_name in ("stable_hot", "long_tail"):
        bucket_styles = global_buckets[role_name]
        if not bucket_styles:
            continue
        for day_offset in range(60):
            target_date = today_local - timedelta(days=day_offset)
            count = _daily_bucket_count(role_name, day_offset)
            for _ in range(count):
                style = random.choice(bucket_styles)
                when_utc = _random_utc_in_local_day(target_date)
                events.append(_make_event(style, when_utc, role_name))

    # emerging_hot: per-style daily count (avoids bucket-share dilution of peak)
    for style in global_buckets["emerging_hot"]:
        for day_offset in range(60):
            target_date = today_local - timedelta(days=day_offset)
            count = _daily_per_style_emerging_count(day_offset)
            for _ in range(count):
                when_utc = _random_utc_in_local_day(target_date)
                events.append(_make_event(style, when_utc, "emerging_hot"))

    # cold: per-style cap of randint(10, 20) over 60 days, uniformly distributed
    for style in global_buckets["cold"]:
        total = random.randint(10, 20)
        for _ in range(total):
            day_offset = random.randint(0, 59)
            target_date = today_local - timedelta(days=day_offset)
            when_utc = _random_utc_in_local_day(target_date)
            events.append(_make_event(style, when_utc, "cold"))

    return events


async def seed_tryons() -> int:
    with ROLES_FILE.open(encoding="utf-8") as f:
        roles = json.load(f)
    async with AsyncSession(engine) as session:
        styles = (await session.execute(select(Style))).scalars().all()
        styles_by_id = {s.id: s for s in styles}
        await session.execute(delete(Tryon))
        events = _build_events(styles_by_id, roles)
        session.add_all(events)
        await session.commit()
    return len(events)


async def _main() -> None:
    n = await seed_tryons()
    print(f"tryons inserted: {n}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
