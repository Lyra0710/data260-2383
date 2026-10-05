from dbm import dumb
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from schemas import (
    FixtureCreate,
    FixtureOut,
    FixtureUpdate,
    RelatedItemOut,
    VenueCreate,
    VenueOut,
    VenueUpdate,
)

from sqlalchemy.orm import Session as DbSession, selectinload
from fastapi.responses import JSONResponse
import models
from db import (
    Base,
    engine,
    get_db,
    get_sql_query_count,
    reset_sql_query_count,
)
from models import Fixture, User, Venue
from routers.auth import get_current_user, router as auth_router
import os
import uvicorn

from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = FastAPI(
    title="Community Sports League Fixtures",
)

app.include_router(auth_router)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)




def fixture_to_dict(fixture: Fixture):
    return {
        "id": fixture.id,
        "fixture_name": fixture.fixture_name,
        "teams": fixture.teams,
        "fixture_code": fixture.fixture_code,
        "available_slots": fixture.available_slots,
        "venue_id": fixture.venue_id,
        "created_at": fixture.created_at,
        "updated_at": fixture.updated_at,
        "related_items": [
            {
                "id": item.id,
                "label": item.label,
                "details": item.details,
            }
            for item in fixture.related_items
        ],
    }

def venue_to_dict(venue: Venue):
    return {
        "id": venue.id,
        "name": venue.name,
        "address": venue.address,
        "code": venue.code,
        "created_at": venue.created_at,
        "updated_at": venue.updated_at,
    }

def fixture_list_response(fixtures):
    response_data = [
        fixture_to_dict(fixture)
        for fixture in fixtures
    ]

    return JSONResponse(
        content=jsonable_encoder(response_data),
        headers={
            "X-SQL-Query-Count": str(
                get_sql_query_count()
            ),
        },
    )

@app.get("/")
def root():
    return {
        "message": "Community Sports League Fixtures API",
    }

