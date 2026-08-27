"""Step 8.1 verification for the assistant Function Calling tool set.

Direct async function calls (no LLM, no HTTP for the tools themselves),
per plan §8.1 verification:
  T1 query_top_styles(today, 3)            -> 3 items, count-desc, names present
  T2 query_top_styles(..., gender=male)    -> only male/both styles
  T3 compare_styles known + unknown ids    -> stats for known, found=False for x_99
  T4 find_trending(0.5, 50)                -> superset of GET /api/ops/trending
                                              (REST adds the collect>=20% rule)
  T5 find_cold(7)                          -> only active styles w/ 0 recent tryons
  T6 execute_action(f_01, boost)           -> SQL: display_order = old_min-1,
                                              ops_actions +1 (operator ai_assistant)
  T7 error paths                           -> unknown style / reorder / bad range /
                                              unknown tool / broken JSON args
  T8 dispatch() with JSON-string arguments -> same result as direct call

Run from backend/:  .venv\\Scripts\\python.exe scripts\\_check_assistant_tools.py
Backend server only needed for T4's REST cross-check.
NOTE: T6 mutates styles.display_order for f_01 and appends one audit row
(same residue class as _check_actions_api.py). Reseed before demos.
"""
from __future__ import annotations

import asyncio
import sys
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


