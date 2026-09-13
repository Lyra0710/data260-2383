
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

app = FastAPI()
APP_DIR = Path(__file__).resolve().parent

# Serves static files (HTML, CSS, JS) from the 'web_application' directory
app.mount(
    "/static",
    StaticFiles(directory=APP_DIR),
    name="static"
)

# home endpoint returns the index.html file
@app.get("/")
async def home():
    return FileResponse(APP_DIR / "index.html")

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
async def get_fixtures():
    return fixtures

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