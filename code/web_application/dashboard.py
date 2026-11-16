"""Streamlit operations and evidence dashboard for Homework 10."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from hw10_observability import read_spans, trace_for_id

ROOT = Path(__file__).resolve().parents[2]
HW10_RAW = ROOT / "reports" / "hw10" / "raw"


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


def trace_window(spans: list[dict]) -> str:
    timestamps = sorted(span.get("start_time", "") for span in spans)
    if not timestamps:
        return "no trace records"
    return f"{timestamps[0]} to {timestamps[-1]}"


def metric_rows(spans: list[dict], latency: dict) -> list[dict]:
    trace_ids = {span["trace_id"] for span in spans}
    cache_spans = [span for span in spans if span.get("stage") == "cache_lookup"]
    hits = sum(span.get("metadata", {}).get("path") == "hit" for span in cache_spans)
    misses = sum(span.get("metadata", {}).get("path") == "miss" for span in cache_spans)
    error_trace_ids = {
        span["trace_id"] for span in spans if span.get("status") == "error"
    }
    stages = latency.get("summary", {}).get("stages", {})
    end_to_end = stages.get("end_to_end", {})
    trace_source = f"HW10 traces; {trace_window(spans)}"
    cache_source = f"HW10 cache_lookup spans; {trace_window(cache_spans)}"
    latency_source = (
        "HW10 50-request cache-miss experiment; "
        f"evaluator mode={latency.get('evaluation_mode', 'unknown')}"
    )
    return [
        {
            "metric": "Recent requests",
            "value": str(len(trace_ids)),
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
            "value": f"{len(error_trace_ids) / len(trace_ids) * 100:.1f}%"
            if trace_ids
            else "n/a",
            "source": trace_source,
        },
        {
            "metric": "Cache-miss end-to-end latency",
            "value": (
                f"p50 {end_to_end.get('p50_ms')} ms; "
                f"p95 {end_to_end.get('p95_ms')} ms"
                if end_to_end
                else "n/a"
            ),
            "source": latency_source,
        },
    ]


def show_summary() -> None:
    st.header("System summary")
    spans = read_spans()
    latency = load_json(str(HW10_RAW / "latency_experiment.json"))
    st.dataframe(
        pd.DataFrame(metric_rows(spans, latency)),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Each metric identifies its local evidence source and time window. "
        "Cache-hit latency remains separate from the 50-request cache-miss experiment."
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
        scored_rows = [row for row in rows if "final_score" in row]
        if scored_rows:
            latest = scored_rows[-1]
            st.caption(
                "Latest scored request: Planner "
                f"{latest['plan_score']}/5, Writer {latest['writer_score']}/5, "
                f"Reviewer {latest['final_score']}/5. "
                f"{latest['improvement_interpretation']}"
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
    display_rows = []
    for row in rows:
        display_row = row.copy()
        display_row["cache_path"] = row.get("metadata", {}).get("path", "n/a")
        display_rows.append(display_row)
    st.dataframe(pd.DataFrame(display_rows), width="stretch", hide_index=True)


st.set_page_config(page_title="HW10 Operations Dashboard", layout="wide")
st.title("Homework 10 Operations Dashboard")
page = st.sidebar.radio("Page", ("Summary", "Evaluation", "Trace lookup"))
if page == "Summary":
    show_summary()
elif page == "Evaluation":
    show_evaluation()
else:
    show_trace_lookup()
