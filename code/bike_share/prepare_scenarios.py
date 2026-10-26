"""Create reproducible Capital Bikeshare CSV scenarios from public archives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "reports" / "hw07" / "raw" / "bike_share"
ARCHIVE_TEMPLATE = "https://s3.amazonaws.com/capitalbikeshare-data/{month}-capitalbikeshare-tripdata.zip"
HIGH_USE_MONTH = "2025-06"
LOW_USE_MONTHS = tuple(
    f"{year}-{month:02d}" for year in (2023, 2024, 2025) for month in range(1, 13)
)
TOTAL_ROWS = 500


def archive_url(month: str) -> str:
    """Return the official Lyft archive URL for one calendar month."""

    return ARCHIVE_TEMPLATE.format(month=month.replace("-", ""))


def parse_timestamp(value: str) -> datetime:
    """Parse the timestamp format used by the selected public archives."""

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def duration_seconds(row: dict[str, str]) -> float:
    """Return trip duration from timestamps without changing source data."""

    start = parse_timestamp(row["started_at"])
    end = parse_timestamp(row["ended_at"])
    return (end - start).total_seconds()


def select_rows(
    month: str,
    predicate: Callable[[dict[str, str]], bool],
    limit: int,
) -> list[dict[str, str]]:
    """Download one archive and keep at most ``limit`` matching rows."""

    print(f"Downloading {month}...", flush=True)
    response = httpx.get(archive_url(month), timeout=120.0)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
        with archive.open(csv_name) as binary_file:
            text_file = io.TextIOWrapper(binary_file, encoding="utf-8-sig", newline="")
            selected = []
            for row in csv.DictReader(text_file):
                if predicate(row):
                    selected.append(row)
                    if len(selected) == limit:
                        break
            print(f"Selected {len(selected)} row(s) from {month}.", flush=True)
            return selected


def valid_classic_trip(row: dict[str, str]) -> bool:
    """Keep only rows with fields needed for the current pricing comparison."""

    return (
        row.get("rideable_type") == "classic_bike"
        and bool(row.get("started_at"))
        and bool(row.get("ended_at"))
    )


def write_csv(name: str, rows: list[dict[str, str]]) -> Path:
    """Write the normalized uploaded-CSV shape used by the application."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / f"{name}.csv"
    fields = ["ride_id", "rideable_type", "started_at", "ended_at", "source_month"]
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def summarize(
    name: str,
    rows: list[dict[str, str]],
    urls: list[str],
    output: Path,
) -> None:
    """Save machine-readable provenance and trip-duration summary information."""

    durations = [duration_seconds(row) for row in rows]
    monthly_trip_counts: dict[str, int] = {}
    for row in rows:
        month = row["source_month"]
        monthly_trip_counts[month] = monthly_trip_counts.get(month, 0) + 1
    output.write_text(
        json.dumps(
            {
                "scenario": name,
                "row_count": len(rows),
                "source_urls": urls,
                "duration_seconds": {
                    "minimum": min(durations),
                    "maximum": max(durations),
                    "average": sum(durations) / len(durations),
                },
                "monthly_trip_counts": monthly_trip_counts,
                "csv_sha256": hashlib.sha256(
                    output.with_suffix(".csv").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def high_use_scenario() -> None:
    """Create a 500-trip, one-month case in which membership should win."""

    rows = select_rows(
        HIGH_USE_MONTH,
        lambda row: valid_classic_trip(row) and 0 < duration_seconds(row) <= 45 * 60,
        TOTAL_ROWS,
    )
    selected = [
        {
            "ride_id": row["ride_id"],
            "rideable_type": row["rideable_type"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "source_month": HIGH_USE_MONTH,
        }
        for row in rows
    ][:TOTAL_ROWS]
    if len(selected) < TOTAL_ROWS:
        raise RuntimeError(
            "The selected archive did not contain 500 eligible classic trips."
        )
    csv_path = write_csv("membership_wins", selected)
    summarize(
        "membership_wins",
        selected,
        [archive_url(HIGH_USE_MONTH)],
        csv_path.with_suffix(".json"),
    )


def low_use_scenario() -> None:
    """Create a 500-trip case distributed across 36 real billing months.

    The assignment requires at least 500 trip rows but also a pay-per-use-win
    scenario. A 500-ride single month cannot make a $25 membership lose because
    pay-per-use has a $1 unlock fee per ride. This scenario therefore preserves
    each public trip's original timestamp and distributes short, two-minute-or-
    less classic-bike trips across 36 original monthly billing periods. At the
    current $1 unlock plus $0.15/minute rate, 500 two-minute trips cost at most
    $650, while 36 monthly memberships cost $900. The resulting recommendation
    is evaluated per month, not as 500 rides in one billing period.
    """

    candidates_by_month: dict[str, list[dict[str, str]]] = {}
    urls = []
    for month in LOW_USE_MONTHS:
        rows = select_rows(
            month,
            lambda row: valid_classic_trip(row) and 0 < duration_seconds(row) <= 120,
            30,
        )
        candidates_by_month[month] = [
            {
                "ride_id": row["ride_id"],
                "rideable_type": row["rideable_type"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "source_month": month,
            }
            for row in rows
        ]
        if not candidates_by_month[month]:
            raise RuntimeError(f"{month} did not contain an eligible short trip.")
        urls.append(archive_url(month))

    selected = []
    positions = {month: 0 for month in LOW_USE_MONTHS}
    while len(selected) < TOTAL_ROWS:
        added_row = False
        for month in LOW_USE_MONTHS:
            position = positions[month]
            monthly_rows = candidates_by_month[month]
            if position < len(monthly_rows):
                selected.append(monthly_rows[position])
                positions[month] += 1
                added_row = True
                if len(selected) == TOTAL_ROWS:
                    break
        if not added_row:
            raise RuntimeError(
                "The selected archives did not contain 500 eligible trips."
            )

    csv_path = write_csv("pay_per_use_wins", selected)
    summarize("pay_per_use_wins", selected, urls, csv_path.with_suffix(".json"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        choices=("membership_wins", "pay_per_use_wins", "all"),
        default="all",
    )
    arguments = parser.parse_args()

    if arguments.scenario in {"membership_wins", "all"}:
        high_use_scenario()
    if arguments.scenario in {"pay_per_use_wins", "all"}:
        low_use_scenario()
    print(f"Created requested {TOTAL_ROWS}-row CSV scenario(s) in {RAW_DIR}")


if __name__ == "__main__":
    main()
