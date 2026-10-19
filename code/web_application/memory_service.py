import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from ollama import Client

from memory_repository import (
    count_user_messages,
    episode_exists,
    fetch_recent_session_messages,
    fetch_session_summaries,
    fetch_user_episodes,
    latest_summary,
    save_episode,
    save_message,
    save_summary,
)
from metrics_logger import append_chat_metric

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.model_client import complete, count_text_tokens, get_token_usage


SHORT_TERM_N = int(os.getenv("SHORT_TERM_N", "8"))
SUMMARIZE_EVERY_USER_MSGS = int(os.getenv("SUMMARIZE_EVERY_USER_MSGS", "3"))
TOP_K_EPISODES = int(os.getenv("TOP_K_EPISODES", "5"))
CHAT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

SYSTEM_PRIMER = (
    "You are a helpful assistant for a community sports league. "
    "Use the supplied memories only when they are relevant. "
    "Do not invent, change, or infer facts such as dates, times, venues, or "
    "preferences. If facts conflict, state the conflict rather than resolving it. "
    "Answer clearly and concisely."
)


def model_text(messages: list[dict], temperature: float = 0.0) -> str:
    response = complete(messages, model=CHAT_MODEL, temperature=temperature)
    return str(response.content).strip()


def prompt_component_tokens(
    short_term_messages: list[dict],
    long_term_summary: str,
    episodic_facts: list[dict],
) -> dict[str, int]:
    short_term_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in short_term_messages
    )
    episodic_text = "\n".join(f"- {fact['fact']}" for fact in episodic_facts)

    return {
        "system_primer_tokens": count_text_tokens(SYSTEM_PRIMER, model=CHAT_MODEL),
        "long_term_summary_tokens": count_text_tokens(
            long_term_summary,
            model=CHAT_MODEL,
        ) if long_term_summary else 0,
        "short_term_window_tokens": count_text_tokens(
            short_term_text,
            model=CHAT_MODEL,
        ) if short_term_text else 0,
        "episodic_facts_tokens": count_text_tokens(
            episodic_text,
            model=CHAT_MODEL,
        ) if episodic_text else 0,
    }


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = Client(
        host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    ).embed(model=EMBEDDING_MODEL, input=texts)
    return [[float(value) for value in embedding] for embedding in response["embeddings"]]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def parse_facts(text: str) -> list[dict]:
    match = re.search(r"\[.*\]", text, flags=re.DOTALL)
    if match is None:
        return []

    try:
        facts = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    if not isinstance(facts, list):
        return []

    valid_facts = []
    for fact in facts[:3]:
        if not isinstance(fact, dict) or not isinstance(fact.get("fact"), str):
            continue

        importance = fact.get("importance", 0.5)
        if not isinstance(importance, (int, float)):
            continue

        valid_facts.append(
            {
                "fact": fact["fact"][:300],
                "importance": max(0.0, min(1.0, float(importance))),
            }
        )

    return valid_facts


def extract_and_store_episodes(user_id: str, session_id: str, message: str) -> None:
    extraction_prompt = [
        {
            "role": "system",
            "content": (
                "Extract up to three durable user facts, preferences, or commitments. "
                "Return only a JSON array with objects containing fact and importance "
                "(a number from 0 to 1). Preserve stated details exactly and do not "
                "infer missing details. Return [] when there are no useful facts."
            ),
        },
        {"role": "user", "content": message},
    ]
    facts = parse_facts(model_text(extraction_prompt))

    new_facts = [
        fact
        for fact in facts
        if not episode_exists(user_id, session_id, fact["fact"])
    ]
    if not new_facts:
        return

    embeddings = embed_texts([fact["fact"] for fact in new_facts])
    for fact, embedding in zip(new_facts, embeddings):
        save_episode(
            user_id,
            session_id,
            fact["fact"],
            fact["importance"],
            embedding,
        )


def retrieve_episodes(user_id: str, message: str) -> list[dict]:
    query_embedding = embed_texts([message])[0]
    scored_episodes = []

    for episode in fetch_user_episodes(user_id):
        score = cosine_similarity(query_embedding, episode["embedding"])
        scored_episodes.append((score, episode))

    scored_episodes.sort(key=lambda item: item[0], reverse=True)
    return [episode for _, episode in scored_episodes[:TOP_K_EPISODES]]


