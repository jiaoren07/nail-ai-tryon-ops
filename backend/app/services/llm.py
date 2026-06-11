"""LLM service: thin wrapper over OpenAI SDK pointing at PPIO's compatible API.

Per implementation-plan §3.3:
- Single AsyncOpenAI client, api_key=PPIO_API_KEY, base_url=PPIO_BASE_URL
- gen_text(prompt, model, max_tokens) — short-form generation (e.g. 9
  recommendation reasons batched in Step 4.5)
- gen_text_with_tools(messages, tools, model="strong") — Function Calling
  style chat for the AI assistant (Phase 8)
- Two tier ids resolved from settings:
  - "quick"  -> settings.LLM_QUICK_MODEL  (default qwen/qwen2.5-7b-instruct)
  - "strong" -> settings.LLM_STRONG_MODEL (default deepseek/deepseek-v3.1)
- PPIO_API_KEY empty -> ConfigError, no silent fallback
- 30s per-call timeout
- Exponential backoff on 429 (max 3 retries), matching data-prep/auto_tag_styles.py
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Literal, Sequence

from openai import APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.config import settings

logger = logging.getLogger("nail_demo.llm")

Tier = Literal["quick", "strong"]

TIMEOUT_SECONDS = 60  # plan §3.3 wrote 30, bumped to 60 for safety margin on
                       # strong-tier reasoning models (deepseek-v4-pro). Probing
                       # showed Function Calling latency 1.8-6.1s typical; 60s
                       # absorbs PPIO cold-start / rate-limit queueing without
                       # masking real failures.
MAX_RETRIES = 3


class ConfigError(Exception):
    """Raised when LLM service config (PPIO_API_KEY) is missing."""


class LLMError(Exception):
    """Raised when an LLM call fails after retries or on non-retryable HTTP errors."""


def _client() -> AsyncOpenAI:
    if not settings.PPIO_API_KEY:
        raise ConfigError("PPIO_API_KEY missing")
    return AsyncOpenAI(
        api_key=settings.PPIO_API_KEY,
        base_url=settings.PPIO_BASE_URL,
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
    )


def _model_id(tier: Tier) -> str:
    if tier == "quick":
        return settings.LLM_QUICK_MODEL
    if tier == "strong":
        return settings.LLM_STRONG_MODEL
    raise ValueError(f"unknown model tier: {tier!r}; use 'quick' or 'strong'")


async def _with_retry(call_fn):
    """Run call_fn() with exponential-backoff retry on 429.

    Matches data-prep/auto_tag_styles.py: wait = 2**attempt + random jitter.
    Timeouts and 4xx/5xx other than 429 are raised immediately as LLMError.
    """
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await call_fn()
        except RateLimitError as e:
            last_err = e
            if attempt == MAX_RETRIES:
                break
            wait = (2 ** attempt) + random.uniform(0, 2)
            logger.warning("LLM 429, retry %d/%d after %.1fs", attempt + 1, MAX_RETRIES, wait)
            await asyncio.sleep(wait)
        except APITimeoutError as e:
            raise LLMError(f"LLM timeout after {TIMEOUT_SECONDS}s") from e
        except APIStatusError as e:
            raise LLMError(f"LLM {e.status_code}: {e.message}") from e
    raise LLMError(f"LLM rate-limited after {MAX_RETRIES} retries: {last_err}")


async def gen_text(prompt: str, model: Tier = "quick", max_tokens: int = 200) -> str:
    """Generate a short text completion.

    Returns the trimmed assistant message content. Empty/None content
    is returned as empty string (caller decides whether that's an error).
    """
    client = _client()
    model_id = _model_id(model)

    async def _call():
        return await client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

    resp = await _with_retry(_call)
    return (resp.choices[0].message.content or "").strip()


async def gen_text_with_tools(
    messages: Sequence[dict],
    tools: Sequence[dict],
    model: Tier = "strong",
) -> Any:
    """Function-Calling style chat. Returns the assistant Message object,
    which has `.content` (text) and `.tool_calls` (list or None).
    """
    client = _client()
    model_id = _model_id(model)

    async def _call():
        return await client.chat.completions.create(
            model=model_id,
            messages=list(messages),
            tools=list(tools),
            tool_choice="auto",
        )

    resp = await _with_retry(_call)
    return resp.choices[0].message
