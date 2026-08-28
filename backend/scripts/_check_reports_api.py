"""Step 9.3 verification for reports + notifications REST endpoints.

Server MUST be started with SMTP_HOST overridden to an unresolvable host
(e.g. $env:SMTP_HOST="smtp-disabled.invalid") so email dispatch exercises
the real failed-path with ZERO outbound SMTP traffic. The live "sent"
test is a separate user-approved step.

  T1 POST reports/generate {daily}      -> report_id (real LLM, ~10-20s)
  T2 immediate re-generate same type    -> 429 generate_debounced
  T3 unread-count baseline +1 within 5s
  T4 GET reports?type=daily&dates       -> contains T1's id, paged shape
  T5 GET reports/{id}                   -> content_md present; email_status
                                           settles to failed (invalid host)
  T6 resend on failed -> pending -> failed again; resend on a SENT report
     (from Step 9.1 stub runs) -> 400 resend_only_failed
  T7 notifications list + mark-one-read -> is_read, unread -1
  T8 read-all -> unread == 0
  T9 404/400 paths: unknown report id, invalid generate type

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

    # ---- T5: detail + email failed path (invalid SMTP host) ------------
    status = None
    for _ in range(15):  # DNS failure is fast; allow a few seconds anyway
        d = get(f"/api/ops/reports/{rid}").json()["data"]
        status = d["email_status"]
        if status != "pending":
            break
        time.sleep(1)
    check(
        "T5 detail: content_md present, email_status -> failed (no real send)",
        len(d.get("content_md", "")) > 100 and status == "failed"
        and d.get("email_error"),
        f"status={status} err={str(d.get('email_error'))[:40]}",
    )

    # ---- T6: resend rules ----------------------------------------------
    r6a = post(f"/api/ops/reports/{rid}/resend", timeout=15)
    time.sleep(3)
    d6 = get(f"/api/ops/reports/{rid}").json()["data"]
    sent_list = get("/api/ops/reports").json()["data"]["items"]
    sent_id = next((it["id"] for it in sent_list if it["email_status"] == "sent"), None)
    r6b = post(f"/api/ops/reports/{sent_id}/resend", timeout=15) if sent_id else None
    check(
        "T6 resend: failed->pending->failed again; sent -> 400",
        r6a.status_code == 200
        and r6a.json()["data"]["email_status"] == "pending"
        and d6["email_status"] == "failed"
        and (r6b is None or (r6b.status_code == 400
             and r6b.json()["msg"] == "resend_only_failed")),
        f"after_resend={d6['email_status']} sent_id={sent_id} "
        f"sent_resend={r6b.status_code if r6b else 'n/a'}",
    )

    # ---- T7: notifications list + mark one read ------------------------
    items = get("/api/ops/notifications", unread_only=True, limit=10).json()["data"]["items"]
    target = items[0]
    r7 = post(f"/api/ops/notifications/{target['id']}/read", timeout=15)
    unread2 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]
    read_back = next(
        it for it in get("/api/ops/notifications", limit=50).json()["data"]["items"]
        if it["id"] == target["id"]
    )
    check(
        "T7 mark one read: is_read=true, unread -1",
        r7.status_code == 200 and read_back["is_read"] is True
        and unread2 == unread1 - 1,
        f"unread {unread1} -> {unread2}",
    )

    # ---- T8: read-all ---------------------------------------------------
    post("/api/ops/notifications/read-all", timeout=15)
    unread3 = get("/api/ops/notifications/unread-count").json()["data"]["unread"]
    check("T8 read-all -> unread == 0", unread3 == 0, f"unread={unread3}")

    # ---- T9: error paths -----------------------------------------------
    r9a = get("/api/ops/reports/999999")
    r9b = post("/api/ops/reports/generate", {"type": "monthly"}, timeout=15)
    r9c = post("/api/ops/notifications/999999/read", timeout=15)
    check(
        "T9 unknown-id 404 x2, invalid type 400",
        r9a.status_code == 404 and r9b.status_code == 400 and r9c.status_code == 404,
        f"{r9a.status_code}/{r9b.status_code}/{r9c.status_code}",
    )

    failed = [n for n, okk, _ in RESULTS if not okk]
    print()
    if failed:
        print(f"FAILED: {len(failed)}/{len(RESULTS)} -> {failed}")
        sys.exit(1)
    print(f"ALL PASS ({len(RESULTS)}/{len(RESULTS)})")


if __name__ == "__main__":
    main()
