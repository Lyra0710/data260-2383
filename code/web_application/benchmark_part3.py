import csv
import json
import os
import time
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

from dotenv import load_dotenv
from subprocess import run

import argparse
from collections import defaultdict
from math import ceil

APP_DIR = Path(__file__).resolve().parent
def get_repository_dir():
    result = run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=APP_DIR,
        check=True,
        capture_output=True,
        text=True,
    )

    return Path(result.stdout.strip())

def get_raw_dir():
    return (
        get_repository_dir()
        / "reports"
        / "hw04"
        / "raw"
    )

PAGE_SIZES = [10, 50, 200]
REQUESTS_PER_CASE = 30
SEED = 2383

IMPLEMENTATIONS = {
    "naive": "/api/fixtures/naive",
    "fixed": "/api/fixtures",
}


load_dotenv(APP_DIR / ".env")

BASE_URL = (
    f"http://127.0.0.1:{os.environ['APP_PORT']}"
)


def send_request(opener, method, path, body=None):
    request_body = None
    headers = {}

    if body is not None:
        request_body = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{BASE_URL}{path}",
        data=request_body,
        headers=headers,
        method=method,
    )

    with opener.open(request, timeout=30) as response:
        return (
            response.status,
            response.headers,
            response.read(),
        )


def login(opener):
    status_code, _, _ = send_request(
        opener,
        "POST",
        "/api/login",
        {
            "email": os.environ["BENCHMARK_EMAIL"],
            "password": os.environ["BENCHMARK_PASSWORD"],
        },
    )

    if status_code != 200:
        raise RuntimeError(
            f"Login failed with status {status_code}."
        )


def verify_response(response_body, page_size):
    fixtures = json.loads(response_body)

    if not isinstance(fixtures, list):
        raise RuntimeError(
            "List endpoint did not return a JSON list."
        )

    if len(fixtures) != page_size:
        raise RuntimeError(
            f"Expected {page_size} fixtures, "
            f"received {len(fixtures)}."
        )

    if not all(
        "related_items" in fixture
        for fixture in fixtures
    ):
        raise RuntimeError(
            "A fixture response is missing related_items."
        )


def run_benchmark():
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(
        "Benchmark started (UTC): "
        f"{datetime.now(timezone.utc).isoformat()}"
    )
    cookie_jar = CookieJar()
    opener = build_opener(
        HTTPCookieProcessor(cookie_jar)
    )

    login(opener)
    measurements = []

    for implementation, endpoint_path in IMPLEMENTATIONS.items():
        for page_size in PAGE_SIZES:
            for request_number in range(
                1,
                REQUESTS_PER_CASE + 1,
            ):
                query_string = urlencode(
                    {"page_size": page_size}
                )

                start_time = time.perf_counter_ns()

                status_code, headers, response_body = send_request(
                    opener,
                    "GET",
                    f"{endpoint_path}?{query_string}",
                )

                latency_ms = (
                    time.perf_counter_ns() - start_time
                ) / 1_000_000

                if status_code != 200:
                    raise RuntimeError(
                        f"{implementation} request failed "
                        f"with status {status_code}."
                    )

                verify_response(
                    response_body,
                    page_size,
                )

                query_count = headers.get(
                    "X-SQL-Query-Count"
                )

                if query_count is None:
                    raise RuntimeError(
                        "Response is missing "
                        "X-SQL-Query-Count."
                    )

                measurement = {
                    "timestamp_utc": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "implementation": implementation,
                    "page_size": page_size,
                    "request_number": request_number,
                    "status_code": status_code,
                    "sql_statements": int(query_count),
                    "latency_ms": round(latency_ms, 3),
                    "returned_records": page_size,
                }

                measurements.append(measurement)

                print(
                    f"{implementation}, "
                    f"page_size={page_size}, "
                    f"request={request_number}, "
                    f"sql={query_count}, "
                    f"latency_ms={latency_ms:.3f}"
                )

    json_path = raw_dir / "n_plus_one_measurements.json"
    csv_path = raw_dir / "n_plus_one_measurements.csv"

    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(
            {
                "seed": SEED,
                "requests_per_case": REQUESTS_PER_CASE,
                "measurements": measurements,
            },
            json_file,
            indent=2,
        )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=measurements[0].keys(),
        )
        writer.writeheader()
        writer.writerows(measurements)

    print(f"\nWrote {len(measurements)} measurements.")
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")

def nearest_rank(values, percentile):
    sorted_values = sorted(values)
    rank = ceil(percentile * len(sorted_values))

    return sorted_values[rank - 1]


def write_metrics():
    raw_dir = get_raw_dir()
    csv_path = raw_dir / "n_plus_one_measurements.csv"
    metrics_path = raw_dir.parent / "METRICS.md"

    measurements = defaultdict(list)

    with csv_path.open(
        newline="",
        encoding="utf-8",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            key = (
                row["implementation"],
                int(row["page_size"]),
            )
            measurements[key].append(row)

    summaries = {}

    for key, rows in measurements.items():
        if len(rows) != REQUESTS_PER_CASE:
            raise RuntimeError(
                f"Expected {REQUESTS_PER_CASE} rows for {key}, "
                f"found {len(rows)}."
            )

        latencies = [
            float(row["latency_ms"])
            for row in rows
        ]
        query_counts = {
            int(row["sql_statements"])
            for row in rows
        }

        if len(query_counts) != 1:
            raise RuntimeError(
                f"SQL query counts varied for {key}."
            )

        summaries[key] = {
            "sql_statements": query_counts.pop(),
            "p50": nearest_rank(latencies, 0.50),
            "p95": nearest_rank(latencies, 0.95),
            "p99": nearest_rank(latencies, 0.99),
        }

    lines = [
        "# HW4 Part 3 Metrics",
        "",
        "Percentiles use the nearest-rank method.",
        "",
        "| Page size | Version | SQL stmts/req | p50 (ms) | p95 (ms) | p99 (ms) |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for page_size in PAGE_SIZES:
        for implementation in ["naive", "fixed"]:
            summary = summaries[
                (implementation, page_size)
            ]

            lines.append(
                f"| {page_size} | {implementation} | "
                f"{summary['sql_statements']} | "
                f"{summary['p50']:.3f} | "
                f"{summary['p95']:.3f} | "
                f"{summary['p99']:.3f} |"
            )

    lines.extend([
        "",
        "## Fixed-version p50 latency reduction",
        "",
        "| Page size | Naive p50 (ms) | Fixed p50 (ms) | Reduction |",
        "|---:|---:|---:|---:|",
    ])

    for page_size in PAGE_SIZES:
        naive_p50 = summaries[("naive", page_size)]["p50"]
        fixed_p50 = summaries[("fixed", page_size)]["p50"]

        reduction = (
            (naive_p50 - fixed_p50)
            / naive_p50
            * 100
        )

        lines.append(
            f"| {page_size} | {naive_p50:.3f} | "
            f"{fixed_p50:.3f} | {reduction:.1f}% |"
        )

    metrics_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote metrics: {metrics_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summarize",
        action="store_true",
    )
    arguments = parser.parse_args()

    if arguments.summarize:
        write_metrics()
    else:   
        run_benchmark()