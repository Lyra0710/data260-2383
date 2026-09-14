import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from agents_demo import AgentOutput, build_graph
from web_application.main import app


REPO_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_DIR / "reports" / "hw02" / "verification.json"

SID4 = "2383"
SEED = 2383
VERIFY_SEED = 262383
MODEL = "qwen3:8b"


def get_commit_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_DIR,
            text=True,
        ).strip()
    except Exception:
        return "unavailable"


def record_check(checks, name, passed, details):
    checks.append(
        {
            "name": name,
            "passed": passed,
            "details": details,
        }
    )


def check_required_files(checks):
    required_files = [
        "reports/hw02/RUN_LOG.txt",
        "reports/hw02/METRICS.md",
        "reports/hw02/AI_USE.md",
        "reports/hw02/reproducible_run_instructions.md",
        "reports/hw02/report.pdf",
        "reports/hw02/cases/schema_input.json",
        "reports/hw02/raw/schema_validation.json",
        "reports/hw02/raw/schema_validation.csv",
        "reports/hw02/raw/ceiling_2.json",
        "reports/hw02/raw/ceiling_2.csv",
        "reports/hw02/raw/ceiling_10.json",
        "reports/hw02/raw/ceiling_10.csv",
        "reports/hw02/raw/adversarial.json",
        "reports/hw02/raw/adversarial.csv",
    ]

    missing_files = [
        path for path in required_files
        if not (REPO_DIR / path).exists()
    ]

    record_check(
        checks,
        "required files exist",
        len(missing_files) == 0,
        "All required files exist."
        if not missing_files
        else f"Missing files: {missing_files}",
    )


def check_fastapi(checks):
    try:
        client = TestClient(app)

        home_response = client.get("/")
        fixtures_response = client.get("/api/fixtures")

        passed = (
            home_response.status_code == 200
            and fixtures_response.status_code == 200
            and isinstance(fixtures_response.json(), list)
        )

        record_check(
            checks,
            "FastAPI smoke test",
            passed,
            (
                f"GET / returned {home_response.status_code}; "
                f"GET /api/fixtures returned {fixtures_response.status_code}."
            ),
        )
    except Exception as error:
        record_check(
            checks,
            "FastAPI smoke test",
            False,
            str(error),
        )


def check_langgraph(checks):
    try:
        graph = build_graph()

        initial_state = {
            "title": "Community Soccer",
            "content": (
                "A local soccer league is organizing a semifinal "
                "match between two community teams."
            ),
            "email": "student@example.com",
            "strict": True,
            "task": (
                "Produce exactly 3 topical tags and a one-sentence summary."
            ),
            "llm": MODEL,
            "turn_count": 0,
            "turn_limit": 2,
        }

        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": 11},
        )

        planner_output = final_state.get("planner_proposal")
        validated_output = AgentOutput.model_validate(planner_output)
        tags = validated_output.data.tags

        passed = (
            final_state.get("turn_count", 0) >= 1
            and len(tags) == 3
        )

        record_check(
            checks,
            "LangGraph smoke test",
            passed,
            (
                f"Graph completed in {final_state.get('turn_count')} turn(s) "
                f"and returned {len(tags)} tags."
            ),
        )
    except Exception as error:
        record_check(
            checks,
            "LangGraph smoke test",
            False,
            str(error),
        )


def main():
    checks = []

    check_required_files(checks)
    check_fastapi(checks)
    check_langgraph(checks)

    verification = {
        "homework": "DATA260 Homework 2",
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "model": MODEL,
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(verification, indent=2) + "\n"
    )

    print(json.dumps(verification, indent=2))

    if not verification["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()