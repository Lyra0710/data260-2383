from fastapi import APIRouter, HTTPException

from file_memory_service import run_command
from schemas import FileMemoryCommandRequest


router = APIRouter(prefix="/api/file-memory", tags=["File Memory"])


@router.post("/command")
def file_memory_command(request: FileMemoryCommandRequest):
    try:
        return run_command(request.command, request.recent_messages)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
