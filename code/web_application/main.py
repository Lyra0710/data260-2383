from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
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
from models import Fixture, User
from routers.auth import get_current_user, router as auth_router
import os
import uvicorn

app = FastAPI(
    title="Community Sports League Fixtures",
)

app.include_router(auth_router)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


class FixtureCreate(BaseModel):
    fixture_name: str
    teams: str


class FixtureUpdate(BaseModel):
    fixture_name: str
    teams: str


def fixture_to_dict(fixture: Fixture):
    return {
        "id": fixture.id,
        "fixture_name": fixture.fixture_name,
        "teams": fixture.teams,
        "related_items": [
            {
                "id": item.id,
                "label": item.label,
                "details": item.details,
            }
            for item in fixture.related_items
        ],
    }

def fixture_list_response(fixtures):
    response_data = [
        fixture_to_dict(fixture)
        for fixture in fixtures
    ]

    return JSONResponse(
        content=response_data,
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

@app.get("/api/fixtures")
def list_fixtures(
    
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reset_sql_query_count()
    fixtures = (
        db.query(Fixture)
        .options(selectinload(Fixture.related_items))
        .order_by(Fixture.id)
        .limit(page_size)
        .all()
    )

    return fixture_list_response(fixtures)

@app.get("/api/fixtures/naive")
def list_fixtures_naive( # Without selectinload, SQLAlchemy waits until the code asks for fixture.related_items, then it queries the database separately for that one fixture.
    page_size: int = Query(default=10, ge=1, le=200),
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    reset_sql_query_count()
    fixtures = (
        db.query(Fixture)
        .order_by(Fixture.id)
        .limit(page_size)
        .all()
    )

    return fixture_list_response(fixtures)

@app.get("/api/fixtures/{fixture_id}")
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


@app.post("/api/fixtures", status_code=201)
def create_fixture(
    request_data: FixtureCreate,
    db: DbSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    fixture = Fixture(
        fixture_name=request_data.fixture_name,
        teams=request_data.teams,
    )

    db.add(fixture)
    db.commit()
    db.refresh(fixture)

    return fixture_to_dict(fixture)


@app.put("/api/fixtures/{fixture_id}")
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

    fixture.fixture_name = request_data.fixture_name
    fixture.teams = request_data.teams

    db.commit()
    db.refresh(fixture)

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