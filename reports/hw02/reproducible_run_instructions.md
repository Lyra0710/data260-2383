# Homework 2 Reproducibility Instructions

Run all commands from the repository root.

## Start Ollama

In a separate terminal, start the Ollama server:

```bash
ollama serve

ollama pull qwen3:8b
```
## Run the LangGraph application test
PYTHONPATH=.:code python code/agents_demo.py \
  --title "Community Soccer" \
  --content "A local soccer league is organizing a semifinal match between two community teams." \
  --email "student@example.com" \
  --strict \
  --turn-limit 10

## Run the 30-run schema-validation experiment
PYTHONPATH=.:code python -u code/verify_hw02.py \
  --runs 30 \
  --turn-limit 10 \
  --output reports/hw02/raw/schema_validation.json

## Run the turn-ceiling experiments
### Turn limit of 2:
PYTHONPATH=.:code python -u code/verify_hw02.py \
  --runs 20 \
  --turn-limit 2 \
  --output reports/hw02/raw/ceiling_2.json

### Turn limit of 10:
PYTHONPATH=.:code python -u code/verify_hw02.py \
  --runs 20 \
  --turn-limit 10 \
  --output reports/hw02/raw/ceiling_10.json

### Run the adversarial-input experiment
PYTHONPATH=.:code python -u code/verify_hw02.py \
  --input reports/hw02/cases/adversarial_input.json \
  --runs 5 \
  --turn-limit 2 \
  --output reports/hw02/raw/adversarial.json

## Calculate summary statistics
```bash
python - <<'PY'
import json
from collections import Counter
from statistics import mean, median

for filename in [
    "reports/hw02/raw/schema_validation.json",
    "reports/hw02/raw/ceiling_2.json",
    "reports/hw02/raw/ceiling_10.json",
    "reports/hw02/raw/adversarial.json",
]:
    with open(filename) as file:
        results = json.load(file)

    counts = Counter(result["classification"] for result in results)
    latencies = [result["latency_ms"] for result in results]

    print(f"\n{filename}")
    print("Classifications:", dict(counts))
    print(f"Mean latency: {mean(latencies):.2f} ms")
    print(f"Median latency: {median(latencies):.2f} ms")
    print(f"Completed: {sum(not r['issues'] for r in results)}/{len(results)}")
PY
```

## Run the Homework 2 self-check

```bash
PYTHONPATH=.:code python code/hw02_self_verify.py
```

The self-check writes its results to `reports/hw02/verification.json` and exits with a nonzero status if a check fails.
