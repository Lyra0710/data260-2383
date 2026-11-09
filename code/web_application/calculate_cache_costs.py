"""Apply the HW9 cache cost model to the completed threshold sweep."""

import json
from pathlib import Path

MISS_COST = 1
FALSE_HIT_COST = 10
SWEEP_PATH = (
    Path(__file__).resolve().parents[2] / "reports/hw09/raw/threshold_sweep.json"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "reports/hw09/raw/cost_analysis.json"
)


def main() -> None:
    sweep = json.loads(SWEEP_PATH.read_text(encoding="utf-8"))
    rows = []

    for threshold_data in sweep["thresholds"]:
        results = threshold_data["results"]
        cache_misses = sum(not result["observed_hit"] for result in results)
        false_hits = sum(result["false_hit"] for result in results)
        total_cost = cache_misses * MISS_COST + false_hits * FALSE_HIT_COST
        threshold_data["summary"]["total_cost"] = total_cost
        rows.append(
            {
                "threshold": threshold_data["summary"]["threshold"],
                "cache_misses": cache_misses,
                "false_hits": false_hits,
                "total_cost": total_cost,
            }
        )

    analysis = {
        "cost_model": {
            "unit": "relative cost unit",
            "cache_miss_cost": MISS_COST,
            "false_hit_support_cost": FALSE_HIT_COST,
        },
        "rows": rows,
    }
    SWEEP_PATH.write_text(json.dumps(sweep, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
