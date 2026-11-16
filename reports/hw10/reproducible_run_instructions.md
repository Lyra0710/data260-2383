# HW10 Reproducible Run Instructions

## Prerequisites

- Python 3.11 virtual environment in `.venv`
- Docker Desktop for Kafka and Redis Stack
- Ollama with `qwen3:8b` and `nomic-embed-text`

From the repository root:

```zsh
source .venv/bin/activate
docker compose up -d kafka redis
```

Start Planner, Writer, Reviewer, and evaluator worker processes in separate
terminals from `code/web_application`.

```zsh
PYTHONPATH=. python3 planner.py
PYTHONPATH=. python3 writer.py
PYTHONPATH=. python3 reviewer.py
HW10_EVALUATION_MODE=full PYTHONPATH=. python3 evaluator_worker.py
```

## Judge validation

```zsh
PYTHONPATH=code/web_application python3 code/web_application/run_hw10_judge.py
```

This writes `reports/hw10/raw/judge_validation.json`.

## Trace examples

```zsh
PYTHONPATH=code/web_application python3 code/web_application/run_hw10_pipeline.py --cache-scope hw10-success-2
PYTHONPATH=code/web_application python3 code/web_application/run_hw10_pipeline.py --force-failure --cache-scope hw10-failure-1
```

Run the successful command once with a new cache scope for a miss and again
with the same scope for a hit.

## Latency experiment

Restart only the evaluator worker in linkage-only mode:

```zsh
HW10_EVALUATION_MODE=linkage_only PYTHONPATH=. python3 evaluator_worker.py
```

Then run:

```zsh
HW10_EVALUATION_MODE=linkage_only PYTHONPATH=code/web_application \
python3 code/web_application/run_hw10_latency_experiment.py --count 50
```

The latency result is written to `reports/hw10/raw/latency_experiment.json`.
The `linkage_only` mode is documented in `METRICS.md`; the full GEval
evaluation is separately validated above.

## Dashboard

```zsh
PYTHONPATH=code/web_application streamlit run code/web_application/dashboard.py
```
