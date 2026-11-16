"""Kafka worker that evaluates one completed Planner/Writer/Reviewer request."""

from __future__ import annotations

import asyncio
import json

from aiokafka import AIOKafkaProducer
from evaluator import evaluate_messages
from hw10_observability import span
from kafka.config import EVALUATION_TOPIC, FINAL_TOPIC, KAFKA_BOOTSTRAP_SERVERS, PREFIX
from kafka.pipeline import message_consumer

EVALUATION_TIMEOUT_SECONDS = 10


def producer() -> AIOKafkaProducer:
    return AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def malformed_result(message: dict, error: str) -> dict:
    correlation_id = str(message.get("correlation_id", ""))
    return {
        "correlation_id": correlation_id,
        "trace_id": str(message.get("trace_id", correlation_id)),
        "status": "error",
        "error": error,
    }


async def evaluate_final_message(message: dict) -> dict:
    correlation_id = message.get("correlation_id")
    required_fields = ("question", "plan", "draft", "answer")
    if not correlation_id:
        return malformed_result(message, "Missing correlation_id")

    missing = [field for field in required_fields if not message.get(field)]
    if missing:
        return malformed_result(
            message,
            f"Missing evaluation fields: {', '.join(missing)}",
        )

    trace_id = str(message.get("trace_id", correlation_id))
    plan_message = {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "question": message["question"],
        "plan": message["plan"],
    }
    draft_message = {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "question": message["question"],
        "plan": message["plan"],
        "draft": message["draft"],
    }

    try:
        with span(trace_id, "evaluation"):
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    evaluate_messages,
                    plan_message,
                    draft_message,
                    message,
                ),
                timeout=EVALUATION_TIMEOUT_SECONDS,
            )
    except Exception as error:
        return malformed_result(message, f"Evaluation failed: {error}")

    return {
        "correlation_id": correlation_id,
        "trace_id": trace_id,
        "status": "complete",
        "evaluation": result,
    }


async def main() -> None:
    consumer = message_consumer(FINAL_TOPIC, f"{PREFIX}_evaluator")
    output = producer()
    await consumer.start()
    await output.start()
    print("Evaluator is ready and listening...")

    try:
        async for kafka_message in consumer:
            result = await evaluate_final_message(kafka_message.value)
            await output.send_and_wait(EVALUATION_TOPIC, result)
            await consumer.commit()
            print(f"Evaluator sent: {result}")
    finally:
        await consumer.stop()
        await output.stop()


if __name__ == "__main__":
    asyncio.run(main())
