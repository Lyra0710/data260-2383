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

## Local model requirement

The recorded agent run used the local Ollama model `qwen3:8b`. Ollama must be running and that model must be available before running the agent or client scripts.

## Recorded web application commands

The following Docker commands were recorded in `reports/hw01/RUN_LOG.TXT`:

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

The fixed experiment input is stored in `reports/hw01/cases/nondeterminism_input.json`. The experiment script runs 20 times at temperature `0.7` and 20 times at temperature `0.0`, using `qwen3:8b`, and saves the results under `reports/hw01/raw/`.

To repeat the experiment:

```bash
python code/run_nondeterminism.py
```

## Model client and token accounting

The recorded five-turn client session used:

```bash
python code/hw1_client.py
```

Use `/stats` during the session to print the turn count, cumulative token counts, and serialized conversation-history length. Use `/exit` to end the session and print final cumulative statistics.

### Why prior conversation context is resent with every turn

Prior conversation context is resent because the model does not remember earlier messages on its own. Sending the history again gives it the context needed to respond consistently to the current request.

### System prompt versus user message

A system prompt gives the model its overall role and rules, such as responding with bullet-only code reviews. A user message is the specific request or question the user wants answered.

### Why input tokens grow over a conversation

Input tokens grow because each new request includes the previous conversation history in addition to the new user message. As the conversation gets longer, there is more text for the model to read each time.

### What limits that growth

The model's context window limits growth because it is the maximum number of tokens the model can process at once. Once that limit is reached, older messages need to be removed or summarized.

## Verification status

`reports/hw01/verification.json` exists but is currently empty. A reproducible self-check command and its JSON output still need to be added before final submission.
