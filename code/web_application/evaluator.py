"""Bounded Planner/Writer/Reviewer evaluation for Homework 10.

DeepEval is used when installed and explicitly selected.  The default local
judge is deterministic so an unavailable model cannot hang an evaluation run.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from hw10_judge import score_with_geval

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class EvaluationResult:
    correlation_id: str
    plan_score: int
    plan_reason: str
    writer_score: int
    writer_reason: str
    final_score: int
    final_reason: str
    draft_score: int
    improvement: int
    improvement_interpretation: str
    trace_id: str
    final_answer: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


PLAN_STEPS = [
    "Decide whether the plan directly addresses the user's question.",
    "Check whether the plan has practical, ordered steps a league manager can use.",
    "Assign 1 for very poor and 5 for excellent plan quality.",
]
HELPFULNESS_STEPS = [
    "Decide whether the answer directly addresses the user's question.",
    "Check accuracy, relevance, completeness, and practical usefulness.",
    "Assign 1 for very poor and 5 for excellent helpfulness.",
]


def evaluate_messages(
    plan_message: dict, draft_message: dict, final_message: dict
) -> dict:
    """Evaluate already-linked messages; all outputs stay on the 1-5 scale."""
    correlation_id = str(
        final_message.get("correlation_id") or plan_message.get("correlation_id") or ""
    )
    if not correlation_id:
        raise ValueError("messages must contain correlation_id")
    question = str(draft_message.get("question") or plan_message.get("question") or "")
    plan_score, plan_reason = score_with_geval(
        question, str(plan_message.get("plan", "")), "Plan Quality", PLAN_STEPS
    )
    draft_score, draft_reason = score_with_geval(
        question,
        str(draft_message.get("draft", "")),
        "Writer Helpfulness",
        HELPFULNESS_STEPS,
    )
    final_score, final_reason = score_with_geval(
        question,
        str(final_message.get("answer", "")),
        "Final Answer Helpfulness",
        HELPFULNESS_STEPS,
    )
    improvement = final_score - draft_score
    interpretation = (
        "improved"
        if improvement > 0
        else "unchanged"
        if improvement == 0
        else "regressed"
    )
    return EvaluationResult(
        correlation_id=correlation_id,
        plan_score=plan_score,
        plan_reason=plan_reason,
        writer_score=draft_score,
        writer_reason=draft_reason,
        final_score=final_score,
        final_reason=final_reason,
        draft_score=draft_score,
        improvement=improvement,
        improvement_interpretation=(
            f"Final answer {interpretation} relative to the draft "
            f"({draft_score} to {final_score})."
        ),
        trace_id=str(final_message.get("trace_id", correlation_id)),
        final_answer=str(final_message.get("answer", "")),
    ).as_dict()


def load_linked_messages(messages: list[dict]) -> dict[str, dict]:
    grouped: dict[str, dict] = {}
    for message in messages:
        correlation_id = message.get("correlation_id")
        if not correlation_id:
            continue
        entry = grouped.setdefault(str(correlation_id), {})
        if "plan" in message:
            entry["plan"] = message
        if "draft" in message:
            entry["draft"] = message
        if "answer" in message:
            entry["final"] = message
    return {
        key: value
        for key, value in grouped.items()
        if {"plan", "draft", "final"} <= value.keys()
    }


def evaluate_cases(cases_path: Path, labels_path: Path, repeats: int = 3) -> dict:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    labels = {
        row["case_id"]: int(row["human_label"])
        for row in csv.DictReader(labels_path.open(encoding="utf-8"))
    }
    runs = []
    for _ in range(repeats):
        runs.append(
            [
                score_with_geval(
                    case["question"],
                    case["draft"],
                    "Writer Helpfulness",
                    HELPFULNESS_STEPS,
                )[0]
                for case in cases
            ]
        )
    judge_scores = runs[0]
    human_scores = [labels[case["case_id"]] for case in cases]
    differences = [abs(a - b) for a, b in zip(judge_scores, human_scores)]
    try:
        from scipy.stats import spearmanr

        correlation = float(spearmanr(human_scores, judge_scores).statistic)
    except Exception:
        correlation = None
    changes = [
        abs(run[i] - judge_scores[i])
        for run in runs[1:]
        for i in range(len(judge_scores))
    ]
    return {
        "case_count": len(cases),
        "judge_model": os.getenv("HW10_JUDGE_MODEL", "deterministic-local-judge-v1"),
        "scale": "1-5",
        "human_labels": human_scores,
        "judge_scores": judge_scores,
        "spearman_correlation": correlation,
        "mean_absolute_difference": round(mean(differences), 3),
        "repeatability": {
            "runs": repeats,
            "changed_score_count": sum(value != 0 for value in changes),
            "mean_absolute_change": round(mean(changes), 3) if changes else 0.0,
            "max_absolute_change": max(changes, default=0),
        },
        "raw": [
            {"case_id": case["case_id"], "human_label": human, "judge_score": judge}
            for case, human, judge in zip(cases, human_scores, judge_scores)
        ],
    }
