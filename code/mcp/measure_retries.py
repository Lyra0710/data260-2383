import asyncio
import json
import math
import random
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

import domain_server


SEED = 2383
RATES = [0.0, 0.2, 0.5]
CALLS_PER_RATE = 50
OUTPUT_DIR = Path("reports/hw05/raw")


def calculate_p99(values):
    ordered = sorted(values)
    index = math.ceil(0.99 * len(ordered)) - 1
    return ordered[index]


async def run_measurements():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for rate in RATES:
        domain_server.FAILURE_RATE = rate
        domain_server.random_generator = random.Random(SEED)

        records = []
        latencies = []

        for call_number in range(1, CALLS_PER_RATE + 1):
            start = time.perf_counter()

            result = await domain_server.fixture_details(1)

            elapsed_ms = (time.perf_counter() - start) * 1000
            latencies.append(elapsed_ms)

            records.append(
                {
                    "seed": SEED,
                    "failure_rate": rate,
                    "call_number": call_number,
                    "ok": result.get("ok") is True,
                    "latency_ms": round(elapsed_ms, 3),
                    "result": result,
                }
            )

        output_file = OUTPUT_DIR / f"retry_rate_{rate}.jsonl"

        with output_file.open("w", encoding="utf-8") as file:
            for record in records:
                file.write(json.dumps(record) + "\n")

        success_count = sum(
            1 for record in records if record["ok"]
        )

        success_rate = success_count / CALLS_PER_RATE

        print(
            f"Failure rate: {rate:.0%} | "
            f"Success rate: {success_rate:.1%} | "
            f"Mean latency: {sum(latencies) / len(latencies):.2f} ms | "
            f"p99 latency: {calculate_p99(latencies):.2f} ms"
        )


if __name__ == "__main__":
    asyncio.run(run_measurements())