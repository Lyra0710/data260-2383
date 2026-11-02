# HW8 Reproducible Run Instructions

## Prerequisites

- Python 3.11 virtual environment in `.venv`
- Docker Desktop
- Ollama with `qwen3:8b` available for the Part 2 pipeline

## Start Part 1 services

From the repository root:

```bash
source .venv/bin/activate
docker compose up --build -d
docker ps
```

The stack starts Kafka at `localhost:9092`, the Kafka worker, and FastAPI at `http://127.0.0.1:8583`.

## Run the Part 1 demo and smoke test

```bash
cd code/web_application
python homework_demo.py
cd ../..
python code/verify_hw08.py
```

## Run the Part 2 pipeline

Keep Ollama running, then open four terminals. In each terminal, activate `.venv` and change to `code/web_application`.

```bash
python planner.py
python writer.py
python reviewer.py
python send_question.py
```

Start Planner, Writer, and Reviewer before sending the question. The sender prints the final JSON from `s2383_final`.

## Reproduce Part 3 ordering summaries

Open two terminals for the two ordering writers, then run the producer:

```bash
python ordering_writer.py --run unkeyed --worker-id writer-1
python ordering_writer.py --run unkeyed --worker-id writer-2
python ordering_experiment.py --run unkeyed
```

Stop both writers after all 20 messages are processed, then run:

```bash
python summarize_ordering.py --run unkeyed
```

Repeat the same commands with `--run keyed`. The raw CSV and JSON evidence is written to `reports/hw08/raw/`.
