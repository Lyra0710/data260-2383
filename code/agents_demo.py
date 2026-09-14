from typing import Annotated
from pydantic import BaseModel, Field, field_validator

import argparse, json, os, re, sys, time
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError, field_validator

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from collections import Counter

from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from src.model_client import complete

from typing import List, Dict, Any, Iterable, Tuple, TypedDict
class AgentState(TypedDict, total=False):
    title: str
    content: str
    email: str
    strict: bool
    task: str
    llm: Any

    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]

    turn_count: int
    turn_limit: int

def planner_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Planner ---")

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
                f"Title: {state['title']}\n\n"
                f"Content: {state['content']}\n\n"
                f"Task: {state['task']}\n\n"
                "Return only one JSON object with keys: "
                "thought, message, and data."
            ),
        },
    ]

    response = complete(
    messages,
    model=state.get("llm", "qwen3:8b"),
)

    proposal = parse_and_coerce(
        response.content,
        state["title"],
        state["content"],
        state.get("strict", False),
    )
    # Temporarily allow incorrect tag counts
    # This lets the Reviewer catch it in the next turn
    # proposal["data"]["tags"] = proposal["data"]["tags"][:2]

    return {
        "planner_proposal": proposal
    }

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Reviewer ---")
    planner_proposal = state["planner_proposal"]

    planner_issues = planner_proposal.get(
        "data",
        {}
    ).get(
        "issues",
        []
    )

    if planner_issues:
        return {
            "reviewer_feedback": planner_proposal
        }

    messages = [
        {
            "role": "system",
            "content": (
                "Review the planner's proposal. Check whether it contains "
                "exactly 3 topical tags and a summary of no more than 25 words. "
                "List any problems in data.issues."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Title: {state['title']}\n\n"
                f"Content: {state['content']}\n\n"
                f"Planner proposal:\n"
                f"{json.dumps(planner_proposal)}\n\n"
                "Return only one JSON object with keys: "
                "thought, message, and data."
            ),
        },
    ]

    response = complete(
    messages,
    model=state.get("llm", "qwen3:8b"),
)

    feedback = parse_and_coerce(
        response.content,
        state["title"],
        state["content"],
        state.get("strict", False),
    )
    # Temporary error for testing purposes
    # feedback["data"]["issues"] = ["Temporary correction-loop test"] 

    # To prevent the model from overriding deterministic Pydantic validation
    try:
        AgentOutput.model_validate(planner_proposal)
        feedback["data"]["issues"] = []
    except ValidationError as error:
        feedback["data"]["issues"] = [
            str(error)
        ]
    return {
        "reviewer_feedback": feedback
    }

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Supervisor ---")

    current_turn = state.get("turn_count", 0)

    return {
        "turn_count": current_turn + 1
    }
def router_logic(state: AgentState) -> str:
    reviewer_feedback = state.get("reviewer_feedback", {})
    data = reviewer_feedback.get("data", {})
    issues = data.get("issues", [])

    if not issues:
        return END

    if state["turn_count"] >= state["turn_limit"]:
        return END

    return "planner"

def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("supervisor", supervisor_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "reviewer")
    builder.add_edge("reviewer", "supervisor")

    builder.add_conditional_edges(
        "supervisor",
        router_logic,
        {
            "planner": "planner",
            END: END,
        },
    )

    return builder.compile()

# ==========================

Tag = Annotated[
    str,
    Field(min_length=3, max_length=30),
]


class OutputData(BaseModel):
    tags: list[Tag] = Field(min_length=3, max_length=3)
    summary: str
    issues: list[str] = Field(default_factory=list)

    @field_validator("summary")
    @classmethod
    def summary_must_have_at_most_25_words(cls, value: str) -> str:
        if len(value.split()) > 25:
            raise ValueError("Summary must contain at most 25 words.")

        return value


class AgentOutput(BaseModel):
    thought: str
    message: str
    data: OutputData


