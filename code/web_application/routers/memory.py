from fastapi import APIRouter

from memory_repository import aggregate_user_memory, fetch_memory_snapshot
from memory_service import COMPACT_SHORT_TERM_N, SHORT_TERM_N, generate_reply
from schemas import ChatRequest, ChatResponse


router = APIRouter(
    prefix="/api",
    tags=["Memory"],
)


@router.get("/memory-config")
def get_memory_config():
    return {
        "short_term_n": SHORT_TERM_N,
        "compact_short_term_n": COMPACT_SHORT_TERM_N,
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id or request.user_id
    return generate_reply(
        request.user_id,
        session_id,
        request.message,
        experiment_id=request.experiment_id,
        experiment_phase=request.experiment_phase,
    )


@router.get("/memory/{user_id}")
def get_memory(user_id: str):
    return fetch_memory_snapshot(user_id)


@router.get("/aggregate/{user_id}")
def get_aggregate(user_id: str):
    return aggregate_user_memory(user_id)
