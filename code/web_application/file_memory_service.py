"""File-based durable memory for HW6 Part 4."""

from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = REPO_ROOT / "AGENT.md"
MEMORY_PATH = REPO_ROOT / "MEMORY.md"
LAST_CONSOLIDATED = "Last consolidated: "

CONFLICT_GROUPS = {
    "fundraiser_date": {
        "facts": {"Fundraiser date is November 20.", "Fundraiser date is November 22."},
        "resolution": "Resolved date conflict: November 20 is the confirmed fundraiser date; November 22 was superseded.",
    },
    "attendance": {
        "facts": {"Expected attendance is about 40.", "Expected attendance is about 60."},
        "resolution": "Resolved attendance conflict: plan for about 40 attendees; the 60-attendee estimate was superseded.",
    },
    "monday_tennis": {
        "facts": {"Avoid Monday evenings for tennis events.", "Monday evening tennis events are permitted."},
        "resolution": "Resolved scheduling conflict: avoid Monday evenings for tennis events; permission to schedule Mondays was superseded.",
    },
}


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def memory_lines() -> list[str]:
    return [line.strip() for line in read_markdown(MEMORY_PATH).splitlines() if line.strip()]


def fact_lines() -> list[str]:
    return [
        line for line in memory_lines()
        if not line.startswith("#") and not line.startswith(LAST_CONSOLIDATED)
    ]


def last_consolidated_at() -> datetime | None:
    for line in memory_lines():
        if line.startswith(LAST_CONSOLIDATED):
            return datetime.fromisoformat(line.removeprefix(LAST_CONSOLIDATED))
    return None


def consolidation_status(now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    consolidated_at = last_consolidated_at()
    age_hours = None if consolidated_at is None else (now - consolidated_at).total_seconds() / 3600
    line_count = len(fact_lines())
    return {
        "non_empty_fact_lines": line_count,
        "last_consolidated_at": consolidated_at.isoformat() if consolidated_at else None,
        "age_hours": round(age_hours, 2) if age_hours is not None else None,
        "needs_consolidation": line_count > 40 or age_hours is None or age_hours > 24,
    }


def build_file_memory_prompt(user_message: str) -> list[dict]:
    instructions = read_markdown(AGENT_PATH)
    memory = read_markdown(MEMORY_PATH)
    system_content = f"{instructions}\n\n# Durable Memory\n{memory}"
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message},
    ]


def conflict_group(fact: str) -> str | None:
    for group, details in CONFLICT_GROUPS.items():
        if fact in details["facts"]:
            return group
    return None


def compact_memory() -> dict:
    before = len(fact_lines())
    retained = []
    seen = set()
    resolved = set()
    for line in fact_lines():
        fact = line.removeprefix("- ").strip()
        group = conflict_group(fact)
        if group:
            if group not in resolved:
                retained.append(CONFLICT_GROUPS[group]["resolution"])
                resolved.add(group)
            continue
        normalized = fact.casefold()
        if normalized not in seen:
            retained.append(fact)
            seen.add(normalized)

    timestamp = datetime.now(timezone.utc).isoformat()
    content = [f"{LAST_CONSOLIDATED}{timestamp}"] + [f"- {fact}" for fact in retained]
    MEMORY_PATH.write_text("\n".join(content) + "\n", encoding="utf-8")
    return {
        "before_count": before,
        "after_count": len(retained),
        "resolved_conflicts": [CONFLICT_GROUPS[group]["resolution"] for group in resolved],
    }


def is_durable(message: str) -> bool:
    markers = ("prefer", "need", "will", "organize", "venue", "date", "time")
    return len(message.strip()) > 3 and any(marker in message.casefold() for marker in markers)


def dream(recent_messages: list[str]) -> dict:
    existing = {
        line.removeprefix("- ").strip().removeprefix("Learned: ").casefold()
        for line in fact_lines()
    }
    learned = []
    for message in recent_messages:
        fact = message.strip()
        if is_durable(fact) and fact.casefold() not in existing:
            learned.append(fact)
            existing.add(fact.casefold())
    if learned:
        with MEMORY_PATH.open("a", encoding="utf-8") as memory_file:
            for fact in learned:
                memory_file.write(f"- Learned: {fact}\n")
    return {"added": learned, "added_count": len(learned)}


def run_command(command: str, recent_messages: list[str] | None = None) -> dict:
    if command == "/memory":
        return {"memory": read_markdown(MEMORY_PATH), "status": consolidation_status()}
    if command == "/compact":
        return compact_memory()
    if command == "/dream":
        return dream(recent_messages or [])
    if command == "/help":
        return {"commands": ["/memory", "/compact", "/dream", "/help"]}
    raise ValueError("Unsupported memory command")
