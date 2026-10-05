import asyncio
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = ROOT / "code" / "mcp"
REPORT_DIR = ROOT / "reports/hw05"
sys.path.insert(0, str(MCP_DIR))

import domain_server
import meals_server


def check_backend():
    with urllib.request.urlopen(
        "http://127.0.0.1:8583/docs",
        timeout=5,
    ) as response:
        return response.status == 200


async def check_domain_tool():
    result = await domain_server.fixture_details(1)
    return result.get("ok") is True


def check_meal_tool():
    result = meals_server.search_meals_by_name(
        "Arrabiata",
        1,
    )
    return isinstance(result, list) and len(result) > 0


def check_offline_tests():
    result = subprocess.run(
        [sys.executable, "code/mcp/test_tools.py"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "8/8 tests passed" in result.stdout


def check_raw_measurements():
    files = [
        ROOT / "reports/hw05/raw/retry_rate_0.0.jsonl",
        ROOT / "reports/hw05/raw/retry_rate_0.2.jsonl",
        ROOT / "reports/hw05/raw/retry_rate_0.5.jsonl",
    ]

    return all(
        path.exists() and len(path.read_text().splitlines()) == 50
        for path in files
    )


def check_agent_log():
    path = ROOT / "agent_runs.jsonl"
    return path.exists() and len(path.read_text().splitlines()) >= 4


def get_commit_hash():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main():
    checks = {}

    try:
        checks["backend responds on port 8583"] = check_backend()
    except Exception:
        checks["backend responds on port 8583"] = False

    try:
        checks["domain MCP tool responds"] = asyncio.run(
            check_domain_tool()
        )
    except Exception:
        checks["domain MCP tool responds"] = False

    try:
        checks["TheMealDB MCP tool responds"] = check_meal_tool()
    except Exception:
        checks["TheMealDB MCP tool responds"] = False

    checks["offline tests pass"] = check_offline_tests()
    checks["150 raw measurement records exist"] = check_raw_measurements()
    checks["agent log contains four runs"] = check_agent_log()

    verification = {
        "homework": "HW5",
        "sid4": "2383",
        "commit_hash": get_commit_hash(),
        "model": "qwen3:8b",
        "seed": 2383,
        "verify_seed": 2383,
        "checks": checks,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORT_DIR / "verification.json"
    output_path.write_text(
        json.dumps(verification, indent=2) + "\n",
        encoding="utf-8",
    )

    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")

    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()