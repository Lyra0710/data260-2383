"""Interactive command-line client for Homework 1."""

import json
import sys
from pathlib import Path


# Locate the repository root without hardcoding an absolute path.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.model_client import complete, get_token_usage


def load_agent_instructions() -> str:
    """Load the system instructions from AGENT.md."""

    agent_path = REPO_ROOT / "AGENT.md"
    return agent_path.read_text(encoding="utf-8")


def serialized_history_length(history: list[dict[str, str]]) -> int:
    """Return the character length of the serialized history."""

    serialized_history = json.dumps(history)
    return len(serialized_history)


def print_stats(
    history: list[dict[str, str]],
    turn_count: int,
    cumulative_input_tokens: int,
    cumulative_output_tokens: int,
) -> None:
    """Display statistics without changing the conversation history."""

    print("\n--- Conversation Statistics ---")
    print(f"Turn count: {turn_count}")
    print(f"Cumulative input tokens: {cumulative_input_tokens}")
    print(f"Cumulative output tokens: {cumulative_output_tokens}")
    print(
        "Serialized conversation-history length: "
        f"{serialized_history_length(history)} characters"
    )
    print()


def main() -> None:
    system_prompt = load_agent_instructions()

    history = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    turn_count = 0
    cumulative_input_tokens = 0
    cumulative_output_tokens = 0

    print("Homework 1 Model Client")
    print("Enter code-review requests.")
    print("For multi-line input (e.g. pasting code), type END on its own line to submit.")
    print("Commands: /stats and /exit")

    try:
        while True:
            first_line = input("\nYou: ")

            if first_line.strip() in ("/stats", "/exit"):
                user_input = first_line.strip()
            else:
                lines = [first_line]
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                user_input = "\n".join(lines).strip()

            if not user_input:
                continue

            if user_input == "/stats":
                print_stats(
                    history,
                    turn_count,
                    cumulative_input_tokens,
                    cumulative_output_tokens,
                )
                continue

            if user_input == "/exit":
                break

            history.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

            response = complete(history)
            assistant_text = str(response.content)

            history.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                }
            )

            usage = get_token_usage(response)

            turn_count += 1
            cumulative_input_tokens += usage["input_tokens"]
            cumulative_output_tokens += usage["output_tokens"]

            print(f"\nAssistant:\n{assistant_text}")
            print("\n--- Token Usage ---")
            print(f"Input tokens: {usage['input_tokens']}")
            print(f"Output tokens: {usage['output_tokens']}")
            print(f"Total tokens: {usage['total_tokens']}")

    except (KeyboardInterrupt, EOFError):
        print()

    finally:
        print("\n--- Final Cumulative Statistics ---")
        print(f"Turn count: {turn_count}")
        print(f"Cumulative input tokens: {cumulative_input_tokens}")
        print(f"Cumulative output tokens: {cumulative_output_tokens}")


if __name__ == "__main__":
    main()