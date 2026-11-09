# HW9 Metrics and Evidence

This file summarizes the recorded HW9 results and implementation behavior.

## Part 1 — Redis Fixture View Counter

`fixture_view_cache.py` calls Redis `INCR` on keys formatted as
`s2383:views:fixture:<fixture_id>`. When the returned count is divisible by
10, it assigns that count to `fixture.view_count`, commits the database
session, and logs a database-sync message.

The recorded run log includes this final state for fixture 3:

| Redis count | MySQL `view_count` |
| ---: | ---: |
| 25 | 20 |

## Part 2 — Semantic Response Cache

The `/api/chat` handler embeds the incoming message and checks the semantic
cache before calling `generate_reply`. On a cache hit it returns the stored
answer, `is_cached=true`, similarity score, and latency. On a miss it calls
`generate_reply`, stores the answer and embedding, and returns
`is_cached=false`.

| Metric | Recorded result |
| --- | ---: |
| Queries | 10 |
| Cache hits | 3 |
| Cache hit rate | 30.0% |
| Average cached latency | 28.07 ms |
| Average non-cached latency | 7,444.27 ms |

The recorded request results show three cache hits, all with similarity score
1.0. The submitted raw result file is `raw/semantic_cache_demo.json`.

## Part 3 — Threshold Sweep

`cache_cases.yaml` contains 40 labeled cases: 10 exact duplicates, 10
paraphrases, 10 superficially similar different-answer cases, and 10
unrelated cases. `raw/threshold_sweep.json` contains the recorded results.

False-hit rate below is false hits divided by observed cache hits, as defined
by `threshold_sweep.py`.

| Threshold | Hit rate | False-hit rate | Mean latency | Total cost |
| ---: | ---: | ---: | ---: | ---: |
| 0.75 | 75.0% | 33.33% | 639.40 ms | 110 |
| 0.80 | 75.0% | 33.33% | 792.08 ms | 110 |
| 0.85 | 75.0% | 33.33% | 699.82 ms | 110 |
| 0.90 | 55.0% | 22.73% | 958.40 ms | 68 |
| 0.95 | 25.0% | 0.0% | 1,405.19 ms | 30 |

### Recorded false-hit example

At threshold 0.85, `similar_miss_02` was recorded as a false hit.

| Item | Recorded value |
| --- | --- |
| Cached query | `Give me fixture 1's code.` |
| Incoming query | `Give me fixture 3's code.` |
| Similarity score | 0.897811233997 |
| Cached answer returned | `The code for Fixture 1 is "F1".` |
| Expected disposition | Miss |

The run log separately records fixture 3's database code as `FIX-002`; that
is the domain record relevant to the incoming query.

### Cost model and threshold choice

`calculate_cache_costs.py` applies a cost of 1 per cache miss and 10 per
false hit, using `misses * 1 + false_hits * 10`. Under that model, threshold
0.95 had the lowest recorded total cost (30) and no recorded false hits.

### Stale answers and invalidation

The run log records creation of fixture 3 related item 1 with details
`Initial cache demonstration note.` and a later database update to
`Updated cache demonstration note.`

The implementation stores a `data_version` field with cache entries.
`update_related_item` commits the related-item update and calls
`semantic_response_cache.bump_data_version()`. `find_similar` rejects an entry
when its stored data version differs from the current version.

## Part 4 — Self-Improving Multi-Agent System

`multi_agent_system.py` defines `AnsweringAgent` and `EvaluatorAgent`. The
evaluator compares answers to `part4/reference_data.json`; the separate
training, validation, and test files contain question records. On `REVISE`,
the runner makes one revision, for a maximum of two attempts.

### Recorded revision sequence

`training_results` records this sequence for `train_01`:

| Step | Recorded value |
| --- | --- |
| Question | What is the fixture code for fixture 1? |
| Initial answer | I do not have a verified value for fixture 1. |
| Evaluator result | `REVISE` |
| Evaluator feedback | The fixture 1 code is FIX-001. |
| Revised answer | The fixture 1 code is FIX-001. |
| Final evaluation | `PASS` |
| Attempts | 2 |

### Lessons and validation

`part4/lessons.json` records two lessons. The `fixture_code` lesson has
`use_count: 2`; the `details` lesson has `use_count: 1`.

The recorded validation result was 1/4 correct before applying selected
lessons and 4/4 correct afterward. `lessons_kept` is `true` in
`part4/multi_agent_results.json`. The validation set includes an unsupported
venue question; it was recorded as `PASS` before and after because the answer
stated that no verified answer was available.

### Final held-out test results

| Variant | Correct | Incorrect | Average attempts | Average latency |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0 | 3 | 1.0 | 0.0 ms |
| Evaluator Repair | 3 | 0 | 2.0 | 0.0 ms |
| Lesson Memory | 3 | 0 | 1.0 | 0.0 ms |
| Validated Improvement | 3 | 0 | 1.0 | 0.0 ms |

The runner records local execution times that round to 0.0 ms in the summary.
