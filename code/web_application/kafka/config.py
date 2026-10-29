import os

# Kafka broker address.
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

# Student-specific Kafka topic prefix.
PREFIX = "s2383"

# Part 1 request/response topics.
ENTITY_REQUEST_TOPIC = f"{PREFIX}_entity_requests"
ENTITY_RESPONSE_TOPIC = f"{PREFIX}_entity_responses"
