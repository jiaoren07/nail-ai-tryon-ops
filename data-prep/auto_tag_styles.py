"""
对 25 张款式图批量打标，对比 Qwen2.5-VL-72B 与 GLM-4.1V-9B-Thinking 的标签质量。

特性：
- 低并发（CONCURRENCY=2）+ 429 自动重试
- 增量恢复：已写入 tags_<label>.json 中 status=ok 的项不会重跑
- GLM-Thinking 给更大的 max_tokens（thinking 阶段会产 reasoning token）

输出：
  dataset/styles/tags_qwen.json
  dataset/styles/tags_glm.json
"""
import asyncio
import base64
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIError

load_dotenv(r"d:\github仓库1\.env")

DATASET = Path(r"d:\美团AI HACKATHON\dataset\styles")
MODELS = [
    # (label, model_id, max_tokens)
    ("qwen", "qwen/qwen2.5-vl-72b-instruct", 400),
    ("glm",  "thudm/glm-4.1v-9b-thinking",   8000),  # Thinking 模型需要大量 reasoning token
]
CONCURRENCY = 2
MAX_RETRY = 5

PROMPT = """你是美甲款式分析专家。这张图展示了一双手戴着某种美甲款式。请仔细观察指甲部位（不要被手或背景分散注意力），按下方 JSON 结构输出。只输出 JSON，不要任何额外文字或 markdown 代码块。

字段定义：
- gender: "female" / "male" / "both"  —— 根据视觉风格判断这款美甲适合哪种性别
- style_tags: 数组，2-4 个风格词，从以下范围选 [法式, 渐变, 纯色, 哑光, 闪光, 镶钻, 复杂图案, 跳色, 透明, 流光, 几何, 卡通, 中式, 韩式, 极简]
- color_main: 主色调的 hex 颜色码，如 "#E8C9A0"
- color_tone: "warm" / "cool" / "neutral"
- length_pref: "short" / "medium" / "long"  —— 视觉上这款适合的指甲长度
- complexity: 1-5 整数  —— 1=极简纯色，5=多元素堆砌
- occasion: 数组，1-3 个场景，从 [日常, 通勤, 约会, 婚礼, 派对, 商务, 旅游] 选

示例输出：
{"gender":"female","style_tags":["法式","渐变"],"color_main":"#E8C9A0","color_tone":"warm","length_pref":"medium","complexity":2,"occasion":["日常","约会"]}"""


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


async def tag_one(client: AsyncOpenAI, model_id: str, img_path: Path, max_tokens: int, sem: asyncio.Semaphore) -> dict:
    async with sem:
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        for attempt in range(1, MAX_RETRY + 1):
            t0 = time.time()
            try:
                resp = await client.chat.completions.create(
                    model=model_id,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }],
                    temperature=0.1,
                    max_tokens=max_tokens,
                )
                content = resp.choices[0].message.content or ""
                parsed = extract_json(content)
                elapsed = time.time() - t0
                u = resp.usage
                status = "ok" if parsed else "parse_failed"
                print(f"  [{status}] {img_path.name} attempt={attempt} {elapsed:.1f}s tokens={u.total_tokens}")
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
                    print(f"  [429!!] {img_path.name} attempt={attempt} giving up")
                    return {"status": "error", "error": f"RateLimitError after {MAX_RETRY} attempts: {str(e)[:100]}"}
                wait = (2 ** attempt) + random.uniform(0, 2)
                print(f"  [429]  {img_path.name} attempt={attempt} backoff {wait:.1f}s")
                await asyncio.sleep(wait)
            except (APITimeoutError, APIError) as e:
                if attempt == MAX_RETRY:
                    print(f"  [err!!] {img_path.name} attempt={attempt} giving up: {type(e).__name__}")
                    return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:100]}"}
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [err]  {img_path.name} attempt={attempt} {type(e).__name__} backoff {wait:.1f}s")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"  [FAIL] {img_path.name} {type(e).__name__}: {str(e)[:100]}")
                return {"status": "error", "error": f"{type(e).__name__}: {str(e)[:100]}"}


def load_existing(out_path: Path) -> dict:
    if out_path.exists():
        try:
            return json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


async def run_label(label: str, model_id: str, max_tokens: int, images: list[Path]):
    out_path = DATASET / f"tags_{label}.json"
    existing = load_existing(out_path)

    pending = []
    for img in images:
        prev = existing.get(img.name)
        if prev and prev.get("status") == "ok":
            continue
        pending.append(img)

    print(f"\n=== {label}: {model_id} ===")
    print(f"  already OK: {len(images) - len(pending)} | pending: {len(pending)}")
    if not pending:
        print(f"  nothing to do.")
        return

    client = AsyncOpenAI(
        api_key=os.environ["PPIO_API_KEY"],
        base_url=os.environ["PPIO_BASE_URL"],
        timeout=180.0,
    )
    sem = asyncio.Semaphore(CONCURRENCY)
    t0 = time.time()
    tasks = [tag_one(client, model_id, p, max_tokens, sem) for p in pending]
    results = await asyncio.gather(*tasks)
    await client.close()

    for img, r in zip(pending, results):
        existing[img.name] = r
    # sort keys
    ordered = {k: existing[k] for k in sorted(existing.keys())}
    out_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in existing.values() if r["status"] == "ok")
    parse_fail = sum(1 for r in existing.values() if r["status"] == "parse_failed")
    err = sum(1 for r in existing.values() if r["status"] == "error")
    tin = sum(r["tokens"]["in"] for r in existing.values() if "tokens" in r)
    tout = sum(r["tokens"]["out"] for r in existing.values() if "tokens" in r)
    print(f"\n  TOTAL: ok={ok} parse_failed={parse_fail} error={err}")
    print(f"  tokens in={tin} out={tout} sum={tin+tout}")
    print(f"  wall {time.time()-t0:.1f}s  saved -> {out_path}")


async def main():
    images = sorted(DATASET.glob("*_enh.png"))
    print(f"Tagging {len(images)} images.")
    for label, model_id, max_tokens in MODELS:
        await run_label(label, model_id, max_tokens, images)


if __name__ == "__main__":
    asyncio.run(main())
