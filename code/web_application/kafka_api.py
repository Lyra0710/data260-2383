import asyncio
import uuid

from fastapi import FastAPI, HTTPException
from kafka.client import send_request

app = FastAPI(title="HW8 Kafka Fixture API")


@app.on_event("startup")
async def announce_startup() -> None:
    print("FastAPI service available at http://127.0.0.1:8583")


async def kafka_response(operation: str, data: dict) -> dict:
    correlation_id = str(uuid.uuid4())

    try:
        response = await asyncio.wait_for(
            send_request(operation, data, correlation_id),
            timeout=15,
        )
    except TimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail="Timed out waiting for Kafka response",
        ) from error

    print(f"FastAPI received response: {response}")
    return response


@app.get("/")
async def root() -> dict:
    return {"message": "HW8 Kafka Fixture API"}


@app.post("/kafka/fixtures")
async def create_fixture(data: dict) -> dict:
    return await kafka_response("CREATE_FIXTURE", data)


@app.get("/kafka/fixtures/{entity_id}")
async def get_fixture(entity_id: str) -> dict:
    return await kafka_response("GET_FIXTURE", {"entity_id": entity_id})
