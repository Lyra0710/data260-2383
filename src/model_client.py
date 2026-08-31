"""Reusable adapter for local Ollama model calls."""

from typing import Any

from langchain_ollama import ChatOllama


def complete(
    messages: list,
    tools: list | None = None,
    *,
    model: str = "qwen3:8b",
    temperature: float = 0.0,
) -> Any:
    """Send messages to Ollama and return the model response."""

    chat_model = ChatOllama(
        model=model,
        temperature=temperature,
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