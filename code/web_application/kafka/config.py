import os

# Kafka broker address.
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

# Student-specific Kafka topic prefix.
PREFIX = "s2383"
VERIFY_SEED = 262383

# Part 1 request/response topics.
ENTITY_REQUEST_TOPIC = f"{PREFIX}_entity_requests"
ENTITY_RESPONSE_TOPIC = f"{PREFIX}_entity_responses"

# Part 2 pipeline topics.
INBOX_TOPIC = f"{PREFIX}_inbox"
TASKS_TOPIC = f"{PREFIX}_tasks"
DRAFTS_TOPIC = f"{PREFIX}_drafts"
FINAL_TOPIC = f"{PREFIX}_final"

# Part 3 failure-handling topic.
DEAD_LETTER_TOPIC = f"{PREFIX}_dead_letter"
