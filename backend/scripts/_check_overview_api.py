"""Step 6.1 verification for GET /api/ops/overview.

Plan checks:
  1. All four top-level keys present (kpis, trend_7d, style_distribution,
     hourly_heat)
  2. trend_7d.length == 7
  3. hourly_heat.length == 24
  4. kpis.tryons_today.value == SELECT SUM(tryon_count) FROM style_stats
     WHERE stat_date = date('now','localtime')

Extras: schema shape sanity, KPI dict shape.
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


def _today_sum_tryon_count() -> int:
    import asyncio
    from sqlalchemy import text
    from app.db import async_session_maker

    async def go():
        async with async_session_maker() as db:
            r = await db.execute(text(
                "SELECT COALESCE(SUM(tryon_count),0) FROM style_stats "
                "WHERE stat_date = date('now','localtime')"
            ))
            return int(r.scalar_one())

    return asyncio.run(go())


def main() -> int:
    failures: list[str] = []

    r = httpx.get(BASE + "/api/ops/overview", headers=HEADERS, timeout=10.0)
    print(f"[GET /api/ops/overview] status={r.status_code}")
    if r.status_code != 200:
        failures.append(f"non-200: {r.text[:200]}")
        print("FAILURES:", failures); return 1

    body = r.json()
    if body.get("code") != 0:
        failures.append(f"envelope code != 0: {body}")
        print("FAILURES:", failures); return 1

    data = body["data"]
    print(f"top-level keys: {sorted(data.keys())}")

    # 1. Four keys present
    for key in ("kpis", "trend_7d", "style_distribution", "hourly_heat"):
        if key not in data:
            failures.append(f"missing top-level key: {key}")

    # 2. trend_7d length
    print(f"trend_7d len={len(data.get('trend_7d', []))}")
    if len(data.get("trend_7d", [])) != 7:
        failures.append(f"trend_7d length != 7 (got {len(data.get('trend_7d', []))})")
    print(f"trend_7d sample: {data.get('trend_7d')[-3:]}")

    # 3. hourly_heat length
    print(f"hourly_heat len={len(data.get('hourly_heat', []))}")
    if len(data.get("hourly_heat", [])) != 24:
        failures.append(f"hourly_heat length != 24 (got {len(data.get('hourly_heat', []))})")

    # 4. KPI tryons_today matches direct SQL
    api_today = data.get("kpis", {}).get("tryons_today", {}).get("value")
    sql_today_stats = _today_sum_tryon_count()
    print(f"kpis.tryons_today.value = {api_today}")
    print(f"SUM(tryon_count) WHERE stat_date=today = {sql_today_stats}")
    # The verification in plan compares against SUM(style_stats); they should
    # match because every tryon also bumps stat counter by 1.
    if api_today != sql_today_stats:
        failures.append(f"KPI value {api_today} != SQL SUM {sql_today_stats}")

    # Extra: KPI shape
    for k in ("tryons_today", "conversion_rate", "active_styles", "new_trending_alerts"):
        kpi = data.get("kpis", {}).get(k)
        if not isinstance(kpi, dict) or "value" not in kpi or "diff_percent" not in kpi:
            failures.append(f"KPI {k!r} bad shape: {kpi}")

    # Extra: style_distribution shape
    sd = data.get("style_distribution", [])
    print(f"style_distribution top-{len(sd)}: {sd}")
    for entry in sd:
        if "style_tag" not in entry or "percent" not in entry:
            failures.append(f"style_distribution entry missing keys: {entry}")

    # Extra: KPI conversion_rate value range
    cr = data.get("kpis", {}).get("conversion_rate", {}).get("value")
    if not (cr is None or 0.0 <= cr <= 1.0):
        failures.append(f"conversion_rate value out of [0,1]: {cr}")

    print()
    print(f"hourly_heat = {data.get('hourly_heat')}")
    print(f"kpis = {data.get('kpis')}")

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
