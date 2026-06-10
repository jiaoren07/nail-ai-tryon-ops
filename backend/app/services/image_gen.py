"""Try-on image generation: abstract provider + Mock fallback + factory.

Per implementation-plan §3.1:
- ImageGenProvider abstracts away the actual image-gen backend.
- MockProvider copies the style cover to /static/cache/, used as the
  demo safety net when the real API is unavailable.
- get_image_provider() reads settings.IMAGE_PROVIDER ('mock' | 'jimeng')
  and returns the matching instance.
"""
from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from pathlib import Path

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


def get_image_provider() -> ImageGenProvider:
    """Factory: pick provider per settings.IMAGE_PROVIDER ('mock' | 'jimeng')."""
    name = settings.IMAGE_PROVIDER.lower().strip()
    if name == "mock":
        return MockProvider()
    if name == "jimeng":
        raise ImageGenError(
            "JimengProvider not implemented yet (lands in Step 3.2). "
            "Set IMAGE_PROVIDER=mock in .env to use the fallback."
        )
    raise ImageGenError(f"unknown IMAGE_PROVIDER: {name!r}")