@app.get("/api/fixtures", response_model=list[FixtureOut])
def list_fixtures(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size     
    reset_sql_query_count()
    fixtures = (
        db.query(Fixture)
        .options(selectinload(Fixture.related_items))
        .order_by(Fixture.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return fixture_list_response(fixtures)

@app.get("/api/fixtures/naive", response_model=list[FixtureOut])
def list_fixtures_naive( # Without selectinload, SQLAlchemy waits until the code asks for fixture.related_items, then it queries the database separately for that one fixture.
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    reset_sql_query_count()
    fixtures = (
        db.query(Fixture)
        .order_by(Fixture.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return fixture_list_response(fixtures)

@app.get("/api/fixtures/{fixture_id}", response_model=FixtureOut)
def get_fixture(
    fixture_id: int,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fixture = (
        db.query(Fixture)
        .options(selectinload(Fixture.related_items))
        .filter(Fixture.id == fixture_id)
        .first()
    )

    if not fixture:
        raise HTTPException(
            status_code=404,
            detail="Fixture not found",
        )

    return fixture_to_dict(fixture)


@app.post("/api/fixtures", status_code=201, response_model=FixtureOut)
def create_fixture(
    request_data: FixtureCreate,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    venue = db.get(Venue, request_data.venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    fixture = Fixture(
        fixture_name=request_data.fixture_name,
        teams=request_data.teams,
        fixture_code=request_data.fixture_code,
        available_slots=request_data.available_slots,
        venue_id=request_data.venue_id,
    )

    try:
        db.add(fixture)
        db.commit()
        db.refresh(fixture)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Fixture code already exists",
        )

    return fixture_to_dict(fixture)


@app.put("/api/fixtures/{fixture_id}", response_model=FixtureOut)
def update_fixture(
    fixture_id: int,
    request_data: FixtureUpdate,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fixture = db.get(Fixture, fixture_id)

    if not fixture:
        raise HTTPException(
            status_code=404,
            detail="Fixture not found",
        )

    venue = db.get(Venue, request_data.venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    fixture.fixture_name = request_data.fixture_name
    fixture.teams = request_data.teams
    fixture.fixture_code = request_data.fixture_code
    fixture.available_slots = request_data.available_slots
    fixture.venue_id = request_data.venue_id

    try:
        db.commit()
        db.refresh(fixture)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Fixture code already exists",
        )

    return fixture_to_dict(fixture)


@app.delete("/api/fixtures/{fixture_id}")
def delete_fixture(
    fixture_id: int,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fixture = db.get(Fixture, fixture_id)

    if not fixture:
        raise HTTPException(
            status_code=404,
            detail="Fixture not found",
        )

    db.delete(fixture)
    db.commit()

    return {
        "message": "Fixture deleted",
        "id": fixture_id,
    }

@app.post("/api/venues", status_code=201, response_model=VenueOut)
def create_venue(
    request_data: VenueCreate, # FastAPI reads the JSON request body and validates it using the VenueCreate Pydantic model.
    db: DbSession = Depends(get_db), # database session using the existing get_db() dependency.
    user: User = Depends(get_current_user),# checks that the user is logged in
):
    venue = Venue(
        name=request_data.name,
        address=request_data.address,
        code=request_data.code,
    )

    try:
        db.add(venue)
        db.commit()
        db.refresh(venue)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Venue code already exists",
        )

    return venue_to_dict(venue)


@app.get("/api/venues", response_model=list[VenueOut])
def list_venues(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size # calculates how many records to skip for the current page 

    venues = (
        db.query(Venue)
        .order_by(Venue.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return [
        venue_to_dict(venue)
        for venue in venues
    ]


@app.get("/api/venues/{venue_id}", response_model=VenueOut)
def get_venue(
    venue_id: int,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    return venue_to_dict(venue)


@app.put("/api/venues/{venue_id}", response_model=VenueOut)
def update_venue(
    venue_id: int,
    request_data: VenueUpdate,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    venue.name = request_data.name
    venue.address = request_data.address
    venue.code = request_data.code

    try:
        db.commit()
        db.refresh(venue)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Venue code already exists",
        )

    return venue_to_dict(venue)


@app.delete("/api/venues/{venue_id}")
def delete_venue(
    venue_id: int,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    fixture_exists = (
        db.query(Fixture)
        .filter(Fixture.venue_id == venue_id)
        .first()
    )

    if fixture_exists:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a venue that has fixtures",
        )

    db.delete(venue)
    db.commit()

    return {
        "message": "Venue deleted",
        "id": venue_id,
    }

@app.get("/api/venues/{venue_id}/fixtures")
def list_fixtures_by_venue(
    venue_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    venue = db.get(Venue, venue_id)

    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found",
        )

    offset = (page - 1) * page_size

    fixtures = (
        db.query(Fixture)
        .options(selectinload(Fixture.related_items))
        .filter(Fixture.venue_id == venue_id)
        .order_by(Fixture.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return [
        fixture_to_dict(fixture)
        for fixture in fixtures
    ]
if __name__ == "__main__":

    uvicorn.run(
        app,
        port=int(os.environ["APP_PORT"]),
    )
# ------------- in-memory fixture implementation homework 3---------------#
# import os
# import uvicorn
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel
# from pathlib import Path
# from starlette.middleware.sessions import SessionMiddleware
# from routers.auth import router as auth_router
# from secret import SECRET_KEY

# app = FastAPI()
# APP_DIR = Path(__file__).resolve().parent
# STATIC_DIR = APP_DIR / "static"

# # Secret key for session signing
# # SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key") # imported SECRET_KEY from secret.py instead of using a visible fallback code. 

# # Enable session support - required for auth
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=SECRET_KEY,
#     https_only=True,
#     # https_only = False, # temporarily added this for local test development. 
#     same_site="lax",
#     max_age=3600
# )


# # Serves static files (HTML, CSS, JS) from the 'web_application' directory
# app.mount(
#     "/static",
#     StaticFiles(directory=STATIC_DIR),
#     name="static"
# )

# # Register routes
# app.include_router(auth_router)


# # previous home endpoint returns the older index.html file which is the form. 
# @app.get("/fixtures")
# async def fixtures_page():
#     return FileResponse(APP_DIR / "static" / "index.html")

# # Model for fixture data - FastAPI uses this to validate the JSON body of a request
# class Fixture(BaseModel):
#     fixtureName: str
#     teams: str
# # hardcoded input ONLY for testing and to make sure deleting the highest record does not immidiately delte the record required for iD 1 update. 
# fixtures = [
#     {"id": 1, "fixtureName": "Community Soccer Semifinal", "teams": "Falcons vs Tigers"}
# ]

# # fastapi uses class to read JSON request body and check if the required fields exist, and their types. 
# # converts the JSON object to a python dict with the keys defined in the class. 
# class FixtureCreate(BaseModel):
#     fixtureName: str
#     teams:str

# class FixtureUpdate(BaseModel):
#     fixtureName: str
#     teams: str

# @app.get("/api/fixtures")
# async def get_fixtures(search: str | None = None):
#     if not search or not search.strip():
#         return fixtures

#     search_term = search.strip().casefold()

#     return [
#         item
#         for item in fixtures
#         if (
#             search_term in item["fixtureName"].casefold() # case insensitive search
#             or search_term in item["teams"].casefold()
#         )
#     ]

# @app.post("/api/fixtures")
# async def create_fixture(fixture: FixtureCreate):
#     new_id = max(
#         [item["id"] for item in fixtures],
#         default=0
#     ) + 1

#     new_fixture = {
#         "id": new_id,
#         **fixture.model_dump() # unpacks the key-value pairs of the dictionary into this new dictionary
#     }

#     fixtures.append(new_fixture)

#     return new_fixture

# @app.put("/api/fixtures/1")
# async def update_fixture(fixture: FixtureUpdate):
#     for item in fixtures:
#         if item["id"] == 1:
#             item["fixtureName"] = fixture.fixtureName
#             item["teams"] = fixture.teams
#             return item

#     raise HTTPException(
#         status_code=404,
#         detail="Fixture ID 1 not found"
#     )

# @app.delete("/api/fixtures/highest")
# async def delete_highest_fixture():
#     if not fixtures:
#         raise HTTPException(
#             status_code=404,
#             detail="No fixtures available to delete"
#         )

#     highest_fixture = max(
#         fixtures,
#         key=lambda item: item["id"]
#     )

#     fixtures.remove(highest_fixture)

#     return highest_fixture