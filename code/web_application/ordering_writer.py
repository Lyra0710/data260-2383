import argparse
import asyncio
import json
import time
from pathlib import Path

from kafka.config import PREFIX, TASKS_TOPIC
from kafka.pipeline import message_consumer

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RAW_DIRECTORY = REPOSITORY_ROOT / "reports" / "hw08" / "raw"


async def main(run_name: str, worker_id: str) -> None:
    consumer = message_consumer(TASKS_TOPIC, f"{PREFIX}_ordering_{run_name}")
    output_path = RAW_DIRECTORY / f"ordering_{run_name}_{worker_id}.jsonl"
    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)

    await consumer.start()
    print("Student: Ananya")
    print(f"Ordering Writer {worker_id} is ready for {run_name} run...")

    try:
        with output_path.open("w", encoding="utf-8") as output_file:
            async for message in consumer:
                incoming = message.value
                if incoming.get("test_type") != "ordering":
                    await consumer.commit()
                    continue

                record = {
                    "run": run_name,
                    "worker_id": worker_id,
                    "sequence": incoming["sequence"],
                    "entity_id": incoming["entity_id"],
                    "correlation_id": incoming["correlation_id"],
                    "partition": message.partition,
                    "offset": message.offset,
                    "processed_at_ns": time.time_ns(),
                }
                output_file.write(json.dumps(record) + "\n")
                output_file.flush()
                await consumer.commit()
                print(f"Ordering Writer {worker_id} processed: {record}")
    finally:
        await consumer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["unkeyed", "keyed"], required=True)
    parser.add_argument("--worker-id", required=True)
    arguments = parser.parse_args()
    asyncio.run(main(arguments.run, arguments.worker_id))
