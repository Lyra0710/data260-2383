import argparse
import asyncio
import random

from kafka.config import PREFIX, TASKS_TOPIC, VERIFY_SEED
from kafka.pipeline import message_producer

ENTITY_ID = "fixture-ordering-2383"
MESSAGE_COUNT = 20


async def main(run_name: str) -> None:
    random_generator = random.Random(VERIFY_SEED)
    producer = message_producer()
    await producer.start()
    print("Student: Ananya")
    print(f"Ordering run: {run_name}; VERIFY_SEED={VERIFY_SEED}")

    try:
        for sequence in range(1, MESSAGE_COUNT + 1):
            message = {
                "test_type": "ordering",
                "correlation_id": f"{PREFIX}-{run_name}-{sequence}",
                "entity_id": ENTITY_ID,
                "sequence": sequence,
            }

            if run_name == "unkeyed":
                partition = random_generator.randrange(2)
                await producer.send_and_wait(TASKS_TOPIC, message, partition=partition)
                print(f"Unkeyed message {sequence} sent to partition {partition}")
            else:
                await producer.send_and_wait(
                    TASKS_TOPIC,
                    message,
                    key=ENTITY_ID.encode("utf-8"),
                )
                print(f"Keyed message {sequence} sent with key {ENTITY_ID}")
    finally:
        await producer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["unkeyed", "keyed"], required=True)
    arguments = parser.parse_args()
    asyncio.run(main(arguments.run))
