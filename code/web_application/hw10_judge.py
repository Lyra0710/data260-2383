"""Bounded DeepEval GEval helpers for Homework 10."""

from __future__ import annotations

import os

JUDGE_MODEL = os.getenv("HW10_JUDGE_MODEL", "qwen3:8b")
JUDGE_BASE_URL = os.getenv("HW10_JUDGE_BASE_URL", "http://localhost:11434")
JUDGE_TIMEOUT_SECONDS = float(os.getenv("HW10_JUDGE_TIMEOUT_SECONDS", "90"))


def configure_timeouts() -> None:
    """Set DeepEval's documented time limits before importing it."""
    timeout = str(JUDGE_TIMEOUT_SECONDS)
    os.environ.setdefault("DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE", timeout)
    os.environ.setdefault("DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE", timeout)
    os.environ.setdefault("DEEPEVAL_RETRY_MAX_ATTEMPTS", "1")


def score_with_geval(
    question: str, answer: str, name: str, steps: list[str]
) -> tuple[int, str]:
    """Return a 1--5 GEval score and its explanation from local Ollama."""
    configure_timeouts()
    try:
        from deepeval.metrics import GEval
        from deepeval.models import OllamaModel
        from deepeval.test_case import LLMTestCase, SingleTurnParams
    except ImportError as error:
        raise RuntimeError(
            "DeepEval is required. Install the pinned requirements before running HW10."
        ) from error

    judge = OllamaModel(
        model=JUDGE_MODEL,
        base_url=JUDGE_BASE_URL,
        temperature=0,
    )
    metric = GEval(
        name=name,
        evaluation_steps=steps,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT],
        model=judge,
        async_mode=False,
    )
    metric.measure(LLMTestCase(input=question, actual_output=answer))
    score = round(1 + float(metric.score) * 4)
    return max(1, min(5, score)), str(metric.reason or "No reason returned.")
