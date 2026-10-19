from datetime import datetime, timezone
from typing import Literal

from mongo_db import episodes_collection, messages_collection, summaries_collection


def save_message(
    user_id: str,
    session_id: str,
    role: Literal["user", "assistant"],
    content: str,
) -> None:
    messages_collection.insert_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc),
        }
    )


def fetch_recent_session_messages(session_id: str, limit: int) -> list[dict]:
    messages = list(
        messages_collection.find(
            {"session_id": session_id},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .limit(limit)
    )
    return list(reversed(messages))


def count_user_messages(session_id: str) -> int:
    return messages_collection.count_documents(
        {"session_id": session_id, "role": "user"}
    )


def latest_summary(
    user_id: str,
    session_id: str | None,
    scope: Literal["session", "user"],
) -> dict | None:
    return summaries_collection.find_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "scope": scope,
        },
        {"_id": 0},
        sort=[("created_at", -1)],
    )


def latest_session_summary(user_id: str) -> dict | None:
    return summaries_collection.find_one(
        {"user_id": user_id, "scope": "session"},
        {"_id": 0},
        sort=[("created_at", -1)],
    )


def save_summary(
    user_id: str,
    session_id: str | None,
    scope: Literal["session", "user"],
    text: str,
) -> None:
    summaries_collection.insert_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "scope": scope,
            "text": text,
            "created_at": datetime.now(timezone.utc),
        }
    )


def fetch_session_summaries(user_id: str) -> list[dict]:
    return list(
        summaries_collection.find(
            {"user_id": user_id, "scope": "session"},
            {"_id": 0},
        ).sort("created_at", 1)
    )


def save_episode(
    user_id: str,
    session_id: str,
    fact: str,
    importance: float,
    embedding: list[float],
) -> None:
    episodes_collection.insert_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "fact": fact,
            "importance": float(importance),
            "embedding": [float(value) for value in embedding],
            "created_at": datetime.now(timezone.utc),
        }
    )


def fetch_user_episodes(user_id: str) -> list[dict]:
    return list(
        episodes_collection.find(
            {"user_id": user_id},
            {"_id": 0},
        )
    )


def fetch_memory_snapshot(user_id: str) -> dict:
    messages = list(
        messages_collection.find(
            {"user_id": user_id},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .limit(16)
    )
    episodes = list(
        episodes_collection.find(
            {"user_id": user_id},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .limit(20)
    )

    return {
        "messages": list(reversed(messages)),
        "session_summary": latest_session_summary(user_id),
        "lifetime_summary": latest_summary(user_id, None, "user"),
        "episodes": episodes,
    }


def aggregate_user_memory(user_id: str) -> dict:
    daily_counts = list(
        messages_collection.aggregate(
            [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at",
                                "timezone": "UTC",
                            }
                        },
                        "message_count": {"$sum": 1},
                    }
                },
                {"$project": {"_id": 0, "date": "$_id", "message_count": 1}},
                {"$sort": {"date": 1}},
            ]
        )
    )
    summaries = list(
        summaries_collection.find(
            {"user_id": user_id},
            {"_id": 0},
        )
        .sort("created_at", -1)
        .limit(5)
    )

    return {"daily_message_counts": daily_counts, "recent_summaries": summaries}
