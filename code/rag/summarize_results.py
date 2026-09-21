import csv
import json
from collections import defaultdict
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "raw"
)

QUESTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "questions.yaml"
)

SUMMARY_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "summary_metrics.csv"
)


def load_expected_sources():
    with QUESTIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    return {
        question["id"]: question["expected_source"]
        for question in data["questions"]
    }


def load_raw_results():
    results = []

    for file_path in sorted(RAW_DIR.glob("*.json")):
        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            results.append(json.load(file))

    return results


def calculate_metrics(raw_results, expected_sources):
    grouped_results = defaultdict(list)

    for result in raw_results:
        grouped_results[result["technique"]].append(
            result
        )

    summary = []

    for technique, results in sorted(
        grouped_results.items()
    ):
        top1_scores = []
        mean_at_5_scores = []
        recalls = []
        latencies = []

        for result in results:
            cosine_scores = [
                row["cosine_similarity"]
                for row in result["results"]
            ]

            sources = [
                row["source"]
                for row in result["results"]
            ]

            top1_scores.append(cosine_scores[0])
            mean_at_5_scores.append(
                sum(cosine_scores) / len(cosine_scores)
            )
            latencies.append(result["latency_ms"])

            expected_source = expected_sources[
                result["question_id"]
            ]

            recalls.append(
                int(expected_source in sources)
            )

        first_result = results[0]

        summary.append(
            {
                "technique": technique,
                "node_count": first_result["node_count"],
                "average_chunk_length": (
                    first_result["average_chunk_length"]
                ),
                "top_1_cosine": (
                    sum(top1_scores)
                    / len(top1_scores)
                ),
                "mean_at_5_cosine": (
                    sum(mean_at_5_scores)
                    / len(mean_at_5_scores)
                ),
                "recall_at_5": (
                    sum(recalls)
                    / len(recalls)
                ),
                "mean_latency_ms": (
                    sum(latencies)
                    / len(latencies)
                ),
            }
        )

    return summary


def save_summary(summary):
    SUMMARY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = list(summary[0].keys())

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(summary)


def main():
    expected_sources = load_expected_sources()
    raw_results = load_raw_results()

    summary = calculate_metrics(
        raw_results,
        expected_sources,
    )

    save_summary(summary)

    for row in summary:
        print(row)


if __name__ == "__main__":
    main()