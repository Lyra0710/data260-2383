"""Streamlit operations and evidence dashboard for Homework 10."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from hw10_observability import read_spans, trace_for_id

ROOT = Path(__file__).resolve().parents[2]
HW10_RAW = ROOT / "reports" / "hw10" / "raw"
METRICS_PATH = ROOT / "reports" / "hw09" / "raw" / "chat_metrics.jsonl"


@st.cache_data
def load_json(path: str) -> dict:
    source = Path(path)
    if not source.exists():
        return {}
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@st.cache_data
def load_jsonl(path: str) -> list[dict]:
    source = Path(path)
    if not source.exists():
        return []
    rows = []
    for line in source.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def metric_rows(spans: list[dict], metrics: list[dict]) -> list[dict]:
    trace_ids = {span["trace_id"] for span in spans}
    cache_spans = [span for span in spans if span.get("stage") == "cache_lookup"]
    hits = sum(span.get("metadata", {}).get("path") == "hit" for span in cache_spans)
    misses = sum(span.get("metadata", {}).get("path") == "miss" for span in cache_spans)
    errors = sum(span.get("status") == "error" for span in spans)
    latencies = [
        float(row["latency_ms"]) for row in metrics if row.get("latency_ms") is not None
    ]
    request_count = len(trace_ids) or len(metrics)
    trace_source = "HW10 trace JSONL; all records currently present"
    cache_source = "HW10 cache_lookup spans"
    return [
        {
            "metric": "Recent requests",
            "value": str(request_count),
            "source": trace_source,
        },
        {"metric": "Cache hits", "value": str(hits), "source": cache_source},
        {"metric": "Cache misses", "value": str(misses), "source": cache_source},
        {
            "metric": "Cache hit rate",
            "value": f"{hits / (hits + misses) * 100:.1f}%" if hits + misses else "n/a",
            "source": cache_source,
        },
        {
            "metric": "Error rate",
            "value": f"{errors / len(spans) * 100:.1f}%" if spans else "n/a",
            "source": "HW10 trace spans",
        },
        {
            "metric": "End-to-end latency",
            "value": f"{sum(latencies) / len(latencies):.2f} ms"
            if latencies
            else "n/a",
            "source": "HW9 chat_metrics.jsonl; all records currently present",
        },
    ]


def show_summary() -> None:
    st.header("System summary")
    spans = read_spans()
    metrics = load_jsonl(str(METRICS_PATH))
    st.dataframe(
        pd.DataFrame(metric_rows(spans, metrics)),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Metrics use all available local evidence records; each row identifies "
        "its data source and window."
    )


def show_evaluation() -> None:
    st.header("Evaluation results")
    validation = load_json(str(HW10_RAW / "judge_validation.json"))
    if validation:
        st.subheader("Judge validation")
        summary_keys = (
            "case_count",
            "judge_model",
            "spearman_correlation",
            "mean_absolute_difference",
            "repeatability",
        )
        st.json({key: validation.get(key) for key in summary_keys})
        st.dataframe(
            pd.DataFrame(validation.get("raw", [])),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No judge-validation results found.")

    pipeline = load_jsonl(str(HW10_RAW / "pipeline_evaluations.jsonl"))
    st.subheader("Planner / Writer / Reviewer evaluation")
    if pipeline:
        rows = [row.get("evaluation", row) for row in pipeline]
        st.dataframe(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Interpretation: compare plan, Writer, and final scores; the "
            "improvement field may be negative."
        )
    else:
        st.info("No pipeline evaluation messages have been persisted yet.")


def show_trace_lookup() -> None:
    st.header("Trace lookup")
    spans = read_spans()
    default_trace = spans[-1]["trace_id"] if spans else ""
    trace_id = st.text_input("trace_id", value=default_trace)
    rows = trace_for_id(trace_id, spans) if trace_id else []
    if not rows:
        st.info("Enter a trace_id with recorded spans.")
        return
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


st.set_page_config(page_title="HW10 Operations Dashboard", layout="wide")
st.title("Homework 10 Operations Dashboard")
page = st.sidebar.radio("Page", ("Summary", "Evaluation", "Trace lookup"))
if page == "Summary":
    show_summary()
elif page == "Evaluation":
    show_evaluation()
else:
    show_trace_lookup()
