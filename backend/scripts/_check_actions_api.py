"""Step 6.4 verification for POST /api/ops/actions.

Plan checks:
  1. boost on f_15 → styles.display_order = min(active display_order)
  2. offline on f_25 → GET /api/styles no longer includes f_25
  3. ops_actions gets a boost row for f_15

Extras:
  - demote on f_10 → display_order = max(active) + 1
  - invalid action_type → 400 invalid_action_type
  - reorder → 501 not_implemented
  - unknown style_id → 404 style_not_found
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"


def _read_style_display_order(style_id: str) -> int | None:
    import asyncio
    from sqlalchemy import select
    from app.db import async_session_maker
    from app.models import Style

    async def go():
        async with async_session_maker() as db:
            v = (await db.execute(
                select(Style.display_order).where(Style.id == style_id)
            )).scalar_one_or_none()
            return v

    return asyncio.run(go())


def _read_min_max_active_display_order() -> tuple[int, int]:
    import asyncio
    from sqlalchemy import func, select
    from app.db import async_session_maker
    from app.models import Style

    async def go():
        async with async_session_maker() as db:
            mn = (await db.execute(
                select(func.min(Style.display_order)).where(Style.is_active == 1)
            )).scalar_one()
            mx = (await db.execute(
                select(func.max(Style.display_order)).where(Style.is_active == 1)
            )).scalar_one()
            return int(mn), int(mx)

    return asyncio.run(go())


def _read_style_is_active(style_id: str) -> int | None:
    import asyncio
    from sqlalchemy import select
    from app.db import async_session_maker
    from app.models import Style

    async def go():
        async with async_session_maker() as db:
            v = (await db.execute(
                select(Style.is_active).where(Style.id == style_id)
            )).scalar_one_or_none()
            return v

    return asyncio.run(go())


def _count_ops_actions(style_id: str, action_type: str) -> int:
    import asyncio
    from sqlalchemy import func, select
    from app.db import async_session_maker
    from app.models import OpsAction

    async def go():
        async with async_session_maker() as db:
            return (await db.execute(
                select(func.count()).select_from(OpsAction)
                .where(OpsAction.style_id == style_id)
                .where(OpsAction.action_type == action_type)
            )).scalar_one()

    return asyncio.run(go())


def main() -> int:
    failures: list[str] = []

    # ---- Test 1: boost f_15 ----
    print("=== T1: boost f_15 ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "f_15", "action_type": "boost", "reason": "verify: identified as trending"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 200 or r.json().get("code") != 0:
        failures.append(f"T1 boost failed: {r.status_code}/{r.json()}")

    # Verify display_order is the minimum among active styles
    f15_order = _read_style_display_order("f_15")
    min_order, _ = _read_min_max_active_display_order()
    print(f"  after boost: f_15.display_order = {f15_order}, current min = {min_order}")
    if f15_order != min_order:
        failures.append(f"T1: f_15.display_order ({f15_order}) != min ({min_order})")

    # Verify ops_actions row appeared
    count = _count_ops_actions("f_15", "boost")
    print(f"  ops_actions count(f_15, boost) = {count}")
    if count < 1:
        failures.append(f"T1: no boost audit row for f_15")

    # ---- Test 2: demote f_10 ----
    print("\n=== T2: demote f_10 ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "f_10", "action_type": "demote"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 200 or r.json().get("code") != 0:
        failures.append(f"T2 demote failed: {r.status_code}/{r.json()}")

    f10_order = _read_style_display_order("f_10")
    _, max_order = _read_min_max_active_display_order()
    print(f"  after demote: f_10.display_order = {f10_order}, current max = {max_order}")
    if f10_order != max_order:
        failures.append(f"T2: f_10.display_order ({f10_order}) != max ({max_order})")

    # ---- Test 3: offline f_25 ----
    print("\n=== T3: offline f_25 ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "f_25", "action_type": "offline", "reason": "verify: cold candidate"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 200 or r.json().get("code") != 0:
        failures.append(f"T3 offline failed: {r.status_code}/{r.json()}")

    f25_active = _read_style_is_active("f_25")
    print(f"  after offline: f_25.is_active = {f25_active}")
    if f25_active != 0:
        failures.append(f"T3: f_25.is_active ({f25_active}) != 0")

    # Verify /api/styles no longer includes f_25
    r = httpx.get(BASE + "/api/styles?size=100", headers=HEADERS, timeout=10.0)
    ids_returned = {it["id"] for it in r.json()["data"]["items"]}
    print(f"  /api/styles returns {len(ids_returned)} styles, f_25 present? {'f_25' in ids_returned}")
    if "f_25" in ids_returned:
        failures.append(f"T3: /api/styles still returns f_25 after offline")

    # ---- Extras: negative paths ----
    print("\n=== T4: invalid action_type ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "f_01", "action_type": "bogus"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 400 or r.json().get("msg") != "invalid_action_type":
        failures.append(f"T4 expected 400/invalid_action_type, got {r.status_code}/{r.json()}")

    print("\n=== T5: reorder (not_implemented) ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "f_01", "action_type": "reorder"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 501 or r.json().get("msg") != "not_implemented":
        failures.append(f"T5 expected 501/not_implemented, got {r.status_code}/{r.json()}")

    print("\n=== T6: unknown style_id ===")
    r = httpx.post(BASE + "/api/ops/actions", json={
        "style_id": "ghost_999", "action_type": "boost"
    }, headers=HEADERS, timeout=10.0)
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 404 or r.json().get("msg") != "style_not_found":
        failures.append(f"T6 expected 404/style_not_found, got {r.status_code}/{r.json()}")

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
