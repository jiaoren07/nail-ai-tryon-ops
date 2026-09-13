"""Batch I: one-off VLM annotation — nail-region bboxes for all 40 covers.

Why: Seedream copies a style cover's whole composition (hand pose,
background) when the cover is a strong full-hand photo, discarding the
user's uploaded hand (reproduced on f_21). Feeding a NAIL CLOSE-UP crop
as the style reference instead removes the copyable composition signal
— verified 2026-09-13, promptlab round 2.

This script asks the VLM (same model as the U1 hand gate) for a tight
bbox around the visible nails on each cover and writes normalized
[x0, y0, x1, y1] (0..1 floats, relative to cover size) to
assets/dataset/nail_bboxes.json. seed_styles.py then crops
static/styles/{sid}_nail.jpg at seed time (pure PIL, no runtime VLM),
and SeedreamProvider prefers that crop as the style reference.

Resumable: styles already present in the JSON are skipped. Styles whose
bbox fails validation are OMITTED — the provider falls back to the full
cover for them (no worse than before). Review the crops visually after
running (a bad crop is worse than no crop) and delete bad entries.

Run from backend/:
    .venv\\Scripts\\python.exe -X utf8 scripts\\annotate_nail_bboxes.py
"""
from __future__ import annotations

import asyncio
import base64
import json
import re
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.services import llm  # noqa: E402

DATASET_DIR = BACKEND_ROOT.parent / "assets" / "dataset"
OUT_JSON = DATASET_DIR / "nail_bboxes.json"

_VLM_SIDE = 768          # downscale before sending (latency, same as hand gate)
_MARGIN = 0.12           # expand the tight bbox so full nails + a little context survive
_MIN_AREA, _MAX_AREA = 0.04, 0.75   # sanity band, fraction of the cover

_PROMPT = (
    "这张图片里有涂着美甲的手指甲。请给出一个矩形框，尽量紧凑地框住所有可见指甲"
    "的区域（允许包含少量周边手指皮肤）。坐标用 0 到 1000 的整数（相对图片宽高的"
    '千分比）。只输出 JSON，格式：{"bbox": [x0, y0, x1, y1]}，不要任何其他文字。'
)


def _covers() -> list[tuple[str, Path]]:
    items = [
        (p.name.removesuffix("_enh.png"), p)
        for p in sorted((DATASET_DIR / "styles").glob("f_*_enh.png"))
    ]
    items += [
        (p.name.removesuffix(".jpg"), p)
        for p in sorted((DATASET_DIR / "styles" / "male").glob("m_*.jpg"))
    ]
    return items


def _to_data_url(path: Path) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((_VLM_SIDE, _VLM_SIDE))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _parse_bbox(answer: str) -> list[float] | None:
    """Extract [x0,y0,x1,y1] in 0..1000 from the model answer, return 0..1."""
    m = re.search(r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]", answer)
    if not m:
        return None
    x0, y0, x1, y1 = (int(g) for g in m.groups())
    if not (0 <= x0 < x1 <= 1000 and 0 <= y0 < y1 <= 1000):
        return None
    return [x0 / 1000, y0 / 1000, x1 / 1000, y1 / 1000]


def _expand_and_validate(box: list[float]) -> list[float] | None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    x0 = max(0.0, x0 - w * _MARGIN)
    y0 = max(0.0, y0 - h * _MARGIN)
    x1 = min(1.0, x1 + w * _MARGIN)
    y1 = min(1.0, y1 + h * _MARGIN)
    area = (x1 - x0) * (y1 - y0)
    if not (_MIN_AREA <= area <= _MAX_AREA):
        return None
    return [round(v, 4) for v in (x0, y0, x1, y1)]


async def main() -> None:
    existing: dict[str, list[float]] = {}
    if OUT_JSON.exists():
        existing = json.loads(OUT_JSON.read_text(encoding="utf-8"))

    covers = _covers()
    print(f"covers: {len(covers)}, already annotated: {len(existing)}")

    done = skipped = failed = 0
    for sid, path in covers:
        if sid in existing:
            skipped += 1
            continue
        try:
            answer = await llm.gen_vision_text(
                _PROMPT, _to_data_url(path), settings.VLM_MODEL, max_tokens=64
            )
        except Exception as e:
            print(f"[FAIL] {sid}: VLM error {type(e).__name__}: {str(e)[:100]}")
            failed += 1
            continue
        box = _parse_bbox(answer)
        box = _expand_and_validate(box) if box else None
        if box is None:
            print(f"[DROP] {sid}: unusable answer {answer[:60]!r}")
            failed += 1
            continue
        existing[sid] = box
        OUT_JSON.write_text(
            json.dumps(existing, ensure_ascii=False, indent=1, sort_keys=True),
            encoding="utf-8",
        )
        done += 1
        print(f"[OK] {sid}: {box}")
        # 8s spacing: the VLM tier rate-limits sustained bursts (~first
        # run got 23 done then solid 429s); this keeps a full 40-cover
        # pass under the per-minute ceiling.
        await asyncio.sleep(8)

    print(f"\nannotated now: {done}, resumed-skip: {skipped}, failed: {failed}")
    print(f"total in JSON: {len(existing)} -> {OUT_JSON}")


if __name__ == "__main__":
    asyncio.run(main())
