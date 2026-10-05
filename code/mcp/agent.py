import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


sys.path.insert(0, str(Path(__file__).parent))

import domain_server


load_dotenv()

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
MAX_STEPS = 3
LOG_FILE = Path("agent_runs.jsonl")


TOOLS = """
Available tools:

1. search_fixtures
   Input: {"query": "text", "limit": 5}

2. fixture_details
   Input: {"fixture_id": 1}

3. venue_fixture_summary
   Input: {"venue_id": 1}
"""


def parse_json(text):
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


async def ask_model(messages):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json=payload,
        )

    response.raise_for_status()
    return response.json()["message"]["content"]


async def run_agent(
    user_input,
    max_steps=MAX_STEPS,
    model_call=ask_model,
):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a fixture assistant. "
                "Choose one available tool when needed. "
                "Respond with JSON only. "
                'Use {"action":"tool","tool":"...","inputs":{}} '
                'or {"action":"final","answer":"..."}.\n'
                + TOOLS
            ),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    steps = []
    final_answer = None
    stop_reason = "max_steps"

    for step_number in range(1, max_steps + 1):
        model_output = await model_call(messages)

        step_record = {
            "step": step_number,
            "model_output": model_output,
        }

        try:
            decision = parse_json(model_output)
        except json.JSONDecodeError:
            stop_reason = "invalid_model_output"
            step_record["error"] = "Model did not return valid JSON."
            steps.append(step_record)
            break

        if decision.get("action") == "final":
            final_answer = decision.get("answer", "")
            stop_reason = "normal_completion"
            step_record["stop_reason"] = stop_reason
            steps.append(step_record)
            break

        if decision.get("action") != "tool":
            stop_reason = "invalid_action"
            step_record["error"] = "Unknown model action."
            steps.append(step_record)
            break

        tool_name = decision.get("tool")
        inputs = decision.get("inputs", {})

        tool_result = await domain_server.execute_tool(
            tool_name,
            inputs,
        )

        step_record["tool"] = tool_name
        step_record["inputs"] = inputs
        step_record["result"] = json.loads(tool_result)
        steps.append(step_record)

        messages.append(
            {
                "role": "assistant",
                "content": model_output,
            }
        )
        messages.append(
            {
                "role": "tool",
                "content": tool_result,
            }
        )

    run_record = {
        "user_input": user_input,
        "steps": steps,
        "final_answer": final_answer,
        "stop_reason": stop_reason,
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(run_record) + "\n")

    return run_record


async def main():
    user_input = " ".join(sys.argv[1:])

    if not user_input:
        print("Provide a user request.")
        return

    result = await run_agent(user_input)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())