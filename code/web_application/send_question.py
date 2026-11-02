import asyncio
import uuid

from kafka.config import FINAL_TOPIC, INBOX_TOPIC, PREFIX
from kafka.pipeline import message_consumer, message_producer

QUESTION = (
    "How should a league manager schedule a weekday-evening tennis fixture "
    "at Spartan Tennis Complex?"
)


async def main() -> None:
    correlation_id = str(uuid.uuid4())
    consumer = message_consumer(FINAL_TOPIC, f"{PREFIX}_final_reader_{correlation_id}")
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")

    try:
        question_message = {
            "correlation_id": correlation_id,
            "question": QUESTION,
        }
        await producer.send_and_wait(INBOX_TOPIC, question_message)
        print(f"Question sender sent: {question_message}")

        async for message in consumer:
            final_message = message.value
            if final_message.get("correlation_id") == correlation_id:
                print(f"Question sender received final: {final_message}")
                await consumer.commit()
                return
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
