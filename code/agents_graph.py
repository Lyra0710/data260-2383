from typing import Any
from typing_extensions import TypedDict

import json

from src.model_client import complete
from agents_demo import parse_and_coerce


class AgentState(TypedDict, total=False): # shape of the shared state of the graph. 
    title: str
    content: str
    email: str
    strict: bool

    planner_output: dict[str, Any]
    reviewer_output: dict[str, Any]
    final_output: dict[str, Any]

    transcript: list[dict[str, str]] # conversation between the agents. 
    approved: bool
    iteration: int # counts revision attempts. 


def planner_node(state: AgentState) -> dict:
    title = state["title"]
    content = state["content"]
    email = state.get("email", "")
    strict = state.get("strict", False)

    messages = [
        {
            "role": "system",
            "content": (
                "Propose exactly 3 distinct, topical tags and "
                "a one-sentence summary for the supplied content."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Title: {title}\n\n"
                f"Content: {content}\n\n"
                f"Email: {email}\n\n"
                "Return only one JSON object with keys: "
                "thought, message, and data."
            ),
        },
    ]

    response = complete(messages)

    planner_result = parse_and_coerce(
        response.content,
        title,
        content,
        strict,
    )

    transcript = list(state.get("transcript", []))
    transcript.append(
        {
            "role": "Planner",
            "content": json.dumps(planner_result),
        }
    )

    return {
        "planner_output": planner_result,
        "transcript": transcript,
        "iteration": state.get("iteration", 0) + 1,
    }

def reviewer_node(state: AgentState) -> dict:
    title = state["title"]
    content = state["content"]
    strict = state.get("strict", False)
    planner_result = state["planner_output"]

    messages = [
        {
            "role": "system",
            "content": (
                "Review the planner's proposed tags and summary. "
                "Check that there are exactly 3 topical tags and that "
                "the summary is no more than 25 words. "
                "List any problems in data.issues."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Title: {title}\n\n"
                f"Content: {content}\n\n"
                f"Planner proposal:\n{json.dumps(planner_result)}\n\n"
                "Return only one JSON object with keys: "
                "thought, message, and data."
            ),
        },
    ]

    response = complete(messages)

    reviewer_result = parse_and_coerce(
        response.content,
        title,
        content,
        strict,
    )

    issues = reviewer_result["data"].get("issues", [])
    approved = len(issues) == 0

    transcript = list(state.get("transcript", []))
    transcript.append(
        {
            "role": "Reviewer",
            "content": json.dumps(reviewer_result),
        }
    )

    return {
        "reviewer_output": reviewer_result,
        "approved": approved,
        "transcript": transcript,
    }

def finalizer_node(state: AgentState) -> dict:
    title = state["title"]
    content = state["content"]
    strict = state.get("strict", False)
    reviewer_result = state["reviewer_output"]

    messages = [
        {
            "role": "system",
            "content": (
                "Finalize the reviewed proposal. "
                "Return exactly 3 topical tags and a summary of no more "
                "than 25 words. Set data.issues to an empty array."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Title: {title}\n\n"
                f"Content: {content}\n\n"
                f"Reviewed proposal:\n{json.dumps(reviewer_result)}\n\n"
                "Return only one JSON object with keys: "
                "thought, message, and data."
            ),
        },
    ]

    response = complete(messages)

    final_result = parse_and_coerce(
        response.content,
        title,
        content,
        strict,
    )

    transcript = list(state.get("transcript", []))
    transcript.append(
        {
            "role": "Finalizer",
            "content": json.dumps(final_result),
        }
    )

    return {
        "final_output": final_result,
        "transcript": transcript,
    }

def review_router(state: AgentState) -> str:
    if state.get("approved", False):
        return "finalizer"

    return "planner"