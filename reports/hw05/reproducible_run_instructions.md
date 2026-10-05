# HW5 reproducible run instructions

Run every command below from the repository root. 


## 1. Install Python dependencies

Create or activate the repository virtual environment and install the pinned
repository dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` does not list the MCP SDK. Install the MCP 1.x-compatible
range used by `code/mcp/domain_server.py` and `code/mcp/meals_server.py`:

```bash
python -m pip install "mcp[cli]>=1.28,<2" httpx
```

Do not install MCP 2.x for this code. The run log records that MCP 2.x does
not provide `mcp.server.fastmcp.FastMCP`, which prevents the MCP servers from
starting.

## 2. Configure the fixtures API and credentials

The fixtures backend requires a running MySQL database. Its database settings
are read by `code/web_application/db.py` from `code/web_application/.env`.
That file is ignored by Git, so it must be created locally. Use values for the
local MySQL installation; the names below are the variables the code reads:

```dotenv
MYSQL_USER=<mysql username>
MYSQL_PASSWORD=<mysql password>
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=s2383_rel
APP_PORT=8583
```

Alternatively, set `MYSQL_SOCKET` in that file. When it is set, the backend
uses the Unix socket instead of `MYSQL_HOST` and `MYSQL_PORT`.

The domain MCP code separately requires `API_EMAIL` and `API_PASSWORD`. Since
the commands below run from the repository root, put those variables in a
root `.env`, or export them in the shell before running the MCP commands:

```dotenv
API_BASE_URL=http://127.0.0.1:8583/api
API_EMAIL=<email of an existing fixtures API user>
API_PASSWORD=<password for that user>
```

The repository does not contain the database password, API credentials, or an
automatic script that creates the observed HW5 records. Therefore, the
database must already contain a valid user and the fixture/venue data needed
by the logged examples, including fixture 1, venue 1, and venue 2. The
backend creates tables at startup but does not create the MySQL database or
populate these records.

Create the database if it does not exist:

```bash
mysql -u <mysql username> -p -e \
  "CREATE DATABASE IF NOT EXISTS s2383_rel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

If the API user does not exist, start the backend first and register one
through the public endpoint, then place the same credentials in the root
`.env`:

```bash
curl -X POST http://127.0.0.1:8583/api/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"HW5 User","email":"<email>","password":"<password>"}'
```

## 3. Start the fixtures backend

From the repository root, in a terminal that remains running:

```bash
source .venv/bin/activate
python code/web_application/main.py
```

The application reads `APP_PORT` and should listen on `127.0.0.1:8583` for
the configuration above. Verify that it responds before continuing:

```bash
curl -i http://127.0.0.1:8583/docs
```

The domain MCP tools log in for each API request. A successful login and API
response are required for the live domain-tool checks and retry measurements.

## 4. Start Ollama and obtain the agent model

In another terminal:

```bash
ollama serve
```

Leave it running. In a third terminal, confirm the model is available:

```bash
ollama list
ollama pull qwen3:8b
```

`code/mcp/agent.py` uses `qwen3:8b` by default and sends requests to
`http://127.0.0.1:11434/api/chat`. A different model can be selected only by
setting `OLLAMA_MODEL`, but that would not reproduce the logged HW5 run.

## 5. Run the offline MCP/tool tests

From the repository root, with `.venv` active:

```bash
python code/mcp/test_tools.py
```

The current code should end with:

```text
8/8 tests passed
```

These tests replace the live API with a fake `get_json` function. They do not
require MySQL, the fixtures backend, Ollama, or TheMealDB.

## 6. Generate the retry measurements

With the fixtures backend and credentials configured, run:

```bash
python code/mcp/measure_retries.py
```

The script uses seed `2383`, tests failure rates `0.0`, `0.2`, and `0.5`, and
makes 50 calls for each rate. It overwrites these files:

```text
reports/hw05/raw/retry_rate_0.0.jsonl
reports/hw05/raw/retry_rate_0.2.jsonl
reports/hw05/raw/retry_rate_0.5.jsonl
```

Each file should contain exactly 50 JSONL records, for 150 records total.
The measured latency values can vary by machine and network conditions; the
script prints the mean and p99 latency for each rate.

## 7. Run the logged Ollama agent scenarios

With both services still running, execute these commands from the repository
root:

```bash
python code/mcp/agent.py "What fixtures are scheduled at venue 1?"
python code/mcp/agent.py "Give me details for fixture 1."
python code/mcp/agent.py "Search for fixtures containing SJSU."
python code/mcp/agent.py "What is the total number of available slots at venue 2?"
```

Each command appends one JSON object to `agent_runs.jsonl`. The logged runs
used two model steps, one domain-tool call, and `normal_completion`; the run
with the wording `Get fixture 1` in the historical log stopped at
`max_steps`, so it is not one of the four successful scenarios above.

## 8. Run HW5 verification

Finally, run:

```bash
python code/verify_hw05.py
```

The verifier checks:

- the backend responds at `http://127.0.0.1:8583/docs`;
- the live domain `fixture_details` tool responds;
- the live TheMealDB `Arrabiata` search returns a result;
- `code/mcp/test_tools.py` reports `8/8 tests passed`;
- all three raw measurement files contain 50 lines each; and
- `agent_runs.jsonl` contains at least four runs.

It writes the result to:

```text
reports/hw05/verification.json
```

The verifier records the current Git commit hash, model `qwen3:8b`, seed
`2383`, and the pass/fail status of each check. The commit hash and live
latencies will differ if the repository or environment changes.

## Optional MCP Inspector checks

The run log also used MCP Inspector to launch the two servers. These checks
are optional for reproducing the verifier and require the MCP CLI:

```bash
mcp dev code/mcp/meals_server.py --with "mcp>=1.28,<2" --with httpx
mcp dev code/mcp/domain_server.py --with "mcp>=1.28,<2" --with httpx
```
