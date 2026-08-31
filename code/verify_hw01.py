"""Run basic Homework 1 repository checks."""

import json
import sys

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "hw01" / "verification.json"


def main():
    html = (
        ROOT / "code" / "web_application" / "index.html"
    ).read_text(encoding="utf-8")

    javascript = (
        ROOT / "code" / "web_application" / "script.js"
    ).read_text(encoding="utf-8")

    client = (
        ROOT / "code" / "hw1_client.py"
    ).read_text(encoding="utf-8")

    raw_results = json.loads(
        (
            ROOT
            / "reports"
            / "hw01"
            / "raw"
            / "nondeterminism_runs.json"
        ).read_text(encoding="utf-8")
    )

    temperature_counts = Counter(
        str(result["temperature"])
        for result in raw_results
    )

    checks = {
        "supported_python_version": (
            sys.version_info[:2] in {(3, 11), (3, 12)}
        ),
        "domain_schema_exists": (
            ROOT / "DOMAIN_SCHEMA.md"
        ).is_file(),
        "agent_instructions_exist": (
            ROOT / "AGENT.md"
        ).is_file(),
        "model_adapter_exists": (
            ROOT / "src" / "model_client.py"
        ).is_file(),
        "hw1_client_imports_adapter": (
            "from src.model_client import" in client
        ),
        "primary_field_has_autofocus": (
            "autofocus" in html
        ),
        "javascript_logs_updated_object": (
            "updatedObject)" in javascript
        ),
        "raw_experiment_has_40_runs": (
            len(raw_results) == 40
        ),
        "temperature_0.7_has_20_runs": (
            temperature_counts["0.7"] == 20
        ),
        "temperature_0.0_has_20_runs": (
            temperature_counts["0.0"] == 20
        ),
        "every_run_has_three_tags": all(
            len(result.get("tags", [])) == 3
            for result in raw_results
        ),
    }

    verification = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "python_version": sys.version.split()[0],
        "all_checks_passed": all(checks.values()),
        "checks": checks,
    }

    OUTPUT.write_text(
        json.dumps(verification, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(verification, indent=2))

    if not verification["all_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()