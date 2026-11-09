import logging
import time

from fastapi import APIRouter
from memory_repository import aggregate_user_memory, fetch_memory_snapshot
from memory_service import (
    COMPACT_SHORT_TERM_N,
    SHORT_TERM_N,
    embed_texts,
    generate_reply,
)
from schemas import ChatRequest, ChatResponse
from semantic_cache import CACHE_THRESHOLD, semantic_response_cache

router = APIRouter(
    prefix="/api",
    tags=["Memory"],
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)
    logger.propagate = False


@router.get("/memory-config")
def get_memory_config():
    return {
        "short_term_n": SHORT_TERM_N,
        "compact_short_term_n": COMPACT_SHORT_TERM_N,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    started_at = time.perf_counter()
    session_id = request.session_id or request.user_id
    query_embedding = embed_texts([request.message])[0]
    data_version = semantic_response_cache.current_data_version()
    cached_response = semantic_response_cache.find_similar(
        query_embedding,
        data_version,
        request.user_id,
        session_id,
        CACHE_THRESHOLD,
    )

    if cached_response is not None:
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "Semantic cache hit: similarity_score=%.4f latency_ms=%.2f",
            cached_response["similarity_score"],
            latency_ms,
        )
        return {
            "reply": cached_response["answer"],
            "memory": None,
            "is_cached": True,
            "similarity_score": cached_response["similarity_score"],
            "latency_ms": latency_ms,
        }

    response = generate_reply(
        request.user_id,
        session_id,
        request.message,
        experiment_id=request.experiment_id,
        experiment_phase=request.experiment_phase,
    )
    semantic_response_cache.store(
        request.message,
        query_embedding,
        response["reply"],
        data_version,
        request.user_id,
        session_id,
    )
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info("Semantic cache miss: latency_ms=%.2f", latency_ms)

    return {
        **response,
        "is_cached": False,
        "similarity_score": None,
        "latency_ms": latency_ms,
    }


@router.get("/memory/{user_id}")
def get_memory(user_id: str):
    return fetch_memory_snapshot(user_id)


@router.get("/aggregate/{user_id}")
def get_aggregate(user_id: str):
    return aggregate_user_memory(user_id)
