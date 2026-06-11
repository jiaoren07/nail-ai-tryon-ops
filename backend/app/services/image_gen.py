"""Try-on image generation: abstract provider + Mock fallback + Seedream real provider + factory.

Per implementation-plan §3.1 / §3.2:
- ImageGenProvider abstracts away the actual image-gen backend.
- MockProvider copies the style cover to /static/cache/, used as the
  demo safety net when the real API is unavailable.
- SeedreamProvider calls PPIO's `/v3/seedream-4.5` with the user's hand
  image + the chosen style cover as two reference images, producing a
  real AI-synthesised try-on. See progress.md Step 3.2 for the model
  comparison rationale (4.5 chosen over 4.0 / 5.0-lite / Qwen).
- get_image_provider() reads settings.IMAGE_PROVIDER ('mock' | 'seedream')
  and returns the matching instance.
"""
from __future__ import annotations

import base64
import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path

import httpx

from app.config import settings

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_STYLES = BACKEND_ROOT / "static" / "styles"
STATIC_CACHE = BACKEND_ROOT / "static" / "cache"


class ImageGenError(Exception):
    """Raised when image generation cannot produce a result."""


class ImageGenProvider(ABC):
    """Abstract base. Implementations produce one try-on image per call.

    Returns the **relative URL** (e.g. `/static/cache/<filename>`) where the
    result is saved, ready to serve via the /static mount.
    """

    @abstractmethod
    async def generate(
        self,
        user_id: str,
        style_id: str,
        hand_image_bytes: bytes,
        prompt_extra: str | None = None,
    ) -> str:
        """Generate one try-on result image.

        Raises ImageGenError on failure; MockProvider should never raise
        unless the style id is unknown (no cover on disk).
        """
        ...


def _resolve_cover_path(style_id: str) -> Path | None:
    """Locate the on-disk cover image for a style id.

    Female styles use `f_NN_enh.png`, male styles use `m_NN.jpg`. Probe both.
    """
    for suffix in ("_enh.png", ".jpg"):
        candidate = STATIC_STYLES / f"{style_id}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _bytes_to_data_url(raw: bytes, fallback_mime: str = "png") -> str:
    """Sniff PNG/JPEG magic bytes and wrap as a data: URL."""
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "png"
    elif raw[:3] == b"\xff\xd8\xff":
        mime = "jpeg"
    else:
        mime = fallback_mime
    return f"data:image/{mime};base64,{base64.b64encode(raw).decode()}"


def _file_to_data_url(path: Path) -> str:
    """Read file + wrap as data: URL. Mime sniffed from suffix."""
    suffix = path.suffix.lower().lstrip(".")
    mime = "png" if suffix == "png" else "jpeg"
    return f"data:image/{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


class MockProvider(ImageGenProvider):
    """Demo fallback: copies the style cover into /static/cache/ as the 'result'.

    Visually deceptive (it IS the style image, not a real synthesis), but it
    lets the entire try-on flow run with zero external dependency. Required
    by design-docu §8: the closed loop must always work even when the real
    image-gen API is unavailable.
    """

    async def generate(
        self,
        user_id: str,
        style_id: str,
        hand_image_bytes: bytes,
        prompt_extra: str | None = None,
    ) -> str:
        cover = _resolve_cover_path(style_id)
        if cover is None:
            raise ImageGenError(f"no cover image found for style {style_id!r}")
        STATIC_CACHE.mkdir(parents=True, exist_ok=True)
        out = STATIC_CACHE / f"{user_id}_{style_id}{cover.suffix}"
        shutil.copyfile(cover, out)
        return f"/static/cache/{out.name}"


