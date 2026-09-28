# HW4 reproducible run instructions

Run the commands below from the repository root:

```text
data260-2383/
```

These instructions describe the current code in this repository. The backend
uses MySQL, and the RAG commands use a local Ollama server.

## 1. Install dependencies

Python 3.11 and Node.js/npm are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cd code/web_application/frontend
npm install
cd ../../..
```

## 2. Configure MySQL and the backend

Create the MySQL database before starting the application. The application
creates its tables at startup, but it does not create the database itself.

For this repository, the database configuration is read from the ignored file
`code/web_application/.env`. Create that file with values appropriate for
your local MySQL installation:

```dotenv
MYSQL_USER=<mysql username>
MYSQL_PASSWORD=<mysql password>
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=s2383_rel
APP_PORT=8583
BENCHMARK_EMAIL=<email of an existing application user>
BENCHMARK_PASSWORD=<password for that user>
```

Alternatively, set `MYSQL_SOCKET` to the MySQL Unix-socket path. When
`MYSQL_SOCKET` is set, `db.py` uses that socket instead of
`MYSQL_HOST` and `MYSQL_PORT`.

Create the configured database using your MySQL client. For example, if the
database is named `s2383_rel`:

```bash
mysql -u <mysql username> -p -e \
  "CREATE DATABASE IF NOT EXISTS s2383_rel;"
```

The benchmark and verification script log in through the API using
`BENCHMARK_EMAIL` and `BENCHMARK_PASSWORD`. If that user does not already
exist, start the backend and register one through `/api/register` before
running the benchmark:

```bash
curl -X POST http://127.0.0.1:8583/api/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"HW4 User","email":"<email>","password":"<password>"}'
```

Put the same email and password in `code/web_application/.env`.

## 3. Start the backend

From the repository root, run:

```bash
source .venv/bin/activate
python code/web_application/main.py
```

Leave this terminal running. The backend listens on the `APP_PORT` value from
`.env` (8583 in the example above).

## 4. Run the HW4 database seed

With the MySQL configuration in place, run this from a second terminal at the
repository root:

```bash
source .venv/bin/activate
python code/web_application/seed_part3.py
```

The script uses seed `2383`, creates 5,000 fixtures, and creates 200 related
items. On a later run it removes only fixtures whose names begin with
`HW4 Fixture` and their related items before inserting the seeded data again.

## 5. Verify the backend

With the backend running and the credentials in `.env` valid:

```bash
python code/verify_hw04.py
```

This checks:

- `GET /` returns HTTP 200
- login succeeds
- the naive list endpoint returns data and reports 11 SQL statements for
  `page_size=10`
- the fixed list endpoint returns data and reports 2 SQL statements for
  `page_size=10`

The script writes `reports/hw04/verification.json`.

## 6. Run the Part 3 benchmark

The backend must remain running, and the seeded database must contain at
least 200 records for the requested page sizes.

```bash
python code/web_application/benchmark_part3.py
```

The benchmark performs 30 requests for each of these six cases:

- naive, page size 10
- naive, page size 50
- naive, page size 200
- fixed, page size 10
- fixed, page size 50
- fixed, page size 200

It writes all 180 measurements to:

```text
reports/hw04/raw/n_plus_one_measurements.csv
reports/hw04/raw/n_plus_one_measurements.json
```

Generate the summary table afterward:

```bash
python code/web_application/benchmark_part3.py --summarize
```

This reads the CSV and writes:

```text
reports/hw04/METRICS.md
```

The summarizer uses nearest-rank p50, p95, and p99 latency calculations.

## 7. Run the React client

Keep the backend running, then use another terminal:

```bash
source .venv/bin/activate
cd code/web_application/frontend
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173/`. The
frontend proxy sends `/api` requests to the `API_PROXY_TARGET` value in
`code/web_application/frontend/.env.development`, which is configured for
`http://127.0.0.1:8583`.

To test a production build instead:

```bash
cd code/web_application/frontend
npm run build
```

## 8. Run the RAG application

The RAG code requires a local Ollama server and the models named by its
defaults. Start the server in one terminal:

```bash
ollama serve
```

In another terminal, pull the models:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:8b
```

Run the following commands from the repository root in another terminal:

```bash
source .venv/bin/activate
python code/rag/rag.py build-index
```

`build-index` reads the five PDFs in `code/rag/corpus/`, uses 500-character
chunks with 50-character overlap, and stores the ChromaDB index in
`code/rag/chroma_db/`.

To print the top-k retrieved chunks for one question:

```bash
python code/rag/rag.py retrieve \
  --question "What is a REST API?" \
  --k 3
```

To run the six-question comparison of No-RAG, Basic-RAG, and Context-RAG:

```bash
python code/rag/rag.py run-evaluation
```

This writes `reports/hw04/raw/rag_comparison.json`.

To run the k=1, k=3, and k=5 sweep for one of the supplied questions:

```bash
python code/rag/rag.py run-sweep --question-id q2
```

This writes `reports/hw04/raw/rag_k_sweep.json`.
