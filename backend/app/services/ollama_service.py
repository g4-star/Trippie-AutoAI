from __future__ import annotations

import json
from typing import Any

import httpx


OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5:3b"


def generate_json(
    *,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    payload = {
        "model": MODEL,
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

    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
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
