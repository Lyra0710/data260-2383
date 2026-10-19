from mongo_db import db


fixture_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "fixture_name",
            "status",
            "sport_type",
            "scheduled_at",
            "created_at",
            "updated_at",
        ],
        "properties": {
            "fixture_name": {
                "bsonType": "string",
                "minLength": 1,
                "maxLength": 100,
            },
            "description": {
                "bsonType": ["string", "null"],
            },
            "status": {
                "enum": ["scheduled", "completed", "cancelled"],
            },
            "sport_type": {
                "enum": [
                    "soccer",
                    "basketball",
                    "tennis",
                    "pickleball",
                ],
            },
            "scheduled_at": {
                "bsonType": "date",
            },
            "created_at": {
                "bsonType": "date",
            },
            "updated_at": {
                "bsonType": "date",
            },
        },
    }
}


message_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "session_id",
            "role",
            "content",
            "created_at",
        ],
        "properties": {
            "user_id": {"bsonType": "string"},
            "session_id": {"bsonType": "string"},
            "role": {"enum": ["user", "assistant"]},
            "content": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
        },
    }
}


summary_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "session_id",
            "scope",
            "text",
            "created_at",
        ],
        "properties": {
            "user_id": {"bsonType": "string"},
            "session_id": {"bsonType": ["string", "null"]},
            "scope": {"enum": ["session", "user"]},
            "text": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
        },
    }
}


episode_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "user_id",
            "session_id",
            "fact",
            "importance",
            "embedding",
            "created_at",
        ],
        "properties": {
            "user_id": {"bsonType": "string"},
            "session_id": {"bsonType": "string"},
            "fact": {"bsonType": "string", "minLength": 1, "maxLength": 300},
            "importance": {"bsonType": "double", "minimum": 0, "maximum": 1},
            "embedding": {
                "bsonType": "array",
                "items": {"bsonType": "double"},
            },
            "created_at": {"bsonType": "date"},
        },
    }
}


def ensure_collection(name: str, validator: dict) -> None:
    if name not in db.list_collection_names():
        db.create_collection(
            name,
            validator=validator,
            validationLevel="strict",
            validationAction="error",
        )
        print(f"Created {name} collection with validation.")
        return

    db.command(
        "collMod",
        name,
        validator=validator,
        validationLevel="strict",
        validationAction="error",
    )
    print(f"Updated {name} collection validation.")


ensure_collection("fixtures", fixture_validator)
ensure_collection("messages", message_validator)
ensure_collection("summaries", summary_validator)
ensure_collection("episodes", episode_validator)

db["messages"].create_index([("user_id", 1), ("session_id", 1), ("created_at", -1)])
db["summaries"].create_index(
    [("user_id", 1), ("session_id", 1), ("scope", 1), ("created_at", -1)]
)
db["episodes"].create_index([("user_id", 1), ("created_at", -1)])