def validate_agent_output(output: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validated_output = AgentOutput.model_validate(output)

        return validated_output.model_dump()

    except ValidationError as error:
        output_copy = dict(output)
        data = dict(output_copy.get("data", {}))

        data["issues"] = [
            str(error)
        ]

        output_copy["data"] = data

        return output_copy

# Optional: students can expand/modify this
STOP = {
    "the", "and", "for", "that", "with", "this", "from", "into", "than", "your", "you",
    "are", "was", "were", "have", "has", "had", "use", "used", "using", "about", "how",
    "can", "will", "more", "less", "very", "over", "under", "their", "there", "then",
    "our", "out", "on", "in", "of", "to", "by", "a", "an", "is", "it", "as",
}


# -------------------------
# Text cleanup + extraction
# -------------------------

def strip_code_and_md(s: str) -> str:
    """
    TODO: Remove markdown/code artifacts from model output.
    Suggested:
      - remove fenced code blocks
      - remove inline backticks
      - normalize whitespace
    """
    text = str(s).strip()
    text = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("```", "")
    text = text.replace("`", "")
    
    return " ".join(text.split())


def extract_json_block(text: str) -> str:
    """
    TODO: Extract the first JSON object from a text response.
    If none is present, wrap text like: {"message": "<cleaned text>"}.
    """
    cleaned_text = strip_code_and_md(text)
    decoder = json.JSONDecoder()

    for index, character in enumerate(cleaned_text):
        if character != "{":
            continue

        try:
            parsed_object, _ = decoder.raw_decode(cleaned_text[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(parsed_object, dict):
            return json.dumps(parsed_object)

    return json.dumps({"message": cleaned_text})


def tokens(txt: str) -> List[str]:
    """
    TODO: Tokenize into lowercase words (optionally keep hyphens), filter junk, etc.
    """
    return re.findall(r"[a-z][a-z\-]+", str(txt).lower())


def ngrams(words: List[str], n: int) -> Iterable[Tuple[str, ...]]:
    """
    TODO: Yield word n-grams from a token list.
    """
    for i in range(max(0, len(words) - n + 1)):
        yield tuple(words[i:i + n])


def phrase_candidates(title: str, content: str, maxn: int = 12) -> List[str]:
    """
    TODO: Build tag candidates derived ONLY from title+content.
    Suggested approach:
      - tokenize + remove STOP words
      - gather bigrams/trigrams
      - rank by frequency
      - fall back to unigrams
      - return up to maxn
    """
    title_words = [
        word for word in tokens(title)
        if word not in STOP
    ]

    content_words = [
        word for word in tokens(content)
        if word not in STOP
    ]

    candidates = []
    seen = set()

    # Prioritize multi-word phrases
    for n in (3, 2):
        phrase_counts = Counter(
            list(ngrams(title_words, n)) +
            list(ngrams(content_words, n))
        )

        for phrase, _ in phrase_counts.most_common():
            candidate = " ".join(phrase)

            if candidate not in seen:
                candidates.append(candidate)
                seen.add(candidate)

            if len(candidates) >= maxn:
                return candidates

    # Use individual words if there are not enough phrases
    word_counts = Counter(title_words + content_words)

    for word, _ in word_counts.most_common():
        if word not in seen:
            candidates.append(word)
            seen.add(word)

        if len(candidates) >= maxn:
            break

    return candidates


# -------------------------
# Output schema coercion
# -------------------------

def coerce_reply(raw_obj: Any, title: str, content: str, strict: bool) -> Dict[str, Any]:
    """
    TODO: Coerce arbitrary model output into the required schema:
      {
        "thought": str,
        "message": str (non-empty, <= 60 words),
        "data": {
          "tags": [str, str, str],        # exactly 3 topical tags
          "summary": str,                # <= 25 words, ends with '.'
          "issues": [str, ...]
        }
      }

    strict=True suggestion:
      - enforce at least two multi-word tags
    """
    # Placeholder minimal schema
    if not isinstance(raw_obj, dict):
        raw_obj = {}

    data = raw_obj.get("data", {})

    if not isinstance(data, dict):
        data = {}

    # Accept tags from either data.tags or top-level tags
    raw_tags = data.get("tags", raw_obj.get("tags", []))

    if isinstance(raw_tags, str):
        raw_tags = raw_tags.split(",")

    if not isinstance(raw_tags, list):
        raw_tags = []

    tags = []
    seen_tags = set()

    for tag in raw_tags:
        cleaned_tag = strip_code_and_md(tag).strip(" \"'").lower()

        if cleaned_tag and cleaned_tag not in seen_tags:
            tags.append(cleaned_tag)
            seen_tags.add(cleaned_tag)

    # Generate fallback tags only from the supplied input
    candidates = phrase_candidates(title, content)

    for candidate in candidates:
        candidate = candidate.lower()

        if len(tags) >= 3:
            break

        if candidate not in seen_tags:
            tags.append(candidate)
            seen_tags.add(candidate)

    # Keep exactly three tags
    tags = tags[:3]

    if len(tags) < 3:
        raise ValueError(
            "The title and content did not provide enough information "
            "to generate exactly three distinct tags."
        )

    # In strict mode, prefer at least two multi-word tags
    if strict:
        multiword_count = sum(
            1 for tag in tags if len(tag.split()) >= 2
        )

        for candidate in candidates:
            if multiword_count >= 2:
                break

            if len(candidate.split()) < 2:
                continue

            candidate = candidate.lower()

            if candidate in tags:
                continue

            # Replace a single-word tag
            for index in range(len(tags) - 1, -1, -1):
                if len(tags[index].split()) == 1:
                    tags[index] = candidate
                    multiword_count += 1
                    break

    # Accept summary from either data.summary or top-level summary
    summary = data.get(
        "summary",
        raw_obj.get("summary", "")
    )

    summary = strip_code_and_md(summary)

    # Use the supplied input if the model omitted the summary
    if not summary:
        summary = strip_code_and_md(content or title)

    # Limit summary to 25 words
    summary_words = summary.split()
    summary = " ".join(summary_words[:25])

    # Require the summary to end with a period
    summary = summary.rstrip(" .,!?:;") + "."

    # Normalize other schema fields
    thought = strip_code_and_md(raw_obj.get("thought", ""))

    message = strip_code_and_md(
        raw_obj.get(
            "message",
            "Proposal reviewed; tags and summary prepared."
        )
    )

    if not message:
        message = "Proposal reviewed; tags and summary prepared."

    message = " ".join(message.split()[:60])

    issues = data.get("issues", [])

    if not isinstance(issues, list):
        issues = [str(issues)]

    issues = [
        strip_code_and_md(issue)
        for issue in issues
        if strip_code_and_md(issue)
    ]

    return {
            "thought": thought,
            "message": message,
            "data": {
            "tags": tags,
            "summary": summary,
            "issues": issues
            }
}


def parse_and_coerce(text: str, title: str, content: str, strict: bool) -> Dict[str, Any]:
    """
    TODO:
      - extract_json_block()
      - json.loads()
      - coerce_reply()
      - handle JSON parse failures gracefully
    """
    try:
        obj = json.loads(extract_json_block(text))
    except Exception:
        obj = {"message": strip_code_and_md(text)}
    return coerce_reply(obj, title, content, strict)


# -------------------------
# Agent wrapper
# -------------------------

@dataclass
class SimpleAgent:
    name: str
    system: str
    model: Any  # LangChain ChatModel

    def respond(
        self,
        conversation: List[Dict[str, str]],
        task: str,
        title: str,
        content: str,
        strict: bool,
    ) -> Dict[str, Any]:
        """
        TODO:
          - Build a ChatPromptTemplate with system + human instructions
          - Inject task + conversation history
          - Run chain: prompt | model | StrOutputParser()
          - parse_and_coerce() the output into the required schema
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system),
            ("human",
                "Title:\n{title}\n\n"
                "Content:\n{content}\n\n"
                "Task:\n{task}\n\n"
                "Conversation so far:\n{history}\n\n"
                "Return ONLY one JSON object (no code fences, no markdown, no explanations). "
                "Keys: thought (string), message (non-empty, <=60 words, no code), "
                "data.tags (array of exactly 3 topical tags), "
                "data.summary (<=25 words, no ellipses), "
                "data.issues (array). "
                "Do not add extra text outside JSON."
            ),
        ])

        history_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in conversation]) or "(empty)"
        chain = prompt | self.model | StrOutputParser()

        raw = chain.invoke({
            "title": title,
            "content": content,
            "task": task,
            "history": history_text
        })
        return parse_and_coerce(raw, title, content, strict)


# -------------------------
# CLI entrypoint
# -------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--title",
        default="Your Blog Title Here",
    )

    parser.add_argument(
        "--content",
        default="Your blog post content goes here.",
    )

    parser.add_argument(
        "--email",
        default="student@example.com",
    )

    parser.add_argument(
        "--model",
        default=os.environ.get("SMOL_MODEL", "qwen3:8b"),
    )

    parser.add_argument(
        "--turn-limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--strict",
        action="store_true",
    )

    args = parser.parse_args()

    task = (
        f'Given title "{args.title}" and content "{args.content}", '
        "produce exactly 3 topical tags and a one-sentence summary."
    )

    graph = build_graph()

    initial_state: AgentState = {
        "title": args.title,
        "content": args.content,
        "email": args.email,
        "strict": args.strict,
        "task": task,
        "llm": args.model,
        "turn_count": 0,
        "turn_limit": args.turn_limit,
    }

    final_state = dict(initial_state)

    for update in graph.stream(
        initial_state,
        config={"recursion_limit": args.turn_limit * 3 + 5},
    ):
        for node_name, node_update in update.items():
            print(f"\n--- {node_name} ---")
            print(json.dumps(node_update, indent=2, default=str))
            final_state.update(node_update)

    print("\n--- Final state ---")
    print(json.dumps(final_state, indent=2, default=str))

if __name__ == "__main__":
    main()