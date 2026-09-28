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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Build the HW4 local RAG vector index.",
    )
    parser.add_argument(
        "command",
        choices=["build-index"],
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


def main():
    arguments = parse_arguments()

    if arguments.command == "build-index":
        build_index(arguments)


if __name__ == "__main__":
    main()