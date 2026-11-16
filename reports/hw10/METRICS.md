# HW10 Metrics and Evidence

This file summarizes the recorded Homework 10 results. Raw evidence is in
`reports/hw10/raw/`.

## Part 1 — Streamlit Operations Dashboard

`dashboard.py` provides Summary, Evaluation, and Trace Lookup pages. Summary
uses HW10 spans and the 50-request experiment to show request count, separate
cache hits and misses, cache hit rate, request-level error rate, and cache-miss
p50/p95 latency. Every metric identifies its local evidence source and time
window.

## Part 2 — Automated Kafka Pipeline Evaluation

The successful cache-miss trace
`39ee2a20-338c-4856-ba24-74a8dc0549cb` used DeepEval GEval with local
`qwen3:8b`.

| Pipeline stage | Score | Recorded interpretation |
| --- | ---: | --- |
| Planner plan quality | 3 / 5 | Practical ordered steps addressed the question. |
| Writer helpfulness | 3 / 5 | Relevant, concise scheduling guidance. |
| Reviewer final helpfulness | 3 / 5 | Relevant, concise scheduling guidance. |
| Final-vs-draft difference | 0 | Final answer was unchanged relative to the draft. |

The unchanged final score is reported as observed; it is not treated as an
improvement claim. Full results are in `raw/pipeline_evaluations.jsonl`.

## Part 3 — Judge Validation

`eval_cases.json` contains 20 frozen Writer drafts, and `human_labels.csv`
contains independently assigned 1–5 labels committed before scoring.

| Metric | Recorded result |
| --- | ---: |
| Judge | DeepEval GEval with local `qwen3:8b` |
| Cases / repeats | 20 / 3 |
| Spearman rank correlation | -0.2536 |
| Mean absolute difference | 1.5 |
| Changed scores | 0 / 40 repeat comparisons |
| Mean / maximum score change | 0.0 / 0 |

The judge was perfectly repeatable but poorly aligned with human labels. It
should not gate deployment without more independently labeled data,
calibration, and better score separation. Per-case results are in
`raw/judge_validation.json`.

## Part 4 — Distributed Tracing and Latency

| Path | Trace ID | Recorded result |
| --- | --- | --- |
| Successful cache miss | `39ee2a20-338c-4856-ba24-74a8dc0549cb` | Cache lookup through evaluation completed. |
| Cache hit | `1cb754d7-821e-46a9-bd7a-9a0d6a827ad1` | Cached answer returned. |
| Failed Writer path | `eed9b9f8-fb35-4b13-9c95-e7bea5164d95` | Three retries then dead letter. |

The 50-request experiment used explicit `linkage_only` evaluation mode. Full
DeepEval scoring was validated in Part 2; latency mode validated linked final
messages without repeating three LLM judge calls per request.

| Stage | p50 (ms) | p95 (ms) | Share of end-to-end |
| --- | ---: | ---: | ---: |
| Cache lookup | 41.95 | 65.08 | 0.28% |
| Planner | 2547.88 | 2845.24 | 15.95% |
| Writer | 2199.89 | 2439.12 | 13.76% |
| Reviewer | 2209.16 | 2470.22 | 13.84% |
| Evaluation (linkage-only) | 0.07 | 0.30 | 0.00% |
| Runner setup | 9067.82 | 9113.48 | 55.97% |
| Kafka queue wait | 24.43 | 36.81 | 0.16% |
| End-to-end | 16120.08 | 16928.52 | 100.00% |

Runner setup is the dominant contributor. Reusing Kafka clients across
requests is the first optimization; after startup overhead, Planner is the
slowest model stage. The raw summary is `raw/latency_experiment.json`.
