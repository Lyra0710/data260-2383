"""Run one observable HW10 Kafka pipeline request.

Start the Planner, Writer, Reviewer, and evaluator workers before running this
script. Use ``--force-failure`` to exercise the Writer dead-letter path.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaConsumer
from hw10_observability import span
from kafka.config import (
    DEAD_LETTER_TOPIC,
    EVALUATION_TOPIC,
    FINAL_TOPIC,
    INBOX_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    PREFIX,
)
from kafka.pipeline import message_producer
from memory_service import embed_texts
from semantic_cache import CACHE_THRESHOLD, semantic_response_cache

QUESTION = (
    "What should a league manager confirm before scheduling a weekday-evening "
    "tennis fixture at Spartan Tennis Complex?"
)
WAIT_SECONDS = float(os.getenv("HW10_PIPELINE_WAIT_SECONDS", "360"))
CACHE_USER_ID = "hw10-observability"
CACHE_SESSION_ID = "hw10-pipeline"


def consumer(topic: str, trace_id: str) -> AIOKafkaConsumer:
    return AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"{PREFIX}_hw10_runner_{topic}_{trace_id}",
        auto_offset_reset="latest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


async def wait_for_message(
    kafka_consumer: AIOKafkaConsumer,
    trace_id: str,
) -> dict:
    async with asyncio.timeout(WAIT_SECONDS):
        async for message in kafka_consumer:
            message_trace_id = message.value.get(
                "trace_id", message.value.get("correlation_id")
            )
            if message_trace_id == trace_id:
                return message.value
    raise TimeoutError(f"Timed out waiting for trace_id={trace_id}")


async def cache_lookup(
    trace_id: str, question: str, context_key: str
) -> tuple[list[float], str, dict | None]:
    """Look up this pipeline question in the existing semantic cache."""
    metadata = {"path": "unknown"}
    with span(trace_id, "cache_lookup", metadata):
        embedding = await asyncio.to_thread(embed_texts, [question])
        data_version = await asyncio.to_thread(
            semantic_response_cache.current_data_version
        )
        cached_response = await asyncio.to_thread(
            semantic_response_cache.find_similar,
            embedding[0],
            data_version,
            CACHE_USER_ID,
            CACHE_SESSION_ID,
            context_key,
            CACHE_THRESHOLD,
        )
        metadata["path"] = "hit" if cached_response else "miss"
    return embedding[0], data_version, cached_response


async def cache_answer(
    question: str,
    embedding: list[float],
    data_version: str,
    answer: str,
    context_key: str,
) -> None:
    await asyncio.to_thread(
        semantic_response_cache.store,
        question,
        embedding,
        answer,
        data_version,
        CACHE_USER_ID,
        CACHE_SESSION_ID,
        context_key,
    )


async def run(
    force_failure: bool,
    question: str = QUESTION,
    cache_scope: str | None = None,
) -> dict:
    trace_id = str(uuid.uuid4())
    context_key = cache_scope or (
        "force-failure" if force_failure else "successful-pipeline"
    )
    embedding, data_version, cached_response = await cache_lookup(
        trace_id, question, context_key
    )
    if cached_response is not None:
        return {
            "trace_id": trace_id,
            "path": "cache_hit",
            "answer": cached_response["answer"],
            "similarity_score": cached_response["similarity_score"],
        }

    final_consumer = consumer(FINAL_TOPIC, trace_id)
    evaluation_consumer = consumer(EVALUATION_TOPIC, trace_id)
    dead_letter_consumer = consumer(DEAD_LETTER_TOPIC, trace_id)
    producer = message_producer()
    started_clients = []

    try:
        for client in (
            final_consumer,
            evaluation_consumer,
            dead_letter_consumer,
            producer,
        ):
            await client.start()
            started_clients.append(client)

        request = {
            "correlation_id": trace_id,
            "trace_id": trace_id,
            "question": question,
        }
        if force_failure:
            request["force_failure"] = True

        with span(trace_id, "inbox", {"cache_path": "miss"}):
            await producer.send_and_wait(INBOX_TOPIC, request)
        if force_failure:
            result = await wait_for_message(dead_letter_consumer, trace_id)
            return {"trace_id": trace_id, "path": "failed", "dead_letter": result}

        final_message = await wait_for_message(final_consumer, trace_id)
        evaluation = await wait_for_message(evaluation_consumer, trace_id)
        await cache_answer(
            question,
            embedding,
            data_version,
            final_message["answer"],
            context_key,
        )
        return {
            "trace_id": trace_id,
            "path": "cache_miss",
            "final": final_message,
            "evaluation": evaluation,
        }
    finally:
        for client in reversed(started_clients):
            await client.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force-failure",
        action="store_true",
        help="send a poison message and wait for the Writer dead-letter result",
    )
    parser.add_argument(
        "--question",
        default=QUESTION,
        help="question sent through the semantic cache and Kafka pipeline",
    )
    parser.add_argument(
        "--cache-scope",
        help="use a new scope to guarantee an isolated semantic-cache miss",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    print(
        json.dumps(
            asyncio.run(
                run(
                    arguments.force_failure,
                    arguments.question,
                    arguments.cache_scope,
                )
            ),
            indent=2,
        )
    )
