"""One-off PPIO quick-tier latency probe — diagnostic only."""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import llm  # noqa: E402


async def go():
    print("=== single call ===")
    t0 = time.perf_counter()
    txt = await llm.gen_text("用一句话介绍美甲，限25字内。", model="quick", max_tokens=80)
    print(f"single elapsed={time.perf_counter()-t0:.2f}s len={len(txt)} text={txt!r}")

    print("\n=== 9 parallel calls ===")
    t0 = time.perf_counter()
    res = await asyncio.gather(*[
        llm.gen_text(f"请用一句话介绍美甲款式{i}", model="quick", max_tokens=40)
        for i in range(9)
    ], return_exceptions=True)
    elapsed = time.perf_counter() - t0
    succ = sum(1 for r in res if isinstance(r, str))
    print(f"9-parallel elapsed={elapsed:.2f}s succ={succ}/9")
    for i, r in enumerate(res):
        if isinstance(r, str):
            print(f"  #{i+1} ok len={len(r)} {r[:40]!r}")
        else:
            print(f"  #{i+1} ERR {type(r).__name__}: {r}")


if __name__ == "__main__":
    asyncio.run(go())
