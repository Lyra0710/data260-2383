import asyncio
import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import (
    ENTITY_REQUEST_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
)

# Store fixtures in memory for this Kafka exercise.
fixtures = {}


def is_non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_fixture(data: dict) -> str | None:
    required_fields = [
        "fixture_name",
        "teams",
        "fixture_code",
        "available_slots",
        "venue_id",
    ]

    for field in required_fields:
        if field not in data:
            return f"Missing required field: {field}"

    if not is_non_empty_text(data["fixture_name"]):
        return "fixture_name cannot be empty"

    teams = data["teams"]
    if not isinstance(teams, list) or not teams:
        return "teams must be a non-empty list"

    if not all(is_non_empty_text(team) for team in teams):
        return "teams must contain non-empty names"

    if not is_non_empty_text(data["fixture_code"]):
        return "fixture_code cannot be empty"

    available_slots = data["available_slots"]
    if (
        not isinstance(available_slots, int)
        or isinstance(available_slots, bool)
        or available_slots < 0
    ):
        return "available_slots must be a non-negative integer"

    venue_id = data["venue_id"]
    if not isinstance(venue_id, int) or isinstance(venue_id, bool) or venue_id <= 0:
        return "venue_id must be a positive integer"

    return None


def create_fixture(data: dict) -> dict:
    error = validate_fixture(data)

    if error:
        return {
            "success": False,
            "error": error,
        }

    # Generate the entity ID in the worker as required.
    entity_id = str(uuid.uuid4())

    fixture = {
        "entity_id": entity_id,
        **data,
    }

    fixtures[entity_id] = fixture

    return {
        "success": True,
        "entity_id": entity_id,
        "message": "Fixture created",
    }


def get_fixture(data: dict) -> dict:
    entity_id = data.get("entity_id")

    if not is_non_empty_text(entity_id):
        return {
            "success": False,
            "error": "Missing required field: entity_id",
        }

    fixture = fixtures.get(entity_id)

    if fixture is None:
        return {
            "success": False,
            "error": "Fixture not found",
        }

    return {
        "success": True,
        "entity": fixture,
    }


def process_request(request: dict) -> dict:
    operation = request.get("operation")
    data = request.get("data")

    if not isinstance(data, dict):
        return {
            "success": False,
            "error": "data must be an object",
        }

    if operation == "CREATE_FIXTURE":
        return create_fixture(data)

    if operation == "GET_FIXTURE":
        return get_fixture(data)

    return {
        "success": False,
        "error": "Unknown operation",
    }


async def main():
    consumer = AIOKafkaConsumer(
        ENTITY_REQUEST_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="s2383_entity_worker",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        auto_offset_reset="earliest",
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )

    await consumer.start()
    await producer.start()

    print("Consumer is ready and listening...")

    try:
        async for message in consumer:
            request = message.value

            print(f"Worker received: {request}")

            correlation_id = request.get("correlation_id")
            reply_to = request.get("reply_to")

            response = process_request(request)

            # Preserve the original correlation ID in every response.
            response["correlation_id"] = correlation_id

            print(f"Worker processed: {response}")

            if reply_to:
                await producer.send_and_wait(reply_to, response)
                print(f"Worker sent response: {response}")

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
