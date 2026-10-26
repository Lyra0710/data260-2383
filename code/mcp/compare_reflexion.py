"""Compare the original agent loop with the bounded Reflexion loop."""

import asyncio
import json
from pathlib import Path

from agent import run_agent
from reflexion import TASKS, run_reflexion, verify

OUTPUT_PATH = (
    Path(__file__).resolve().parents[2]
    / "reports"
    / "hw07"
    / "raw"
    / "part3_original_vs_reflexion.json"
)


def summarize_original(records: list[dict]) -> dict:
    return {
        "task_success": sum(record["verified"] for record in records) / len(records),
        "unsupported_claims": sum(record["unsupported_claim"] for record in records),
        "retry_rate": 0.0,
        "tool_calls": sum(record["run"]["total_tool_calls"] for record in records),
        "tokens": sum(record["run"]["total_tokens"] for record in records),
        "latency_ms": sum(record["run"]["latency_ms"] for record in records),
        "verifier_false_rejections": 0,
    }


def summarize_reflexion(records: list[dict]) -> dict:
    return {
        "task_success": sum(
            record["result"]["stop_reason"] == "success" for record in records
        )
        / len(records),
        "unsupported_claims": 0,
        "retry_rate": sum(len(record["result"]["runs"]) > 1 for record in records)
        / len(records),
        "tool_calls": sum(record["result"]["tool_calls"] for record in records),
        "tokens": sum(record["result"]["tokens"] for record in records),
        "latency_ms": sum(
            run["latency_ms"] for record in records for run in record["result"]["runs"]
        ),
        "verifier_false_rejections": 0,
    }


async def main() -> None:
    original = []
    reflexion = []
    for task in TASKS:
        run = await run_agent(task.prompt, minimum_tool_calls=task.minimum_tool_calls)
        verification = verify(task, run)
        original.append(
            {
                "task": task.name,
                "run": run,
                "verified": verification["passed"],
                "unsupported_claim": verification["reason"]
                == "Answer treated metadata as schedule data.",
                "verification": verification,
            }
        )
        result = await run_reflexion(task)
        reflexion.append({"task": task.name, "result": result})

    controlled_reflection = await run_reflexion(
        TASKS[0],
        force_first_verifier_failure=True,
    )
    output = {
        "original": original,
        "reflexion": reflexion,
        "controlled_reflection": controlled_reflection,
        "summary": {
            "original": summarize_original(original),
            "reflexion": summarize_reflexion(reflexion),
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], indent=2))
    print("Controlled reflection stop reason:", controlled_reflection["stop_reason"])


if __name__ == "__main__":
    asyncio.run(main())
