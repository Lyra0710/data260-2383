import logging
import sys

import httpx
from mcp.server.fastmcp import FastMCP


logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
)

mcp = FastMCP("meals")

BASE_URL = "https://www.themealdb.com/api/json/v1/1"


@mcp.tool()
def search_meals_by_name(
    query: str,
    limit: int = 5,
) -> list[dict]:
    """Search TheMealDB meals by name."""

    if not query.strip():
        raise ValueError("query cannot be empty")

    if not 1 <= limit <= 25:
        raise ValueError("limit must be between 1 and 25")

    try:
        response = httpx.get(
            f"{BASE_URL}/search.php",
            params={"s": query},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise RuntimeError(f"TheMealDB request failed: {error}") from error

    meals = payload.get("meals") or []

    return [
        {
            "id": meal["idMeal"],
            "name": meal["strMeal"],
            "area": meal["strArea"],
            "category": meal["strCategory"],
            "thumb": meal["strMealThumb"],
        }
        for meal in meals[:limit]
    ]

@mcp.tool()
def meals_by_ingredient(
    ingredient: str,
    limit: int = 12,
) -> list[dict]:
    """Find meals by main ingredient."""

    if not ingredient.strip():
        raise ValueError("ingredient cannot be empty")

    if not 1 <= limit <= 25:
        raise ValueError("limit must be between 1 and 25")

    try:
        response = httpx.get(
            f"{BASE_URL}/filter.php",
            params={"i": ingredient},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise RuntimeError(f"TheMealDB request failed: {error}") from error

    meals = payload.get("meals") or []

    return [
        {
            "id": meal["idMeal"],
            "name": meal["strMeal"],
            "thumb": meal["strMealThumb"],
        }
        for meal in meals[:limit]
    ]

def format_meal_details(meal: dict) -> dict:
    ingredients = []

    for number in range(1, 21):
        name = meal.get(f"strIngredient{number}")
        measure = meal.get(f"strMeasure{number}")

        if name and name.strip():
            ingredients.append(
                {
                    "name": name.strip(),
                    "measure": (measure or "").strip(),
                }
            )

    return {
        "id": meal["idMeal"],
        "name": meal["strMeal"],
        "category": meal["strCategory"],
        "area": meal["strArea"],
        "instructions": meal["strInstructions"],
        "image": meal["strMealThumb"],
        "source": meal.get("strSource"),
        "youtube": meal.get("strYoutube"),
        "ingredients": ingredients,
    }


@mcp.tool()
def random_meal() -> dict:
    """Return one random meal with full recipe details."""

    try:
        response = httpx.get(
            f"{BASE_URL}/random.php",
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise RuntimeError(f"TheMealDB request failed: {error}") from error

    meals = payload.get("meals") or []

    if not meals:
        raise RuntimeError("TheMealDB returned no random meal")

    return format_meal_details(meals[0])

@mcp.tool()
def meal_details(id: str | int) -> dict:
    """Return full recipe details for one meal ID."""

    meal_id = str(id).strip()

    if not meal_id:
        raise ValueError("id cannot be empty")

    try:
        response = httpx.get(
            f"{BASE_URL}/lookup.php",
            params={"i": meal_id},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise RuntimeError(f"TheMealDB request failed: {error}") from error

    meals = payload.get("meals") or []

    if not meals:
        raise ValueError(f"No meal found for ID {meal_id}")

    return format_meal_details(meals[0])

if __name__ == "__main__":
    mcp.run(transport="stdio")