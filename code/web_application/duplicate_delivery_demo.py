import argparse
import asyncio
import uuid

from kafka.config import DRAFTS_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import message_consumer, message_producer


async def main(expected_drafts: int) -> None:
    correlation_id = str(uuid.uuid4())
    consumer = message_consumer(
        DRAFTS_TOPIC,
        f"{PREFIX}_duplicate_reader_{correlation_id}",
    )
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")
    print(f"Duplicate-delivery test correlation_id: {correlation_id}")

    task = {
        "correlation_id": correlation_id,
        "question": "How should a league manager confirm a tennis fixture?",
        "plan": "1. Confirm availability. 2. Notify participants. 3. Record details.",
    }

    try:
        await producer.send_and_wait(TASKS_TOPIC, task)
        print(f"Replay 1 sent: {task}")
        await producer.send_and_wait(TASKS_TOPIC, task)
        print(f"Replay 2 sent: {task}")

        drafts_received = 0
        while drafts_received < expected_drafts:
            message = await asyncio.wait_for(consumer.getone(), timeout=90)
            draft = message.value
            if draft.get("correlation_id") != correlation_id:
                continue

            drafts_received += 1
            print(f"Draft side effect {drafts_received}: {draft}")
            await consumer.commit()

        print(f"Expected draft side effects observed: {drafts_received}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-drafts", type=int, choices=[1, 2], required=True)
    arguments = parser.parse_args()
    asyncio.run(main(arguments.expected_drafts))
