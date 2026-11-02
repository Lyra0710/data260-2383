import asyncio

from kafka.config import DEAD_LETTER_TOPIC, DRAFTS_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import (
    IDEMPOTENCY_ENABLED,
    PROCESSING_DELAY_SECONDS,
    ask_model,
    message_consumer,
    message_producer,
)

completed_correlation_ids = set()
MAX_RETRIES = 3


async def main() -> None:
    consumer = message_consumer(TASKS_TOPIC, f"{PREFIX}_writer")
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")
    print("Writer is ready and listening...")

    try:
        async for message in consumer:
            incoming = message.value
            print(f"Writer received: {incoming}")

            correlation_id = incoming["correlation_id"]
            if IDEMPOTENCY_ENABLED and correlation_id in completed_correlation_ids:
                print(f"Writer duplicate skipped: {correlation_id}")
                await consumer.commit()
                continue

            if PROCESSING_DELAY_SECONDS:
                print(f"Writer processing delay: {PROCESSING_DELAY_SECONDS} seconds")
                await asyncio.sleep(PROCESSING_DELAY_SECONDS)

            if incoming.get("force_failure"):
                for attempt in range(1, MAX_RETRIES + 1):
                    print(f"Writer retry {attempt}/{MAX_RETRIES}: {correlation_id}")
                    await asyncio.sleep(1)

                dead_letter = {
                    "correlation_id": correlation_id,
                    "error": "Forced poison-message failure",
                    "retry_count": MAX_RETRIES,
                    "original_message": incoming,
                }
                await producer.send_and_wait(DEAD_LETTER_TOPIC, dead_letter)
                await consumer.commit()
                print(f"Writer sent to dead letter: {dead_letter}")
                continue

            draft = await asyncio.to_thread(
                ask_model,
                "Write a concise, practical answer for a community sports league "
                "manager. Follow the supplied plan. Return plain text only.",
                f"Question: {incoming['question']}\n\nPlan: {incoming['plan']}",
            )
            draft_message = {
                "correlation_id": correlation_id,
                "question": incoming["question"],
                "plan": incoming["plan"],
                "draft": draft,
            }

            await producer.send_and_wait(DRAFTS_TOPIC, draft_message)
            if IDEMPOTENCY_ENABLED:
                completed_correlation_ids.add(correlation_id)
            await consumer.commit()
            print(f"Writer sent: {draft_message}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
