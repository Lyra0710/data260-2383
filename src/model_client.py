"""Reusable adapter for local Ollama model calls."""

import math
from typing import Any

from langchain_ollama import ChatOllama


def complete(
    messages: list,
    tools: list | None = None,
    *,
    model: str = "qwen3:8b",
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> Any:
    """Send messages to Ollama and return the model response."""

    chat_model = ChatOllama(
        model=model,
        temperature=temperature,
        reasoning=False,
        num_predict=max_tokens,
    )

    if tools:
        chat_model = chat_model.bind_tools(tools)

    return chat_model.invoke(messages)


def get_token_usage(response: Any) -> dict[str, int]:
    """Extract token counts from a ChatOllama response."""

    usage = response.usage_metadata or {}

    input_tokens = usage.get(
        "input_tokens",
        response.response_metadata.get("prompt_eval_count", 0),
    )

    output_tokens = usage.get(
        "output_tokens",
        response.response_metadata.get("eval_count", 0),
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }


def count_text_tokens(text: str, *, model: str = "qwen3:8b") -> int:
    """Estimate component tokens when the local model exposes only total usage."""

    del model
    return math.ceil(len(text) / 4) if text else 0