def long_term_memory(user_id: str, session_id: str) -> str:
    summaries = []
    lifetime = latest_summary(user_id, None, "user")
    session = latest_summary(user_id, session_id, "session")

    if lifetime:
        summaries.append(f"Lifetime summary:\n{lifetime['text']}")
    if session:
        summaries.append(f"Session summary:\n{session['text']}")

    return "\n\n".join(summaries)


def build_prompt(
    short_term_messages: list[dict],
    long_term_summary: str,
    episodic_facts: list[dict],
    current_message: str,
) -> list[dict]:
    system_content = SYSTEM_PRIMER
    if long_term_summary:
        system_content += f"\n\n{long_term_summary}"
    if episodic_facts:
        facts = "\n".join(f"- {fact['fact']}" for fact in episodic_facts)
        system_content += f"\n\nRelevant episodic facts:\n{facts}"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(
        {"role": message["role"], "content": message["content"]}
        for message in short_term_messages
    )
    messages.append({"role": "user", "content": current_message})
    return messages


def maybe_update_summaries(user_id: str, session_id: str) -> None:
    user_message_count = count_user_messages(session_id)
    if user_message_count % SUMMARIZE_EVERY_USER_MSGS != 0:
        return

    conversation = fetch_recent_session_messages(session_id, 50)
    transcript = "\n".join(
        f"{message['role']}: {message['content']}" for message in conversation
    )
    summary = model_text(
        [
            {
                "role": "system",
                "content": (
                    "Summarize the conversation as concise bullets. Preserve goals, "
                    "decisions, preferences, and commitments exactly as stated. Do not "
                    "invent or alter dates, times, venues, or preferences. State any "
                    "conflict explicitly."
                ),
            },
            {"role": "user", "content": transcript},
        ]
    )
    save_summary(user_id, session_id, "session", summary)

    session_summaries = fetch_session_summaries(user_id)
    if len(session_summaries) % 3 != 0:
        return

    source = "\n\n".join(summary["text"] for summary in session_summaries)
    lifetime_summary = model_text(
        [
            {
                "role": "system",
                "content": (
                    "Create a concise, up-to-date lifetime user summary using only "
                    "the supplied summaries. Preserve exact dates, times, venues, and "
                    "preferences. Do not infer missing details; state conflicts explicitly."
                ),
            },
            {"role": "user", "content": source},
        ]
    )
    save_summary(user_id, None, "user", lifetime_summary)


def generate_reply(
    user_id: str,
    session_id: str,
    message: str,
    experiment_id: str | None = None,
    experiment_phase: str | None = None,
) -> dict:
    started_at = time.perf_counter()
    save_message(user_id, session_id, "user", message)
    short_term_messages = fetch_recent_session_messages(session_id, SHORT_TERM_N + 1)[:-1]
    extract_and_store_episodes(user_id, session_id, message)
    episodic_facts = retrieve_episodes(user_id, message)
    summary = long_term_memory(user_id, session_id)
    prompt = build_prompt(short_term_messages, summary, episodic_facts, message)
    reply_response = complete(prompt, model=CHAT_MODEL, temperature=0.2)
    reply = str(reply_response.content).strip()
    token_usage = get_token_usage(reply_response)
    component_tokens = prompt_component_tokens(
        short_term_messages,
        summary,
        episodic_facts,
    )
    save_message(user_id, session_id, "assistant", reply)
    maybe_update_summaries(user_id, session_id)

    append_chat_metric(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "session_id": session_id,
            "experiment_id": experiment_id,
            "experiment_phase": experiment_phase,
            "short_term_n": SHORT_TERM_N,
            "model": CHAT_MODEL,
            "prompt_tokens": token_usage["input_tokens"],
            "completion_tokens": token_usage["output_tokens"],
            "system_primer_tokens": component_tokens["system_primer_tokens"],
            "long_term_summary_tokens": component_tokens[
                "long_term_summary_tokens"
            ],
            "short_term_window_tokens": component_tokens[
                "short_term_window_tokens"
            ],
            "episodic_facts_tokens": component_tokens["episodic_facts_tokens"],
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
        }
    )

    return {
        "reply": reply,
        "memory": {
            "short_term_count": len(short_term_messages),
            "short_term_messages": short_term_messages,
            "long_term_summary": summary or None,
            "episodic_facts": episodic_facts,
        },
    }
