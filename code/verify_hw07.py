"""Write the HW7 smoke-test results without changing application code."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "hw07"
OUTPUT_PATH = REPORT_DIR / "verification.json"
SEED = 2383
VERIFY_SEED = 262383

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / "code" / "web_application" / ".env")


def check(name: str, function) -> dict[str, str]:
    """Run one objective check and preserve a useful pass/fail detail."""
    try:
        details = function()
        return {"name": name, "status": "pass", "details": details}
    except Exception as error:  # Verification should report failures, not abort early.
        return {"name": name, "status": "fail", "details": str(error)}


def git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
    ).strip()


def api_base_url() -> str:
    port = os.getenv("APP_PORT", "8583")
    return f"http://127.0.0.1:{port}"


def check_backend() -> str:
    response = requests.get(f"{api_base_url()}/", timeout=10)
    response.raise_for_status()
    if response.json().get("message") != "Community Sports League Fixtures API":
        raise AssertionError("Unexpected root response.")
    return "GET / returned the expected API message."


def check_login() -> str:
    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    if not username or not password:
        raise RuntimeError("API_USERNAME and API_PASSWORD must be configured.")
    login_url = f"{api_base_url()}/auth/login"
    valid = requests.post(
        login_url,
        data={"username": username, "password": password},
        timeout=10,
    )
    valid.raise_for_status()
    if not valid.json().get("access_token"):
        raise AssertionError("Valid login did not return an access token.")
    invalid = requests.post(
        login_url,
        data={"username": username, "password": "not-the-demo-password"},
        timeout=10,
    )
    if invalid.status_code != 401:
        raise AssertionError(f"Invalid login returned {invalid.status_code}, not 401.")
    return "Valid login returned a token and invalid login returned HTTP 401."


def check_agent_loop() -> str:
    mcp_directory = REPO_ROOT / "code" / "mcp"
    sys.path.insert(0, str(mcp_directory))
    from agent import run_agent  # noqa: PLC0415

    result = asyncio.run(
        run_agent(
            "Search for fixtures containing SJSU, then retrieve details for the "
            "first result.",
            minimum_tool_calls=2,
        )
    )
    if result["stop_reason"] != "normal_completion" or result["total_tool_calls"] < 2:
        raise AssertionError(
            "Agent did not complete normally with the required two tool calls."
        )
    return "Bounded agent completed a two-tool verification task."


def check_part6() -> str:
    sys.path.insert(0, str(REPO_ROOT / "code"))
    from file_tools import run_demo  # noqa: PLC0415

    result = run_demo()
    if not result["safety_gate"]["all_expectations_passed"]:
        raise AssertionError("The five-pass/five-block safety-gate test failed.")
    if result["integration"]["search_matches"][0]["path"] != "beta.py":
        raise AssertionError("The glob-search-read integration did not find beta.py.")
    return "File-tool integration and all ten safety-gate expectations passed."


def check_required_raw_artifacts() -> str:
    required = [
        "part2_reliability_attempts.json",
        "part2_reliability_attempts.csv",
        "part3_original_vs_reflexion.json",
        "part5_attack_results.json",
        "part6_safety_gate_results.json",
        "bike_share/membership_wins.csv",
        "bike_share/pay_per_use_wins.csv",
    ]
    missing = [path for path in required if not (REPORT_DIR / "raw" / path).is_file()]
    if missing:
        raise AssertionError(f"Missing required raw artifact(s): {', '.join(missing)}")
    return f"Found {len(required)} required HW7 raw artifacts."


def main() -> None:
    checks = [
        check("backend root", check_backend),
        check("JWT login", check_login),
        check("bounded agent loop", check_agent_loop),
        check("file tools and safety gate", check_part6),
        check("required raw artifacts", check_required_raw_artifacts),
    ]
    result = {
        "homework": "HW7",
        "sid4": "2383",
        "commit_hash": git_commit(),
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "model_configuration": {
            "chat_model": os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            "embedding_model": "nomic-embed-text",
            "agent_max_steps": 6,
            "agent_max_repairs": 1,
        },
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
