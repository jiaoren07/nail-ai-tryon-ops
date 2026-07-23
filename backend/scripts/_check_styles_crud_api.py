"""Step 6.5 verification for GET/PATCH /api/ops/styles.

Checks:
  1. ops GET returns all 40 styles and keeps an inactive row
  2. PATCH is_active=false removes that style from the C-side GET
  3. PATCH display_order writes both the style value and a reorder audit
  4. repeating the same PATCH is idempotent and writes no audit
  5. unknown style id returns 404 style_not_found
  6. empty body returns 400 no_fields_to_update

Run scripts/seed_all.py immediately before this script so the mutation
fixtures start from their known active/order values.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
from sqlalchemy import func, select

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.db import async_session_maker  # noqa: E402
from app.models import OpsAction, Style  # noqa: E402

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"


async def _read_style_state(style_id: str) -> tuple[int, int] | None:
    async with async_session_maker() as db:
        row = (await db.execute(
            select(Style.is_active, Style.display_order).where(Style.id == style_id)
        )).one_or_none()
        return (int(row[0]), int(row[1])) if row is not None else None


async def _count_actions(style_id: str, action_type: str) -> int:
    async with async_session_maker() as db:
        return int((await db.execute(
            select(func.count()).select_from(OpsAction)
            .where(OpsAction.style_id == style_id)
            .where(OpsAction.action_type == action_type)
        )).scalar_one())


def _style_state(style_id: str) -> tuple[int, int] | None:
    return asyncio.run(_read_style_state(style_id))


def _action_count(style_id: str, action_type: str) -> int:
    return asyncio.run(_count_actions(style_id, action_type))


def main() -> int:
    failures: list[str] = []

    # ---- T1: full ops list includes an inactive row ----
    print("=== T1: GET all 40 styles, including inactive ===")
    offline_before = _action_count("f_25", "offline")
    r = httpx.patch(
        BASE + "/api/ops/styles/f_25",
        json={"is_active": False, "reason": "verify: inactive row remains manageable"},
        headers=HEADERS,
        timeout=10.0,
    )
    print(f"  setup PATCH status={r.status_code} body={r.json()}")
    if r.status_code != 200 or r.json().get("data", {}).get("changed") is not True:
        failures.append(f"T1 setup PATCH failed: {r.status_code}/{r.json()}")

    f25_state = _style_state("f_25")
    offline_after = _action_count("f_25", "offline")
    print(f"  SQL: f_25 state={f25_state}, offline audits {offline_before}->{offline_after}")
    if f25_state is None or f25_state[0] != 0:
        failures.append(f"T1: SQL did not persist f_25.is_active=0: {f25_state}")
    if offline_after != offline_before + 1:
        failures.append(f"T1: offline audit delta != 1: {offline_before}->{offline_after}")

    r = httpx.get(BASE + "/api/ops/styles", headers=HEADERS, timeout=10.0)
    body = r.json()
    items = body.get("data", {}).get("items", [])
    total = body.get("data", {}).get("total")
    f25 = next((item for item in items if item.get("id") == "f_25"), None)
    ordering = [(item["display_order"], item["id"]) for item in items]
    print(
        f"  GET status={r.status_code}, total={total}, len(items)={len(items)}, "
        f"f_25.is_active={f25.get('is_active') if f25 else None}"
    )
    if r.status_code != 200 or body.get("code") != 0:
        failures.append(f"T1 GET failed: {r.status_code}/{body}")
    if total != 40 or len(items) != 40:
        failures.append(f"T1: expected 40 rows, got total={total}, len={len(items)}")
    if f25 is None or f25.get("is_active") is not False:
        failures.append("T1: inactive f_25 missing or not marked inactive")
    if ordering != sorted(ordering):
        failures.append("T1: items are not ordered by display_order ASC, id ASC")

    # ---- T2: C-side list reflects offline immediately ----
    print("\n=== T2: PATCH offline changes C-side GET ===")
    r = httpx.get(BASE + "/api/styles?size=100", headers=HEADERS, timeout=10.0)
    c_items = r.json().get("data", {}).get("items", [])
    c_ids = {item["id"] for item in c_items}
    print(f"  C-side rows={len(c_items)}, f_25 present? {'f_25' in c_ids}")
    if r.status_code != 200 or "f_25" in c_ids:
        failures.append(f"T2: C-side still returns f_25: {r.status_code}/{r.json()}")

    # ---- T3: display_order mutation + reorder audit ----
    print("\n=== T3: PATCH display_order writes reorder audit ===")
    state_before = _style_state("f_24")
    if state_before is None:
        failures.append("T3 precondition: f_24 missing")
        new_order = 999
    else:
        new_order = state_before[1] + 100
    reorder_before = _action_count("f_24", "reorder")
    r = httpx.patch(
        BASE + "/api/ops/styles/f_24",
        json={"display_order": new_order, "reason": "verify: manual reorder"},
        headers=HEADERS,
        timeout=10.0,
    )
    print(f"  status={r.status_code} body={r.json()}")
    state_after = _style_state("f_24")
    reorder_after = _action_count("f_24", "reorder")
    print(f"  SQL: f_24 state={state_after}, reorder audits {reorder_before}->{reorder_after}")
    if r.status_code != 200 or r.json().get("data", {}).get("changed") is not True:
        failures.append(f"T3 PATCH failed: {r.status_code}/{r.json()}")
    if state_after is None or state_after[1] != new_order:
        failures.append(f"T3: SQL display_order != {new_order}: {state_after}")
    if reorder_after != reorder_before + 1:
        failures.append(f"T3: reorder audit delta != 1: {reorder_before}->{reorder_after}")

    # ---- T4: idempotent repeat ----
    print("\n=== T4: unchanged PATCH is idempotent ===")
    r = httpx.patch(
        BASE + "/api/ops/styles/f_24",
        json={"display_order": new_order, "reason": "verify: repeated reorder"},
        headers=HEADERS,
        timeout=10.0,
    )
    repeated_state = _style_state("f_24")
    repeated_count = _action_count("f_24", "reorder")
    print(f"  status={r.status_code} body={r.json()}")
    print(f"  SQL: f_24 state={repeated_state}, reorder audits={repeated_count}")
    if r.status_code != 200 or r.json().get("data", {}).get("changed") is not False:
        failures.append(f"T4 expected changed=false: {r.status_code}/{r.json()}")
    if repeated_state != state_after:
        failures.append(f"T4: SQL state changed: {state_after}->{repeated_state}")
    if repeated_count != reorder_after:
        failures.append(f"T4: unchanged PATCH wrote an audit: {reorder_after}->{repeated_count}")

    # ---- T5: unknown id ----
    print("\n=== T5: unknown style id ===")
    r = httpx.patch(
        BASE + "/api/ops/styles/ghost_999",
        json={"is_active": False},
        headers=HEADERS,
        timeout=10.0,
    )
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 404 or r.json().get("msg") != "style_not_found":
        failures.append(f"T5 expected 404/style_not_found: {r.status_code}/{r.json()}")

    # ---- T6: empty body ----
    print("\n=== T6: empty body ===")
    r = httpx.patch(
        BASE + "/api/ops/styles/f_01",
        json={},
        headers=HEADERS,
        timeout=10.0,
    )
    print(f"  status={r.status_code} body={r.json()}")
    if r.status_code != 400 or r.json().get("msg") != "no_fields_to_update":
        failures.append(f"T6 expected 400/no_fields_to_update: {r.status_code}/{r.json()}")

    print()
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
