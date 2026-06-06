"""Seed script: import 40 styles into DB + copy cover images + 17 hand samples.

Sources (external dataset, not in repo):
- d:\\美团AI HACKATHON\\dataset\\styles\\tags_qwen.json   (25 female, key=f_NN_enh.png)
- d:\\美团AI HACKATHON\\dataset\\styles\\male\\tags_qwen.json  (15 male, key=m_NN.jpg)
- d:\\美团AI HACKATHON\\dataset\\hands\\01.png ~ 17.png  (17 sample hands)

Idempotent: DELETE FROM styles then INSERT; static files overwritten.

Run from anywhere:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_styles.py
Or from backend/:
    .\\.venv\\Scripts\\python.exe scripts\\seed_styles.py
"""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import engine  # noqa: E402
from app.models import Style  # noqa: E402

DATASET_DIR = Path(r"d:\美团AI HACKATHON\dataset")
FEMALE_DIR = DATASET_DIR / "styles"
MALE_DIR = DATASET_DIR / "styles" / "male"
HANDS_DIR = DATASET_DIR / "hands"

STATIC_STYLES = BACKEND_ROOT / "static" / "styles"
STATIC_SAMPLES = BACKEND_ROOT / "static" / "samples"


def _name_from_tags(tags: list[str]) -> str:
    if not tags:
        return "未命名款式"
    return "".join(tags[:3])


def _build_rows() -> list[Style]:
    now = datetime.now(timezone.utc)
    rows: list[Style] = []

    with (FEMALE_DIR / "tags_qwen.json").open(encoding="utf-8") as f:
        female_data = json.load(f)
    for key in sorted(female_data.keys()):
        sid = key.removesuffix("_enh.png")
        parsed = female_data[key].get("parsed") or {}
        tags = parsed.get("style_tags", [])
        rows.append(Style(
            id=sid,
            name=_name_from_tags(tags),
            gender="female",
            cover_url=f"/static/styles/{sid}_enh.png",
            style_tags=json.dumps(tags, ensure_ascii=False),
            color_main=parsed.get("color_main", "#FFFFFF"),
            color_tone=parsed.get("color_tone", "neutral"),
            length_pref=parsed.get("length_pref", "medium"),
            complexity=int(parsed.get("complexity", 3)),
            heat_score=50.0,
            is_active=1,
            display_order=0,
            created_at=now,
        ))

    with (MALE_DIR / "tags_qwen.json").open(encoding="utf-8") as f:
        male_data = json.load(f)
    for key in sorted(male_data.keys()):
        sid = key.removesuffix(".jpg")
        parsed = male_data[key].get("parsed") or {}
        tags = parsed.get("style_tags", [])
        rows.append(Style(
            id=sid,
            name=_name_from_tags(tags),
            gender=parsed.get("gender", "male"),
            cover_url=f"/static/styles/{sid}.jpg",
            style_tags=json.dumps(tags, ensure_ascii=False),
            color_main=parsed.get("color_main", "#000000"),
            color_tone=parsed.get("color_tone", "neutral"),
            length_pref=parsed.get("length_pref", "medium"),
            complexity=int(parsed.get("complexity", 3)),
            heat_score=50.0,
            is_active=1,
            display_order=0,
            created_at=now,
        ))

    rows.sort(key=lambda r: r.id)
    for idx, r in enumerate(rows):
        r.display_order = idx
    return rows


def _copy_static() -> dict[str, int]:
    counts = {"female": 0, "male": 0, "samples": 0}
    STATIC_STYLES.mkdir(parents=True, exist_ok=True)
    STATIC_SAMPLES.mkdir(parents=True, exist_ok=True)

    for png in sorted(FEMALE_DIR.glob("f_*_enh.png")):
        shutil.copyfile(png, STATIC_STYLES / png.name)
        counts["female"] += 1
    for jpg in sorted(MALE_DIR.glob("m_*.jpg")):
        shutil.copyfile(jpg, STATIC_STYLES / jpg.name)
        counts["male"] += 1
    for png in sorted(HANDS_DIR.glob("[0-9][0-9].png")):
        shutil.copyfile(png, STATIC_SAMPLES / png.name)
        counts["samples"] += 1
    return counts


async def seed_styles() -> int:
    rows = _build_rows()
    async with AsyncSession(engine) as session:
        await session.execute(delete(Style))
        session.add_all(rows)
        await session.commit()
    return len(rows)


async def _main() -> None:
    inserted = await seed_styles()
    counts = _copy_static()
    print(f"styles inserted: {inserted}")
    print(f"static files copied: female={counts['female']} male={counts['male']} samples={counts['samples']}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
