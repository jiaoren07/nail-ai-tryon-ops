"""Step 8.2 verification for POST /api/ops/chat (real PPIO strong-model FC).

Plan checks:
  T1 「今天哪款式试戴最多？」 -> reply names the top style,
     components contains top_styles_table (>=3 rows)
  T2 「把 f_15 加入首页推荐」 -> DB: f_15 display_order == active min,
     ops_actions +1 (boost, ai_assistant); components has action_result
  T3 「这周哪些款式涨得最快？」 -> reply mentions >=2 style names,
     components contains trending_list
  T4 request validation: empty messages / bad role / assistant-last -> 400

Run from backend/ with uvicorn on :8000. Makes ~4-7 real LLM calls
(deepseek strong tier); a 10s pause between questions avoids 429 noise.
T2 mutates f_15 + appends one audit row (normal check residue).
Reseed before running if the day has rolled over since the last seed.
"""
from __future__ import annotations

import asyncio
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
# 30s between questions: the strong tier rate-limits per minute too; each
# question costs ~2 LLM calls, so back-to-back questions trip 429 and the
# endpoint (correctly) degrades to template replies. Spacing matches how an
# operator actually chats.
PAUSE_SECONDS = 30

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def ask(question: str) -> dict:
    t0 = time.time()
    r = httpx.post(
        f"{BASE}/api/ops/chat",
        headers=HEADERS,
        json={"messages": [{"role": "user", "content": question}], "session_id": "check"},
        timeout=180,
    )
    took = time.time() - t0
    r.raise_for_status()
    payload = r.json()
    print(f"    Q: {question}  ({took:.1f}s, rounds={payload['data'].get('tool_rounds')})")
    print(f"    A: {payload['data']['reply'][:120]}")
    return payload


def db_state() -> dict:
    import asyncio as aio
    from sqlalchemy import func, select
    from app.db import async_session_maker
    from app.models import OpsAction, Style

    async def go():
        async with async_session_maker() as db:
            f15 = (await db.execute(
                select(Style.display_order).where(Style.id == "f_15")
            )).scalar_one()
            min_active = (await db.execute(
                select(func.min(Style.display_order)).where(Style.is_active == 1)
            )).scalar_one()
            audits = (await db.execute(
                select(func.count()).select_from(OpsAction)
            )).scalar_one()
            last = (await db.execute(
                select(OpsAction).order_by(OpsAction.id.desc()).limit(1)
            )).scalar_one_or_none()
            return {
                "f15": int(f15),
                "min": int(min_active),
                "audits": int(audits),
                "last": (last.style_id, last.action_type, last.operator) if last else None,
            }

    return aio.run(go())


def main() -> None:
    # ---- T1: top styles today ------------------------------------------
    p1 = ask("今天哪款式试戴最多？")
    d1 = p1["data"]
    comps1 = {c["component"] for c in d1["components"]}
    top_table = next(
        (c["data"] for c in d1["components"] if c["component"] == "top_styles_table"), []
    )
    top_named = bool(top_table) and top_table[0]["name"] in d1["reply"]
    check(
        "T1 top question: top_styles_table >=3 rows + reply names top style",
        p1["code"] == 0 and "top_styles_table" in comps1
        and len(top_table) >= 3 and top_named,
        f"comps={sorted(comps1)} top={top_table[0]['name'] if top_table else '-'}",
    )
    time.sleep(PAUSE_SECONDS)

    # ---- T2: execute action --------------------------------------------
    before = db_state()
    p2 = ask("把 f_15 加入首页推荐")
    d2 = p2["data"]
    after = db_state()
    comps2 = {c["component"] for c in d2["components"]}
    check(
        "T2 boost f_15: order==active-min, audit +1 (boost/ai_assistant)",
        p2["code"] == 0
        and "action_result" in comps2
        and after["f15"] == after["min"]
        and after["f15"] < before["f15"]
        and after["audits"] == before["audits"] + 1
        and after["last"] == ("f_15", "boost", "ai_assistant"),
        f"f15 {before['f15']}->{after['f15']} (min={after['min']}) audits {before['audits']}->{after['audits']}",
    )
    time.sleep(PAUSE_SECONDS)

    # ---- T3: trending question -----------------------------------------
    p3 = ask("这周哪些款式涨得最快？")
    d3 = p3["data"]
    comps3 = {c["component"] for c in d3["components"]}
    trend = next(
        (c["data"] for c in d3["components"] if c["component"] == "trending_list"), []
    )
    named = [it["name"] for it in trend if it.get("name") and it["name"] in d3["reply"]]
    check(
        "T3 trending question: trending_list + reply mentions >=2 names",
        p3["code"] == 0 and "trending_list" in comps3 and len(named) >= 2,
        f"listed={len(trend)} named_in_reply={len(named)}",
    )

    # ---- T4: validation paths (no LLM cost) ----------------------------
    r_empty = httpx.post(f"{BASE}/api/ops/chat", headers=HEADERS,
                         json={"messages": []}, timeout=15)
    r_role = httpx.post(f"{BASE}/api/ops/chat", headers=HEADERS,
                        json={"messages": [{"role": "system", "content": "x"}]}, timeout=15)
    r_last = httpx.post(
        f"{BASE}/api/ops/chat", headers=HEADERS,
        json={"messages": [{"role": "user", "content": "hi"},
                           {"role": "assistant", "content": "yo"}]},
        timeout=15,
    )
    check(
        "T4 validation: empty/bad-role/assistant-last all 400",
        r_empty.status_code == 400 and r_role.status_code == 400
        and r_last.status_code == 400,
        f"codes={r_empty.status_code}/{r_role.status_code}/{r_last.status_code}",
    )

    failed = [n for n, okk, _ in RESULTS if not okk]
    print()
    if failed:
        print(f"FAILED: {len(failed)}/{len(RESULTS)} -> {failed}")
        sys.exit(1)
    print(f"ALL PASS ({len(RESULTS)}/{len(RESULTS)})")


if __name__ == "__main__":
    main()
