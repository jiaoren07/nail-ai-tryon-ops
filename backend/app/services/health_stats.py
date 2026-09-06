"""In-process service health counters (Batch E: degradation visibility).

Motivation: every AI/external call in this product degrades gracefully
(template reasons, mock images, summary chat replies, failed-email flag)
— which once let a 100%-fallback regression hide for days. This module
makes degradation LOUD: call sites record outcomes here, and
GET /api/ops/health (surfaced in O7 账号工作台) shows them.

Deliberately in-memory (resets on restart): the panel states its window
is "since process start". No persistence, no locks needed beyond the
GIL for these tiny dict ops.
"""
from __future__ import annotations

from datetime import datetime, timezone

_MAX_DEGRADATION_EVENTS = 30

_started_at = datetime.now(timezone.utc)
_services: dict[str, dict] = {}
_degradations: list[dict] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_call(service: str, ok: bool, reason: str | None = None) -> None:
    """Count one outbound call outcome for a service key
    (llm_quick / llm_strong / image_gen / email)."""
    entry = _services.setdefault(service, {
        "ok": 0, "fail": 0,
        "last_ok_at": None, "last_fail_at": None, "last_fail_reason": None,
    })
    if ok:
        entry["ok"] += 1
        entry["last_ok_at"] = _now_iso()
    else:
        entry["fail"] += 1
        entry["last_fail_at"] = _now_iso()
        entry["last_fail_reason"] = (reason or "")[:200]


def record_degradation(source: str, reason: str) -> None:
    """Record one user-visible fallback event (e.g. template reasons
    served instead of LLM copy)."""
    _degradations.append({
        "at": _now_iso(),
        "source": source,
        "reason": (reason or "")[:200],
    })
    if len(_degradations) > _MAX_DEGRADATION_EVENTS:
        del _degradations[0]


def snapshot() -> dict:
    uptime = (datetime.now(timezone.utc) - _started_at).total_seconds()
    return {
        "started_at": _started_at.isoformat(),
        "uptime_seconds": int(uptime),
        "services": _services,
        "degradations": list(reversed(_degradations)),  # newest first
    }
