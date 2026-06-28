"""One-off probe to benchmark PPIO's Qwen-Image-Edit for nail try-on.

Goal: A/B-compare against Seedream 4.5's existing baseline saved in
`backend/static/cache/bench/bench_4_5_0.png` (Step 3.2). Same inputs:
  - hand:  backend/static/samples/05.png  (the darker-skin hand sample)
  - style: backend/static/styles/f_01_enh.png  (red female style)

PPIO Qwen-Image-Edit is an ASYNC API:
  POST https://api.ppinfra.com/v3/async/qwen-image-edit
  -> returns {task_id, ...}
  GET  https://api.ppinfra.com/v3/async/task-result?task_id=...
  -> poll until status terminal

PPIO docs describe `image` as `string` (singular). Some third-party
mirrors of Qwen-Image-Edit-Plus accept up to 3 reference images. We try
BOTH approaches so the user can compare:

  Approach A — single-image:  image = hand only, prompt = style described
                              in words derived from the f_01 tags JSON
  Approach B — multi-image:   image = [hand, style_ref] (as Seedream),
                              prompt = "替换指甲" style directive

Outputs land in:
  backend/static/cache/bench/qwen_edit_<approach>_<ms>.png
Plus a comparison/ folder gets the Seedream baseline + new Qwen result(s)
copied in for side-by-side viewing.

Run:
  backend/.venv/Scripts/python.exe data-prep/probe_qwen_image_edit.py
"""
from __future__ import annotations

import asyncio
import base64
import json
import shutil
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "backend" / ".env")
API_KEY = os.environ.get("PPIO_API_KEY", "")
if not API_KEY:
    print("PPIO_API_KEY missing in backend/.env"); sys.exit(2)

HAND = ROOT / "backend" / "static" / "samples" / "05.png"
STYLE = ROOT / "backend" / "static" / "styles" / "f_01_enh.png"
OUT_DIR = ROOT / "backend" / "static" / "cache" / "bench"
COMPARE_DIR = ROOT / "compare_qwen_vs_seedream"
SEEDREAM_BASELINE = OUT_DIR / "bench_4_5_0.png"

# Style metadata for the single-image prompt path (derived from
# dataset/styles/tags_qwen.json[f_01_enh.png])
STYLE_DESCRIPTION = (
    "纯红色（猩红/正红 #C20000 系），亮面高光，纯色无图案，"
    "圆形或方圆形甲面，长度中等。"
)

ENDPOINT_SUBMIT = "https://api.ppinfra.com/v3/async/qwen-image-edit"
ENDPOINT_RESULT = "https://api.ppinfra.com/v3/async/task-result"
TIMEOUT = 180
POLL_INTERVAL = 2.0
POLL_MAX_SECS = 120


def to_data_url(p: Path) -> str:
    raw = p.read_bytes()
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "png"
    elif raw[:3] == b"\xff\xd8\xff":
        mime = "jpeg"
    else:
        mime = "png"
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"


