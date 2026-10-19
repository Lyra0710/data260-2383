from fastapi import APIRouter

from memory_repository import aggregate_user_memory, fetch_memory_snapshot
from memory_service import generate_reply
from schemas import ChatRequest, ChatResponse


router = APIRouter(
    prefix="/api",
    tags=["Memory"],
)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id or request.user_id
    return generate_reply(request.user_id, session_id, request.message)


@router.get("/memory/{user_id}")
def get_memory(user_id: str):
    return fetch_memory_snapshot(user_id)


@router.get("/aggregate/{user_id}")
def get_aggregate(user_id: str):
    return aggregate_user_memory(user_id)
