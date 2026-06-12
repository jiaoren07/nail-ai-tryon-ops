"""Step 4.4 unit test for app.services.recommend.

5 fake users (3 female × 2 male) × the 40-style seeded DB. Asserts:
  - returns 9 items per call
  - top-9 covers at least 3 distinct first-tag categories (diversity)
  - for `dark_cool` male users, top-3 leans cool > warm (only male pool
    has cool styles per CLAUDE.md "Female 25 has 0 cool-tone styles")

Run:
    backend\\.venv\\Scripts\\python.exe backend\\tests\\test_recommend.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db import engine  # noqa: E402
from app.services.recommend import recommend  # noqa: E402

USERS = [
    ("F1 light_warm", "female", {"skin_tone": "light_warm", "hand_shape": "average"}),
    ("F2 dark_cool",  "female", {"skin_tone": "dark_cool",  "hand_shape": "average"}),
    ("F3 medium",     "female", {"skin_tone": "medium",     "hand_shape": "average"}),
    ("M1 light_warm", "male",   {"skin_tone": "light_warm", "hand_shape": "average"}),
    ("M2 dark_cool",  "male",   {"skin_tone": "dark_cool",  "hand_shape": "average"}),
]


async def main() -> int:
    failures: list[str] = []
    async with AsyncSession(engine) as db:
        for label, gender, feats in USERS:
            res = await recommend(db, gender, feats, top_k=9)
            print(f"\n== {label} ({gender}, {feats['skin_tone']}) → {len(res)} items ==")
            for i, r in enumerate(res):
                print(
                    f"  #{i+1} {r['id']:6s} {r['color_tone']:8s} {r['length_pref']:6s} "
                    f"score={r['final_score']:.3f} (skin={r['skin_score']:.2f} "
                    f"shape={r['shape_score']:.2f} heat={r['heat_score']:.2f}) "
                    f"tag0={r['style_tags'][0] if r['style_tags'] else '_'}"
                )

            if len(res) != 9:
                failures.append(f"{label}: expected 9, got {len(res)}")

            first_tags = {r["style_tags"][0] for r in res if r["style_tags"]}
            if len(first_tags) < 3:
                failures.append(
                    f"{label}: only {len(first_tags)} distinct first-tag categories "
                    f"(expected ≥3): {sorted(first_tags)}"
                )

            # plan check: dark_cool top-3 leans cool. Female pool has 0 cool
            # styles per CLAUDE.md, so this only applies to male.
            if "dark_cool" in label and gender == "male":
                top3 = res[:3]
                cool = sum(1 for r in top3 if r["color_tone"] == "cool")
                warm = sum(1 for r in top3 if r["color_tone"] == "warm")
                print(f"  [dark_cool male top-3 tone] cool={cool} warm={warm}")
                if cool <= warm:
                    failures.append(
                        f"{label}: top-3 cool={cool} warm={warm} — not cool-leaning"
                    )

            # cross-pollination guard: returned gender matches request set
            allowed = {"female", "both"} if gender == "female" else {"male", "both"}
            bad = [r["id"] for r in res if r["gender"] not in allowed]
            if bad:
                failures.append(f"{label}: returned wrong-gender items: {bad}")

    await engine.dispose()

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
