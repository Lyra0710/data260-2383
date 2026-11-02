import asyncio
import uuid

from kafka.config import DEAD_LETTER_TOPIC, DRAFTS_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import message_consumer, message_producer


async def wait_for_message(consumer, correlation_id: str) -> dict:
    while True:
        message = await asyncio.wait_for(consumer.getone(), timeout=180)
        value = message.value
        if value.get("correlation_id") == correlation_id:
            await consumer.commit()
            return value


async def main() -> None:
    poison_correlation_id = str(uuid.uuid4())
    valid_correlation_id = str(uuid.uuid4())
    dead_letter_consumer = message_consumer(
        DEAD_LETTER_TOPIC,
        f"{PREFIX}_dead_letter_reader_{poison_correlation_id}",
    )
    draft_consumer = message_consumer(
        DRAFTS_TOPIC,
        f"{PREFIX}_poison_draft_reader_{valid_correlation_id}",
    )
    producer = message_producer()

    await dead_letter_consumer.start()
    await draft_consumer.start()
    await producer.start()
    print("Student: Ananya")

    poison_task = {
        "correlation_id": poison_correlation_id,
        "question": "This task intentionally fails.",
        "plan": "No plan is executed.",
        "force_failure": True,
    }
    valid_task = {
        "correlation_id": valid_correlation_id,
        "question": "How should a league manager confirm a tennis fixture?",
        "plan": "1. Confirm availability. 2. Notify participants. 3. Record details.",
    }

    try:
        await producer.send_and_wait(TASKS_TOPIC, poison_task, key=b"poison-demo")
        print(f"Poison task sent: {poison_task}")
        await producer.send_and_wait(TASKS_TOPIC, valid_task, key=b"poison-demo")
        print(f"Valid task sent after poison task: {valid_task}")

        dead_letter = await wait_for_message(
            dead_letter_consumer,
            poison_correlation_id,
        )
        print(f"Dead-letter message received: {dead_letter}")

        draft = await wait_for_message(draft_consumer, valid_correlation_id)
        print(f"Later valid task completed: {draft}")
    finally:
        await dead_letter_consumer.stop()
        await draft_consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
