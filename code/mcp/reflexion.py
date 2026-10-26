"""Bounded Reflexion wrapper for the fixed fixture verification tasks."""

import json
from dataclasses import dataclass
from pathlib import Path

from agent import run_agent

MAX_RETRIES = 2
MAX_TOOL_CALLS = 12
MAX_TOKENS = 6_000
REFLECTION_LOG = (
    Path(__file__).resolve().parents[2]
    / "reports"
    / "hw07"
    / "raw"
    / "part3_reflections.jsonl"
)


@dataclass(frozen=True)
class VerificationTask:
    name: str
    prompt: str
    minimum_tool_calls: int


TASKS = (
    VerificationTask(
        "A_search_then_detail",
        "Search for fixtures containing SJSU, then retrieve details for the "
        "first result and give a concise summary.",
        2,
    ),
    VerificationTask(
        "B_aggregate_then_example",
        "For venue 1, report the aggregate fixture count and total available "
        "slots. Then search for SJSU and name one matching fixture as supporting "
        "evidence.",
        2,
    ),
    VerificationTask(
        "C_compare_two_fixtures",
        "Search for fixtures containing vs. Use the first two results, retrieve "
        "details for each fixture, then compare their names, teams, available "
        "slots, and venue IDs. Do not answer until you have retrieved both detail "
        "records.",
        3,
    ),
)


def tool_names(run: dict) -> list[str]:
    return [
        call["name"] for step in run["steps"] for call in step.get("tool_calls", [])
    ]


def verify(task: VerificationTask, run: dict) -> dict:
    answer = (run["final_answer"] or "").casefold()
    names = tool_names(run)
    if run["stop_reason"] != "normal_completion":
        return {"passed": False, "reason": "Agent did not complete normally."}
    if run["total_tool_calls"] < task.minimum_tool_calls:
        return {"passed": False, "reason": "Required tool-call count was not reached."}
    if "scheduled" in answer or "created_at" in answer:
        return {"passed": False, "reason": "Answer treated metadata as schedule data."}

    expected = {
        "A_search_then_detail": (
            ["search_fixtures", "fixture_details"],
            ["sjsu vs stanford", "15"],
        ),
        "B_aggregate_then_example": (
            ["venue_fixture_summary", "search_fixtures"],
            ["1", "15", "sjsu vs stanford"],
        ),
        "C_compare_two_fixtures": (
            ["search_fixtures", "fixture_details", "fixture_details"],
            ["sjsu vs stanford", "round 2", "15", "12"],
        ),
    }[task.name]
    expected_tools, expected_terms = expected
    if names != expected_tools:
        return {"passed": False, "reason": f"Unexpected tool sequence: {names}."}
    if any(term not in answer for term in expected_terms):
        return {"passed": False, "reason": "Answer omitted required verified facts."}
    return {"passed": True, "reason": "Deterministic checks passed."}


def reflection_record(
    task: VerificationTask, attempt: int, run: dict, reason: str
) -> dict:
    return {
        "task": task.name,
        "attempt": attempt,
        "evidence": {
            "tool_names": tool_names(run),
            "stop_reason": run["stop_reason"],
            "final_answer": run["final_answer"],
        },
        "failure": reason,
        "strategy": "Follow the required tool sequence and state only verified facts.",
    }


async def run_reflexion(
    task: VerificationTask,
    *,
    force_first_verifier_failure: bool = False,
) -> dict:
    runs = []
    reflections = []
    used_tools = 0
    used_tokens = 0
    retry_prompt = task.prompt
    stop_reason = "human_review"

    for attempt in range(MAX_RETRIES + 1):
        remaining_tools = MAX_TOOL_CALLS - used_tools
        remaining_tokens = MAX_TOKENS - used_tokens
        if remaining_tools <= 0 or remaining_tokens <= 0:
            stop_reason = "budget_exhausted"
            break

        run = await run_agent(
            retry_prompt,
            minimum_tool_calls=task.minimum_tool_calls,
            max_steps=task.minimum_tool_calls + 2,
            max_tool_calls=remaining_tools,
            max_total_tokens=remaining_tokens,
        )
        runs.append(run)
        used_tools += run["total_tool_calls"]
        used_tokens += run["total_tokens"]

        if run["stop_reason"] in {"tool_budget", "token_budget"}:
            stop_reason = "budget_exhausted"
            break

        result = verify(task, run)
        if force_first_verifier_failure and attempt == 0:
            result = {
                "passed": False,
                "reason": "Controlled test-only verifier failure for retry coverage.",
            }
        if result["passed"]:
            stop_reason = "success"
            break

        if attempt == MAX_RETRIES:
            stop_reason = "human_review"
            break

        reflection = reflection_record(task, attempt + 1, run, result["reason"])
        reflections.append(reflection)
        retry_prompt = (
            f"{task.prompt}\n\n"
            f"Previous attempt failed verification: {reflection['failure']} "
            f"Strategy: {reflection['strategy']}"
        )

    output = {
        "task": task.name,
        "runs": runs,
        "reflections": reflections,
        "stop_reason": stop_reason,
        "tool_calls": used_tools,
        "tokens": used_tokens,
    }
    if reflections:
        REFLECTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with REFLECTION_LOG.open("a", encoding="utf-8") as file:
            for reflection in reflections:
                file.write(json.dumps(reflection) + "\n")
    return output