async def main() -> None:
    from sqlalchemy import func, select, text
    from app.db import async_session_maker
    from app.models import OpsAction, Style
    from app.services.assistant_tools import (
        TOOL_SCHEMAS,
        compare_styles,
        dispatch,
        execute_action,
        find_cold,
        find_trending,
        query_top_styles,
    )

    async with async_session_maker() as db:
        # ---- T0: schema sanity ------------------------------------------
        names = [t["function"]["name"] for t in TOOL_SCHEMAS]
        check(
            "T0 schemas: 5 tools, OpenAI shape",
            len(TOOL_SCHEMAS) == 5
            and all(t["type"] == "function" for t in TOOL_SCHEMAS)
            and names == [
                "query_top_styles", "compare_styles", "find_trending",
                "find_cold", "execute_action",
            ],
            f"names={names}",
        )

        # ---- T1: top styles today ---------------------------------------
        r1 = await query_top_styles(db, date_range="today", top_n=3)
        counts = [it["tryon_count"] for it in r1.get("items", [])]
        check(
            "T1 query_top_styles(today,3): 3 rows, desc, named",
            r1.get("ok") is True
            and len(r1["items"]) == 3
            and counts == sorted(counts, reverse=True)
            and all(it["name"] for it in r1["items"]),
            f"counts={counts} top={r1['items'][0]['style_id'] if r1.get('items') else '-'}",
        )

        # ---- T2: gender filter ------------------------------------------
        r2 = await query_top_styles(db, date_range="last_7d", top_n=10, gender="male")
        ids2 = [it["style_id"] for it in r2.get("items", [])]
        genders = {}
        if ids2:
            genders = {
                s.id: s.gender
                for s in (
                    await db.execute(select(Style).where(Style.id.in_(ids2)))
                ).scalars()
            }
        check(
            "T2 gender=male: only male/both styles",
            r2.get("ok") is True
            and len(ids2) > 0
            and all(genders[sid] in {"male", "both"} for sid in ids2),
            f"n={len(ids2)}",
        )

        # ---- T3: compare with unknown id --------------------------------
        r3 = await compare_styles(db, style_ids=["f_15", "f_09", "x_99"], date_range="last_7d")
        by_id = {it["style_id"]: it for it in r3.get("items", [])}
        check(
            "T3 compare_styles: stats + found=False for x_99",
            r3.get("ok") is True
            and by_id["f_15"]["found"] and by_id["f_15"]["tryon_count"] > 0
            and by_id["f_09"]["found"] and by_id["f_09"]["tryon_count"] > 0
            and by_id["x_99"]["found"] is False,
            f"f_15={by_id.get('f_15', {}).get('tryon_count')} f_09={by_id.get('f_09', {}).get('tryon_count')}",
        )

        # ---- T4: find_trending superset of REST endpoint ----------------
        r4 = await find_trending(db, growth_threshold=0.5, min_volume=50)
        tool_ids = {it["style_id"] for it in r4.get("items", [])}
        try:
            rest = httpx.get(f"{BASE}/api/ops/trending", headers=HEADERS, timeout=15)
            rest_ids = {it["style_id"] for it in rest.json()["data"]["items"]}
            check(
                "T4 find_trending(0.5,50) ⊇ REST /api/ops/trending",
                r4.get("ok") is True and rest_ids.issubset(tool_ids),
                f"tool={sorted(tool_ids)} rest={sorted(rest_ids)}",
            )
        except httpx.HTTPError as e:
            check("T4 find_trending superset (REST cross-check)", False,
                  f"server not reachable: {e}")

        # ---- T5: find_cold zero-activity semantics ----------------------
        r5 = await find_cold(db, days_no_activity=7)
        cold_ids = [it["style_id"] for it in r5.get("items", [])]
        ok5 = r5.get("ok") is True
        if ok5 and cold_ids:
            for sid in cold_ids:
                cnt = (await db.execute(text(
                    "SELECT COUNT(*) FROM tryons WHERE style_id=:sid "
                    "AND created_at >= datetime('now','-7 days')"
                ), {"sid": sid})).scalar_one()
                active = (await db.execute(
                    select(Style.is_active).where(Style.id == sid)
                )).scalar_one()
                if int(cnt) != 0 or int(active) != 1:
                    ok5 = False
                    break
        check("T5 find_cold(7): active styles with 0 recent tryons",
              ok5, f"n={len(cold_ids)} ids={cold_ids[:5]}")

        # ---- T6: execute_action(boost) real mutation + audit ------------
        old_min = (await db.execute(
            select(func.min(Style.display_order)).where(Style.is_active == 1)
        )).scalar_one()
        audits_before = (await db.execute(
            select(func.count()).select_from(OpsAction)
        )).scalar_one()

        r6 = await execute_action(db, style_id="f_01", action_type="boost")

        new_order = (await db.execute(
            select(Style.display_order).where(Style.id == "f_01")
        )).scalar_one()
        audits_after = (await db.execute(
            select(func.count()).select_from(OpsAction)
        )).scalar_one()
        last_audit = (await db.execute(
            select(OpsAction).order_by(OpsAction.id.desc()).limit(1)
        )).scalar_one()
        check(
            "T6 execute_action(f_01,boost): order=min-1, audit +1, ai_assistant",
            r6.get("ok") is True
            and int(new_order) == int(old_min) - 1
            and int(audits_after) == int(audits_before) + 1
            and last_audit.style_id == "f_01"
            and last_audit.action_type == "boost"
            and last_audit.operator == "ai_assistant",
            f"order {old_min}->{new_order} audits {audits_before}->{audits_after}",
        )

        # ---- T7: error paths never raise --------------------------------
        e1 = await execute_action(db, style_id="x_99", action_type="boost")
        e2 = await execute_action(db, style_id="f_01", action_type="reorder")
        e3 = await query_top_styles(db, date_range="last_5d", top_n=3)
        e4 = await dispatch(db, "no_such_tool", {})
        e5 = await dispatch(db, "query_top_styles", "{broken json")
        e6 = await dispatch(db, "query_top_styles", {"date_range": "today", "nope": 1})
        check(
            "T7 error paths: all ok=False with error text, no exceptions",
            all(r.get("ok") is False and r.get("error") for r in (e1, e2, e3, e4, e5, e6)),
            f"e1={e1['error'][:28]}... e6={e6['error'][:28]}...",
        )

        # ---- T8: dispatch with JSON-string args == direct call ----------
        r8 = await dispatch(
            db, "query_top_styles", '{"date_range": "today", "top_n": 3}'
        )
        check(
            "T8 dispatch(JSON string) == direct call",
            r8.get("ok") is True
            and [i["style_id"] for i in r8["items"]]
            == [i["style_id"] for i in r1["items"]],
            f"top3={[i['style_id'] for i in r8.get('items', [])]}",
        )

    failed = [n for n, okk, _ in RESULTS if not okk]
    print()
    if failed:
        print(f"FAILED: {len(failed)}/{len(RESULTS)} -> {failed}")
        sys.exit(1)
    print(f"ALL PASS ({len(RESULTS)}/{len(RESULTS)})")


if __name__ == "__main__":
    asyncio.run(main())
