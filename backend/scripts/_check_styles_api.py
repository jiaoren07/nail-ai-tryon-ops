"""Internal verification helper for Step 4.3 GET /api/styles.

Spawns 7 HTTP calls against a running uvicorn on 127.0.0.1:8000 and asserts
plan checks + stable-pagination tiebreakers. Mirrors `_check_tryons.py`
naming pattern. Not part of runtime.
"""
from __future__ import annotations

import json
import sys

import httpx

UID = "550e8400-e29b-41d4-a716-446655440000"
HEADERS = {"X-User-Id": UID}
BASE = "http://127.0.0.1:8000"


def fetch(path: str) -> dict:
    r = httpx.get(BASE + path, headers=HEADERS, timeout=10.0)
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(f"envelope error: {body}")
    return body["data"]


def main() -> int:
    failures: list[str] = []

    # 1. No params: plan said total=25 (25-female era); now 40 active styles
    d1 = fetch("/api/styles")
    print(f"1. no params → total={d1['total']} page={d1['page']} size={d1['size']} items_len={len(d1['items'])}")
    if d1["total"] != 40:
        failures.append(f"  total != 40 (got {d1['total']})")
    if d1["size"] != 24 or len(d1["items"]) != 24:
        failures.append(f"  default page size not 24 (got size={d1['size']}, items_len={len(d1['items'])})")

    # 2. gender=female: should be 25 (we have 25 female + 0 both)
    d2 = fetch("/api/styles?gender=female&size=100")
    bad_gender = [i["id"] for i in d2["items"] if i["gender"] not in {"female", "both"}]
    print(f"2. gender=female → total={d2['total']} all_items_gender_ok={not bad_gender}")
    if d2["total"] != 25:
        failures.append(f"  gender=female total != 25 (got {d2['total']})")
    if bad_gender:
        failures.append(f"  gender=female returned non-female/both: {bad_gender}")

    # 2b. gender=male: should be 15
    d2b = fetch("/api/styles?gender=male&size=100")
    bad_male = [i["id"] for i in d2b["items"] if i["gender"] not in {"male", "both"}]
    print(f"2b. gender=male → total={d2b['total']} all_items_gender_ok={not bad_male}")
    if d2b["total"] != 15:
        failures.append(f"  gender=male total != 15 (got {d2b['total']})")
    if bad_male:
        failures.append(f"  gender=male returned non-male/both: {bad_male}")

    # 3. tags=极简: every item's style_tags should contain "极简"
    d3 = fetch("/api/styles?tags=极简&size=100")
    bad_tag = [i["id"] for i in d3["items"] if "极简" not in i["style_tags"]]
    print(f"3. tags=极简 → total={d3['total']} all_items_contain_极简={not bad_tag}")
    if d3["total"] == 0:
        failures.append("  tags=极简 returned zero — unexpected with 40-style seed")
    if bad_tag:
        failures.append(f"  tags=极简 returned non-matching items: {bad_tag}")

    # 4. sort=new&size=5: 5 items, ordered by created_at desc (id asc tie-break)
    d4 = fetch("/api/styles?sort=new&size=5")
    ids4 = [i["id"] for i in d4["items"]]
    print(f"4. sort=new&size=5 → ids={ids4}")
    if len(d4["items"]) != 5:
        failures.append(f"  sort=new&size=5 returned {len(d4['items'])} items, expected 5")
    # With all created_at equal, tiebreak by id ASC → first 5 alphabetically: f_01..f_05
    if ids4 != ["f_01", "f_02", "f_03", "f_04", "f_05"]:
        failures.append(f"  sort=new&size=5 tiebreaker not stable, got {ids4}")

    # 5. sort=smart default ordering by display_order
    d5 = fetch("/api/styles?sort=smart&size=5")
    ids5 = [i["id"] for i in d5["items"]]
    print(f"5. sort=smart&size=5 → ids={ids5}")
    # display_order 0..39 was assigned by id sort in seed_styles, so first 5 = f_01..f_05
    if ids5 != ["f_01", "f_02", "f_03", "f_04", "f_05"]:
        failures.append(f"  sort=smart ordering wrong, got {ids5}")

    # 6. invalid gender → 400
    r6 = httpx.get(BASE + "/api/styles?gender=other", headers=HEADERS, timeout=10.0)
    print(f"6. gender=other → status={r6.status_code} body={r6.json()}")
    if r6.status_code != 400 or r6.json().get("msg") != "invalid_gender":
        failures.append(f"  gender=other did not 400/invalid_gender (got {r6.status_code} {r6.json()})")

    # 7. invalid sort → 400
    r7 = httpx.get(BASE + "/api/styles?sort=foo", headers=HEADERS, timeout=10.0)
    print(f"7. sort=foo → status={r7.status_code} body={r7.json()}")
    if r7.status_code != 400 or r7.json().get("msg") != "invalid_sort":
        failures.append(f"  sort=foo did not 400/invalid_sort (got {r7.status_code} {r7.json()})")

    # 8. pagination: page=2 size=10 → 10 items, none overlap with page=1
    p1 = fetch("/api/styles?page=1&size=10")
    p2 = fetch("/api/styles?page=2&size=10")
    overlap = set(i["id"] for i in p1["items"]) & set(i["id"] for i in p2["items"])
    print(f"8. pagination → page1_len={len(p1['items'])} page2_len={len(p2['items'])} overlap={len(overlap)}")
    if overlap:
        failures.append(f"  pagination overlap: {overlap}")

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
