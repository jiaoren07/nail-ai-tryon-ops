"""
给 15 张男款式图打标（PPIO Qwen2.5-VL-72B）。
复用 auto_tag_styles.py 的核心结构，prompt 调整为男性视角。

输入：d:\\美团AI HACKATHON\\dataset\\styles\\male\\m_*.jpg
输出：d:\\美团AI HACKATHON\\dataset\\styles\\male\\tags_qwen.json

特性：低并发（2）+ 429 自动退避重试 + 增量恢复。
"""
import asyncio
import base64
import json
import os
import random
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIError

load_dotenv(r"d:\github仓库1\.env")

DATASET = Path(r"d:\美团AI HACKATHON\dataset\styles\male")
# Qwen2.5-VL-72B 限流严重，换更宽松的 MoE 模型
MODEL_ID = "qwen/qwen3-vl-30b-a3b-instruct"
OUT_PATH = DATASET / "tags_qwen.json"
CONCURRENCY = 1
MAX_RETRY = 6

PROMPT = """你是美甲款式分析专家。**这张图属于男性美甲款式池**，请按男性视角评估该款式的属性。只输出 JSON，不要任何额外文字或 markdown 代码块。

字段定义：
- gender: "male" / "both"  —— male=明确男性向；both=中性可男可女（不要返回 female，因为本图已属男性款池）
- style_tags: 数组，2-4 个风格词，从以下范围选 [极简, 哑光, 纯色, 商务, 深色系, 个性, 酷炫, 几何, 闪光, 镶钻, 渐变, 复杂图案, 跳色, 透明, 朋克]
- color_main: 主色调的 hex 颜色码，如 "#1A1A1A"
- color_tone: "warm" / "cool" / "neutral"
- length_pref: "short" / "medium" / "long"  —— 视觉上这款适合的指甲长度
- complexity: 1-5 整数  —— 1=极简纯色，5=多元素堆砌
- occasion: 数组，1-3 个场景，从 [日常, 通勤, 商务, 派对, 社交, 个性表达, 婚礼] 选

示例输出：
{"gender":"male","style_tags":["哑光","纯色","商务"],"color_main":"#1A1A1A","color_tone":"cool","length_pref":"short","complexity":1,"occasion":["商务","通勤"]}"""


def extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


async def tag_one(client: AsyncOpenAI, img_path: Path, sem: asyncio.Semaphore) -> dict:
    async with sem:
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        mime = "image/jpeg" if img_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        for attempt in range(1, MAX_RETRY + 1):
            t0 = time.time()
            try:
                resp = await client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        ],
                    }],
                    temperature=0.1,
                    max_tokens=400,
                )
                content = resp.choices[0].message.content or ""
                parsed = extract_json(content)
                elapsed = time.time() - t0
                u = resp.usage
                status = "ok" if parsed else "parse_failed"
                print(f"  [{status}] {img_path.name} attempt={attempt} {elapsed:.1f}s tokens={u.total_tokens}", flush=True)
                return {
                    "status": status,
                    "parsed": parsed,
                    "raw": content if not parsed else None,
                    "elapsed_s": round(elapsed, 2),
                    "tokens": {"in": u.prompt_tokens, "out": u.completion_tokens, "total": u.total_tokens},
                    "attempt": attempt,
                }
            except RateLimitError as e:
                if attempt == MAX_RETRY:
                    print(f"  [429!!] {img_path.name} giving up", flush=True)
                    return {"status": "error", "error": f"RateLimit after {MAX_RETRY}: {str(e)[:100]}"}
                wait = 5 * (2 ** attempt) + random.uniform(0, 3)  # 起步 10s, 然后 20/40/80/160s
                print(f"  [429]  {img_path.name} backoff {wait:.1f}s", flush=True)
                await asyncio.sleep(wait)
            except (APITimeoutError, APIError) as e:
                if attempt == MAX_RETRY:
                    print(f"  [err!!] {img_path.name} giving up: {type(e).__name__}", flush=True)
                    return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:100]}"}
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [err]  {img_path.name} {type(e).__name__} backoff {wait:.1f}s", flush=True)
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"  [FAIL] {img_path.name} {type(e).__name__}: {str(e)[:100]}", flush=True)
                return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:100]}"}


def load_existing() -> dict:
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


async def main():
    images = sorted(DATASET.glob("m_*.jpg"))
    existing = load_existing()
    pending = [p for p in images if not (existing.get(p.name, {}).get("status") == "ok")]

    print(f"Total {len(images)} male styles. Already OK: {len(images) - len(pending)}. Pending: {len(pending)}.", flush=True)
    if not pending:
        print("Nothing to do.", flush=True)
        return

    client = AsyncOpenAI(
        api_key=os.environ["PPIO_API_KEY"],
        base_url=os.environ["PPIO_BASE_URL"],
        timeout=180.0,
    )
    sem = asyncio.Semaphore(CONCURRENCY)
    t0 = time.time()
    tasks = [tag_one(client, p, sem) for p in pending]
    results = await asyncio.gather(*tasks)
    await client.close()

    for img, r in zip(pending, results):
        existing[img.name] = r
    ordered = {k: existing[k] for k in sorted(existing.keys())}
    OUT_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in existing.values() if r["status"] == "ok")
    pf = sum(1 for r in existing.values() if r["status"] == "parse_failed")
    err = sum(1 for r in existing.values() if r["status"] == "error")
    tin = sum(r["tokens"]["in"] for r in existing.values() if "tokens" in r)
    tout = sum(r["tokens"]["out"] for r in existing.values() if "tokens" in r)
    print(f"\n  TOTAL: ok={ok} parse_failed={pf} error={err}", flush=True)
    print(f"  tokens in={tin} out={tout}", flush=True)
    print(f"  wall {time.time()-t0:.1f}s  saved -> {OUT_PATH}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
