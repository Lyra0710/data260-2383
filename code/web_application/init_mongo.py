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


if "fixtures" not in db.list_collection_names():
    db.create_collection(
        "fixtures",
        validator=fixture_validator,
        validationLevel="strict",
        validationAction="error",
    )
    print("Created fixtures collection with validation.")
else:
    db.command(
        "collMod",
        "fixtures",
        validator=fixture_validator,
        validationLevel="strict",
        validationAction="error",
    )
    print("Updated fixtures collection validation.")