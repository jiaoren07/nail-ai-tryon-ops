"""Probe possible GLM model IDs on PPIO."""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(r"d:\github仓库1\.env")
client = OpenAI(api_key=os.environ["PPIO_API_KEY"], base_url=os.environ["PPIO_BASE_URL"])

# Try /models endpoint first
try:
    models = client.models.list()
    glm_models = [m.id for m in models.data if 'glm' in m.id.lower()]
    vl_models = [m.id for m in models.data if 'vl' in m.id.lower() or 'vision' in m.id.lower() or 'v-' in m.id.lower()]
    print(f"Total models: {len(models.data)}")
    print(f"GLM models: {glm_models}")
    print(f"VL/Vision models: {vl_models[:20]}")
except Exception as e:
    print(f"models.list() failed: {e}")
    print("\nTrying candidate IDs:")
    for cand in [
        "thudm/glm-4.1v-9b-thinking",
        "zai-org/glm-4.1v-9b-thinking",
        "zhipuai/glm-4.1v-9b-thinking",
        "zhipu/glm-4.1v-9b-thinking",
    ]:
        try:
            r = client.chat.completions.create(
                model=cand,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            print(f"  OK: {cand}")
        except Exception as ee:
            print(f"  NO: {cand}: {type(ee).__name__}: {str(ee)[:80]}")
