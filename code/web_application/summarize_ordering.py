import argparse
import csv
import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RAW_DIRECTORY = REPOSITORY_ROOT / "reports" / "hw08" / "raw"
MESSAGE_COUNT = 20


def main(run_name: str) -> None:
    records = []
    for path in RAW_DIRECTORY.glob(f"ordering_{run_name}_*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            records.append(json.loads(line))

    records.sort(key=lambda record: record["processed_at_ns"])
    if len(records) != MESSAGE_COUNT:
        raise ValueError(f"Expected {MESSAGE_COUNT} records, found {len(records)}.")

    sequences = [record["sequence"] for record in records]
    partitions = sorted({record["partition"] for record in records})
    summary = {
        "run": run_name,
        "message_count": len(records),
        "partitions_used": partitions,
        "processing_sequence": sequences,
        "preserves_input_order": sequences == list(range(1, MESSAGE_COUNT + 1)),
    }

    json_path = RAW_DIRECTORY / f"ordering_{run_name}_summary.json"
    csv_path = RAW_DIRECTORY / f"ordering_{run_name}_records.csv"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["unkeyed", "keyed"], required=True)
    arguments = parser.parse_args()
    main(arguments.run)
