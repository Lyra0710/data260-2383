## Part 2 — Agent Reliability

Model: qwen3:8b
SEED: 2383
Attempts: 21 across three fixed verification tasks

| Metric | Before repair path | After repair path |
|---|---:|---:|
| Well-formed tool-use attempts | 21 / 21 (100.0%) | 21 / 21 (100.0%) |

| Failure type | Count |
|---|---:|
| Malformed arguments | 0 |
| Unknown tool | 0 |
| Text when a tool was required | 0 |
| Lost multi-step chain | 0 |
