import asyncio
import uuid

from kafka.client import send_request

VALID_FIXTURE = {
    "fixture_name": "Validation Fixture",
    "teams": ["Team A", "Team B"],
    "fixture_code": "VALID-001",
    "available_slots": 10,
    "venue_id": 1,
}


def fixture_with(**changes: object) -> dict:
    fixture = VALID_FIXTURE.copy()
    fixture.update(changes)
    return fixture


async def run_case(
    name: str,
    operation: str,
    data: dict,
    expected_error: str,
) -> None:
    correlation_id = str(uuid.uuid4())

    response = await send_request(
        operation=operation,
        data=data,
        correlation_id=correlation_id,
    )

    passed = (
        response.get("success") is False
        and response.get("error") == expected_error
        and response.get("correlation_id") == correlation_id
    )

    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"Response: {response}")

    if not passed:
        raise AssertionError(f"{name} did not return the expected error response.")


async def main() -> None:
    print("Student: Ananya")
    print("HW8 Part 1 Kafka validation/error test")

    cases = [
        (
            "Missing fixture_code",
            "CREATE_FIXTURE",
            {
                "fixture_name": "Validation Fixture",
                "teams": ["Team A", "Team B"],
                "available_slots": 10,
                "venue_id": 1,
            },
            "Missing required field: fixture_code",
        ),
        (
            "Empty fixture_name",
            "CREATE_FIXTURE",
            fixture_with(fixture_name="   "),
            "fixture_name cannot be empty",
        ),
        (
            "Empty teams",
            "CREATE_FIXTURE",
            fixture_with(teams=[]),
            "teams must be a non-empty list",
        ),
        (
            "Empty fixture_code",
            "CREATE_FIXTURE",
            fixture_with(fixture_code=""),
            "fixture_code cannot be empty",
        ),
        (
            "Negative available_slots",
            "CREATE_FIXTURE",
            fixture_with(available_slots=-1),
            "available_slots must be a non-negative integer",
        ),
        (
            "Invalid available_slots type",
            "CREATE_FIXTURE",
            fixture_with(available_slots="ten"),
            "available_slots must be a non-negative integer",
        ),
        (
            "Invalid venue_id",
            "CREATE_FIXTURE",
            fixture_with(venue_id=0),
            "venue_id must be a positive integer",
        ),
        (
            "Unknown operation",
            "DELETE_FIXTURE",
            {},
            "Unknown operation",
        ),
        (
            "GET missing entity_id",
            "GET_FIXTURE",
            {},
            "Missing required field: entity_id",
        ),
        (
            "GET unknown entity_id",
            "GET_FIXTURE",
            {"entity_id": "does-not-exist"},
            "Fixture not found",
        ),
    ]

    for case in cases:
        await run_case(*case)

    print("All validation/error cases passed.")


if __name__ == "__main__":
    asyncio.run(main())
