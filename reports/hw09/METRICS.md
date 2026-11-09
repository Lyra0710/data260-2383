# HW9 Metrics

## Part 2 Semantic Cache

| Metric | Observed result |
| --- | ---: |
| Queries | 10 |
| Cache hits | 3 |
| Cache hit rate | 30.0% |
| Average cached latency | 28.07 ms |
| Average non-cached latency | 7444.27 ms |

## Part 3 Threshold Sweep

The false-hit rate is false hits divided by observed cache hits. Cost uses
relative units: a cache miss costs 1 unit and a false hit costs 10 units.

| Threshold | Hit rate | False-hit rate | Mean latency | Total cost |
| ---: | ---: | ---: | ---: | ---: |
| 0.75 | 75.0% | 33.33% | 639.40 ms | 110 |
| 0.80 | 75.0% | 33.33% | 792.08 ms | 110 |
| 0.85 | 75.0% | 33.33% | 699.82 ms | 110 |
| 0.90 | 55.0% | 22.73% | 958.40 ms | 68 |
| 0.95 | 25.0% | 0.0% | 1405.19 ms | 30 |

## Threshold Choice

Threshold 0.95 has the lowest total cost and no observed false hits. Its
trade-off is a lower hit rate because only exact duplicates were served from
the cache in this run.

## Part 4 Multi-Agent Variants

The evaluator uses only the small reference dataset. The validation gate kept
the learned lessons because validation improved from 1/4 to 4/4 correct and
did not regress a previous pass.

| Variant | Correct | Incorrect | Average attempts |
| --- | ---: | ---: | ---: |
| Baseline | 0 | 3 | 1.0 |
| Evaluator Repair | 3 | 0 | 2.0 |
| Lesson Memory | 3 | 0 | 1.0 |
| Validated Improvement | 3 | 0 | 1.0 |

The runner is deterministic and local, so its sub-millisecond execution time
rounds to 0.0 ms in the summary; it is not an external model-latency claim.
