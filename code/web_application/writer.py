import asyncio

from kafka.config import DRAFTS_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import ask_model, message_consumer, message_producer


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

            draft = await asyncio.to_thread(
                ask_model,
                "Write a concise, practical answer for a community sports league "
                "manager. Follow the supplied plan. Return plain text only.",
                f"Question: {incoming['question']}\n\nPlan: {incoming['plan']}",
            )
            draft_message = {
                "correlation_id": incoming["correlation_id"],
                "question": incoming["question"],
                "plan": incoming["plan"],
                "draft": draft,
            }

            await producer.send_and_wait(DRAFTS_TOPIC, draft_message)
            await consumer.commit()
            print(f"Writer sent: {draft_message}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
