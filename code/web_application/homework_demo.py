import asyncio
import uuid

from kafka.client import send_request


async def main():
    # Create one correlation ID for the complete demo flow.
    correlation_id = str(uuid.uuid4())

    fixture_data = {
        "fixture_name": "HW8 Test Fixture",
        "teams": ["Team A", "Team B"],
        "fixture_code": "HW8-001",
        "available_slots": 10,
        "venue_id": 1,
    }

    print("\n--- CREATE_FIXTURE ---")

    create_response = await send_request(
        operation="CREATE_FIXTURE",
        data=fixture_data,
        correlation_id=correlation_id,
    )

    if not create_response.get("success"):
        print("CREATE_FIXTURE failed.")
        return

    # Use the generated ID returned by the worker.
    entity_id = create_response["entity_id"]

    print(f"Generated entity_id: {entity_id}")

    print("\n--- GET_FIXTURE ---")

    get_response = await send_request(
        operation="GET_FIXTURE",
        data={"entity_id": entity_id},
        correlation_id=correlation_id,
    )

    if not get_response.get("success"):
        print("GET_FIXTURE failed.")
        return

    print(f"Retrieved fixture: {get_response['entity']}")

    # Confirm that the correlation ID stayed unchanged.
    if get_response["correlation_id"] == correlation_id:
        print("Correlation ID preserved: True")
    else:
        print("Correlation ID preserved: False")


if __name__ == "__main__":
    asyncio.run(main())
