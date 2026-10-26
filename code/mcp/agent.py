"""A bounded tool-calling agent for the fixtures domain."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import domain_server  # noqa: E402, I001
from src.model_client import complete, get_token_usage  # noqa: E402, I001


load_dotenv(REPO_ROOT / ".env")

MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
MAX_STEPS = 6
MAX_REPAIRS = 1
LOG_FILE = REPO_ROOT / "reports" / "hw07" / "raw" / "agent_runs.jsonl"

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_fixtures",
            "description": "Search fixtures by name, teams, or fixture code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 25},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_details",
            "description": "Return fixture details for one numeric fixture ID.",
            "parameters": {
                "type": "object",
                "properties": {"fixture_id": {"type": "integer", "minimum": 1}},
                "required": ["fixture_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "venue_fixture_summary",
            "description": "Return an aggregate fixture summary for one venue ID.",
            "parameters": {
                "type": "object",
                "properties": {"venue_id": {"type": "integer", "minimum": 1}},
                "required": ["venue_id"],
                "additionalProperties": False,
            },
        },
    },
]


def validate_tool_call(name: Any, arguments: Any) -> str | None:
    if name not in {"search_fixtures", "fixture_details", "venue_fixture_summary"}:
        return f"Unknown tool: {name}."
    if not isinstance(arguments, dict):
        return "Tool arguments must be a JSON object."

    allowed_keys = {
        "search_fixtures": {"query", "limit"},
        "fixture_details": {"fixture_id"},
        "venue_fixture_summary": {"venue_id"},
    }[name]
    if set(arguments) - allowed_keys:
        return f"{name} received unsupported argument names."

    required_key = {
        "search_fixtures": "query",
        "fixture_details": "fixture_id",
        "venue_fixture_summary": "venue_id",
    }[name]
    if required_key not in arguments:
        return f"{name} requires {required_key}."

    if name == "search_fixtures":
        if not isinstance(arguments["query"], str) or not arguments["query"].strip():
            return "search_fixtures.query must be a non-empty string."
        limit = arguments.get("limit", 10)
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 25
        ):
            return "search_fixtures.limit must be an integer from 1 through 25."
    else:
        value = arguments[required_key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            return f"{name}.{required_key} must be a positive integer."
    return None


def model_tool_result(result: str) -> str:
    """Remove timestamp metadata that is not a fixture schedule."""

    def remove_metadata(value: Any) -> Any:
        if isinstance(value, list):
            return [remove_metadata(item) for item in value]
        if isinstance(value, dict):
            return {
                key: remove_metadata(item)
                for key, item in value.items()
                if key not in {"created_at", "updated_at"}
            }
        return value

    return json.dumps(remove_metadata(json.loads(result)))


async def ask_model(messages: list) -> Any:
    return await asyncio.to_thread(
        complete,
        messages,
        TOOL_SCHEMAS,
        model=MODEL,
        temperature=0.0,
    )


async def run_agent(
    user_input: str,
    *,
    minimum_tool_calls: int = 0,
    max_steps: int = MAX_STEPS,
    model_call=ask_model,
) -> dict:
    messages = [
        SystemMessage(
            content=(
                "You are a fixtures assistant. Use the available tools for factual "
                "fixture questions. Do not invent tool results. After using tools, "
                "give a concise answer based only on their results. Do not treat "
                "created_at or updated_at as a scheduled date, and do not infer a "
                "venue name from venue_id."
            )
        ),
        HumanMessage(content=user_input),
    ]
    steps = []
    repair_count = 0
    tool_calls = 0
    total_tokens = 0
    final_answer = None
    stop_reason = "max_steps"
    started_at = perf_counter()

    for step_number in range(1, max_steps + 1):
        response = await model_call(messages)
        usage = get_token_usage(response)
        total_tokens += usage["total_tokens"]
        calls = getattr(response, "tool_calls", []) or []
        step_record = {
            "step": step_number,
            "model_content": str(response.content),
            "tool_calls": calls,
            "tokens": usage,
        }

        if not calls:
            if tool_calls < minimum_tool_calls:
                problem = (
                    f"A tool call is still required. Complete at least "
                    f"{minimum_tool_calls} tool calls before answering."
                )
            else:
                final_answer = str(response.content).strip()
                stop_reason = "normal_completion"
                steps.append(step_record)
                break

            if repair_count >= MAX_REPAIRS:
                step_record["error"] = problem
                steps.append(step_record)
                stop_reason = "repair_limit"
                break
            repair_count += 1
            step_record["repair"] = problem
            steps.append(step_record)
            messages.extend([response, HumanMessage(content=problem)])
            continue

        messages.append(response)
        invalid_call = False
        for call in calls:
            name = call.get("name")
            arguments = call.get("args")
            error = validate_tool_call(name, arguments)
            if error:
                step_record.setdefault("errors", []).append(error)
                invalid_call = True
                messages.append(
                    ToolMessage(
                        content=json.dumps({"ok": False, "error": error}),
                        tool_call_id=call["id"],
                    )
                )
                continue

            result = await domain_server.execute_tool(name, arguments)
            tool_calls += 1
            step_record.setdefault("results", []).append(
                {"name": name, "arguments": arguments, "result": json.loads(result)}
            )
            messages.append(
                ToolMessage(
                    content=model_tool_result(result),
                    tool_call_id=call["id"],
                )
            )

        steps.append(step_record)
        if invalid_call:
            problem = "; ".join(step_record["errors"])
            if repair_count >= MAX_REPAIRS:
                stop_reason = "repair_limit"
                break
            repair_count += 1
            messages.append(HumanMessage(content=f"Repair the tool call: {problem}"))

    run_record = {
        "user_input": user_input,
        "steps": steps,
        "final_answer": final_answer,
        "stop_reason": stop_reason,
        "total_tool_calls": tool_calls,
        "repair_count": repair_count,
        "total_tokens": total_tokens,
        "latency_ms": round((perf_counter() - started_at) * 1000, 2),
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(run_record) + "\n")
    return run_record


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("user_input", nargs="+")
    parser.add_argument("--minimum-tool-calls", type=int, default=0)
    arguments = parser.parse_args()
    user_input = " ".join(arguments.user_input)
    if not user_input:
        print("Provide a user request.")
        return
    result = await run_agent(
        user_input,
        minimum_tool_calls=arguments.minimum_tool_calls,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
