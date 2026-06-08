"""Unified seed entry: init_db -> seed_styles + static copy -> seed_tryons -> seed_stats.

Prints start/end times + affected row counts per step. Whole pipeline
should finish in under 60 seconds on a typical laptop.

Run from anywhere:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\seed_all.py
"""
from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(HERE))

from app.db import engine, init_db  # noqa: E402
from seed_stats import seed_stats  # noqa: E402
from seed_styles import _copy_static, seed_styles  # noqa: E402
from seed_tryons import seed_tryons  # noqa: E402


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


async def main() -> None:
    overall_start = time.time()
    print(f"[{_ts()}] === seed_all start ===\n")

    # Step 1: init_db
    t0 = time.time()
    print(f"[{_ts()}] step 1/4 init_db()")
    await init_db()
    print(f"[{_ts()}]   done in {time.time() - t0:.2f}s\n")

    # Step 2: seed_styles + static file copy
    t0 = time.time()
    print(f"[{_ts()}] step 2/4 seed_styles() + _copy_static()")
    n_styles = await seed_styles()
    static_counts = _copy_static()
    print(f"[{_ts()}]   done in {time.time() - t0:.2f}s  "
          f"styles={n_styles}  "
          f"static: female={static_counts['female']} male={static_counts['male']} samples={static_counts['samples']}\n")

    # Step 3: seed_tryons
    t0 = time.time()
    print(f"[{_ts()}] step 3/4 seed_tryons()")
    n_tryons = await seed_tryons()
    print(f"[{_ts()}]   done in {time.time() - t0:.2f}s  tryons={n_tryons}\n")

    # Step 4: seed_stats
    t0 = time.time()
    print(f"[{_ts()}] step 4/4 seed_stats()")
    n_stats = await seed_stats()
    print(f"[{_ts()}]   done in {time.time() - t0:.2f}s  stats={n_stats}\n")

    elapsed = time.time() - overall_start
    print(f"[{_ts()}] === seed_all done in {elapsed:.2f}s ===")
    print(f"FINAL: styles={n_styles} tryons={n_tryons} stats={n_stats}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
