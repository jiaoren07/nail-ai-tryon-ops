"""Step 4.6 verification for POST /api/tryon.

Sequence:
  0. Take counts-before snapshot (tryons total, style_stats.tryon_count for today)
  1. POST /api/user/upload to get a fresh photo_id
  2. POST /api/tryon with a known style_id
  3. Verify result_url is fetchable
  4. Verify tryons +1 and style_stats today +1 in the SAME transaction
  5. Negative paths: bad style_id, bad photo_id, user_id mismatch
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
STYLE_ID = "f_01"
SAMPLE_HAND = BACKEND_ROOT / "static" / "samples" / "01.png"
_BJT = timezone(timedelta(hours=8))


def _today_bjt():
    return datetime.now(_BJT).date()


def _db_counts() -> tuple[int, int]:
    """Read tryons total + today's style_stats.tryon_count for STYLE_ID."""
    import asyncio

    from sqlalchemy import func, select

    from app.db import async_session_maker
    from app.models import StyleStats, Tryon

    async def _go():
        async with async_session_maker() as db:
            n_tryons = (await db.execute(
                select(func.count()).select_from(Tryon).where(Tryon.style_id == STYLE_ID)
            )).scalar_one()
            today_count = (await db.execute(
                select(StyleStats.tryon_count)
                .where(StyleStats.style_id == STYLE_ID)
                .where(StyleStats.stat_date == _today_bjt())
            )).scalar_one_or_none() or 0
            return n_tryons, today_count

    return asyncio.run(_go())


def upload_photo() -> str:
    files = {"file": (SAMPLE_HAND.name, SAMPLE_HAND.read_bytes(), "image/png")}
    data = {"user_id": UID}
    r = httpx.post(BASE + "/api/user/upload", files=files, data=data, headers=HEADERS, timeout=10.0)
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(f"upload failed: {body}")
    return body["data"]["photo_id"]


def main() -> int:
    failures: list[str] = []

    # ---- step 0: counts BEFORE ----
    n_tryons_before, today_count_before = _db_counts()
    print(f"[0] BEFORE  tryons({STYLE_ID})={n_tryons_before}  today_stats={today_count_before}")

    # ---- step 1: upload sample hand ----
    photo_id = upload_photo()
    print(f"[1] uploaded photo_id={photo_id}")

    # ---- step 2: post tryon ----
    body = {"user_id": UID, "style_id": STYLE_ID, "photo_id": photo_id, "from_module": "browse"}
    r2 = httpx.post(BASE + "/api/tryon", json=body, headers=HEADERS, timeout=30.0)
    r2.raise_for_status()
    body2 = r2.json()
    assert body2.get("code") == 0, body2
    d = body2["data"]
    print(f"[2] tryon ok  tryon_id={d['tryon_id']}  result_url={d['result_url']}  elapsed_ms={d['elapsed_ms']}")
    if not d.get("result_url", "").startswith("/static/cache/"):
        failures.append(f"result_url does not start with /static/cache/: {d.get('result_url')}")

    # ---- step 3: fetch result_url ----
    r3 = httpx.get(BASE + d["result_url"], headers=HEADERS, timeout=10.0)
    print(f"[3] GET {d['result_url']}  status={r3.status_code}  bytes={len(r3.content)}")
    if r3.status_code != 200 or len(r3.content) < 1000:
        failures.append(f"result_url not fetchable / empty: status={r3.status_code} bytes={len(r3.content)}")

    # ---- step 4: counts AFTER ----
    n_tryons_after, today_count_after = _db_counts()
    print(f"[4] AFTER   tryons({STYLE_ID})={n_tryons_after}  today_stats={today_count_after}")
    if n_tryons_after != n_tryons_before + 1:
        failures.append(f"tryons not +1 (before={n_tryons_before}, after={n_tryons_after})")
    if today_count_after != today_count_before + 1:
        failures.append(f"today style_stats not +1 (before={today_count_before}, after={today_count_after})")

    # ---- step 5: negative paths ----
    r5a = httpx.post(BASE + "/api/tryon",
        json={"user_id": UID, "style_id": "ghost_999", "photo_id": photo_id},
        headers=HEADERS, timeout=10.0)
    print(f"[5a] bad style → status={r5a.status_code} body={r5a.json()}")
    if r5a.status_code != 404 or r5a.json().get("msg") != "style_not_found":
        failures.append(f"bad style_id did not 404/style_not_found: {r5a.status_code}/{r5a.json()}")

    r5b = httpx.post(BASE + "/api/tryon",
        json={"user_id": UID, "style_id": STYLE_ID, "photo_id": "no_such_photo.png"},
        headers=HEADERS, timeout=10.0)
    print(f"[5b] bad photo → status={r5b.status_code} body={r5b.json()}")
    if r5b.status_code != 404 or r5b.json().get("msg") != "photo_not_found":
        failures.append(f"bad photo_id did not 404/photo_not_found: {r5b.status_code}/{r5b.json()}")

    r5c = httpx.post(BASE + "/api/tryon",
        json={"user_id": "11111111-1111-1111-1111-111111111111", "style_id": STYLE_ID, "photo_id": photo_id},
        headers=HEADERS, timeout=10.0)
    print(f"[5c] uid mismatch → status={r5c.status_code} body={r5c.json()}")
    if r5c.status_code != 400 or r5c.json().get("msg") != "user_id_mismatch":
        failures.append(f"uid mismatch did not 400/user_id_mismatch: {r5c.status_code}/{r5c.json()}")

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
