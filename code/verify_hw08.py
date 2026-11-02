"""Write objective HW8 smoke-test results for the running Kafka services."""

from __future__ import annotations

import asyncio
import json
import platform
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_APPLICATION_DIRECTORY = REPO_ROOT / "code" / "web_application"
REPORT_DIRECTORY = REPO_ROOT / "reports" / "hw08"
OUTPUT_PATH = REPORT_DIRECTORY / "verification.json"
SID4 = "2383"
SEED = 2383
VERIFY_SEED = 262383


def check(name: str, function) -> dict[str, str]:
    try:
        return {"name": name, "status": "pass", "details": function()}
    except Exception as error:
        return {"name": name, "status": "fail", "details": str(error)}


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def check_fastapi() -> str:
    with urlopen("http://127.0.0.1:8583/", timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))

    if body.get("message") != "HW8 Kafka Fixture API":
        raise AssertionError("Unexpected FastAPI root response.")
    return "FastAPI root returned the expected HW8 service message."


async def kafka_round_trip() -> str:
    sys.path.insert(0, str(WEB_APPLICATION_DIRECTORY))
    from kafka.client import send_request  # noqa: PLC0415

    correlation_id = str(uuid.uuid4())
    fixture_data = {
        "fixture_name": "HW8 Verification Fixture",
        "teams": ["Verification A", "Verification B"],
        "fixture_code": f"VERIFY-{correlation_id[:8]}",
        "available_slots": 1,
        "venue_id": 1,
    }

    create_response = await send_request(
        "CREATE_FIXTURE",
        fixture_data,
        correlation_id,
    )
    if not create_response.get("success"):
        raise AssertionError(f"CREATE_FIXTURE failed: {create_response}")
    if create_response.get("correlation_id") != correlation_id:
        raise AssertionError("CREATE_FIXTURE changed the correlation ID.")

    get_response = await send_request(
        "GET_FIXTURE",
        {"entity_id": create_response["entity_id"]},
        correlation_id,
    )
    if not get_response.get("success"):
        raise AssertionError(f"GET_FIXTURE failed: {get_response}")
    if get_response.get("correlation_id") != correlation_id:
        raise AssertionError("GET_FIXTURE changed the correlation ID.")
    if get_response["entity"] != {
        "entity_id": create_response["entity_id"],
        **fixture_data,
    }:
        raise AssertionError("GET_FIXTURE did not return the created fixture.")

    return "CREATE_FIXTURE and GET_FIXTURE completed through Kafka."


def check_kafka_round_trip() -> str:
    return asyncio.run(kafka_round_trip())


def check_raw_artifacts() -> str:
    required = [
        "failure_results.json",
        "ordering_unkeyed_records.csv",
        "ordering_unkeyed_summary.json",
        "ordering_keyed_records.csv",
        "ordering_keyed_summary.json",
    ]
    missing = [
        path for path in required if not (REPORT_DIRECTORY / "raw" / path).is_file()
    ]
    if missing:
        raise AssertionError(f"Missing raw artifact(s): {', '.join(missing)}")
    return f"Found {len(required)} required HW8 raw artifacts."


def main() -> None:
    checks = [
        check("FastAPI service", check_fastapi),
        check("Kafka fixture round trip", check_kafka_round_trip),
        check("HW8 raw artifacts", check_raw_artifacts),
    ]
    result = {
        "homework": "HW8",
        "sid4": SID4,
        "commit_hash": git_commit(),
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "model_configuration": {"chat_model": "qwen3:8b"},
        "hardware": platform.platform(),
        "checks": checks,
        "overall_status": (
            "pass" if all(item["status"] == "pass" for item in checks) else "fail"
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
