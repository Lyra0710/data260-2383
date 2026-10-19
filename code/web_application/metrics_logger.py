import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METRICS_PATH = REPO_ROOT / "reports" / "hw06" / "raw" / "chat_metrics.jsonl"


def append_chat_metric(record: dict) -> None:
    path = Path(os.getenv("HW6_METRICS_PATH", DEFAULT_METRICS_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as metrics_file:
        metrics_file.write(json.dumps(record, default=str) + "\n")
