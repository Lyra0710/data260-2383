# DATA-260 Homework 1

This repository contains my Homework 1 work for DATA-260. My assigned domain is community sports league fixtures.

## Project contents

- `code/web_application/` contains the HTML and JavaScript fixture form.
- `code/Dockerfile` packages the web application with Nginx.
- `code/agents_demo.py` runs the Planner → Reviewer → Finalizer agent flow.
- `code/run_nondeterminism.py` runs the 40-run temperature experiment.
- `src/model_client.py` contains the reusable local-model adapter.
- `code/hw1_client.py` is the five-turn model-client and token-accounting demo.
- `reports/hw01/` contains the run log, raw experiment data, metrics, fixed input, and AI-use notes.

## Python and local model requirements

This homework uses Python 3.11 or 3.12 and the packages listed in `requirements.txt`.

```bash
python -m pip install -r requirements.txt
```

The recorded agent run used the local Ollama model `qwen3:8b`. Ollama must be running and that model must be available before running the agent or client scripts. The current agent code uses `http://localhost:11434` as its default Ollama URL.

If the model is not already available locally:

```bash
ollama pull qwen3:8b
```

## Recorded web application commands

The following Docker commands were recorded in `reports/hw01/RUN_LOG.txt`:

```bash
docker build -t data260-hw1 -f code/Dockerfile code
docker run -d --name data260-hw1-container -p 8583:80 data260-hw1
```

After starting the container, the application was available at:

```text
http://localhost:8583
```

## Recorded agent command

The following command was used for the recorded Planner → Reviewer → Finalizer run:

```bash
python code/agents_demo.py \
  --title "Community Soccer Semifinal" \
  --content "The Falcons and Tigers will compete at Spartan Stadium on September 12. Both teams must arrive 30 minutes early for player check-in." \
  --model qwen3:8b \
  --strict
```

## Non-determinism experiment

The fixed experiment input is stored in `reports/hw01/cases/nondeterminism_input.json`. The current script uses `qwen3:8b`, runs 20 times at temperature `0.7` and 20 times at temperature `0.0`, and saves results under `reports/hw01/raw/`.

To run or resume the experiment:

```bash
python code/run_nondeterminism.py
```

The script preserves existing rows in `nondeterminism_runs.json` and only runs the missing rows for each temperature. The current raw files already contain 20 runs at each temperature, so running the command now will report the experiment as complete without creating replacement runs.

## Model client and token accounting

The recorded five-turn client session used:

```bash
python code/hw1_client.py
```

For each code-review request, enter `END` on its own line to submit the request. Use `/stats` during the session to print the turn count, cumulative token counts, and serialized conversation-history length. Use `/exit` to end the session and print final cumulative statistics.

The Part 4 client loads the bullet-only review instructions from `AGENT.md` and sends model requests through `src/model_client.py`.

### Why prior conversation context is resent with every turn

Prior conversation context is resent because the model does not remember earlier messages on its own. Sending the history again gives it the context needed to respond consistently to the current request.

### System prompt versus user message

A system prompt gives the model its overall role and rules, such as responding with bullet-only code reviews. A user message is the specific request or question the user wants answered.

### Why input tokens grow over a conversation

Input tokens grow because each new request includes the previous conversation history in addition to the new user message. As the conversation gets longer, there is more text for the model to read each time.

### What limits that growth

The model's context window limits growth because it is the maximum number of tokens the model can process at once. Once that limit is reached, older messages need to be removed or summarized.

## Verification status

Run the repository self-check with:

```bash
python code/verify_hw01.py
```

The script writes its results to `reports/hw01/verification.json` and exits with a nonzero status if a check fails. The current verification output was generated with Python 3.11.9 and reports that all checks passed.
