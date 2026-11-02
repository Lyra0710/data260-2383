import json
import sys
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from .config import KAFKA_BOOTSTRAP_SERVERS

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.model_client import complete  # noqa: E402


def message_producer() -> AIOKafkaProducer:
    return AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )


def message_consumer(topic: str, group_id: str) -> AIOKafkaConsumer:
    return AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        enable_auto_commit=False,
        auto_offset_reset="latest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )


def ask_model(instruction: str, content: str) -> str:
    response = complete(
        [
            {"role": "system", "content": instruction},
            {"role": "user", "content": content},
        ],
        model="qwen3:8b",
        temperature=0.0,
        max_tokens=250,
    )
    return response.content.strip()
