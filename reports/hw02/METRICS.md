# Homework 2 Metrics

## Configuration and data sources

The experiments were configured with qwen3:8b, strict=true, and SEED=2383. SEED=2383 identifies the experiment configuration; it should not be described as controlling Ollama sampling unless the seed was passed to the model. The main input is `cases/schema_input.json`; the adversarial input is `cases/adversarial_input.json`.

The tables below report the contents of these raw files:

- `raw/schema_validation.json` and `.csv`
- `raw/ceiling_2.json` and `.csv`
- `raw/ceiling_10.json` and `.csv`
- `raw/adversarial.json` and `.csv`

Latency values are the `latency_ms` values recorded by the experiment script. Mean, median, minimum, and maximum are calculated from the corresponding JSON files.

## Schema-validation experiment

| Metric | Result |
|---|---:|
| Runs | 30 |
| Turn limit | 10 |
| Valid first attempt | 30/30 (100%) |
| Valid after one retry | 0/30 (0%) |
| Valid after 2+ retries | 0/30 (0%) |
| Hit turn ceiling | 0/30 (0%) |
| Runs with exactly 3 planner tags | 30/30 (100%) |
| Runs with no recorded issues | 30/30 (100%) |
| Planner/reviewer/supervisor node sequence | 30/30 |
| Latency minimum | 70,773.59 ms |
| Latency mean | 78,766.45 ms |
| Latency median | 80,250.86 ms |
| Latency maximum | 89,498.78 ms |

## Turn-ceiling comparison

| Turn limit | Runs | Valid first attempt | Valid after one retry | Valid after 2+ retries | Hit turn ceiling | Mean latency | Median latency | Minimum–maximum latency |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 20 | 20/20 (100%) | 0/20 (0%) | 0/20 (0%) | 0/20 (0%) | 71,690.20 ms | 71,702.45 ms | 70,532.72–76,117.25 ms |
| 10 | 20 | 20/20 (100%) | 0/20 (0%) | 0/20 (0%) | 0/20 (0%) | 75,748.13 ms | 75,205.18 ms | 70,563.78–83,619.44 ms |

Because both ceilings achieved 100% completion, turn limit 2 was selected for deployment because it had the lower mean latency.

## Adversarial-input experiment

| Metric | Result |
|---|---:|
| Runs | 5 |
| Turn limit | 2 |
| Valid first attempt | 5/5 (100%) |
| Valid after one retry | 0/5 (0%) |
| Valid after 2+ retries | 0/5 (0%) |
| Hit turn ceiling | 0/5 (0%) |
| Runs with exactly 3 planner tags | 5/5 (100%) |
| Runs with no recorded issues | 5/5 (100%) |
| Planner/reviewer/supervisor node sequence | 5/5 |
| Distinct planner tag sets | 1 |
| Stored planner summaries with 25 words | 5/5 |
| Latency minimum | 65,571.37 ms |
| Latency mean | 67,709.98 ms |
| Latency median | 66,404.33 ms |
| Latency maximum | 73,557.82 ms |

The adversarial input did not cause the system to reach the turn ceiling. All five runs produced valid first-attempt outputs. Although the reviewer text claimed that the summary exceeded 25 words, Pydantic validation accepted the stored planner output, so no issue was recorded. The final pipeline therefore produced schema-valid output despite the conflicting content instructions.

## Supplementary schema-validation test

The separate `raw/schema_validation_test.json` and `.csv` contain 2 additional runs. Both are recorded as `valid first attempt`, with `turn_count=1`, no recorded issues, and the planner/reviewer/supervisor node sequence. Their latencies were 101,450.31 ms and 95,714.21 ms; the mean and median were both 98,582.26 ms.
