# HW4 Part 3 Metrics

Percentiles use the nearest-rank method.

| Page size | Version | SQL stmts/req | p50 (ms) | p95 (ms) | p99 (ms) |
|---:|---|---:|---:|---:|---:|
| 10 | naive | 11 | 3.305 | 3.863 | 4.603 |
| 10 | fixed | 2 | 1.453 | 1.670 | 2.157 |
| 50 | naive | 51 | 8.398 | 11.114 | 11.377 |
| 50 | fixed | 2 | 1.838 | 2.139 | 2.360 |
| 200 | naive | 201 | 28.919 | 34.089 | 38.089 |
| 200 | fixed | 2 | 3.107 | 3.517 | 17.197 |

## Fixed-version p50 latency reduction

| Page size | Naive p50 (ms) | Fixed p50 (ms) | Reduction |
|---:|---:|---:|---:|
| 10 | 3.305 | 1.453 | 56.0% |
| 50 | 8.398 | 1.838 | 78.1% |
| 200 | 28.919 | 3.107 | 89.3% |
