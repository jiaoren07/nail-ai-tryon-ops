"""Step 6.2 verification for GET /api/ops/trending.

Plan §6.2 checks:
  1. All 3 emerging_hot styles from Step 1.4 (f_09, f_15, m_15) appear
     in /api/ops/trending result
  2. No stable_hot / cold / long_tail style is falsely flagged

Extras: shape sanity, trend_7d length == 7, suggested_action non-empty.
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

    r = httpx.get(BASE + "/api/ops/trending", headers=HEADERS, timeout=10.0)
    print(f"[GET /api/ops/trending] status={r.status_code}")
    if r.status_code != 200:
        failures.append(f"non-200: {r.text[:300]}")
        print("FAILURES:", failures); return 1

    body = r.json()
    if body.get("code") != 0:
        failures.append(f"envelope code != 0: {body}")
        print("FAILURES:", failures); return 1

    items = body["data"]["items"]
    print(f"trending items: {len(items)}")
    for it in items:
        print(f"  {it['style_id']:6s}  name={it['name']:20s}  "
              f"growth={it['growth_rate']}  collect={it['collect_rate']:.2%}  "
              f"24h={it['last_24h_tryons']}  trend_7d={it['trend_7d']}  "
              f"action={it['suggested_action']}")

    returned_ids = {it["style_id"] for it in items}

    # ---- 1. all emerging_hot present ----
    roles = _load_roles()
    emerging = set(roles["female"]["emerging_hot"]) | set(roles["male"]["emerging_hot"])
    print(f"\nexpected emerging_hot (from style_roles.json): {sorted(emerging)}")
    missing = emerging - returned_ids
    if missing:
        failures.append(f"emerging_hot missing from trending: {sorted(missing)}")

    # ---- 2. no false positives from other roles ----
    stable = set(roles["female"]["stable_hot"]) | set(roles["male"]["stable_hot"])
    cold = set(roles["female"]["cold"]) | set(roles["male"]["cold"])
    long_tail = set(roles["female"]["long_tail"]) | set(roles["male"]["long_tail"])
    for label, role_set in [("stable_hot", stable), ("cold", cold), ("long_tail", long_tail)]:
        bad = role_set & returned_ids
        if bad:
            failures.append(f"{label} falsely flagged as trending: {sorted(bad)}")
        else:
            print(f"  no {label} false positives ({len(role_set)} styles checked)")

    # ---- shape ----
    for it in items:
        if len(it["trend_7d"]) != 7:
            failures.append(f"  {it['style_id']} trend_7d length != 7")
        if not it["suggested_action"]:
            failures.append(f"  {it['style_id']} empty suggested_action")
        for k in ("style_id", "name", "cover_url", "growth_rate", "collect_rate",
                  "detected_at", "suggested_action", "last_24h_tryons"):
            if k not in it:
                failures.append(f"  {it['style_id']} missing key {k}")

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
