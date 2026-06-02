"""Quick connectivity test: tag 1 image with Qwen2.5-VL-72B."""
import base64
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(r"d:\github仓库1\.env")

client = OpenAI(
    api_key=os.environ["PPIO_API_KEY"],
    base_url=os.environ["PPIO_BASE_URL"],
)

img = Path(r"d:\美团AI HACKATHON\dataset\styles\01_enh.png")
b64 = base64.b64encode(img.read_bytes()).decode()

resp = client.chat.completions.create(
    model="qwen/qwen2.5-vl-72b-instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "这张图是什么？用一句话简单描述。"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ],
    }],
    temperature=0.1,
    max_tokens=200,
)
print("model:", resp.model)
print("usage:", resp.usage)
print("content:", resp.choices[0].message.content)
