import argparse
import json
from itertools import islice
from pathlib import Path
from urllib.request import Request, urlopen

import chromadb
from pypdf import PdfReader


RAG_DIR = Path(__file__).resolve().parent
CORPUS_DIR = RAG_DIR / "corpus"
VECTOR_STORE_DIR = RAG_DIR / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_BATCH_SIZE = 32
COLLECTION_NAME = "hw4_course_documents"

REPOSITORY_DIR = RAG_DIR.parents[1]
RAW_OUTPUT_DIR = REPOSITORY_DIR / "reports" / "hw04" / "raw"
QUESTIONS_PATH = RAG_DIR / "questions.json"

REFUSAL_MESSAGE = (
    "I cannot answer this question from the provided documents"
)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Build the HW4 local RAG vector index.",
    )
    parser.add_argument(
        "command",
        choices=[
    "build-index",
    "retrieve",
    "run-evaluation",
    "run-sweep",
],
    )
    parser.add_argument(
        "--question-id",
        help="Question ID used for the k-sweep.",
    )
    parser.add_argument(
        "--embedding-model",
        default="nomic-embed-text",
        help="Local Ollama embedding model.",
    )
    parser.add_argument(
        "--ollama-host",
        default="http://localhost:11434",
        help="Local Ollama server URL.",
    )
    parser.add_argument(
        "--question",
        help="Question used for retrieval.",
    )
    parser.add_argument(
        "--k",
        type=int,
        choices=[1, 3, 5],
        default=3,
        help="Number of chunks to retrieve.",
    )
    parser.add_argument(
        "--chat-model",
        default="qwen3:8b",
        help="Local Ollama chat model.",
    )
    return parser.parse_args()


def chunks(items, size):
    iterator = iter(items)

    while batch := list(islice(iterator, size)):
        yield batch


def chunk_text(text):
    cleaned_text = " ".join(text.split())
    step = CHUNK_SIZE - CHUNK_OVERLAP

    return [
        cleaned_text[start : start + CHUNK_SIZE]
        for start in range(0, len(cleaned_text), step)
        if cleaned_text[start : start + CHUNK_SIZE].strip()
    ]


def read_corpus():
    records = []

    for pdf_path in sorted(CORPUS_DIR.glob("*.pdf")):
        reader = PdfReader(pdf_path)

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""

            for chunk_number, text in enumerate(chunk_text(page_text), start=1):
                records.append(
                    {
                        "id": (
                            f"{pdf_path.stem}-"
                            f"page-{page_number}-"
                            f"chunk-{chunk_number}"
                        ),
                        "text": text,
                        "metadata": {
                            "source": pdf_path.name,
                            "page": page_number,
                            "chunk": chunk_number,
                        },
                    }
                )

    if not records:
        raise RuntimeError(
            f"No readable PDF text found in {CORPUS_DIR}."
        )

    return records


