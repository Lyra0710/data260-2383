"""Small, dependency-free tracing and metrics helpers for Homework 10."""

from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACE_PATH = REPOSITORY_ROOT / "reports" / "hw10" / "raw" / "traces.jsonl"
_WRITE_LOCK = threading.Lock()


def trace_path() -> Path:
    return Path(os.getenv("HW10_TRACE_PATH", str(DEFAULT_TRACE_PATH)))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_span(
    trace_id: str,
    stage: str,
    started_at: str,
    ended_at: str,
    status: str = "ok",
    error: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Append one complete JSON span and return the record."""
    start = datetime.fromisoformat(started_at).timestamp()
    end = datetime.fromisoformat(ended_at).timestamp()
    record = {
        "trace_id": trace_id,
        "stage": stage,
        "start_time": started_at,
        "end_time": ended_at,
        "duration_ms": round(max(0.0, end - start) * 1000, 2),
        "status": status,
        "error": error,
    }
    if metadata:
        record["metadata"] = metadata
    path = trace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK, path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


@contextmanager
def span(trace_id: str, stage: str, metadata: dict | None = None) -> Iterator[None]:
    started_at = utc_now()
    try:
        yield
    except Exception as error:
        write_span(
            trace_id, stage, started_at, utc_now(), "error", str(error), metadata
        )
        raise
    else:
        write_span(trace_id, stage, started_at, utc_now(), "ok", None, metadata)


def read_spans(path: Path | None = None) -> list[dict]:
    source = path or trace_path()
    if not source.exists():
        return []
    spans = []
    for line in source.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("trace_id"):
            spans.append(value)
    return spans


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    return round(
        ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower), 2
    )


def latency_summary(spans: list[dict], trace_ids: set[str] | None = None) -> dict:
    selected = [s for s in spans if not trace_ids or s["trace_id"] in trace_ids]
    stages = sorted({s["stage"] for s in selected})
    result = {}
    for stage in stages:
        durations = [float(s["duration_ms"]) for s in selected if s["stage"] == stage]
        result[stage] = {
            "p50_ms": percentile(durations, 50),
            "p95_ms": percentile(durations, 95),
            "count": len(durations),
        }
    return result


def trace_for_id(trace_id: str, spans: list[dict] | None = None) -> list[dict]:
    return sorted(
        [
            s
            for s in (spans if spans is not None else read_spans())
            if s.get("trace_id") == trace_id
        ],
        key=lambda item: item.get("start_time", ""),
    )
