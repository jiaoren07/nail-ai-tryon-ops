"""Batch H: U1 upload gate — "is this actually a hand photo?".

A cheap VLM check between upload and analysis, so a photo of a desk or
an apple gets a clear rejection instead of a nonsense skin-tone reading
(pre-gate, ANY image produced a confident-looking analysis).

Design constraints:
- FAIL OPEN: model error / timeout / unparseable answer lets the upload
  through (recorded as a degradation on the O7 health panel) — a broken
  gate must never lock real users out of the core flow.
- Sample images skip the gate entirely (they are known hands; keeps the
  1s sample fast-path intact). The frontend flags them via is_sample —
  spoofable, but this is UX guidance, not a security boundary.
"""
from __future__ import annotations

import asyncio
import base64
import logging
from io import BytesIO

from PIL import Image

from app.config import settings
from app.services import health_stats, llm

logger = logging.getLogger("nail_demo.hand_gate")

_GATE_TIMEOUT_SECONDS = 10
_MAX_SIDE = 768  # downscale before base64 — latency matters, fidelity doesn't

_PROMPT = (
    "这张照片中是否清晰可见真人的手部（手掌、手背或手指均可，戴美甲也算）？"
    "只回答一个字：是 或 否。"
)


def _to_data_url(image_bytes: bytes) -> str:
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((_MAX_SIDE, _MAX_SIDE))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


async def is_hand_photo(image_bytes: bytes) -> bool | None:
    """True/False = confident verdict; None = gate unavailable (fail open)."""
    try:
        data_url = _to_data_url(image_bytes)
        answer = await asyncio.wait_for(
            llm.gen_vision_text(_PROMPT, data_url, settings.VLM_MODEL),
            timeout=_GATE_TIMEOUT_SECONDS,
        )
    except Exception as e:
        logger.warning("hand gate unavailable, failing open: %s", e)
        health_stats.record_degradation("hand_gate", str(e))
        return None

    ans = answer.strip()
    # "不是" contains "是" — negative patterns must win before the bare
    # substring check.
    if ans.startswith("是"):
        return True
    if ans.startswith("否") or ans.startswith("不") or "否" in ans or "不是" in ans:
        return False
    if "是" in ans:
        return True
    logger.warning("hand gate unparseable answer %r, failing open", ans)
    health_stats.record_degradation("hand_gate", f"unparseable: {ans[:50]}")
    return None
