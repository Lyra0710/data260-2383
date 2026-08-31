import csv
import json
import subprocess
import sys
import time

from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    ROOT
    / "reports"
    / "hw01"
    / "cases"
    / "nondeterminism_input.json"
)

RAW_DIRECTORY = ROOT / "reports" / "hw01" / "raw"

JSON_PATH = RAW_DIRECTORY / "nondeterminism_runs.json"
CSV_PATH = RAW_DIRECTORY / "nondeterminism_runs.csv"
LOG_PATH = ROOT / "reports" / "hw01" / "RUN_LOG.txt"

TEMPERATURES = (0.7, 0.0)
RUNS_PER_TEMPERATURE = 20


def save_results(results):
    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)

    with JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    fieldnames = [
        "run_number",
        "temperature",
        "tags",
        "summary",
        "latency_ms",
        "timestamp"
    ]

    with CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            csv_result = result.copy()
            csv_result["tags"] = json.dumps(result["tags"])
            writer.writerow(csv_result)


def read_publish_package(console_output):
    marker = "Publish Package"

    if marker not in console_output:
        raise ValueError(
            "Publish Package was not found in agent output."
        )

    publish_text = console_output.split(marker, 1)[1].strip()

    package, _ = json.JSONDecoder().raw_decode(publish_text)
    return package


def write_log(message):
    print(message)

    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(message + "\n")


def main():
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        fixed_input = json.load(file)

    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if JSON_PATH.exists():
        with JSON_PATH.open("r", encoding="utf-8") as file:
            results = json.load(file)
    else:
        results = []

    for temperature in TEMPERATURES:
        completed = sum(
            1
            for result in results
            if result["temperature"] == temperature
        )

        for run_number in range(
            completed + 1,
            RUNS_PER_TEMPERATURE + 1
        ):
            start_message = (
                f"{datetime.now(timezone.utc).isoformat()} "
                f"Starting temperature={temperature}, "
                f"run={run_number}"
            )
            write_log(start_message)

            command = [
                sys.executable,
                str(ROOT / "code" / "agents_demo.py"),
                "--title",
                fixed_input["title"],
                "--content",
                fixed_input["content"],
                "--model",
                "qwen3:8b",
                "--temperature",
                str(temperature),
                "--strict"
            ]

            start_time = time.perf_counter()

            process = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True
            )

            latency_ms = round(
                (time.perf_counter() - start_time) * 1000
            )

            if process.returncode != 0:
                write_log(
                    f"Run failed: temperature={temperature}, "
                    f"run={run_number}\n{process.stderr}"
                )
                save_results(results)
                sys.exit(1)

            package = read_publish_package(process.stdout)
            final_output = package["agents"]["final"]

            result = {
                "run_number": run_number,
                "temperature": temperature,
                "tags": final_output["tags"],
                "summary": final_output["summary"],
                "latency_ms": latency_ms,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            results.append(result)
            save_results(results)

            write_log(
                f"Completed temperature={temperature}, "
                f"run={run_number}, latency_ms={latency_ms}, "
                f"tags={final_output['tags']}"
            )

    write_log(
        f"Experiment complete: {len(results)} total runs."
    )


if __name__ == "__main__":
    main()