from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from mongo_db import fixtures_collection
from schemas import DocumentFixtureCreate


router = APIRouter(
    prefix="/api/documents",
    tags=["MongoDB Documents"],
)


@router.post("", status_code=201)
def create_fixture(fixture: DocumentFixtureCreate):
    now = datetime.now(timezone.utc)

    document = fixture.model_dump(mode="json")
    document["scheduled_at"] = fixture.scheduled_at
    document["created_at"] = now
    document["updated_at"] = now

    try:
        result = fixtures_collection.insert_one(document)
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to create fixture",
        )

    document["_id"] = str(result.inserted_id)

    return document