def embed_texts(texts, ollama_host, embedding_model):
    request = Request(
        url=f"{ollama_host.rstrip('/')}/api/embed",
        data=json.dumps(
            {
                "model": embedding_model,
                "input": texts,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        result = json.load(response)

    return result["embeddings"]

# Stores each chunk’s text, source filename, and page number in persistent ChromaDB.
def build_index(arguments):
    records = read_corpus()

    client = chromadb.PersistentClient(
        path=str(VECTOR_STORE_DIR),
    )

    if COLLECTION_NAME in client.list_collections():
        client.delete_collection(COLLECTION_NAME)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    for batch in chunks(records, EMBEDDING_BATCH_SIZE):
        embeddings = embed_texts(
            texts=[record["text"] for record in batch],
            ollama_host=arguments.ollama_host,
            embedding_model=arguments.embedding_model,
        )

        collection.upsert(
            ids=[record["id"] for record in batch],
            documents=[record["text"] for record in batch],
            metadatas=[record["metadata"] for record in batch],
            embeddings=embeddings,
        )

    print(f"PDF files read: {len(list(CORPUS_DIR.glob('*.pdf')))}")
    print(f"Chunks indexed: {collection.count()}")
    print(f"Chunk size: {CHUNK_SIZE}")
    print(f"Chunk overlap: {CHUNK_OVERLAP}")
    print(f"Embedding model: {arguments.embedding_model}")

def get_retrieved_chunks(arguments, question, k):
    client = chromadb.PersistentClient(
        path=str(VECTOR_STORE_DIR),
    )
    collection = client.get_collection(
        name=COLLECTION_NAME,
    )

    query_embedding = embed_texts(
        texts=[question],
        ollama_host=arguments.ollama_host,
        embedding_model=arguments.embedding_model,
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "source": metadata["source"],
            "page": metadata["page"],
            "chunk": metadata["chunk"],
            "score": 1 - distance,
            "text": document,
        }
        for document, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def print_retrieved_chunks(question, retrieved_chunks):
    print(f"\nQuestion: {question}")
    print("Retrieved chunks:")

    for rank, chunk in enumerate(retrieved_chunks, start=1):
        print(
            f"\n{rank}. {chunk['source']} "
            f"(page {chunk['page']}, "
            f"score {chunk['score']:.4f})"
        )
        print(chunk["text"])


def retrieve(arguments):
    if not arguments.question:
        raise ValueError(
            "--question is required for the retrieve command."
        )

    retrieved_chunks = get_retrieved_chunks(
        arguments,
        arguments.question,
        arguments.k,
    )
    print_retrieved_chunks(
        arguments.question,
        retrieved_chunks,
    )

def call_llm(arguments, prompt):
    request = Request(
        url=f"{arguments.ollama_host.rstrip('/')}/api/generate",
        data=json.dumps(
            {
                "model": arguments.chat_model,
                "prompt": prompt,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 256,
                },
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=300) as response:
        result = json.load(response)

    return result["response"].strip()


def basic_rag_prompt(question, retrieved_chunks):
    context = "\n\n".join(
        f"Chunk {rank}:\n{chunk['text']}"
        for rank, chunk in enumerate(retrieved_chunks, start=1)
    )

    return (
        "Answer the question using the retrieved context.\n\n"
        f"Retrieved context:\n{context}\n\n"
        f"Question: {question}"
    )


def context_rag_prompt(question, retrieved_chunks):
    unique_chunks = []
    seen_text = set()

    for chunk in sorted(
        retrieved_chunks,
        key=lambda item: item["score"],
        reverse=True,
    ):
        normalized_text = " ".join(chunk["text"].split())

        if normalized_text in seen_text:
            continue

        seen_text.add(normalized_text)
        unique_chunks.append(chunk)

    context = "\n\n".join(
        f"[Source {rank}: {chunk['source']}, page {chunk['page']}]\n"
        f"{chunk['text']}"
        for rank, chunk in enumerate(unique_chunks, start=1)
    )

    return (
        "Answer only from the labeled context below. "
        "Cite the source number(s) used in your answer. "
        f"If the evidence is insufficient, reply exactly: "
        f"'{REFUSAL_MESSAGE}'.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
        "If the question has multiple supported meanings, distinguish them rather than choosing only one. "
    )


def no_rag_prompt(question):
    return (
        "Answer the question concisely.\n\n"
        f"Question: {question}"
    )


def load_questions():
    return json.loads(
        QUESTIONS_PATH.read_text(encoding="utf-8")
    )


def save_raw_output(filename, data):
    RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_OUTPUT_DIR / filename
    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    print(f"\nSaved: {output_path}")


def run_evaluation(arguments):
    results = []

    for item in load_questions():
        question = item["question"]
        retrieved_chunks = get_retrieved_chunks(
            arguments,
            question,
            k=3,
        )

        print(f"\n{'=' * 60}\n{item['id'].upper()}")
        print_retrieved_chunks(question, retrieved_chunks)

        answers = {
            "no_rag": call_llm(
                arguments,
                no_rag_prompt(question),
            ),
            "basic_rag": call_llm(
                arguments,
                basic_rag_prompt(question, retrieved_chunks),
            ),
            "context_rag": call_llm(
                arguments,
                context_rag_prompt(question, retrieved_chunks),
            ),
        }

        for configuration, answer in answers.items():
            print(f"\n{configuration}:\n{answer}")

        results.append(
            {
                **item,
                "k": 3,
                "retrieved_chunks": retrieved_chunks,
                "answers": answers,
            }
        )

    save_raw_output("rag_comparison.json", results)


def run_sweep(arguments):
    
    question = next(
        (
            item
            for item in load_questions()
            if item["id"] == arguments.question_id
        ),
        None,
    )

    if not question:
        raise ValueError(
            f"Question ID '{arguments.question_id}' was not found."
        )

    results = []

    for k in [1, 3, 5]:
        retrieved_chunks = get_retrieved_chunks(
            arguments,
            question["question"],
            k,
        )

        print(f"\n{'=' * 60}\nK = {k}")
        print_retrieved_chunks(
            question["question"],
            retrieved_chunks,
        )

        answer = call_llm(
            arguments,
            context_rag_prompt(
                question["question"],
                retrieved_chunks,
            ),
        )

        print(f"\ncontext_rag:\n{answer}")

        results.append(
            {
                "k": k,
                "retrieved_chunks": retrieved_chunks,
                "answer": answer,
            }
        )

    save_raw_output(
        "rag_k_sweep.json",
        {
            "question": question,
            "configuration": "context_rag",
            "results": results,
        },
    )
def main():
    arguments = parse_arguments()

    if arguments.command == "build-index":
        build_index(arguments)
    elif arguments.command == "retrieve":
        retrieve(arguments)
    elif arguments.command == "run-evaluation":
        run_evaluation(arguments)
    elif arguments.command == "run-sweep":
        run_sweep(arguments)

if __name__ == "__main__":
    main()