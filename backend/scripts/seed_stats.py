"""Seed script: aggregate tryons into style_stats per (style_id, stat_date).

For each (style_id, stat_date) bucket in tryons:
- tryon_count   = COUNT(*)
- collect_count = SUM(is_collected = 1)
- exposure_count = tryon_count × random.uniform(8, 20)
- click_count    = max(tryon_count, exposure_count × random.uniform(0.05, 0.25))

stat_date is the **local Beijing** date (uses SQLite `date(created_at, 'localtime')`),
matching design-docu §4 时区约定 and Step 1.4's storage layout (created_at = UTC).

Idempotent: DELETE FROM style_stats then INSERT.

Run from anywhere:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_stats.py
"""
from __future__ import annotations

import asyncio
import random
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import StyleStats  # noqa: E402


async def seed_stats() -> int:
    # Fixed seed for Step 1.6 strict idempotence on exposure_count/click_count.
    random.seed(42)
    async with AsyncSession(engine) as session:
        await session.execute(delete(StyleStats))

        agg = (await session.execute(text(
            "SELECT style_id, "
            "       date(created_at, 'localtime') AS stat_date, "
            "       COUNT(*) AS tryon_count, "
            "       SUM(CASE WHEN is_collected = 1 THEN 1 ELSE 0 END) AS collect_count "
            "FROM tryons "
            "GROUP BY style_id, date(created_at, 'localtime')"
        ))).all()

        rows: list[StyleStats] = []
        for r in agg:
            tryon_count = int(r.tryon_count)
            collect_count = int(r.collect_count or 0)
            exposure_count = int(tryon_count * random.uniform(8, 20))
            click_count = max(
                tryon_count,
                int(exposure_count * random.uniform(0.05, 0.25)),
            )
            rows.append(StyleStats(
                style_id=r.style_id,
                stat_date=date.fromisoformat(r.stat_date),
                tryon_count=tryon_count,
                collect_count=collect_count,
                exposure_count=exposure_count,
                click_count=click_count,
            ))

        session.add_all(rows)
        await session.commit()
    return len(rows)


async def apply_heat_scores() -> int:
    """Derive styles.heat_score from seeded cumulative tryon volume.

    Min-max scaled to [25, 95], 1 decimal. Deterministic (tryons are
    seeded with a fixed RNG), and consistent with the numbers shown in
    O3/O6 — replaces the uniform 50.0 placeholder that made the O6 heat
    column look fake and fed the recommender's 20% heat weight no signal.
    """
    async with AsyncSession(engine) as session:
        counts = (await session.execute(text(
            "SELECT style_id, COUNT(*) AS n FROM tryons GROUP BY style_id"
        ))).all()
        by_style = {r.style_id: int(r.n) for r in counts}
        if not by_style:
            return 0
        low, high = min(by_style.values()), max(by_style.values())
        span = (high - low) or 1
        for style_id, n in by_style.items():
            heat = round(25 + (n - low) / span * 70, 1)
            await session.execute(
                text("UPDATE styles SET heat_score = :h WHERE id = :sid"),
                {"h": heat, "sid": style_id},
            )
        # styles with zero seeded tryons (none today, but be safe) -> floor
        await session.execute(text(
            "UPDATE styles SET heat_score = 25.0 "
            "WHERE id NOT IN (SELECT DISTINCT style_id FROM tryons)"
        ))
        await session.commit()
    return len(by_style)


async def _main() -> None:
    n = await seed_stats()
    print(f"style_stats inserted: {n}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
