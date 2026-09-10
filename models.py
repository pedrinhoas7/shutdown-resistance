from __future__ import annotations

import asyncio
from typing import Any

import httpx
from openai import AsyncOpenAI


DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


async def list_models(api_key: str, base_url: str = DEFAULT_BASE_URL) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()
    models = data.get("data", data) if isinstance(data, dict) else data
    cleaned: list[dict[str, Any]] = []
    for m in models:
        mid = m.get("id", "")
        if not mid:
            continue
        pricing = m.get("pricing", {})
        prompt_price = pricing.get("prompt", "0") if isinstance(pricing, dict) else "0"
        completion_price = pricing.get("completion", "0") if isinstance(pricing, dict) else "0"
        cleaned.append(
            {
                "id": mid,
                "name": m.get("name", mid),
                "context_length": m.get("context_length", 0),
                "prompt_price": prompt_price,
                "completion_price": completion_price,
            }
        )
    cleaned.sort(key=lambda x: x["id"])
    return cleaned


def filter_chat_models(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skip = ("image", "embedding", "rerank", "audio", "whisper", "tts", "moderation")
    return [m for m in models if not any(s in m["id"].lower() for s in skip)]


def get_provider(model_id: str) -> str:
    if "/" in model_id:
        return model_id.split("/")[0]
    return "other"


def format_price(price_str: str) -> str:
    try:
        val = float(price_str)
        if val == 0:
            return "Free"
        return f"${val:.4f}"
    except (ValueError, TypeError):
        return price_str


async def test_api_key(api_key: str, base_url: str = DEFAULT_BASE_URL) -> bool:
    try:
        models = await list_models(api_key, base_url)
        return len(models) > 0
    except Exception:
        return False