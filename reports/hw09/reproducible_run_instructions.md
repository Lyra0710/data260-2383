# HW9 Reproducible Run Instructions

## Prerequisites

- Python 3.11 virtual environment in `.venv`
- Docker Desktop for Redis Stack
- MySQL database configured in `code/web_application/.env`
- Ollama running with `qwen3:8b` and `nomic-embed-text`

From the repository root, activate the environment and start Redis:

```bash
source .venv/bin/activate
docker compose up -d redis
docker compose exec redis redis-cli PING
```

## Prepare the database and start the API

Run the HW9 migration once against the configured MySQL database, then start
the application from the web-application directory:

```bash
set -a
source code/web_application/.env
set +a
mysql -u "$MYSQL_USER" -p "$MYSQL_DATABASE" < code/web_application/migrations/002_hw9_fixture_view_count.sql
cd code/web_application
uvicorn main:app --reload --port 8583
```

If `MYSQL_SOCKET` is set in `.env`, add `--socket "$MYSQL_SOCKET"` to the
`mysql` command.

Keep the API running in this terminal for Parts 1 and 2.

## Part 1 — View counter

Request the same fixture repeatedly through the authenticated fixture endpoint.
The Redis value can be inspected with:

```bash
docker compose exec redis redis-cli GET s2383:views:fixture:3
```

After every tenth access, inspect the corresponding MySQL `fixtures.view_count`
value to confirm the write-behind synchronization.

## Part 2 — Semantic-cache demo

In a second terminal, activate `.venv` and run:

```bash
cd code/web_application
python semantic_cache_demo.py
```

The script writes the ten request results and latency summary to
`reports/hw09/raw/semantic_cache_demo.json`.

## Part 3 — Threshold sweep and cost analysis

From `code/web_application`, run:

```bash
python threshold_sweep.py
python calculate_cache_costs.py
```

The fixed cases are in `reports/hw09/cache_cases.yaml`. The sweep and cost
outputs are written to `reports/hw09/raw/threshold_sweep.json` and
`reports/hw09/raw/cost_analysis.json`.

## Part 4 — Multi-agent evaluation

From `code/web_application`, run:

```bash
python multi_agent_system.py
```

The runner reads the reference, training, validation, and held-out test data
from `reports/hw09/part4/`. It rewrites `lessons.json` and
`multi_agent_results.json` with the evaluation output.

## Notes

The Part 2–4 commands overwrite their generated raw result files. Preserve the
submitted evidence before rerunning them if you need to retain the original
measurements.
