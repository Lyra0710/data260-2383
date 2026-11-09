"""Run ten Part 2 semantic-cache requests and save the observed results."""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

API_URL = "http://127.0.0.1:8583/api/chat"
OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "reports/hw09/raw/semantic_cache_demo.json"
)

CASES = [
    ("new", "What should a league coordinator confirm before scheduling a fixture?"),
    (
        "exact_duplicate",
        "What should a league coordinator confirm before scheduling a fixture?",
    ),
    ("paraphrase", "What needs checking before a league fixture is scheduled?"),
    ("paraphrase", "What should I verify before booking a sports match?"),
    (
        "exact_duplicate",
        "What should a league coordinator confirm before scheduling a fixture?",
    ),
    ("new", "How are fixture view counts synchronized?"),
    ("new", "What information is required to create a fixture?"),
    ("unrelated", "How does a referee prepare for a match?"),
    ("exact_duplicate", "How are fixture view counts synchronized?"),
    ("unrelated", "What should spectators bring to an outdoor game?"),
]


def send_request(payload: dict) -> dict:
    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def summarize(results: list[dict]) -> dict:
    cached_latencies = [item["latency_ms"] for item in results if item["is_cached"]]
    non_cached_latencies = [
        item["latency_ms"] for item in results if not item["is_cached"]
    ]
    cache_hits = sum(item["is_cached"] for item in results)

    return {
        "query_count": len(results),
        "cache_hits": cache_hits,
        "cache_hit_rate_percent": round(cache_hits / len(results) * 100, 2),
        "average_cached_latency_ms": mean(cached_latencies),
        "average_non_cached_latency_ms": mean(non_cached_latencies),
    }


def main() -> None:
    session_id = f"semantic_cache_demo_{uuid4().hex}"
    results = []

    for number, (category, message) in enumerate(CASES, start=1):
        started_at = datetime.now(timezone.utc)
        response = send_request(
            {
                "user_id": "hw9_demo",
                "session_id": session_id,
                "message": message,
            }
        )
        finished_at = datetime.now(timezone.utc)
        result = {
            "number": number,
            "category": category,
            "query": message,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "is_cached": response["is_cached"],
            "similarity_score": response["similarity_score"],
            "latency_ms": response["latency_ms"],
            "reply": response["reply"],
        }
        results.append(result)
        print(
            f"Query {number}: cached={result['is_cached']} "
            f"similarity={result['similarity_score']} "
            f"latency_ms={result['latency_ms']}"
        )

    output = {
        "session_id": session_id,
        "results": results,
        "summary": summarize(results),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], indent=2))


if __name__ == "__main__":
    main()
