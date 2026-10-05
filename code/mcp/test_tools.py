import asyncio
import json
import sys
from pathlib import Path
from agent import run_agent

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
    passed = 0

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

    try:
        blocked_result = await domain_server.execute_tool(
            "search_fixtures",
            {
                "query": "DROP TABLE fixtures",
                "limit": 5,
            },
        )

        blocked_result = json.loads(blocked_result)

        assert blocked_result["ok"] is False
        print("PASS: safety rule blocks destructive query")
        passed += 1

    except AssertionError:
        print("FAIL: safety rule blocks destructive query")

    try:
        agent_result = await run_agent(
            "Get fixture 1",
            max_steps=2,
            model_call=mock_model,
        )

        assert agent_result["stop_reason"] == "max_steps"
        assert len(agent_result["steps"]) == 2

        print("PASS: MockModel stops at max_steps")
        passed += 1

    except AssertionError:
        print("FAIL: MockModel stops at max_steps")

    print(f"\n{passed}/8 tests passed")
# mock 
async def mock_model(messages):
    return json.dumps(
        {
            "action": "tool",
            "tool": "fixture_details",
            "inputs": {"fixture_id": 1},
        }
    )
if __name__ == "__main__":
    asyncio.run(main())