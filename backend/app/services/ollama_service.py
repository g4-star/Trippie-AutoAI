from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings


def generate_json(
    *,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    }

    headers = {}

    if settings.ollama_api_key:
        headers["Authorization"] = (
            f"Bearer {settings.ollama_api_key}"
        )

    response = httpx.post(
        f"{settings.ollama_url.rstrip('/')}/api/chat",
        json=payload,
        headers=headers,
        timeout=httpx.Timeout(300.0, connect=10.0),
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data.get("message", {})
        .get("content", "")
        .strip()
    )

    if not content:
        raise RuntimeError(
            "Ollama returned an empty response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Ollama returned invalid JSON: {content}"
        ) from error

    if not isinstance(result, dict):
        raise RuntimeError(
            "Ollama response was not a JSON object."
        )

    return result
