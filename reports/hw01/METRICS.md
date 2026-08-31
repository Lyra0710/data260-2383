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
