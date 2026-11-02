import asyncio
import uuid

from kafka.config import DRAFTS_TOPIC, PREFIX, TASKS_TOPIC
from kafka.pipeline import message_consumer, message_producer


async def main() -> None:
    correlation_id = str(uuid.uuid4())
    consumer = message_consumer(
        DRAFTS_TOPIC,
        f"{PREFIX}_restart_reader_{correlation_id}",
    )
    producer = message_producer()

    await consumer.start()
    await producer.start()
    print("Student: Ananya")
    print(f"Consumer-death test correlation_id: {correlation_id}")

    task = {
        "correlation_id": correlation_id,
        "question": "How should a league manager confirm a tennis fixture?",
        "plan": "1. Confirm availability. 2. Notify participants. 3. Record details.",
    }

    try:
        await producer.send_and_wait(TASKS_TOPIC, task)
        print(f"Task sent before Writer restart: {task}")

        while True:
            message = await asyncio.wait_for(consumer.getone(), timeout=180)
            draft = message.value
            if draft.get("correlation_id") != correlation_id:
                continue

            print(f"Draft received after Writer restart: {draft}")
            await consumer.commit()
            return
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
