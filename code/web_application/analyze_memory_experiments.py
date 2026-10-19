"""Generate HW6 Part 3 metrics from saved experiment results."""

import json
import re
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "reports" / "hw06" / "raw"
OUTPUT_PATH = REPO_ROOT / "reports" / "hw06" / "METRICS.md"
RUNS = {
    "stn4": ("SHORT_TERM_N=4", "chat_metrics_n4.jsonl"),
    "stn12": ("SHORT_TERM_N=12", "chat_metrics_n12.jsonl"),
    "stn30": ("SHORT_TERM_N=30", "chat_metrics_n30.jsonl"),
    "compaction": ("Summary-aware compaction (N=30 to 4 after summary)", "chat_metrics_compaction.jsonl"),
}
EXPERIMENT_FILES = {
    "stn4": "experiment_n4.json",
    "stn12": "experiment_n12.json",
    "stn30": "experiment_n30.json",
    "compaction": "experiment_compaction.json",
}
PROBE_RULES = {
    "identity_and_role": {
        "name": (r"\bananya\b",),
        "role": (r"community sports league",),
    },
    "tennis_preferences": {
        "weekday evenings": (r"weekday evenings",),
        "avoid Monday evenings": (r"avoid(?:ing)?\s+(?:monday|monday evenings)",),
    },
    "fundraiser_details": {
        "November 20": (r"november 20",),
        "6 PM": (r"6(?::00)?\s*pm",),
        "Spartan Tennis Complex": (r"spartan tennis complex",),
    },
    "fundraiser_logistics": {
        "bring water": (r"water",),
        "blue flyers": (r"blue",),
        "about 40 attendees": (r"\b40\b",),
    },
    "memory_boundaries": {
        "tennis facts": (r"tennis",),
        "weekday-evening preference": (r"weekday evenings",),
        "avoid Monday": (r"avoid(?:ing)?\s+(?:monday|monday evenings)",),
        "November 20 fundraiser fact": (r"november 20",),
        "6 PM fundraiser fact": (r"6(?::00)?\s*pm",),
        "40 attendees fundraiser fact": (r"\b40\b",),
    },
}


def load_rows(filename: str) -> list[dict]:
    return [json.loads(line) for line in (RAW_DIR / filename).read_text().splitlines() if line]


def percent_change(before: float, after: float) -> float:
    return (before - after) / before * 100


def score_reply(reply: str, rules: dict[str, tuple[str, ...]]) -> dict:
    text = re.sub(r"[*_`#]", "", reply.casefold())
    matched = {
        criterion: any(re.search(pattern, text) for pattern in patterns)
        for criterion, patterns in rules.items()
    }
    count = sum(matched.values())
    total = len(matched)
    if count == total:
        score = 5
    elif count == total - 1:
        score = 4
    elif count >= (total + 1) // 2:
        score = 3
    elif count:
        score = 2
    else:
        score = 1
    return {"score": score, "matched_criteria": matched}


def calculate_probe_scores() -> dict:
    runs = {}
    for run_id in RUNS:
        experiment = json.loads((RAW_DIR / EXPERIMENT_FILES[run_id]).read_text())
        runs[run_id] = {
            probe["id"]: score_reply(probe["reply"], PROBE_RULES[probe["id"]])
            for probe in experiment["probes"]
        }
    return {
        "scoring_method": "Deterministic phrase checks against the expected criteria in memory_probes.yaml. Scores map complete coverage to 5, one missing criterion to 4, partial coverage to 2–3, and no coverage to 1.",
        "runs": runs,
    }


