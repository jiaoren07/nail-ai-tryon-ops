"""Step 5.8 verification for GET /api/tryon/:id + POST /api/events/collect.

Sequence:
  0. Upload a hand to get photo_id
  1. POST /api/tryon to create a fresh tryon row (style=f_02)
  2. GET /api/tryon/:id → 200, payload has result_url + original_url + style.*
  3. Read style_stats.collect_count for (f_02, today_bjt) — snapshot BEFORE
  4. POST /api/events/collect {tryon_id} → 200, changed=true
  5. Read collect_count AFTER → +1
  6. SELECT is_collected FROM tryons WHERE id=:tid → 1
  7. POST /api/events/collect {tryon_id} again → 200, changed=false (idempotent)
  8. Read collect_count → unchanged from step 5
  9. POST /api/events/collect {tryon_id: 999999} → 404 tryon_not_found
 10. GET /api/tryon/999999 → 404 tryon_not_found
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"
STYLE_ID = "f_02"
SAMPLE_HAND = BACKEND_ROOT / "static" / "samples" / "01.png"
_BJT = timezone(timedelta(hours=8))


def _today_bjt():
    return datetime.now(_BJT).date()


def _collect_count_for(style_id: str) -> int:
    import asyncio
    from sqlalchemy import select
    from app.db import async_session_maker
    from app.models import StyleStats

    async def go():
        async with async_session_maker() as db:
            v = (await db.execute(
                select(StyleStats.collect_count)
                .where(StyleStats.style_id == style_id)
                .where(StyleStats.stat_date == _today_bjt())
            )).scalar_one_or_none()
            return int(v or 0)

    return asyncio.run(go())


def _is_collected_for(tid: int) -> int:
    import asyncio
    from sqlalchemy import select
    from app.db import async_session_maker
    from app.models import Tryon

    async def go():
        async with async_session_maker() as db:
            v = (await db.execute(
                select(Tryon.is_collected).where(Tryon.id == tid)
            )).scalar_one_or_none()
            return int(v or 0)

    return asyncio.run(go())


def upload() -> str:
    files = {"file": (SAMPLE_HAND.name, SAMPLE_HAND.read_bytes(), "image/png")}
    data = {"user_id": UID}
    r = httpx.post(BASE + "/api/user/upload", files=files, data=data, headers=HEADERS, timeout=10.0)
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(f"upload failed: {body}")
    return body["data"]["photo_id"]


def post_tryon(photo_id: str) -> int:
    body = {"user_id": UID, "style_id": STYLE_ID, "photo_id": photo_id, "from_module": "result"}
    r = httpx.post(BASE + "/api/tryon", json=body, headers=HEADERS, timeout=30.0)
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0:
        raise RuntimeError(f"tryon failed: {j}")
    return j["data"]["tryon_id"]


def main() -> int:
    failures: list[str] = []

    photo_id = upload()
    tid = post_tryon(photo_id)
    print(f"[setup] photo_id={photo_id} tryon_id={tid}")

    # ---- step 2: GET /api/tryon/:id ----
    r = httpx.get(BASE + f"/api/tryon/{tid}", headers=HEADERS, timeout=10.0)
    print(f"[2] GET /api/tryon/{tid} status={r.status_code}")
    body = r.json()
    print(f"    body keys = {list(body.get('data', {}).keys())}")
    if r.status_code != 200 or body.get("code") != 0:
        failures.append(f"GET /api/tryon/{tid} did not return 200/code=0: {body}")
    d = body.get("data", {})
    for k in ("tryon_id", "result_url", "original_url", "style", "is_collected"):
        if k not in d:
            failures.append(f"  missing key {k!r}")
    if d.get("style", {}).get("id") != STYLE_ID:
        failures.append(f"  style.id != {STYLE_ID}, got {d.get('style', {}).get('id')!r}")
    if d.get("is_collected") is not False:
        failures.append(f"  is_collected expected False, got {d.get('is_collected')!r}")
    print(f"    result_url = {d.get('result_url')}")
    print(f"    original_url = {d.get('original_url')}")
    print(f"    style.name = {d.get('style', {}).get('name')}")

    # ---- step 3: collect_count BEFORE ----
    before_cc = _collect_count_for(STYLE_ID)
    print(f"[3] BEFORE: style_stats.collect_count({STYLE_ID}, today) = {before_cc}")

    # ---- step 4: first collect ----
    r = httpx.post(BASE + "/api/events/collect", json={"tryon_id": tid}, headers=HEADERS, timeout=10.0)
    j = r.json()
    print(f"[4] collect 1 status={r.status_code} body={j}")
    if r.status_code != 200 or j.get("code") != 0:
        failures.append(f"first collect did not 200/code=0: {j}")
    if j.get("data", {}).get("changed") is not True:
        failures.append(f"first collect changed != True: {j}")

    # ---- step 5: collect_count AFTER first ----
    after_cc = _collect_count_for(STYLE_ID)
    print(f"[5] AFTER first: collect_count = {after_cc}  (delta = {after_cc - before_cc})")
    if after_cc - before_cc != 1:
        failures.append(f"collect_count delta {after_cc - before_cc}, expected 1")

    # ---- step 6: is_collected = 1 ----
    isc = _is_collected_for(tid)
    print(f"[6] tryons.is_collected = {isc}")
    if isc != 1:
        failures.append(f"is_collected expected 1, got {isc}")

    # ---- step 7: second collect (idempotent) ----
    r = httpx.post(BASE + "/api/events/collect", json={"tryon_id": tid}, headers=HEADERS, timeout=10.0)
    j = r.json()
    print(f"[7] collect 2 status={r.status_code} body={j}")
    if r.status_code != 200 or j.get("code") != 0:
        failures.append(f"second collect did not 200/code=0: {j}")
    if j.get("data", {}).get("changed") is not False:
        failures.append(f"second collect changed != False: {j}")

    # ---- step 8: collect_count unchanged ----
    after2_cc = _collect_count_for(STYLE_ID)
    print(f"[8] AFTER second: collect_count = {after2_cc}  (should equal {after_cc})")
    if after2_cc != after_cc:
        failures.append(f"second collect bumped count from {after_cc} to {after2_cc}")

    # ---- step 9: collect non-existent ----
    r = httpx.post(BASE + "/api/events/collect", json={"tryon_id": 999999}, headers=HEADERS, timeout=10.0)
    print(f"[9] collect 999999 status={r.status_code} body={r.json()}")
    if r.status_code != 404 or r.json().get("msg") != "tryon_not_found":
        failures.append(f"collect 999999 expected 404/tryon_not_found: {r.status_code}/{r.json()}")

    # ---- step 10: GET non-existent tryon ----
    r = httpx.get(BASE + "/api/tryon/999999", headers=HEADERS, timeout=10.0)
    print(f"[10] GET /api/tryon/999999 status={r.status_code} body={r.json()}")
    if r.status_code != 404 or r.json().get("msg") != "tryon_not_found":
        failures.append(f"GET 999999 expected 404/tryon_not_found: {r.status_code}/{r.json()}")

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
