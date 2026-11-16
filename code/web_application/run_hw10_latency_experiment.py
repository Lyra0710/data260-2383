"""Measure cache-miss latency for the Homework 10 Kafka pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from hw10_observability import percentile, read_spans
from run_hw10_pipeline import QUESTION, run

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "reports" / "hw10" / "raw" / "latency_experiment.json"
STAGES = ("cache_lookup", "planner", "writer", "reviewer", "evaluation")
TRACE_ORDER = ("cache_lookup", "inbox", "planner", "writer", "reviewer", "evaluation")


def timestamp(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


def trace_metrics(trace_id: str, spans: list[dict]) -> dict | None:
    """Calculate stage, queue-wait, and end-to-end durations for one trace."""
    trace_spans = {
        span["stage"]: span for span in spans if span["trace_id"] == trace_id
    }
    if not all(stage in trace_spans for stage in TRACE_ORDER):
        return None

    durations = {stage: float(trace_spans[stage]["duration_ms"]) for stage in STAGES}
    queue_wait_ms = 0.0
    for earlier, later in zip(TRACE_ORDER, TRACE_ORDER[1:]):
        gap = timestamp(trace_spans[later]["start_time"]) - timestamp(
            trace_spans[earlier]["end_time"]
        )
        queue_wait_ms += max(0.0, gap * 1000)

    end_to_end_ms = (
        timestamp(trace_spans["evaluation"]["end_time"])
        - timestamp(trace_spans["cache_lookup"]["start_time"])
    ) * 1000
    return {
        "trace_id": trace_id,
        **durations,
        "queue_wait_ms": round(queue_wait_ms, 2),
        "end_to_end_ms": round(end_to_end_ms, 2),
    }


def summarize(records: list[dict]) -> dict:
    """Return the required p50, p95, and latency shares."""
    keys = (*STAGES, "queue_wait_ms", "end_to_end_ms")
    summary = {}
    total_end_to_end = sum(record["end_to_end_ms"] for record in records)
    for key in keys:
        values = [record[key] for record in records]
        label = key.removesuffix("_ms")
        summary[label] = {
            "p50_ms": percentile(values, 50),
            "p95_ms": percentile(values, 95),
            "percent_of_end_to_end": round(sum(values) / total_end_to_end * 100, 2),
        }

    dominant_stage = max(
        (*STAGES, "queue_wait_ms"),
        key=lambda key: sum(record[key] for record in records),
    ).removesuffix("_ms")
    return {"stages": summary, "dominant_stage": dominant_stage}


async def run_experiment(count: int) -> dict:
    """Run `count` isolated cache misses and save their latency summary."""
    trace_ids = []
    evaluation_modes = []
    for number in range(1, count + 1):
        scope = f"hw10-latency-{uuid.uuid4()}"
        question = f"{QUESTION} This is latency experiment request {number}."
        result = await run(False, question, scope)
        if result["path"] != "cache_miss":
            raise RuntimeError(f"Expected a cache miss for request {number}")
        trace_ids.append(result["trace_id"])
        evaluation_modes.append(result["evaluation"]["evaluation"].get("mode", "full"))

    spans = read_spans()
    records = [trace_metrics(trace_id, spans) for trace_id in trace_ids]
    complete_records = [record for record in records if record is not None]
    if len(complete_records) != count:
        raise RuntimeError("One or more traces did not contain every required stage")

    requested_mode = os.getenv("HW10_EVALUATION_MODE", "full")
    observed_modes = sorted(set(evaluation_modes))
    if observed_modes != [requested_mode]:
        raise RuntimeError(
            f"Requested evaluator mode {requested_mode!r}, "
            f"but observed {observed_modes!r}"
        )

    result = {
        "request_count": count,
        "cache_path": "miss",
        "evaluation_mode": requested_mode,
        "observed_evaluation_modes": observed_modes,
        "trace_ids": trace_ids,
        "summary": summarize(complete_records),
        "records": complete_records,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.count < 1:
        raise ValueError("--count must be at least 1")
    print(json.dumps(asyncio.run(run_experiment(arguments.count)), indent=2))
