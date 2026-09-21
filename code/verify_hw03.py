import json
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CORPUS_DIR = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "corpus"
)

QUESTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "questions.yaml"
)

RAW_DIR = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "raw"
)

SUMMARY_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "summary_metrics.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "verification.json"
)


def main():
    checks = {}

    checks["questions_file_exists"] = QUESTIONS_PATH.exists()

    with QUESTIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        questions = yaml.safe_load(file)["questions"]

    checks["five_questions"] = len(questions) == 5

    corpus_files = list(
        CORPUS_DIR.glob("*.pdf")
    ) + list(
        CORPUS_DIR.glob("*.html")
    )

    corpus_size = sum(
        file_path.stat().st_size
        for file_path in corpus_files
    )

    checks["six_corpus_files"] = (
        len(corpus_files) == 6
    )

    checks["corpus_at_least_200kb"] = (
        corpus_size >= 200_000
    )

    raw_files = list(RAW_DIR.glob("*.json"))

    checks["fifteen_raw_files"] = (
        len(raw_files) == 15
    )

    raw_files_valid = True

    for file_path in raw_files:
        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                result = json.load(file)

            if len(result["results"]) != 5:
                raw_files_valid = False

        except (json.JSONDecodeError, KeyError):
            raw_files_valid = False

    checks["raw_files_valid"] = raw_files_valid
    checks["summary_file_exists"] = (
        SUMMARY_PATH.exists()
    )

    passed = all(checks.values())

    verification = {
        "passed": passed,
        "checks": checks,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            verification,
            file,
            indent=2,
        )

    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()