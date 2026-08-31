# Part 3 — Measuring Non-Determinism

## Experiment setup

- Fixed input: `reports/hw01/cases/nondeterminism_input.json`
- Runs per temperature: 20
- Temperatures: `0.0` and `0.7`
- Total runs: 40
- Raw results: `reports/hw01/raw/nondeterminism_runs.json` and `reports/hw01/raw/nondeterminism_runs.csv`
- Percentiles: calculated from the 20 sorted latency values for each temperature using linear interpolation.

## Tag variability

| Metric | Temp 0.0 | Temp 0.7 |
|---|---:|---:|
| Distinct tag sets | 2 | 20 |
| Tags in all 20 runs | `soccer match rescheduling` | None |
| Tags in exactly 1 run | `event logistics update`; `venue change notification` | `backup venue preparation`; `community center backup venue`; `community event logistics`; `community soccer semifinal rescheduling`; `event logistics changes`; `field maintenance`; `field maintenance notice`; `field maintenance update`; `logistical updates`; `logistics and backup venue`; `rain backup venue info`; `spartan stadium event details`; `stadium location change`; `stadium relocation`; `venue change logistics`; `venue change notice`; `venue logistics update` |

## Latency

| Metric | Temp 0.0 | Temp 0.7 |
|---|---:|---:|
| p50 | 82,441 ms | 103,358 ms |
| p95 | 92,363 ms | 142,961 ms |
| p99 | 93,513 ms | 149,838 ms |

# Part 4 — Model Client and Token Accounting

## Five-turn conversation token usage

| Turn | Input tokens | Output tokens | Total tokens |
|---:|---:|---:|---:|
| 1 | 88 | 647 | 735 |
| 2 | 283 | 599 | 882 |
| 3 | 489 | 576 | 1,065 |
| 4 | 647 | 692 | 1,339 |
| 5 | 865 | 739 | 1,604 |

## `/stats` checkpoints

| Checkpoint | Turn count | Cumulative input tokens | Cumulative output tokens | Serialized conversation-history length |
|---|---:|---:|---:|---:|
| After turn 3 | 3 | 860 | 1,822 | 2,919 characters |
| After turn 5 | 5 | 2,372 | 3,253 | 4,768 characters |

On exit, the client reported 5 turns, 2,372 cumulative input tokens, and 3,253 cumulative output tokens.