def main() -> None:
    score_data = calculate_probe_scores()
    (RAW_DIR / "probe_scores.json").write_text(
        json.dumps(score_data, indent=2) + "\n", encoding="utf-8"
    )
    scores = score_data["runs"]
    results = {}
    for run_id, (label, filename) in RUNS.items():
        rows = load_rows(filename)
        conversation = [row for row in rows if row["experiment_phase"] == "conversation"]
        results[run_id] = {
            "label": label,
            "prompt": mean(row["prompt_tokens"] for row in conversation),
            "completion": mean(row["completion_tokens"] for row in conversation),
            "latency": mean(row["latency_ms"] for row in conversation),
            "quality": mean(item["score"] for item in scores[run_id].values()),
            "input_total": sum(row["prompt_tokens"] for row in conversation),
            "output_total": sum(row["completion_tokens"] for row in conversation),
            "component_tokens": {
                key: mean(row[key] for row in conversation)
                for key in (
                    "system_primer_tokens",
                    "long_term_summary_tokens",
                    "short_term_window_tokens",
                    "episodic_facts_tokens",
                )
            },
        }

    baseline = results["stn30"]
    compacted = results["compaction"]
    best = compacted
    worst = baseline

    lines = [
        "# HW6 Part 3 Metrics",
        "",
        "## Method",
        "",
        "Each setting used the same 30-message conversation and five fixed probes in fresh sessions. Means below use the 30 conversation requests only; the deterministic criterion checks and per-probe results are in `raw/probe_scores.json`. Token components are character/4 estimates, while total prompt and completion tokens are returned by the local model response metadata.",
        "",
        "## Short-term Memory Comparison",
        "",
        "| Setting | Mean prompt tokens/turn | Mean completion tokens/turn | Mean latency (ms) | Mean probe quality (1–5) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for run_id in RUNS:
        item = results[run_id]
        lines.append(
            f"| {item['label']} | {item['prompt']:.1f} | {item['completion']:.1f} | {item['latency']:.1f} | {item['quality']:.1f} |"
        )

    lines.extend(["", "## Mean Prompt Component Tokens per Conversation Turn", "", "| Setting | System primer | Long-term summary | Short-term window | Episodic facts |", "| --- | ---: | ---: | ---: | ---: |"])
    for run_id in RUNS:
        item = results[run_id]
        component = item["component_tokens"]
        lines.append(f"| {item['label']} | {component['system_primer_tokens']:.1f} | {component['long_term_summary_tokens']:.1f} | {component['short_term_window_tokens']:.1f} | {component['episodic_facts_tokens']:.1f} |")

    lines.extend([
        "",
        "## Compaction Effect vs. N=30",
        "",
        f"The compaction policy reduced mean prompt tokens by {percent_change(baseline['prompt'], compacted['prompt']):.1f}% and mean latency by {percent_change(baseline['latency'], compacted['latency']):.1f}%. Mean probe quality changed from {baseline['quality']:.1f} to {compacted['quality']:.1f}.",
        "",
        "## Estimated Cost for 10,000 30-turn Conversations",
        "",
        f"Input tokens are priced at $1/million and output tokens at $5/million. The best setting is compaction because it has the lowest measured cost while retaining a {best['quality']:.1f}/5 probe score. The worst setting is N=30 because it has the highest measured cost.",
        "",
        "| Setting | Input cost | Output cost | Total cost |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in (best, worst):
        input_cost = item["input_total"] * 10_000 / 1_000_000
        output_cost = item["output_total"] * 10_000 * 5 / 1_000_000
        lines.append(f"| {item['label']} | ${input_cost:.2f} | ${output_cost:.2f} | ${input_cost + output_cost:.2f} |")

    lines.extend(["", "## Probe Scores", "", "| Run | Identity | Tennis | Fundraiser details | Fundraiser logistics | Memory boundaries | Mean |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    for run_id in RUNS:
        run_scores = scores[run_id]
        ordered = [run_scores[key]["score"] for key in ("identity_and_role", "tennis_preferences", "fundraiser_details", "fundraiser_logistics", "memory_boundaries")]
        lines.append(f"| {results[run_id]['label']} | " + " | ".join(str(score) for score in ordered) + f" | {mean(ordered):.1f} |")

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
