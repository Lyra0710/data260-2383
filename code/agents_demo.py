

import argparse, json, os, re, sys, time
from dataclasses import dataclass
from typing import List, Dict, Any, Iterable, Tuple

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from collections import Counter

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Your Blog Title Here")
    ap.add_argument("--content", default="Your blog post content goes here.")
    ap.add_argument("--email", default="student@example.com")
    ap.add_argument("--model", default=os.environ.get("SMOL_MODEL", "qwen3:8b"))
    ap.add_argument("--base_url", default=os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument(
    "--temperature",
    type=float,
    default=0.0,
    help="Model sampling temperature"
)
    args = ap.parse_args()

    # Initialize Ollama chat model (students can adjust params)
    try:
        llm = ChatOllama(
            model=args.model,
            temperature=args.temperature,
            base_url=args.base_url,
            num_ctx=2048,
            format="json",  # asks Ollama to produce JSON when supported
        )
    except Exception:
        print(
            "Failed to initialize ChatOllama. Is Ollama running and the model available?\n"
            "Try: `ollama serve` and `ollama pull <your-model-tag>`.",
            file=sys.stderr,
        )
        raise

    # Define three agents (Planner -> Reviewer -> Finalizer)
    planner = SimpleAgent(
        name="Planner",
        system="Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the supplied title and content.",
        model=llm,
    )
    reviewer = SimpleAgent(
        name="Reviewer",
        system=(
            "Validate: tags topical and not generic; summary ≤ 25 words; no code or markdown. "
            "If issues, list in data.issues; otherwise echo cleaned tags/summary."
        ),
        model=llm,
    )
    finalizer = SimpleAgent(
        name="Finalizer",
        system=(
            "Use reviewer feedback to finalize. Output exactly 3 tags in data.tags and the final summary in data.summary. "
            "Set data.issues to []."
        ),
        model=llm,
    )

    task = (
        f'Given title "{args.title}" and content "{args.content}", produce exactly 3 topical tags '
        f'and a one-sentence summary in your own words. Email is {args.email}.'
    )

    transcript: List[Dict[str, str]] = []

    # Planner
    t0 = time.time()
    a = planner.respond(transcript, task, args.title, args.content, args.strict)
    t1 = time.time()
    transcript.append({
    "role": "Planner",
    "content": json.dumps(a)
})
    print(f"\n--- Planner ({int((t1 - t0) * 1000)} ms) ---\n{json.dumps(a, indent=2)}")

    # Reviewer
    t0 = time.time()
    b = reviewer.respond(transcript, task, args.title, args.content, args.strict)
    t1 = time.time()
    transcript.append({
    "role": "Reviewer",
    "content": json.dumps(b)
})
    print(f"\n--- Reviewer ({int((t1 - t0) * 1000)} ms) ---\n{json.dumps(b, indent=2)}")

    # Finalizer
    final = finalizer.respond(transcript, task, args.title, args.content, args.strict)
    print(f"\n Finalized Output \n{json.dumps(final, indent=2)}")

    # Publish package
    package = {
        "title": args.title,
        "email": args.email,
        "content": args.content,
        "agents": {"transcript": transcript, "final": final.get("data", {})},
        "submissionDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print(f"\n Publish Package \n{json.dumps(package, indent=2)}")


if __name__ == "__main__":
    main()
