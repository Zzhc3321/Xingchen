from __future__ import annotations

import base64
import http.client
import json
import os
import re
from datetime import datetime
from pathlib import Path

API_HOST = "ai.kegeai.top"
API_PATH = "/v1/images/generations"
MODEL = "gpt-image-2-all"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def slugify(text: str, max_length: int = 40) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_length] or "image"


def get_api_key() -> str:
    api_key = os.getenv("KEGEAI_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 KEGEAI_API_KEY 或 API_KEY")
    return api_key


def save_image(data: dict, prompt: str) -> list[Path]:
    if "data" not in data or not data["data"]:
        raise RuntimeError(f"返回内容中没有图片数据：{data}")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    prompt_tag = slugify(prompt)
    saved_paths: list[Path] = []

    for idx, item in enumerate(data["data"], start=1):
        output_path = ASSETS_DIR / f"{timestamp}_{prompt_tag}_{idx}.png"

        image_bytes = None
        if isinstance(item, dict):
            if item.get("url"):
                import urllib.request

                with urllib.request.urlopen(item["url"]) as resp:
                    image_bytes = resp.read()
            elif item.get("b64_json"):
                image_bytes = base64.b64decode(item["b64_json"])
            elif item.get("base64"):
                image_bytes = base64.b64decode(item["base64"])

        if not image_bytes:
            raise RuntimeError(f"无法识别的返回结构：{data}")

        output_path.write_bytes(image_bytes)
        saved_paths.append(output_path)

    return saved_paths


def main() -> None:
    prompt = "春夏季节的新疆赛里木湖。"

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "3840x2160",
        "quality": "high",
        "format": "jpeg",
    })
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer sk-e0u7J5kHA0IfsngGYpuA25jn94Dyy4smniNmZhuwc4KJ59Nr",
        "Content-Type": "application/json",
    }

    conn = http.client.HTTPSConnection(API_HOST, timeout=120)
    conn.request("POST", API_PATH, payload, headers)
    res = conn.getresponse()
    body = res.read().decode("utf-8")

    if res.status >= 400:
        raise RuntimeError(f"请求失败：{res.status} {res.reason}\n{body}")

    data = json.loads(body)
    saved_paths = save_image(data, prompt)
    for path in saved_paths:
        print(f"图片已保存到: {path.resolve()}")


if __name__ == "__main__":
    main()