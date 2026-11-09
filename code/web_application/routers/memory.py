import logging
import time

from db import get_db
from fastapi import APIRouter, Depends, HTTPException
from memory_repository import aggregate_user_memory, fetch_memory_snapshot
from memory_service import (
    COMPACT_SHORT_TERM_N,
    SHORT_TERM_N,
    embed_texts,
    generate_reply,
)
from models import FixtureRelatedItem
from schemas import ChatRequest, ChatResponse
from semantic_cache import CACHE_THRESHOLD, semantic_response_cache
from sqlalchemy.orm import Session as DbSession

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


def related_item_context(request: ChatRequest, db: DbSession) -> tuple[str | None, str]:
    if request.related_item_id is None:
        return None, "none"

    related_item = db.get(FixtureRelatedItem, request.related_item_id)
    if related_item is None or (
        request.fixture_id is not None and related_item.fixture_id != request.fixture_id
    ):
        raise HTTPException(status_code=404, detail="Fixture related item not found")

    context = (
        f"Related item {related_item.id}: label={related_item.label}; "
        f"details={related_item.details or ''}"
    )
    return context, f"related_item_{related_item.id}"


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: DbSession = Depends(get_db)):
    started_at = time.perf_counter()
    session_id = request.session_id or request.user_id
    domain_context, context_key = related_item_context(request, db)
    query_embedding = embed_texts([request.message])[0]
    data_version = semantic_response_cache.current_data_version()
    cached_response = semantic_response_cache.find_similar(
        query_embedding,
        data_version,
        request.user_id,
        session_id,
        context_key,
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
        domain_context=domain_context,
    )
    semantic_response_cache.store(
        request.message,
        query_embedding,
        response["reply"],
        data_version,
        request.user_id,
        session_id,
        context_key,
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
