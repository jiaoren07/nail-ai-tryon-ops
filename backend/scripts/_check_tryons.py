"""One-shot verifier for the 5 Step 1.4 checks. Reads nail_demo.db + style_roles.json.

Run from backend/:
    python scripts\\_check_tryons.py
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
DB_PATH = BACKEND_ROOT / "nail_demo.db"
ROLES_PATH = HERE / "style_roles.json"

BJ = timezone(timedelta(hours=8))


def _check(name: str, ok: bool, detail: str) -> bool:
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}: {detail}")
    return ok


def main() -> None:
    c = sqlite3.connect(DB_PATH)
    with ROLES_PATH.open(encoding="utf-8") as f:
        roles = json.load(f)
    today = datetime.now(BJ).date()
    results = []

    print("\n=== 1) total tryons ∈ [4000, 18000] ===")
    total = c.execute("SELECT COUNT(*) FROM tryons").fetchone()[0]
    results.append(_check("total", 4000 <= total <= 18000, f"got {total}"))

    print("\n=== 2) date range = [today-59, today] (Beijing local) ===")
    mn, mx = c.execute(
        "SELECT date(MIN(created_at), 'localtime'), date(MAX(created_at), 'localtime') FROM tryons"
    ).fetchone()
    exp_min = (today - timedelta(days=59)).isoformat()
    exp_max = today.isoformat()
    results.append(_check(
        "date range",
        mn == exp_min and mx == exp_max,
        f"got [{mn}, {mx}], expect [{exp_min}, {exp_max}]",
    ))

    print("\n=== 3) every emerging_hot style: peak day ≥ 5× pre-55 avg ===")
    for sid in roles["female"]["emerging_hot"] + roles["male"]["emerging_hot"]:
        rows = c.execute(
            "SELECT date(created_at, 'localtime') d, COUNT(*) cnt "
            "FROM tryons WHERE style_id = ? GROUP BY d",
            (sid,),
        ).fetchall()
        by_day = {d: cnt for d, cnt in rows}
        pre = [by_day.get((today - timedelta(days=i)).isoformat(), 0) for i in range(5, 60)]
        last5 = [by_day.get((today - timedelta(days=i)).isoformat(), 0) for i in range(0, 5)]
        pre_avg = sum(pre) / len(pre) if pre else 0.0
        peak = max(last5) if last5 else 0
        ratio = (peak / pre_avg) if pre_avg else 0.0
        results.append(_check(
            sid,
            ratio >= 5,
            f"pre_avg={pre_avg:.1f}, peak={peak}, ratio={ratio:.2f}x",
        ))

    print("\n=== 4) every cold style: count ≤ 20 ===")
    for sid in roles["female"]["cold"] + roles["male"]["cold"]:
        n = c.execute("SELECT COUNT(*) FROM tryons WHERE style_id = ?", (sid,)).fetchone()[0]
        results.append(_check(sid, n <= 20, f"count={n}"))

    print("\n=== 5) gender consistency (cross-pollination = 0) ===")
    fm = c.execute(
        "SELECT COUNT(*) FROM tryons t JOIN styles s ON t.style_id = s.id "
        "WHERE s.gender = 'female' AND t.user_gender = 'male'"
    ).fetchone()[0]
    mf = c.execute(
        "SELECT COUNT(*) FROM tryons t JOIN styles s ON t.style_id = s.id "
        "WHERE s.gender = 'male' AND t.user_gender = 'female'"
    ).fetchone()[0]
    results.append(_check(
        "cross-pollination",
        fm == 0 and mf == 0,
        f"female-style x male-user = {fm}, male-style x female-user = {mf}",
    ))

    c.close()
    print()
    if all(results):
        print("ALL 5 CHECKS PASSED.")
    else:
        n_fail = sum(1 for r in results if not r)
        print(f"{n_fail} CHECK(S) FAILED — re-run seed_tryons.py and check again.")


if __name__ == "__main__":
    main()
