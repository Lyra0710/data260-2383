"""Create reproducible HW6 Part 4 file-memory evidence."""

import json
import shutil
from pathlib import Path

from file_memory_service import (
    AGENT_PATH,
    MEMORY_PATH,
    build_file_memory_prompt,
    consolidation_status,
    run_command,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "reports" / "hw06" / "raw" / "MEMORY_before_compaction.md"
OUTPUT_PATH = REPO_ROOT / "reports" / "hw06" / "raw" / "file_memory_demo.json"


def main() -> None:
    shutil.copyfile(SOURCE_PATH, MEMORY_PATH)
    before = consolidation_status()
    compact = run_command("/compact")
    dream = run_command(
        "/dream",
        ["I prefer email reminders one week before each event."],
    )
    prompt = build_file_memory_prompt("What should I remember about the fundraiser?")
    results = {
        "memory_command": run_command("/memory"),
        "help_command": run_command("/help"),
        "before_compaction": before,
        "compact_command": compact,
        "dream_command": dream,
        "after_demo": consolidation_status(),
        "agent_in_system_prompt": AGENT_PATH.read_text(encoding="utf-8") in prompt[0]["content"],
        "memory_in_system_prompt": MEMORY_PATH.read_text(encoding="utf-8") in prompt[0]["content"],
    }
    OUTPUT_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
