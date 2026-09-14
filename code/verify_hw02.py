import argparse
import csv
import json
import time
from pathlib import Path

from agents_demo import build_graph
import random

SEED = 2383
VERIFY_SEED = 262383

def run_once(graph, case, turn_limit):
    task = (
        f'Given title "{case["title"]}" and content '
        f'"{case["content"]}", produce exactly 3 topical tags '
        "and a one-sentence summary."
    )

    initial_state = {
        "title": case["title"],
        "content": case["content"],
        "email": case["email"],
        "strict": case.get("strict", False),
        "task": task,
        "llm": case.get("model", "qwen3:8b"),
        "turn_count": 0,
        "turn_limit": turn_limit,
    }

    final_state = dict(initial_state)
    nodes = []

    start_time = time.perf_counter()

    for update in graph.stream(
        initial_state,
        config={"recursion_limit": (turn_limit *3 ) + 5},
    ):
        for node_name, node_update in update.items():
            nodes.append(node_name)
            final_state.update(node_update)

    latency_ms = (time.perf_counter() - start_time) * 1000

    reviewer_feedback = final_state.get("reviewer_feedback", {})
    issues = reviewer_feedback.get("data", {}).get("issues", [])
    turn_count = final_state.get("turn_count", 0)

    if not issues:
        if turn_count == 1:
            classification = "valid first attempt"
        elif turn_count == 2:
            classification = "valid after one retry"
        else:
            classification = "valid after 2+ retries"
    else:
        classification = "hit turn ceiling"

    return {
        "turn_limit": turn_limit,
        "turn_count": turn_count,
        "classification": classification,
        "latency_ms": round(latency_ms, 2),
        "issues": issues,
        "nodes": nodes,
        "planner_proposal": final_state.get("planner_proposal"),
        "reviewer_feedback": reviewer_feedback,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default="reports/hw02/cases/schema_input.json",
    )

    parser.add_argument(
        "--runs",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--turn-limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--output",
        default="reports/hw02/raw/schema_validation.json",
    )

    args = parser.parse_args()
    random.seed(SEED)
    case = json.loads(
        Path(args.input).read_text()
    )

    graph = build_graph()
    results = []

    for run_number in range(1, args.runs + 1):
        print(f"Starting run {run_number}/{args.runs}")

        result = run_once(
            graph,
            case,
            args.turn_limit,
        )

        result["run"] = run_number
        results.append(result)

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(results, indent=2)
    )

    csv_path = output_path.with_suffix(".csv")

    with csv_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "run",
                "turn_limit",
                "turn_count",
                "classification",
                "latency_ms",
                "issues",
            ],
        )

        writer.writeheader()

        for result in results:
            writer.writerow({
                "run": result["run"],
                "turn_limit": result["turn_limit"],
                "turn_count": result["turn_count"],
                "classification": result["classification"],
                "latency_ms": result["latency_ms"],
                "issues": json.dumps(result["issues"]),
            })


if __name__ == "__main__":
    main()