class SeedreamProvider(ImageGenProvider):
    """Real AI try-on synthesis via PPIO's Seedream 4.5.

    Posts the user's hand image + chosen style cover as two reference images
    plus a directive prompt; downloads the returned image to
    `/static/cache/seedream_*.png` and returns its URL.

    Locked defaults (see progress.md Step 3.2 for the benchmark rationale):
    - Model: seedream-4.5 (best skin-tone fidelity among PPIO's image
      catalog; 4.0 over-darkens, 5.0-lite rejects darker hands, Qwen-Image
      edit only accepts a single image).
    - Prompt: V1 short version (V2 expanded version showed no observable
      improvement in the benchmark; the additional constraints did not
      change model output meaningfully).
    - size: "2K" (demo display target is well under 4K).
    - watermark: false (we're presenting these as "your try-on", not
      external content that needs source attribution).

    Cost: ~¥0.2 per call on PPIO at time of writing.
    Typical latency: 40-60 seconds.
    """

    ENDPOINT = "https://api.ppio.com/v3/seedream-4.5"
    TIMEOUT_SECONDS = 180
    DOWNLOAD_TIMEOUT = 60

    PROMPT_TEMPLATE = (
        "将第一张图中手的指甲外观替换为第二张图所示的美甲款式设计。"
        "保持手的肤色、形状、姿势和背景与第一张图完全一致，"
        "仅改变指甲表面的颜色与图案。结果要写实、自然，不要卡通化。"
    )

    async def generate(
        self,
        user_id: str,
        style_id: str,
        hand_image_bytes: bytes,
        prompt_extra: str | None = None,
    ) -> str:
        if not settings.PPIO_API_KEY:
            raise ImageGenError(
                "PPIO_API_KEY missing — set it in backend/.env to use SeedreamProvider"
            )
        cover = _resolve_cover_path(style_id)
        if cover is None:
            raise ImageGenError(f"no cover image found for style {style_id!r}")

        hand_url = _bytes_to_data_url(hand_image_bytes, "png")
        style_url = _file_to_data_url(cover)
        prompt = self.PROMPT_TEMPLATE
        if prompt_extra:
            prompt = f"{prompt}\n\n{prompt_extra}"

        payload = {
            "prompt": prompt,
            "image": [hand_url, style_url],
            "size": "2K",
            "watermark": False,
        }
        headers = {
            "Authorization": f"Bearer {settings.PPIO_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            try:
                resp = await client.post(self.ENDPOINT, headers=headers, json=payload)
            except httpx.HTTPError as e:
                raise ImageGenError(f"network error calling Seedream: {e}") from e

            if resp.status_code != 200:
                # 400 InputImageSensitiveContentDetected, 401, 429, 5xx all land here.
                # We do not retry — the caller decides (Step 4.6 routes can fall back to Mock).
                raise ImageGenError(
                    f"Seedream {resp.status_code}: {resp.text[:400]}"
                )

            try:
                data = resp.json()
            except Exception as e:
                raise ImageGenError(f"Seedream returned non-JSON: {resp.text[:300]}") from e

            images = data.get("images") or []
            if not images:
                raise ImageGenError(f"Seedream returned no images: {data}")
            first = images[0]
            img_url = first if isinstance(first, str) else (
                first.get("url") or first.get("download_url")
            )
            if not img_url:
                raise ImageGenError(f"Seedream response missing image URL: {data}")

            try:
                dl = await client.get(img_url, timeout=self.DOWNLOAD_TIMEOUT)
            except httpx.HTTPError as e:
                raise ImageGenError(f"Seedream output download failed: {e}") from e

            STATIC_CACHE.mkdir(parents=True, exist_ok=True)
            # Timestamp-suffixed filename so repeated try-ons of the same style
            # don't overwrite earlier results (each tryons row keeps a stable URL).
            ts = int(time.time() * 1000)
            out = STATIC_CACHE / f"seedream_{user_id}_{style_id}_{ts}.png"
            out.write_bytes(dl.content)
            return f"/static/cache/{out.name}"


def get_image_provider() -> ImageGenProvider:
    """Factory: pick provider per settings.IMAGE_PROVIDER ('mock' | 'seedream')."""
    name = settings.IMAGE_PROVIDER.lower().strip()
    if name == "mock":
        return MockProvider()
    if name == "seedream":
        return SeedreamProvider()
    raise ImageGenError(
        f"unknown IMAGE_PROVIDER: {name!r}; valid values: mock, seedream"
    )
