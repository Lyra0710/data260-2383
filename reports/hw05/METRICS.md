# Part 5 Metrics

Model: `qwen3:8b`  
Provider: Local Ollama  
Maximum steps: 3

Retry experiment configuration:

- Seed: `2383`
- Calls per failure rate: `50`
- Failure rates: `0.0`, `0.2`, and `0.5`
- Maximum retries: `2`
- Initial backoff: `0.2` seconds, with exponential backoff

| Scenario | Steps | Stop reason | Tool calls |
|---|---:|---|---:|
| What fixtures are scheduled at venue 1? | 2 | normal_completion | 1 |
| Give me details for fixture 1. | 2 | normal_completion | 1 |
| Search for fixtures containing SJSU. | 2 | normal_completion | 1 |
| What is the total number of available slots at venue 2? | 2 | normal_completion | 1 |

All four Ollama scenarios completed normally within the maximum step limit. Each scenario used one domain-tool call followed by a final response.

## Retry measurements

The retry experiment called `fixture_details(1)` 50 times at each configured
failure rate. The raw records are stored in
`reports/hw05/raw/retry_rate_*.jsonl`.

| Simulated failure rate | Calls | Success rate | Mean latency | p99 latency |
|---:|---:|---:|---:|---:|
| 0% | 50 | 100.0% | 39.49 ms | 55.68 ms |
| 20% | 50 | 100.0% | 70.00 ms | 262.19 ms |
| 50% | 50 | 92.0% | 199.72 ms | 656.59 ms |


## Validation results

- Offline MCP/domain-tool tests: `8/8 tests passed`.
- Raw retry records: `150` total records, with 50 records per failure rate.
- Live backend smoke check: `/docs` responded on port `8583`.
- Live domain-tool smoke check: `fixture_details(1)` returned successfully.
- Live TheMealDB smoke check: `Arrabiata` search returned a meal.
- Agent log: at least four runs were recorded in `agent_runs.jsonl`.

The run log also contains an earlier intermediate `6/6 tests passed` result;
the current test code includes the safety-rule and maximum-step checks and
expects `8/8`.
