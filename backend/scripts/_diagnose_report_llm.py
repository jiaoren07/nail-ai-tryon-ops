"""One-off: diagnose empty report content from the strong model.

Calls the exact daily-report prompt and dumps the raw response fields:
finish_reason, content length, reasoning_content length, usage.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


async def main() -> None:
    from app.db import async_session_maker
    from app.services import report
    from app.services.llm import _client, _model_id

    async with async_session_maker() as db:
        start, end = report.compute_period("daily")
        stats = await report._aggregate_stats(db, "daily", start, end)
    prompt = report._build_prompt("daily", stats)
    print(f"prompt chars: {len(prompt)}")

    client = _client()
    for max_tokens in (2000, 4000):
        resp = await client.chat.completions.create(
            model=_model_id("strong"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        choice = resp.choices[0]
        msg = choice.message
        content = msg.content or ""
        reasoning = getattr(msg, "reasoning_content", None) or ""
        usage = resp.usage
        print(f"\n--- max_tokens={max_tokens} ---")
        print(f"finish_reason : {choice.finish_reason}")
        print(f"content len   : {len(content)}")
        print(f"reasoning len : {len(reasoning)}")
        print(f"usage         : prompt={usage.prompt_tokens} completion={usage.completion_tokens}")
        print(f"content head  : {content[:120]!r}")
        if not content and reasoning:
            print(f"reasoning head: {reasoning[:120]!r}")
        await asyncio.sleep(15)


if __name__ == "__main__":
    asyncio.run(main())
