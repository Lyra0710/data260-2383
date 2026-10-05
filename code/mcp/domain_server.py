import logging
import os
import sys
from dotenv import load_dotenv
import httpx
from mcp.server.fastmcp import FastMCP
import asyncio
import random
import json

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("domain")

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8583/api",
)
load_dotenv()

API_EMAIL = os.getenv("API_EMAIL")
API_PASSWORD = os.getenv("API_PASSWORD")

VERIFY_SEED = 2383
FAILURE_RATE = 0.5

MAX_RETRIES = 2
BACKOFF_SECONDS = 0.2

random_generator = random.Random(VERIFY_SEED)

def success(data):
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def failure(message):
    return {
        "ok": False,
        "data": None,
        "error": message,
    }

async def run_with_retries(operation):
    for attempt in range(MAX_RETRIES + 1):
        logging.info("Attempt %d", attempt + 1)

        try:
            if random_generator.random() < FAILURE_RATE:
                raise httpx.RequestError("Simulated failure")

            return await operation()

        except httpx.RequestError:
            if attempt == MAX_RETRIES:
                raise

            delay = BACKOFF_SECONDS * (2 ** attempt)
            logging.info("Retrying after %.2f seconds", delay)
            await asyncio.sleep(delay)

async def get_json(path, params=None):
    if not API_EMAIL or not API_PASSWORD:
        return None, "API_EMAIL and API_PASSWORD are not configured."

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            async def request():
                login_response = await client.post(
                    f"{API_BASE_URL}/login",
                    json={
                        "email": API_EMAIL,
                        "password": API_PASSWORD,
                    },
                )

                login_response.raise_for_status()

                return await client.get(
                    f"{API_BASE_URL}{path}",
                    params=params,
                )

            response = await run_with_retries(request)

        if response.status_code == 404:
            return None, "Resource not found."

        response.raise_for_status()
        return response.json(), None

    except httpx.RequestError as error:
        logging.error("Request failed: %s", error)
        return None, "The domain API request failed after retries."

    except httpx.HTTPStatusError as error:
        logging.error("API returned an error: %s", error)
        return None, "The domain API returned an error."

def get_items(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        return (
            payload.get("items")
            or payload.get("data")
            or payload.get("fixtures")
            or []
        )

    return []


@mcp.tool()
async def search_fixtures(query: str, limit: int = 10):
    """Search fixtures by name, teams, or fixture code."""
    query = query.strip().lower()

    if not query:
        return failure("query must not be empty.")

    if limit < 1 or limit > 25:
        return failure("limit must be between 1 and 25.")

    payload, error = await get_json(
        "/fixtures",
        params={"page": 1, "page_size": 100},
    )

    if error:
        return failure(error)

    fixtures = payload if isinstance(payload, list) else []

    matches = []

    for fixture in fixtures:
        searchable_text = (
            f"{fixture.get('fixture_name', '')} "
            f"{fixture.get('teams', '')} "
            f"{fixture.get('fixture_code', '')}"
        ).lower()

        if query in searchable_text:
            matches.append(fixture)
    return success(matches[:limit])
    


@mcp.tool()
async def fixture_details(fixture_id: int):
    """Return one fixture by ID."""
    if fixture_id < 1:
        return failure("fixture_id must be a positive integer.")

    payload, error = await get_json(f"/fixtures/{fixture_id}")

    if error:
        return failure(error)

    return success(payload)


@mcp.tool()
async def venue_fixture_summary(venue_id: int):
    """Return an aggregate summary of fixtures at a venue."""
    if venue_id < 1:
        return failure("venue_id must be a positive integer.")

    payload, error = await get_json(
        f"/venues/{venue_id}/fixtures",
        params={"page": 1, "page_size": 100},
    )

    if error:
        return failure(error)

    fixtures = get_items(payload)

    total_available_slots = sum(
        int(fixture.get("available_slots", 0))
        for fixture in fixtures
    )

    summary = {
        "venue_id": venue_id,
        "fixture_count": len(fixtures),
        "total_available_slots": total_available_slots,
        "fixture_names": [
            fixture.get("fixture_name")
            for fixture in fixtures
        ],
    }

    return success(summary)

async def execute_tool(name: str, inputs: dict):
    """Safely execute one of the three domain tools."""
    try:
        if name == "search_fixtures":
            result = await search_fixtures(**inputs)

        elif name == "fixture_details":
            result = await fixture_details(**inputs)

        elif name == "venue_fixture_summary":
            result = await venue_fixture_summary(**inputs)

        else:
            result = failure(f"Unknown tool: {name}")

        return json.dumps(result)

    except Exception as error:
        logging.error("execute_tool failed: %s", error)

        return json.dumps(
            failure("Tool execution failed.")
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")