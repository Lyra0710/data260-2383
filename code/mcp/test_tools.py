import asyncio
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import domain_server


FIXTURE = {
    "id": 1,
    "fixture_name": "SJSU vs Stanford",
    "teams": "SJSU, Stanford",
    "fixture_code": "FIX-001",
    "available_slots": 15,
    "venue_id": 1,
    "related_items": [],
}


async def fake_get_json(path, params=None):
    if path == "/fixtures":
        return [FIXTURE], None

    if path == "/fixtures/1":
        return FIXTURE, None

    if path == "/venues/1/fixtures":
        return [FIXTURE], None

    if path in ["/fixtures/10", "/venues/9/fixtures"]:
        return None, "Resource not found."

    return None, "Unexpected test path."


domain_server.get_json = fake_get_json
domain_server.FAILURE_RATE = 0.0


async def run_test(name, tool_name, inputs, expected_ok):
    raw_result = await domain_server.execute_tool(
        tool_name,
        inputs,
    )

    result = json.loads(raw_result)

    assert result["ok"] is expected_ok

    print(f"PASS: {name}")


async def main():
    tests = [
        (
            "search valid input",
            "search_fixtures",
            {"query": "SJSU", "limit": 5},
            True,
        ),
        (
            "search invalid limit",
            "search_fixtures",
            {"query": "SJSU", "limit": 0},
            False,
        ),
        (
            "fixture details valid input",
            "fixture_details",
            {"fixture_id": 1},
            True,
        ),
        (
            "fixture details missing fixture",
            "fixture_details",
            {"fixture_id": 10},
            False,
        ),
        (
            "venue summary valid input",
            "venue_fixture_summary",
            {"venue_id": 1},
            True,
        ),
        (
            "venue summary missing venue",
            "venue_fixture_summary",
            {"venue_id": 9},
            False,
        ),
    ]

    passed = 0

    for name, tool_name, inputs, expected_ok in tests:
        try:
            await run_test(
                name,
                tool_name,
                inputs,
                expected_ok,
            )
            passed += 1

        except AssertionError:
            print(f"FAIL: {name}")

    print(f"\n{passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    asyncio.run(main())