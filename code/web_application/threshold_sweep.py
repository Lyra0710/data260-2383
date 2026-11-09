"""Measure semantic-cache behavior for the fixed HW9 threshold cases."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from memory_service import embed_texts, generate_reply
from semantic_cache import semantic_response_cache

THRESHOLDS = [0.75, 0.80, 0.85, 0.90, 0.95]
CASES_PATH = Path(__file__).resolve().parents[2] / "reports/hw09/cache_cases.yaml"
OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "reports/hw09/raw/threshold_sweep.json"
)


def generate_and_cache(
    user_id: str,
    session_id: str,
    query: str,
    embedding: list[float],
    data_version: str,
) -> str:
    response = generate_reply(user_id, session_id, query)
    semantic_response_cache.store(
        query,
        embedding,
        response["reply"],
        data_version,
        user_id,
        session_id,
    )
    return response["reply"]


def run_case(case: dict, threshold: float) -> dict:
    user_id = "hw9_threshold_sweep"
    session_id = f"threshold_sweep_{threshold}_{case['id']}"
    data_version = semantic_response_cache.current_data_version()
    cached_embedding = embed_texts([case["cached_query"]])[0]
    generate_and_cache(
        user_id,
        session_id,
        case["cached_query"],
        cached_embedding,
        data_version,
    )

    started_at = time.perf_counter()
    incoming_embedding = embed_texts([case["incoming_query"]])[0]
    cached_response = semantic_response_cache.find_similar(
        incoming_embedding,
        data_version,
        user_id,
        session_id,
        threshold,
    )
    is_cached = cached_response is not None

    if is_cached:
        answer = cached_response["answer"]
        similarity_score = cached_response["similarity_score"]
    else:
        answer = generate_and_cache(
            user_id,
            session_id,
            case["incoming_query"],
            incoming_embedding,
            data_version,
        )
        similarity_score = None

    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    return {
        "id": case["id"],
        "category": case["category"],
        "expected_hit": case["expected_hit"],
        "observed_hit": is_cached,
        "false_hit": is_cached and not case["expected_hit"],
        "similarity_score": similarity_score,
        "latency_ms": latency_ms,
        "cached_answer": answer if is_cached else None,
    }


def summarize(results: list[dict], threshold: float) -> dict:
    observed_hits = sum(result["observed_hit"] for result in results)
    false_hits = sum(result["false_hit"] for result in results)

    return {
        "threshold": threshold,
        "hit_rate_percent": round(observed_hits / len(results) * 100, 2),
        "false_hit_rate_percent": round(
            false_hits / observed_hits * 100 if observed_hits else 0,
            2,
        ),
        "mean_latency_ms": round(
            sum(result["latency_ms"] for result in results) / len(results),
            2,
        ),
        "total_cost": None,
    }


def main() -> None:
    cases = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))["cases"]
    output = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "false_hit_rate_definition": "false hits divided by observed cache hits",
        "thresholds": [],
    }

    for threshold in THRESHOLDS:
        results = []
        for case in cases:
            result = run_case(case, threshold)
            results.append(result)
            print(
                f"threshold={threshold:.2f} case={case['id']} "
                f"hit={result['observed_hit']} latency_ms={result['latency_ms']}"
            )

        summary = summarize(results, threshold)
        output["thresholds"].append({"summary": summary, "results": results})
        print(json.dumps(summary))
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    output["finished_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
