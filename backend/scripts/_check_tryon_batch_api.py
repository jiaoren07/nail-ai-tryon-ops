"""Step 4.7 verification for POST /api/tryon/batch.

  T1: 3 valid style_ids -> 3 ok, 3 distinct result_urls, tryons +=3
  T2: 2 valid + 1 ghost -> 2 ok + 1 failed, tryons += 2 (only ok writes)
  T3: 5 ids -> 400 style_ids_count_invalid
  T4: 1 id -> 400 style_ids_count_invalid (lower bound)
  T5: order of items in response matches order of input style_ids
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
SAMPLE_HAND = BACKEND_ROOT / "static" / "samples" / "01.png"


def _tryons_total() -> int:
    import asyncio
    from sqlalchemy import func, select
    from app.db import async_session_maker
    from app.models import Tryon

    async def _go():
        async with async_session_maker() as db:
            return (await db.execute(select(func.count()).select_from(Tryon))).scalar_one()

    return asyncio.run(_go())


def upload_photo() -> str:
    files = {"file": (SAMPLE_HAND.name, SAMPLE_HAND.read_bytes(), "image/png")}
    data = {"user_id": UID}
    r = httpx.post(BASE + "/api/user/upload", files=files, data=data, headers=HEADERS, timeout=10.0)
    r.raise_for_status()
    return r.json()["data"]["photo_id"]


def post_batch(style_ids: list[str], photo_id: str, *, expect_status: int = 200) -> dict:
    body = {"user_id": UID, "photo_id": photo_id, "style_ids": style_ids}
    r = httpx.post(BASE + "/api/tryon/batch", json=body, headers=HEADERS, timeout=30.0)
    if expect_status != r.status_code:
        print(f"  WARN status={r.status_code} expected={expect_status} body={r.json()}")
    return {"status_code": r.status_code, "body": r.json()}


def main() -> int:
    failures: list[str] = []
    photo_id = upload_photo()
    print(f"[setup] photo_id={photo_id}")

    # T1: 3 valid
    before = _tryons_total()
    sids_t1 = ["f_01", "f_05", "f_10"]
    res = post_batch(sids_t1, photo_id)
    items = res["body"]["data"]["items"]
    print(f"\n[T1] 3 valid -> {[(i['style_id'], i['status']) for i in items]}")
    for it in items:
        print(f"  {it['style_id']}: status={it['status']} result_url={it.get('result_url')} elapsed={it.get('elapsed_ms')}")
    after = _tryons_total()
    if [i["status"] for i in items] != ["ok", "ok", "ok"]:
        failures.append(f"T1: expected 3 ok, got {[i['status'] for i in items]}")
    distinct = {i["result_url"] for i in items if i["status"] == "ok"}
    if len(distinct) != 3:
        failures.append(f"T1: result_urls not distinct: {distinct}")
    if after - before != 3:
        failures.append(f"T1: tryons delta {after - before}, expected 3")
    if [i["style_id"] for i in items] != sids_t1:
        failures.append(f"T1: order not preserved {[i['style_id'] for i in items]}")

    # T2: 2 valid + 1 ghost
    before = _tryons_total()
    sids_t2 = ["f_02", "ghost_999", "m_01"]
    res = post_batch(sids_t2, photo_id)
    items = res["body"]["data"]["items"]
    print(f"\n[T2] 2 valid + 1 ghost -> {[(i['style_id'], i['status'], i.get('error')) for i in items]}")
    after = _tryons_total()
    statuses = [i["status"] for i in items]
    if statuses != ["ok", "failed", "ok"]:
        failures.append(f"T2: expected [ok, failed, ok], got {statuses}")
    if items[1].get("error") != "style_not_found":
        failures.append(f"T2: ghost error msg = {items[1].get('error')}")
    if after - before != 2:
        failures.append(f"T2: tryons delta {after - before}, expected 2 (only ok writes)")

    # T3: 5 ids -> 400
    res = post_batch(["f_01", "f_02", "f_03", "f_04", "f_05"], photo_id, expect_status=400)
    print(f"\n[T3] 5 ids -> status={res['status_code']} body={res['body']}")
    if res["status_code"] != 400 or res["body"].get("msg") != "style_ids_count_invalid":
        failures.append(f"T3: expected 400/style_ids_count_invalid, got {res}")

    # T4: 1 id -> 400
    res = post_batch(["f_01"], photo_id, expect_status=400)
    print(f"\n[T4] 1 id -> status={res['status_code']} body={res['body']}")
    if res["status_code"] != 400 or res["body"].get("msg") != "style_ids_count_invalid":
        failures.append(f"T4: expected 400/style_ids_count_invalid, got {res}")

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
