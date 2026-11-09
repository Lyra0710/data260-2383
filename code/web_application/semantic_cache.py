import os
import re
import uuid

import numpy as np
import redis
from redis.commands.search.field import TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

PREFIX = os.getenv("PREFIX", "s2383")
CACHE_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85"))
INDEX_NAME = f"{PREFIX}:semantic-cache:index:v2"
ENTRY_PREFIX = f"{PREFIX}:semantic-cache:entry:v2:"
DATA_VERSION_KEY = f"{PREFIX}:semantic-cache:data-version"


class SemanticResponseCache:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    def current_data_version(self) -> str:
        self.redis_client.setnx(DATA_VERSION_KEY, "0")
        return str(self.redis_client.get(DATA_VERSION_KEY))

    def bump_data_version(self) -> str:
        return str(self.redis_client.incr(DATA_VERSION_KEY))

    def find_similar(
        self,
        embedding: list[float],
        data_version: str,
        user_id: str,
        session_id: str,
        context_key: str,
        threshold: float,
    ) -> dict | None:
        self.ensure_index(len(embedding))
        user_tag = self.escape_tag(user_id)
        session_tag = self.escape_tag(session_id)
        context_tag = self.escape_tag(context_key)
        query = (
            Query(
                f"(@user_id:{{{user_tag}}} @session_id:{{{session_tag}}} "
                f"@context_key:{{{context_tag}}})"
                "=>[KNN 1 @embedding $embedding AS distance]"
            )
            .return_fields("answer", "data_version", "distance")
            .sort_by("distance")
            .dialect(2)
        )
        result = self.redis_client.ft(INDEX_NAME).search(
            query,
            query_params={"embedding": self.vector_bytes(embedding)},
        )
        if not result.docs:
            return None

        match = result.docs[0]
        similarity_score = 1 - float(match.distance)
        if similarity_score < threshold or match.data_version != data_version:
            return None

        return {
            "answer": match.answer,
            "similarity_score": similarity_score,
        }

    def store(
        self,
        query: str,
        embedding: list[float],
        answer: str,
        data_version: str,
        user_id: str,
        session_id: str,
        context_key: str,
    ) -> None:
        self.ensure_index(len(embedding))
        key = f"{ENTRY_PREFIX}{uuid.uuid4()}"
        self.redis_client.hset(
            key,
            mapping={
                "query": query,
                "embedding": self.vector_bytes(embedding),
                "answer": answer,
                "data_version": data_version,
                "user_id": user_id,
                "session_id": session_id,
                "context_key": context_key,
            },
        )

    def ensure_index(self, dimensions: int) -> None:
        try:
            self.redis_client.ft(INDEX_NAME).info()
            return
        except redis.ResponseError:
            pass

        self.redis_client.ft(INDEX_NAME).create_index(
            (
                TextField("query"),
                TextField("answer"),
                TagField("data_version"),
                TagField("user_id"),
                TagField("session_id"),
                TagField("context_key"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": dimensions,
                        "DISTANCE_METRIC": "COSINE",
                    },
                ),
            ),
            definition=IndexDefinition(
                prefix=[ENTRY_PREFIX],
                index_type=IndexType.HASH,
            ),
        )

    @staticmethod
    def vector_bytes(embedding: list[float]) -> bytes:
        return np.asarray(embedding, dtype=np.float32).tobytes()

    @staticmethod
    def escape_tag(value: str) -> str:
        return re.sub(r"([^A-Za-z0-9_])", r"\\\1", value)


semantic_response_cache = SemanticResponseCache(
    redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
)
