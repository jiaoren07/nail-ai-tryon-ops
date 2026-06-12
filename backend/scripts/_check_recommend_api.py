"""Step 4.5 verification for POST /api/recommend.

Two passes against a running uvicorn on 127.0.0.1:8000:
  Pass A: with real PPIO_API_KEY -> LLM-generated reasons, <=25 chars, <6s
  Pass B: caller-driven fallback path is exercised separately by the
          companion script `_check_recommend_fallback.py`, which restarts
          uvicorn with PPIO_API_KEY="" set in env (smarter than mutating
          .env from within this script).

Usage:
    backend\\.venv\\Scripts\\python.exe backend\\scripts\\_check_recommend_api.py
"""
from __future__ import annotations

import sys
import time

import httpx

UID = "550e8400-e29b-41d4-a716-446655440000"
BASE = "http://127.0.0.1:8000"


def call(gender: str, skin_tone: str, hand_shape: str = "average") -> tuple[float, dict]:
    body = {
        "user_id": UID,
        "gender": gender,
        "hand_features": {"skin_tone": skin_tone, "hand_shape": hand_shape},
    }
    t0 = time.perf_counter()
    r = httpx.post(
        BASE + "/api/recommend",
        json=body,
        headers={"X-User-Id": UID},
        timeout=30.0,
    )
    elapsed = time.perf_counter() - t0
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 0:
        raise RuntimeError(f"envelope error: {body}")
    return elapsed, body["data"]


def main() -> int:
    failures: list[str] = []

    # Test 1: female + light_warm
    elapsed, data = call("female", "light_warm")
    print(f"\n[T1] female / light_warm  elapsed={elapsed:.2f}s  summary='{data['user_summary']}'")
    for i, r in enumerate(data["recommendations"]):
        flag = "" if len(r["reason"]) <= 25 else " OVER25!"
        print(f"  #{i+1} {r['style_id']:6s} {r['color_main']} {r['style_tags'][:2]} score={r['score']:.3f} ({len(r['reason']):2d}) '{r['reason']}'{flag}")
    if len(data["recommendations"]) != 9:
        failures.append(f"T1 expected 9 recs, got {len(data['recommendations'])}")
    over_chars = [r["reason"] for r in data["recommendations"] if len(r["reason"]) > 25]
    if over_chars:
        failures.append(f"T1 reasons over 25 chars: {over_chars}")
    if elapsed >= 6.0:
        failures.append(f"T1 elapsed {elapsed:.2f}s >= 6.0s")
    required_fields = {"style_id", "name", "cover_url", "color_main", "style_tags", "score", "reason"}
    missing = [
        sorted(required_fields - r.keys()) for r in data["recommendations"]
        if not required_fields.issubset(r.keys())
    ]
    if missing:
        failures.append(f"T1 recommendations missing fields: {missing[0]}")

    # Test 2: male + dark_cool (should hit cool-leaning style pool)
    elapsed, data = call("male", "dark_cool")
    print(f"\n[T2] male / dark_cool  elapsed={elapsed:.2f}s  summary='{data['user_summary']}'")
    for i, r in enumerate(data["recommendations"]):
        flag = "" if len(r["reason"]) <= 25 else " OVER25!"
        print(f"  #{i+1} {r['style_id']:6s} score={r['score']:.3f} ({len(r['reason']):2d}) '{r['reason']}'{flag}")
    if len(data["recommendations"]) != 9:
        failures.append(f"T2 expected 9 recs, got {len(data['recommendations'])}")
    over_chars = [r["reason"] for r in data["recommendations"] if len(r["reason"]) > 25]
    if over_chars:
        failures.append(f"T2 reasons over 25 chars: {over_chars}")
    if elapsed >= 6.0:
        failures.append(f"T2 elapsed {elapsed:.2f}s >= 6.0s")

    # Test 3: invalid gender -> 400
    r3 = httpx.post(
        BASE + "/api/recommend",
        json={"user_id": UID, "gender": "other", "hand_features": {"skin_tone": "medium"}},
        headers={"X-User-Id": UID},
        timeout=5.0,
    )
    print(f"\n[T3] gender=other -> status={r3.status_code} body={r3.json()}")
    if r3.status_code != 400 or r3.json().get("msg") != "invalid_gender":
        failures.append(f"T3 expected 400/invalid_gender, got {r3.status_code}/{r3.json()}")

    # Test 4: header X-User-Id != body user_id -> 400
    r4 = httpx.post(
        BASE + "/api/recommend",
        json={"user_id": "11111111-1111-1111-1111-111111111111", "gender": "female",
              "hand_features": {"skin_tone": "medium"}},
        headers={"X-User-Id": UID},
        timeout=5.0,
    )
    print(f"\n[T4] body.user_id != header -> status={r4.status_code} body={r4.json()}")
    if r4.status_code != 400 or r4.json().get("msg") != "user_id_mismatch":
        failures.append(f"T4 expected 400/user_id_mismatch, got {r4.status_code}/{r4.json()}")

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
