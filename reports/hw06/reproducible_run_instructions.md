# HW6 Reproducible Run Instructions

Run commands from the repository root unless a command says otherwise. HW6 uses SID4 `2383`, port `8583`, MongoDB database `s2383_doc`, local chat model `qwen3:8b`, and embedding model `nomic-embed-text`.

## 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Configure local services

The shared FastAPI application imports the prior relational-fixtures code as well as the HW6 MongoDB code. Create `code/web_application/.env` with local MySQL settings and a MongoDB connection string. Do not commit this file.

```dotenv
MYSQL_USER=<mysql username>
MYSQL_PASSWORD=<mysql password>
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=s2383_rel
APP_PORT=8583
MONGO_URI=mongodb://127.0.0.1:27017
```

Start MongoDB and Ollama in separate terminals. The MongoDB command below is for a Homebrew installation; use the equivalent command for another installation.

```bash
brew services start mongodb-community
ollama serve
```

In another terminal, obtain the two local models:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

Initialize or refresh the MongoDB validators and indexes:

```bash
cd code/web_application
../../.venv/bin/python init_mongo.py
cd ../..
```

## 3. Start the API

Run this command from `code/web_application` and leave it running:

```bash
../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8583
```

Confirm the application is available:

```bash
curl -sS http://127.0.0.1:8583/ | .venv/bin/python -m json.tool
```

## 4. Run the Part 2 memory demonstration

From `code/web_application`, send messages to `/api/chat` with a consistent user and session ID. The saved homework run uses `hw6-demo-user` and `hw6-demo-session`. After at least 10 messages, inspect memory and aggregate results:

```bash
curl -sS http://127.0.0.1:8583/api/memory/hw6-demo-user | \
  ../../.venv/bin/python -m json.tool

curl -sS http://127.0.0.1:8583/api/aggregate/hw6-demo-user | \
  ../../.venv/bin/python -m json.tool
```

The saved evidence is in `reports/hw06/raw/memory_demo.json` and `reports/hw06/raw/aggregate_demo.json`.

## 5. Reproduce Part 3 experiments

The four complete experiment outputs are already committed under `reports/hw06/raw/`. Re-running a setting overwrites its corresponding raw output and can take several minutes because each setting makes 35 local-model requests. Run one setting at a time: stop the server, start it with the listed environment variables, then run the listed experiment command from `code/web_application`.

| Run ID | Server environment | Experiment command |
| --- | --- | --- |
| `stn4` | `SHORT_TERM_N=4 COMPACT_SHORT_TERM_N=0 HW6_METRICS_PATH=../../reports/hw06/raw/chat_metrics_n4.jsonl` | `../../.venv/bin/python run_memory_experiment.py --short-term-n 4 --run-id stn4 --output ../../reports/hw06/raw/experiment_n4.json` |
| `stn12` | `SHORT_TERM_N=12 COMPACT_SHORT_TERM_N=0 HW6_METRICS_PATH=../../reports/hw06/raw/chat_metrics_n12.jsonl` | `../../.venv/bin/python run_memory_experiment.py --short-term-n 12 --run-id stn12 --output ../../reports/hw06/raw/experiment_n12.json` |
| `stn30` | `SHORT_TERM_N=30 COMPACT_SHORT_TERM_N=0 HW6_METRICS_PATH=../../reports/hw06/raw/chat_metrics_n30.jsonl` | `../../.venv/bin/python run_memory_experiment.py --short-term-n 30 --run-id stn30 --output ../../reports/hw06/raw/experiment_n30.json` |
| `compaction` | `SHORT_TERM_N=30 COMPACT_SHORT_TERM_N=4 HW6_METRICS_PATH=../../reports/hw06/raw/chat_metrics_compaction.jsonl` | `../../.venv/bin/python run_memory_experiment.py --short-term-n 30 --compact-short-term-n 4 --run-id compaction --output ../../reports/hw06/raw/experiment_compaction.json` |

For example, start the N=4 server with:

```bash
SHORT_TERM_N=4 COMPACT_SHORT_TERM_N=0 \
HW6_METRICS_PATH=../../reports/hw06/raw/chat_metrics_n4.jsonl \
../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8583
```

After all four settings finish, generate the scored probe JSON and metrics report:

```bash
../../.venv/bin/python analyze_memory_experiments.py
```

This writes `reports/hw06/raw/probe_scores.json` and `reports/hw06/METRICS.md`.

## 6. Run the Part 4 file-memory demonstration

From `code/web_application`:

```bash
../../.venv/bin/python run_file_memory_demo.py
```

The script restores the controlled 55-line input from `raw/MEMORY_before_compaction.md`, runs `/compact`, runs `/dream`, writes the final root-level `MEMORY.md`, and saves `raw/file_memory_demo.json`.

With the API running, test the command endpoint:

```bash
curl -sS -X POST http://127.0.0.1:8583/api/file-memory/command \
  -H "Content-Type: application/json" \
  -d '{"command":"/help"}' | ../../.venv/bin/python -m json.tool
```

## 7. Run HW6 verification

Start the API with a temporary metrics destination so the smoke-test chat request does not change the submitted Part 3 raw files:

```bash
cd code/web_application
HW6_METRICS_PATH=/tmp/hw6_verification_metrics.jsonl \
../../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8583
```

In another terminal at the repository root:

```bash
.venv/bin/python code/verify_hw06.py
```

The verifier checks the root endpoint, file-memory command endpoint, chat endpoint, and required artifacts. It writes `reports/hw06/verification.json` with the tested commit hash, configuration, hardware string, and pass/fail details.

## Saved HW6 artifacts

- `RUN_LOG.txt` contains real console output from the submitted runs.
- `raw/` contains MongoDB-memory evidence, all experiment outputs, per-request metrics, probe scores, and file-memory evidence.
- `METRICS.md` contains the generated Part 3 comparison and cost tables.
- `AI_USE.md` documents AI assistance and the independently reviewed unsuitable model output.
