"""Step 9.3 verification for reports + notifications REST endpoints.

Batch H: email delivery was removed product-wide, so this script covers
the in-app report flow only (generate / list / detail / notifications).

  T1 POST reports/generate {daily}      -> report_id (real LLM, ~10-20s)
  T2 immediate re-generate same type    -> 429 generate_debounced
  T3 unread-count baseline +1 within 5s
  T4 GET reports?type=daily&dates       -> contains T1's id, paged shape
  T5 GET reports/{id}                   -> content_md present, no email fields
  T6 notifications list + mark-one-read -> is_read, unread -1
  T7 read-all -> unread == 0
  T8 404/400 paths: unknown report id, invalid generate type

Run from backend/:  .venv\\Scripts\\python.exe -X utf8 scripts\\_check_reports_api.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def get(path: str, **params):
    return httpx.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=30)


def post(path: str, body: dict | None = None, timeout: int = 120):
    return httpx.post(f"{BASE}{path}", headers=HEADERS, json=body, timeout=timeout)


def main() -> None:
    unread0 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]

    # ---- T1: generate daily (real LLM) ---------------------------------
    t0 = time.time()
    r1 = post("/api/ops/reports/generate", {"type": "daily"})
    took = time.time() - t0
    rid = r1.json().get("data", {}).get("report_id")
    check(
        "T1 generate daily -> report_id",
        r1.status_code == 200 and r1.json()["code"] == 0 and isinstance(rid, int),
        f"id={rid} ({took:.1f}s)",
    )

    # ---- T2: debounce (immediately, inside the 30s window) -------------
    r2 = post("/api/ops/reports/generate", {"type": "daily"}, timeout=15)
    check(
        "T2 re-generate within 30s -> 429 generate_debounced",
        r2.status_code == 429 and r2.json()["msg"] == "generate_debounced",
        f"status={r2.status_code}",
    )

    # ---- T3: notification appeared -------------------------------------
    time.sleep(2)
    unread1 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]
    check("T3 unread-count +1 within 5s", unread1 == unread0 + 1,
          f"{unread0} -> {unread1}")

    # ---- T4: list filters ----------------------------------------------
    r4 = get("/api/ops/reports", type="daily",
             start_date="2026-01-01", end_date="2026-12-31").json()["data"]
    ids = [it["id"] for it in r4["items"]]
    check(
        "T4 list daily by date range contains new id, paged shape",
        rid in ids and {"total", "page", "size", "items"} <= set(r4)
        and all(it["type"] == "daily" for it in r4["items"])
        and all("content_md" not in it for it in r4["items"]),
        f"total={r4['total']} ids[:4]={ids[:4]}",
    )

    # ---- T5: detail — content present, email surface gone --------------
    d = get(f"/api/ops/reports/{rid}").json()["data"]
    check(
        "T5 detail: content_md present, no email fields",
        len(d.get("content_md", "")) > 100
        and "email_status" not in d and "email_error" not in d,
        f"md_len={len(d.get('content_md', ''))}",
    )

    # ---- T6: notifications list + mark one read ------------------------
    items = get("/api/ops/notifications", unread_only=True, limit=10).json()["data"]["items"]
    target = items[0]
    r6 = post(f"/api/ops/notifications/{target['id']}/read", timeout=15)
    unread2 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]
    read_back = next(
        it for it in get("/api/ops/notifications", limit=50).json()["data"]["items"]
        if it["id"] == target["id"]
    )
    check(
        "T6 mark one read: is_read=true, unread -1",
        r6.status_code == 200 and read_back["is_read"] is True
        and unread2 == unread1 - 1,
        f"unread {unread1} -> {unread2}",
    )

    # ---- T7: read-all ---------------------------------------------------
    post("/api/ops/notifications/read-all", timeout=15)
    unread3 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]
    check("T7 read-all -> unread == 0", unread3 == 0, f"unread={unread3}")

    # ---- T8: error paths -----------------------------------------------
    r8a = get("/api/ops/reports/999999")
    r8b = post("/api/ops/reports/generate", {"type": "monthly"}, timeout=15)
    r8c = post("/api/ops/notifications/999999/read", timeout=15)
    check(
        "T8 unknown-id 404 x2, invalid type 400",
        r8a.status_code == 404 and r8b.status_code == 400 and r8c.status_code == 404,
        f"{r8a.status_code}/{r8b.status_code}/{r8c.status_code}",
    )

    failed = [n for n, okk, _ in RESULTS if not okk]
    print()
    if failed:
        print(f"FAILED: {len(failed)}/{len(RESULTS)} -> {failed}")
        sys.exit(1)
    print(f"ALL PASS ({len(RESULTS)}/{len(RESULTS)})")


if __name__ == "__main__":
    main()
