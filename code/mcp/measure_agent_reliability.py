"""Measure bounded tool-calling reliability across fixed fixture tasks."""

import asyncio
import csv
import json
import os
from collections import Counter
from pathlib import Path

from agent import run_agent, validate_tool_call

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "reports" / "hw07" / "raw"
ATTEMPTS = 21
MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
SEED = 2383

TASKS = [
    {
        "name": "A_search_then_detail",
        "minimum_tool_calls": 2,
        "prompt": (
            "Search for fixtures containing SJSU, then retrieve details for the "
            "first result and give a concise summary."
        ),
    },
    {
        "name": "B_aggregate_then_example",
        "minimum_tool_calls": 2,
        "prompt": (
            "For venue 1, report the aggregate fixture count and total available "
            "slots. Then search for SJSU and name one matching fixture as supporting "
            "evidence."
        ),
    },
    {
        "name": "C_compare_two_fixtures",
        "minimum_tool_calls": 3,
        "prompt": (
            "Search for fixtures containing vs. Use the first two results, retrieve "
            "details for each fixture, then compare their names, teams, available "
            "slots, and venue IDs. Do not answer until you have retrieved both detail "
            "records."
        ),
    },
]


def failure_types(run: dict, minimum_tool_calls: int) -> list[str]:
    failures = []
    for step in run["steps"]:
        for error in step.get("errors", []):
            if error.startswith("Unknown tool:"):
                failures.append("unknown_tool")
            else:
                failures.append("malformed_arguments")
        if step.get("repair", "").startswith("A tool call is still required"):
            failures.append("text_when_tool_required")

    if run["total_tool_calls"] < minimum_tool_calls:
        failures.append("lost_multi_step_chain")
    return sorted(set(failures))


def first_response_is_well_formed(run: dict) -> bool:
    first_step = run["steps"][0]
    calls = first_step.get("tool_calls", [])
    return bool(calls) and all(
        validate_tool_call(call.get("name"), call.get("args")) is None for call in calls
    )


async def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    for attempt_number in range(1, ATTEMPTS + 1):
        task = TASKS[(attempt_number - 1) % len(TASKS)]
        run = await run_agent(
            task["prompt"],
            minimum_tool_calls=task["minimum_tool_calls"],
        )
        failures = failure_types(run, task["minimum_tool_calls"])
        records.append(
            {
                "attempt": attempt_number,
                "task": task["name"],
                "model": MODEL,
                "seed": SEED,
                "before_repair_well_formed": first_response_is_well_formed(run),
                "after_repair_well_formed": run["stop_reason"] == "normal_completion"
                and not failures,
                "failure_types": failures,
                "tool_calls": run["total_tool_calls"],
                "repair_count": run["repair_count"],
                "tokens": run["total_tokens"],
                "latency_ms": run["latency_ms"],
                "stop_reason": run["stop_reason"],
            }
        )
        print(
            f"Attempt {attempt_number}/{ATTEMPTS}: {task['name']} "
            f"({run['stop_reason']}, {run['total_tool_calls']} tool calls)"
        )

    json_path = OUTPUT_DIR / "part2_reliability_attempts.json"
    csv_path = OUTPUT_DIR / "part2_reliability_attempts.csv"
    json_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        for record in records:
            row = record.copy()
            row["failure_types"] = ";".join(row["failure_types"])
            writer.writerow(row)

    failure_counts = Counter(
        failure for record in records for failure in record["failure_types"]
    )
    before_rate = sum(record["before_repair_well_formed"] for record in records) / len(
        records
    )
    after_rate = sum(record["after_repair_well_formed"] for record in records) / len(
        records
    )
    summary = {
        "attempts": len(records),
        "before_repair_well_formed_rate": before_rate,
        "after_repair_well_formed_rate": after_rate,
        "failure_counts": {
            category: failure_counts[category]
            for category in (
                "malformed_arguments",
                "unknown_tool",
                "text_when_tool_required",
                "lost_multi_step_chain",
            )
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