async def submit_and_poll(approach: str, payload: dict) -> tuple[bytes | None, float, str]:
    """Submit a Qwen edit task and poll until done. Returns (image_bytes, elapsed, status_log)."""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    t0 = time.perf_counter()
    log_lines = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            r = await client.post(ENDPOINT_SUBMIT, headers=headers, json=payload)
        except httpx.HTTPError as e:
            return None, time.perf_counter() - t0, f"network: {e}"

        log_lines.append(f"submit status={r.status_code}")
        if r.status_code != 200:
            log_lines.append(f"submit body: {r.text[:400]}")
            return None, time.perf_counter() - t0, "\n".join(log_lines)

        try:
            submit_data = r.json()
        except Exception:
            log_lines.append(f"submit body not json: {r.text[:400]}")
            return None, time.perf_counter() - t0, "\n".join(log_lines)

        task_id = submit_data.get("task_id") or submit_data.get("id") or submit_data.get("data", {}).get("task_id")
        if not task_id:
            log_lines.append(f"submit returned no task_id: {submit_data}")
            return None, time.perf_counter() - t0, "\n".join(log_lines)

        log_lines.append(f"task_id={task_id}")

        # Poll
        deadline = t0 + POLL_MAX_SECS
        image_bytes: bytes | None = None
        first_poll = True
        while time.perf_counter() < deadline:
            await asyncio.sleep(POLL_INTERVAL)
            try:
                rp = await client.get(ENDPOINT_RESULT, headers=headers, params={"task_id": task_id})
            except httpx.HTTPError as e:
                log_lines.append(f"poll network: {e}")
                continue

            if rp.status_code != 200:
                log_lines.append(f"poll status={rp.status_code} body={rp.text[:200]}")
                continue

            try:
                pdata = rp.json()
            except Exception:
                log_lines.append(f"poll non-json: {rp.text[:200]}")
                continue

            if first_poll:
                log_lines.append(f"first poll raw response: {json.dumps(pdata, ensure_ascii=False)[:600]}")
                first_poll = False

            # PPIO Qwen response shape (confirmed from probe):
            #   { "task": {"status": "TASK_STATUS_SUCCEED" | "..._PROCESSING" | "..._FAILED", ...},
            #     "images": [{"image_url": "..."}], "videos": [...], ... }
            status = pdata.get("task", {}).get("status", "")
            log_lines.append(f"poll status={status!r} elapsed={time.perf_counter()-t0:.1f}s")

            su = status.upper()
            terminal_ok = "SUCCEED" in su or "SUCCESS" in su or "COMPLETE" in su or "FINISH" in su
            terminal_fail = "FAIL" in su or "ERROR" in su or "CANCEL" in su

            if terminal_ok:
                images = pdata.get("images") or []
                if not images:
                    log_lines.append(f"SUCCEED but no images: {json.dumps(pdata, ensure_ascii=False)[:400]}")
                    break
                first = images[0]
                url = first if isinstance(first, str) else (first.get("image_url") or first.get("url") or first.get("download_url"))
                if not url:
                    log_lines.append(f"image entry has no url: {first}")
                    break
                try:
                    dl = await client.get(url, timeout=60)
                    image_bytes = dl.content
                    log_lines.append(f"downloaded {len(image_bytes)} bytes from {url[:60]}...")
                except httpx.HTTPError as e:
                    log_lines.append(f"download failed: {e}")
                break

            if terminal_fail:
                log_lines.append(f"terminal failure body: {json.dumps(pdata, ensure_ascii=False)[:400]}")
                break

        elapsed = time.perf_counter() - t0
        return image_bytes, elapsed, "\n".join(log_lines)


async def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)

    if not SEEDREAM_BASELINE.exists():
        print(f"WARN: Seedream baseline missing at {SEEDREAM_BASELINE}")
    else:
        shutil.copyfile(SEEDREAM_BASELINE, COMPARE_DIR / "seedream_4.5.png")
        shutil.copyfile(HAND, COMPARE_DIR / "_input_hand.png")
        shutil.copyfile(STYLE, COMPARE_DIR / "_input_style.png")
        print(f"[setup] copied baseline + inputs to {COMPARE_DIR}")

    # ---- Approach A: single image (hand only), describe style in words ----
    print("\n=== Approach A: single image (hand) + text style description ===")
    payload_A = {
        "prompt": (
            f"将这只手的所有指甲外观替换为以下款式：{STYLE_DESCRIPTION} "
            "保持手的肤色、形状、姿势、背景与原图完全一致，仅改变指甲表面的颜色与材质。"
            "结果要写实自然，不要卡通化。"
        ),
        "image": to_data_url(HAND),
        "output_format": "png",
        "watermark": False,
    }
    img_A, ms_A, log_A = await submit_and_poll("A", payload_A)
    print(log_A)
    print(f"[A] elapsed={ms_A:.1f}s, got_image={img_A is not None}")

    if img_A:
        ts = int(time.time() * 1000)
        out = OUT_DIR / f"qwen_edit_singleimg_{ts}.png"
        out.write_bytes(img_A)
        shutil.copyfile(out, COMPARE_DIR / "qwen_singleimg.png")
        print(f"[A] saved {out} -> compare/qwen_singleimg.png")

    # Approach B (multi-image array) was confirmed unsupported by PPIO:
    # submit returns 400 "invalid value for string field image: [".
    # The `image` field on PPIO's Qwen-Image-Edit accepts only a single
    # string (URL or data URL). Skipping that run on subsequent probes.
    img_B, ms_B = None, 0.0

    # ---- Final summary ----
    print("\n=== Summary ===")
    print(f"Seedream 4.5 baseline (from Step 3.2): bench_4_5_0.png  | elapsed ≈ 54s (recorded)")
    print(f"Qwen single-image: elapsed={ms_A:.1f}s | output={'OK' if img_A else 'FAIL'}")
    print(f"Qwen multi-image:  elapsed={ms_B:.1f}s | output={'OK' if img_B else 'FAIL'}")
    print(f"\nVisual comparison folder: {COMPARE_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
