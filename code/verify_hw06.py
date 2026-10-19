"""Run the HW6 smoke test against the local FastAPI server."""

import argparse
import json
import platform
import subprocess
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "reports" / "hw06" / "verification.json"
SID4 = "2383"
PORT_BASE = 8583
PREFIX = "s2383"
SEED = 2383
VERIFY_SEED = 262383
DOMAIN_ID = 7
MODEL = "qwen3:8b"


def commit_hash() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_check(name: str, check) -> dict:
    try:
        return {"name": name, "status": "pass", "details": check()}
    except Exception as error:
        return {"name": name, "status": "fail", "details": str(error)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=f"http://127.0.0.1:{PORT_BASE}")
    arguments = parser.parse_args()
    base_url = arguments.base_url.rstrip("/")

    def check_root() -> str:
        response = requests.get(f"{base_url}/", timeout=15)
        response.raise_for_status()
        if response.json().get("message") != "Community Sports League Fixtures API":
            raise ValueError("Unexpected root response.")
        return "GET / returned the expected API message."

    def check_file_commands() -> str:
        response = requests.post(
            f"{base_url}/api/file-memory/command",
            json={"command": "/help"},
            timeout=15,
        )
        response.raise_for_status()
        expected = ["/memory", "/compact", "/dream", "/help"]
        if response.json().get("commands") != expected:
            raise ValueError("File-memory command list did not match.")
        return "POST /api/file-memory/command returned all four commands."

    def check_chat() -> str:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "user_id": "hw6-verify-user",
                "session_id": f"verify-{VERIFY_SEED}",
                "message": "Reply with a short greeting for the HW6 smoke test.",
            },
            timeout=600,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload.get("reply"), str) or not payload["reply"].strip():
            raise ValueError("POST /api/chat did not return a non-empty reply.")
        if "memory" not in payload:
            raise ValueError("POST /api/chat did not return memory details.")
        return "POST /api/chat returned a non-empty reply and memory details."

    def check_artifacts() -> str:
        required = [
            ROOT / "AGENT.md",
            ROOT / "MEMORY.md",
            ROOT / "reports" / "hw06" / "METRICS.md",
            ROOT / "reports" / "hw06" / "memory_probes.yaml",
            ROOT / "reports" / "hw06" / "raw" / "file_memory_demo.json",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        if missing:
            raise FileNotFoundError(", ".join(missing))
        return "Required HW6 memory artifacts exist."

    checks = [
        run_check("backend responds on PORT_BASE", check_root),
        run_check("file-memory commands respond", check_file_commands),
        run_check("chat endpoint returns a reply", check_chat),
        run_check("required HW6 artifacts exist", check_artifacts),
    ]
    verification = {
        "homework": "HW6",
        "sid4": SID4,
        "port_base": PORT_BASE,
        "prefix": PREFIX,
        "seed": SEED,
        "verify_seed": VERIFY_SEED,
        "domain_id": DOMAIN_ID,
        "commit_hash": commit_hash(),
        "model": MODEL,
        "hardware": platform.platform(),
        "checks": checks,
        "overall_status": "pass" if all(check["status"] == "pass" for check in checks) else "fail",
    }
    OUTPUT_PATH.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))
    if verification["overall_status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
