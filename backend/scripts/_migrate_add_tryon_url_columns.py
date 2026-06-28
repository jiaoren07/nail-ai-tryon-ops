"""One-shot migration: add result_url + photo_id columns to existing tryons table.

Step 5.8 needs these columns to back the new GET /api/tryon/:id endpoint.
`create_all` doesn't ALTER existing tables so this script does the ALTER manually.

Safe to re-run: PRAGMA table_info() is consulted first to skip columns that
already exist.

Run from anywhere:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\_migrate_add_tryon_url_columns.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import text  # noqa: E402

from app.db import engine  # noqa: E402


async def main() -> int:
    async with engine.begin() as conn:
        cols = await conn.execute(text("PRAGMA table_info(tryons)"))
        existing = {row[1] for row in cols.fetchall()}
        print(f"existing columns: {sorted(existing)}")

        to_add = [
            ("result_url", "TEXT"),
            ("photo_id", "TEXT"),
        ]
        for name, typ in to_add:
            if name in existing:
                print(f"  - {name}: already present, skip")
                continue
            await conn.execute(text(f"ALTER TABLE tryons ADD COLUMN {name} {typ}"))
            print(f"  + {name}: added ({typ})")

        cols2 = await conn.execute(text("PRAGMA table_info(tryons)"))
        new_existing = {row[1] for row in cols2.fetchall()}
        print(f"final columns: {sorted(new_existing)}")

    await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
