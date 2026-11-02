import asyncio

from kafka.config import DRAFTS_TOPIC, FINAL_TOPIC, PREFIX
from kafka.pipeline import ask_model, message_consumer, message_producer


async def main() -> None:
    consumer = message_consumer(DRAFTS_TOPIC, f"{PREFIX}_reviewer")
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")
    print("Reviewer is ready and listening...")

    try:
        async for message in consumer:
            incoming = message.value
            print(f"Reviewer received: {incoming}")

            answer = await asyncio.to_thread(
                ask_model,
                "Review the draft for correctness, clarity, and practicality. "
                "Return an improved final answer only.",
                f"Question: {incoming['question']}\n\nDraft: {incoming['draft']}",
            )
            final_message = {
                "correlation_id": incoming["correlation_id"],
                "status": "approved",
                "answer": answer,
            }

            await producer.send_and_wait(FINAL_TOPIC, final_message)
            await consumer.commit()
            print(f"Reviewer sent: {final_message}")
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
