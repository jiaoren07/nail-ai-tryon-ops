"""Step 4.5 Pass B verification: empty PPIO_API_KEY -> all 9 fallback reasons.

Assumes uvicorn is already running on 127.0.0.1:8000 with PPIO_API_KEY="" in
its env (start it with `$env:PPIO_API_KEY = ""; python -m uvicorn ...`).
"""
from __future__ import annotations

import sys
import time

import httpx

UID = "550e8400-e29b-41d4-a716-446655440000"
BASE = "http://127.0.0.1:8000"


def main() -> int:
    failures: list[str] = []
    body = {
        "user_id": UID,
        "gender": "female",
        "hand_features": {"skin_tone": "light_warm", "hand_shape": "average"},
    }
    t0 = time.perf_counter()
    r = httpx.post(BASE + "/api/recommend", json=body, headers={"X-User-Id": UID}, timeout=20.0)
    elapsed = time.perf_counter() - t0
    r.raise_for_status()
    data = r.json()["data"]

    print(f"\n[Pass B] empty PPIO_API_KEY  elapsed={elapsed:.2f}s")
    print(f"  user_summary: {data['user_summary']}")
    for i, rec in enumerate(data["recommendations"]):
        print(f"  #{i+1} {rec['style_id']:6s} ({len(rec['reason']):2d}) '{rec['reason']}'")

    if len(data["recommendations"]) != 9:
        failures.append(f"expected 9 recs, got {len(data['recommendations'])}")
    over = [r["reason"] for r in data["recommendations"] if len(r["reason"]) > 25]
    if over:
        failures.append(f"reasons over 25 chars: {over}")
    if elapsed >= 6.0:
        failures.append(f"elapsed {elapsed:.2f}s >= 6.0s")

    # All reasons must look like fallback templates `<tag>款，<descriptor>`
    # (containing "款，"). Real LLM output uses no such fixed prefix.
    non_fallback = [r["reason"] for r in data["recommendations"] if "款，" not in r["reason"]]
    if non_fallback:
        failures.append(f"unexpected non-fallback reasons (LLM should be unreachable): {non_fallback}")

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
