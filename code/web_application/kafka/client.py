import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import (
    ENTITY_REQUEST_TOPIC,
    ENTITY_RESPONSE_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
)


async def send_request(operation: str, data: dict, correlation_id: str) -> dict:
    request = {
        "correlation_id": correlation_id,
        "reply_to": ENTITY_RESPONSE_TOPIC,
        "operation": operation,
        "data": data,
    }

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )

    consumer = AIOKafkaConsumer(
        ENTITY_RESPONSE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"s2383_client_{correlation_id}",
        auto_offset_reset="latest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    await consumer.start()
    await producer.start()

    try:
        # Send the request to Kafka.
        await producer.send_and_wait(
            ENTITY_REQUEST_TOPIC,
            request,
        )

        print(f"Client sent: {request}")

        # Wait for the response with the matching correlation ID.
        async for message in consumer:
            response = message.value

            if response.get("correlation_id") == correlation_id:
                print(f"Client received: {response}")
                return response

    finally:
        await producer.stop()
        await consumer.stop()
