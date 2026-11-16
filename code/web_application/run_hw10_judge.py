"""Run the HW10 judge-validation experiment on the frozen dataset."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from evaluator import HELPFULNESS_STEPS
from hw10_judge import JUDGE_MODEL, JUDGE_TIMEOUT_SECONDS, score_with_geval

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "reports" / "hw10" / "eval_cases.json"
LABELS_PATH = ROOT / "reports" / "hw10" / "human_labels.csv"
OUTPUT_PATH = ROOT / "reports" / "hw10" / "raw" / "judge_validation.json"
TIMEOUT_SECONDS = JUDGE_TIMEOUT_SECONDS


def bounded_score(case: dict) -> tuple[int, str, str]:
    """Run GEval using its configured per-task and per-attempt time limits."""
    try:
        score, reason = score_with_geval(
            case["question"],
            case["draft"],
            "Writer Helpfulness",
            HELPFULNESS_STEPS,
        )
        return score, reason, JUDGE_MODEL
    except Exception as error:
        raise RuntimeError(
            f"GEval could not score {case['case_id']}: {error}"
        ) from error


def load_labels() -> dict[str, int]:
    with LABELS_PATH.open(encoding="utf-8", newline="") as source:
        return {
            row["case_id"]: int(row["human_label"]) for row in csv.DictReader(source)
        }


def rank_correlation(left: list[int], right: list[int]) -> float | None:
    try:
        from scipy.stats import spearmanr

        return round(float(spearmanr(left, right).statistic), 4)
    except Exception:
        return None


def run() -> dict:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    labels = load_labels()
    repeats = int(os.getenv("HW10_JUDGE_REPEATS", "3"))
    runs = []
    judge_model = ""

    for _ in range(repeats):
        scored = []
        for case in cases:
            score, reason, judge_model = bounded_score(case)
            scored.append(
                {"case_id": case["case_id"], "score": score, "reason": reason}
            )
        runs.append(scored)

    first_scores = [row["score"] for row in runs[0]]
    human_scores = [labels[case["case_id"]] for case in cases]
    differences = [
        abs(human - judge) for human, judge in zip(human_scores, first_scores)
    ]
    changes = [
        abs(run[index]["score"] - first_scores[index])
        for run in runs[1:]
        for index in range(len(first_scores))
    ]
    result = {
        "dataset": str(CASES_PATH.relative_to(ROOT)),
        "label_reference": str(LABELS_PATH.relative_to(ROOT)),
        "case_count": len(cases),
        "scale": "1-5",
        "judge_model": judge_model,
        "settings": {
            "repeats": repeats,
            "timeout_seconds": TIMEOUT_SECONDS,
            "judge_type": "DeepEval GEval with local Ollama",
        },
        "spearman_correlation": rank_correlation(human_scores, first_scores),
        "mean_absolute_difference": round(sum(differences) / len(differences), 4),
        "repeatability": {
            "changed_score_count": sum(change != 0 for change in changes),
            "comparison_count": len(changes),
            "mean_absolute_change": (
                round(sum(changes) / len(changes), 4) if changes else 0.0
            ),
            "max_absolute_change": max(changes, default=0),
        },
        "runs": runs,
        "raw": [
            {
                "case_id": case["case_id"],
                "human_label": labels[case["case_id"]],
                "judge_score": first["score"],
                "reason": first["reason"],
            }
            for case, first in zip(cases, runs[0])
        ],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
