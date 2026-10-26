# HW7 Reproducible Run Instructions

Run commands from the repository root. HW7 uses SID4 `2383`, API port `8583`,
local chat model `qwen3:8b`, embedding model `nomic-embed-text`, seed `2383`,
and verification seed `262383`.

## 1. Install dependencies and configure local values

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create `code/web_application/.env` with local MySQL settings and a JWT secret.
Do not commit this file.

```dotenv
MYSQL_USER=<mysql username>
MYSQL_PASSWORD=<mysql password>
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=s2383_rel
APP_PORT=8583
JWT_SECRET_KEY=<a long random value>
```

Create a root `.env` for the domain tools and verifier. Use the credentials of
one seeded user.

```dotenv
API_BASE_URL=http://127.0.0.1:8583/api
API_USERNAME=reader_demo
API_PASSWORD=<reader_demo password>
OLLAMA_MODEL=qwen3:8b
```

Start MySQL and Ollama, then obtain the local models:

```bash
ollama serve
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

## 2. Apply the authentication migration and create demonstration users

```bash
MYSQL_PWD="$MYSQL_PASSWORD" mysql --protocol=SOCKET \
  --socket="$MYSQL_SOCKET" -u "$MYSQL_USER" -D "$MYSQL_DATABASE" \
  < code/web_application/migrations/001_hw7_jwt_roles.sql

python code/web_application/seed_hw7_users.py
```

The seed script prompts for the three local passwords. Set `API_USERNAME` and
`API_PASSWORD` in the root `.env` to one of those accounts.

## 3. Start the API and test Part 1

In a terminal that remains running:

```bash
python code/web_application/main.py
```

Visit `http://127.0.0.1:8583/` and use the login form. A valid account returns
a token; an incorrect password returns HTTP 401. The `/auth/me` endpoint
requires `Authorization: Bearer <token>`.

## 4. Run the Part 2 and Part 3 agent evaluations

With the API, MySQL, and Ollama running:

```bash
python code/mcp/measure_agent_reliability.py
python code/mcp/compare_reflexion.py
```

These overwrite the Part 2 reliability data and Part 3 comparison data in
`reports/hw07/raw/`. Model timing can differ between runs.

## 5. Recreate Part 4 and Part 5 evidence

The scripts download public Capital Bikeshare archives and current policy
pages. Network content and access timestamps can change.

```bash
python code/bike_share/prepare_scenarios.py --scenario membership_wins
python code/bike_share/prepare_scenarios.py --scenario pay_per_use_wins
python code/bike_share/capture_pricing_snapshots.py
python code/bike_share/test_prompt_injection.py
```

With the API still running, open `http://127.0.0.1:8583/bike-share`, upload
one scenario CSV at a time from `reports/hw07/raw/bike_share/`, keep the
Capital Bikeshare pricing URL, and run the recommendation.

## 6. Run the Part 6 file-tool and safety-gate test

```bash
python code/file_tools.py
```

The demonstration creates test files only in a temporary directory. It writes
the ten command decisions to `reports/hw07/raw/part6_safety_gate_results.json`.

## 7. Run the HW7 smoke test

Keep the API and Ollama running, then run:

```bash
python code/verify_hw07.py
```

The verifier checks the backend root, valid and invalid JWT login, a two-tool
agent task, the pure-Python file-tool/safety-gate test, and required raw
artifacts. It writes `reports/hw07/verification.json`. It does not modify
application code; the agent smoke test can append a new raw agent-run record.

## 8. Final repository state

Review the generated files, commit them, and tag the submission commit:

```bash
git add code/verify_hw07.py reports/hw07
git commit -m "Add HW7 verification and reproducibility instructions"
git tag -a hw7 -m "HW7 submission"
git push origin main --tags
```

`RUN_LOG.txt` contains timestamped console evidence, `raw/` contains the
machine-readable outputs, and `METRICS.md` contains the report tables.
