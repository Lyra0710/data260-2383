from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from mongo_db import fixtures_collection
from schemas import DocumentFixtureCreate, DocumentFixtureUpdate


router = APIRouter(
    prefix="/api/documents",
    tags=["MongoDB Documents"],
)


def fixture_response(document: dict) -> dict:
    document["_id"] = str(document["_id"])
    return document


def fixture_object_id(fixture_id: str) -> ObjectId:
    try:
        return ObjectId(fixture_id)
    except InvalidId as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid fixture ID",
        ) from error


@router.post("", status_code=201)
def create_fixture(fixture: DocumentFixtureCreate):
    now = datetime.now(timezone.utc)

    document = fixture.model_dump()
    document.update(created_at=now, updated_at=now)

    try:
        result = fixtures_collection.insert_one(document)
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to create fixture",
        )

    document["_id"] = result.inserted_id

    return fixture_response(document)


@router.get("")
def list_fixtures():
    try:
        fixtures = fixtures_collection.find().sort("scheduled_at", 1)
        return [fixture_response(fixture) for fixture in fixtures]
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve fixtures",
        )


@router.get("/{fixture_id}")
def get_fixture(fixture_id: str):
    try:
        fixture = fixtures_collection.find_one(
            {"_id": fixture_object_id(fixture_id)}
        )
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve fixture",
        )

    if fixture is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    return fixture_response(fixture)


@router.put("/{fixture_id}")
def update_fixture(fixture_id: str, fixture: DocumentFixtureUpdate):
    updates = fixture.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No update fields provided")

    updates["updated_at"] = datetime.now(timezone.utc)

    try:
        result = fixtures_collection.find_one_and_update(
            {"_id": fixture_object_id(fixture_id)},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to update fixture",
        )

    if result is None:
        raise HTTPException(status_code=404, detail="Fixture not found")

    return fixture_response(result)


@router.delete("/{fixture_id}", status_code=204)
def delete_fixture(fixture_id: str):
    try:
        result = fixtures_collection.delete_one(
            {"_id": fixture_object_id(fixture_id)}
        )
    except PyMongoError:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete fixture",
        )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fixture not found")
