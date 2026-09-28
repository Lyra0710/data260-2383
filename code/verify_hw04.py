import json
import os
import subprocess
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

from dotenv import load_dotenv


CODE_DIR = Path(__file__).resolve().parent
REPOSITORY_DIR = CODE_DIR.parent
APP_DIR = CODE_DIR / "web_application"
REPORT_DIR = REPOSITORY_DIR / "reports" / "hw04"
VERIFICATION_PATH = REPORT_DIR / "verification.json"

load_dotenv(APP_DIR / ".env")

APP_PORT = os.environ["APP_PORT"]
BASE_URL = f"http://127.0.0.1:{APP_PORT}"

SID4 = "2383"
SEED = 2383

checks = []
cookie_jar = CookieJar()
opener = build_opener(
    HTTPCookieProcessor(cookie_jar),
)


def make_request(method, path, body=None):
    request = Request(
        url=f"{BASE_URL}{path}",
        data=(
            json.dumps(body).encode("utf-8")
            if body is not None
            else None
        ),
        headers={"Content-Type": "application/json"},
        method=method,
    )

    with opener.open(request, timeout=30) as response:
        response_data = json.load(response)

        return (
            response.status,
            response.headers,
            response_data,
        )


def run_check(name, check_function):
    try:
        details = check_function()

        checks.append(
            {
                "name": name,
                "status": "pass",
                "details": details,
            }
        )
    except Exception as error:
        checks.append(
            {
                "name": name,
                "status": "fail",
                "details": str(error),
            }
        )


def check_backend_root():
    status, _, _ = make_request("GET", "/")

    if status != 200:
        raise RuntimeError(f"Expected HTTP 200, received {status}.")

    return "GET / returned HTTP 200."


def check_login():
    email = os.getenv("BENCHMARK_EMAIL")
    password = os.getenv("BENCHMARK_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "BENCHMARK_EMAIL and BENCHMARK_PASSWORD "
            "must be set in code/.env."
        )

    status, _, _ = make_request(
        "POST",
        "/api/login",
        {
            "email": email,
            "password": password,
        },
    )

    if status != 200:
        raise RuntimeError(f"Expected HTTP 200, received {status}.")

    return "POST /api/login returned HTTP 200."


def check_naive_endpoint():
    status, headers, response_data = make_request(
        "GET",
        "/api/fixtures/naive?page_size=10",
    )

    query_count = headers.get("X-Sql-Query-Count")

    if status != 200:
        raise RuntimeError(f"Expected HTTP 200, received {status}.")
    if not isinstance(response_data, list) or not response_data:
        raise RuntimeError("Naive endpoint did not return fixture data.")
    if query_count != "11":
        raise RuntimeError(
            f"Expected 11 SQL statements, received {query_count}."
        )

    return (
        "Naive endpoint returned fixture data with "
        "X-Sql-Query-Count = 11."
    )


def check_fixed_endpoint():
    status, headers, response_data = make_request(
        "GET",
        "/api/fixtures?page_size=10",
    )

    query_count = headers.get("X-Sql-Query-Count")

    if status != 200:
        raise RuntimeError(f"Expected HTTP 200, received {status}.")
    if not isinstance(response_data, list) or not response_data:
        raise RuntimeError("Fixed endpoint did not return fixture data.")
    if query_count != "2":
        raise RuntimeError(
            f"Expected 2 SQL statements, received {query_count}."
        )

    return (
        "Fixed endpoint returned fixture data with "
        "X-Sql-Query-Count = 2."
    )


def get_commit_hash():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def main():
    run_check("backend_root", check_backend_root)
    run_check("login", check_login)
    run_check("naive_fixture_list", check_naive_endpoint)
    run_check("fixed_fixture_list", check_fixed_endpoint)

    verification = {
        "homework": "HW4",
        "sid4": SID4,
        "commit_hash": get_commit_hash(),
        "seed": SEED,
        "model_configuration": {
            "chat_model": "qwen3:8b",
            "embedding_model": "nomic-embed-text",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "vector_store": "ChromaDB",
        },
        "checks": checks,
        "overall_status": (
            "pass"
            if all(check["status"] == "pass" for check in checks)
            else "fail"
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    VERIFICATION_PATH.write_text(
        json.dumps(verification, indent=2),
        encoding="utf-8",
    )

    print(f"Saved: {VERIFICATION_PATH}")
    print(f"Overall status: {verification['overall_status']}")


if __name__ == "__main__":
    main()