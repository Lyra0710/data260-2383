import os
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from routers.auth import router as auth_router


app = FastAPI()
APP_DIR = Path(__file__).resolve().parent

# Secret key for session signing
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

# Enable session support - required for auth
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True,
    same_site="lax",
max_age=3600
)


# Serves static files (HTML, CSS, JS) from the 'web_application' directory
app.mount(
    "/static",
    StaticFiles(directory=APP_DIR),
    name="static"
)

# Register routes
app.include_router(auth_router)


# home endpoint returns the index.html file
# @app.get("/")
# async def home():
#     return FileResponse(APP_DIR / "index.html")

# Model for fixture data - FastAPI uses this to validate the JSON body of a request
class Fixture(BaseModel):
    fixtureName: str
    teams: str
# hardcoded input ONLY for testing and to make sure deleting the highest record does not immidiately delte the record required for iD 1 update. 
fixtures = [
    {"id": 1, "fixtureName": "Community Soccer Semifinal", "teams": "Falcons vs Tigers"}
]

# fastapi uses class to read JSON request body and check if the required fields exist, and their types. 
# converts the JSON object to a python dict with the keys defined in the class. 
class FixtureCreate(BaseModel):
    fixtureName: str
    teams:str

class FixtureUpdate(BaseModel):
    fixtureName: str
    teams: str

@app.get("/api/fixtures")
async def get_fixtures(search: str | None = None):
    if not search or not search.strip():
        return fixtures

    search_term = search.strip().casefold()

    return [
        item
        for item in fixtures
        if (
            search_term in item["fixtureName"].casefold() # case insensitive search
            or search_term in item["teams"].casefold()
        )
    ]

@app.post("/api/fixtures")
async def create_fixture(fixture: FixtureCreate):
    new_id = max(
        [item["id"] for item in fixtures],
        default=0
    ) + 1

    new_fixture = {
        "id": new_id,
        **fixture.model_dump() # unpacks the key-value pairs of the dictionary into this new dictionary
    }

    fixtures.append(new_fixture)

    return new_fixture

@app.put("/api/fixtures/1")
async def update_fixture(fixture: FixtureUpdate):
    for item in fixtures:
        if item["id"] == 1:
            item["fixtureName"] = fixture.fixtureName
            item["teams"] = fixture.teams
            return item

    raise HTTPException(
        status_code=404,
        detail="Fixture ID 1 not found"
    )

@app.delete("/api/fixtures/highest")
async def delete_highest_fixture():
    if not fixtures:
        raise HTTPException(
            status_code=404,
            detail="No fixtures available to delete"
        )

    highest_fixture = max(
        fixtures,
        key=lambda item: item["id"]
    )

    fixtures.remove(highest_fixture)

    return highest_fixture