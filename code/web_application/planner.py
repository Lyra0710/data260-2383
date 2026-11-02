import asyncio

from kafka.config import INBOX_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import ask_model, message_consumer, message_producer


async def main() -> None:
    consumer = message_consumer(INBOX_TOPIC, f"{PREFIX}_planner")
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")
    print("Planner is ready and listening...")

    try:
        async for message in consumer:
            incoming = message.value
            print(f"Planner received: {incoming}")

            plan = await asyncio.to_thread(
                ask_model,
                "Create a short three-step plan for answering a community sports "
                "league fixture question. Return plain text only.",
                incoming["question"],
            )
            task = {
                "correlation_id": incoming["correlation_id"],
                "question": incoming["question"],
                "plan": plan,
            }

            await producer.send_and_wait(TASKS_TOPIC, task)
            await consumer.commit()
            print(f"Planner sent: {task}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
