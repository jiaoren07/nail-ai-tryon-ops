"""Step 6.3 verification for GET /api/ops/cold.

Plan checks:
  1. All Step 1.4 cold styles (f_05, f_08, f_11, m_10, m_13) appear
  2. No stable_hot style is falsely flagged
Extras: shape sanity, reason/suggestion non-empty, ordering by
recent_7d_tryons asc.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"
ROLES_PATH = HERE / "style_roles.json"


def _load_roles():
    with ROLES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    failures: list[str] = []

    r = httpx.get(BASE + "/api/ops/cold", headers=HEADERS, timeout=10.0)
    print(f"[GET /api/ops/cold] status={r.status_code}")
    if r.status_code != 200:
        failures.append(f"non-200: {r.text[:300]}")
        print("FAILURES:", failures); return 1

    body = r.json()
    if body.get("code") != 0:
        failures.append(f"envelope code != 0: {body}")
        print("FAILURES:", failures); return 1

    items = body["data"]["items"]
    print(f"cold items: {len(items)}")
    for it in items:
        print(f"  {it['style_id']:6s}  7d={it['recent_7d_tryons']:3d}  "
              f"cum={it['cumulative_tryons']:4d}  days={it['days_since_listed']:3d}  "
              f"ratio={it['exposure_click_ratio']:.2%}  "
              f"reason={it['cold_reason']}")

    returned_ids = {it["style_id"] for it in items}
    roles = _load_roles()

    # ---- 1. all cold present ----
    cold = set(roles["female"]["cold"]) | set(roles["male"]["cold"])
    print(f"\nexpected cold (from style_roles.json): {sorted(cold)}")
    missing = cold - returned_ids
    if missing:
        failures.append(f"cold missing from /api/ops/cold: {sorted(missing)}")

    # ---- 2. no stable_hot false positives ----
    stable = set(roles["female"]["stable_hot"]) | set(roles["male"]["stable_hot"])
    bad_stable = stable & returned_ids
    if bad_stable:
        failures.append(f"stable_hot falsely flagged as cold: {sorted(bad_stable)}")
    else:
        print(f"no stable_hot false positives ({len(stable)} styles checked)")

    # ---- extras ----
    for it in items:
        if not it["cold_reason"] or not it["suggestion"]:
            failures.append(f"  {it['style_id']} empty reason/suggestion")
        for k in ("style_id", "name", "cover_url", "recent_7d_tryons",
                  "exposure_click_ratio", "days_since_listed",
                  "cold_reason", "suggestion", "cumulative_tryons"):
            if k not in it:
                failures.append(f"  {it['style_id']} missing key {k}")

    # ---- ordering: coldest first (recent_7d ascending) ----
    for i in range(len(items) - 1):
        if items[i]["recent_7d_tryons"] > items[i + 1]["recent_7d_tryons"]:
            failures.append(f"  ordering broken at index {i}")
            break

    # ---- long_tail may appear (plan doesn't forbid) — informational only ----
    long_tail = set(roles["female"]["long_tail"]) | set(roles["male"]["long_tail"])
    lt_flagged = long_tail & returned_ids
    print(f"\nlong_tail also flagged (not a failure): {len(lt_flagged)} / {len(long_tail)}")

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
