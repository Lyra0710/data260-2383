import time
from pathlib import Path

import numpy as np

from llama_index.core import (
    Document,
    Settings,
    VectorStoreIndex,
)
from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WARMUP_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "warmup"
    / "tinyshakespeare.txt"
)


def load_document(file_path: Path):
    text = file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    document = Document(
        text=text,
        metadata={
            "source": file_path.name,
        },
    )

    return document

def load_embedding_model():
    return HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

# token splitter 
def create_token_nodes(document):
    splitter = TokenTextSplitter(
        chunk_size=256,
        chunk_overlap=40,
        separator=" ",
    )

    nodes = splitter.get_nodes_from_documents(
        [document]
    )

    return nodes

# index to retreive top chunks
def retrieve_chunks(
    nodes,
    embed_model,
    query,
    top_k=5,
):
 

    index = VectorStoreIndex(nodes)

    retriever = index.as_retriever(
        similarity_top_k=top_k
    )

    results = retriever.retrieve(query)

    query_vector = np.asarray(
        embed_model.get_query_embedding(query),
        dtype=float,
    )

    print("Query vector shape:", query_vector.shape)
    print("Query vector first 8 values:", query_vector[:8])

    print("\nTop retrieved chunks:")

    for rank, result in enumerate(results, start=1):
        preview = " ".join(
            result.node.get_content().split()
        )[:160]

        document_vector = np.asarray(
            embed_model.get_text_embedding(
                result.node.get_content()
            ),
            dtype=float,
        )

        cosine_score = calculate_cosine_similarity(
            query_vector,
            document_vector,
        )

        print(f"\nRank {rank}")
        print("Store similarity score:", result.score)
        print("Explicit cosine similarity:", cosine_score)
        print("Chunk length:", len(result.node.get_content()))
        print("Preview:", preview)

    return results

# similarity
def calculate_cosine_similarity(vector_a, vector_b):
    vector_a = np.asarray(vector_a, dtype=float)
    vector_b = np.asarray(vector_b, dtype=float)

    denominator = (
        np.linalg.norm(vector_a)
        * np.linalg.norm(vector_b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(vector_a, vector_b) / denominator
    )

def create_semantic_nodes(document, embed_model):
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model,
    )

    nodes = splitter.get_nodes_from_documents(
        [document]
    )

    return nodes

def create_sentence_window_nodes(document):
    splitter = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_sentence",
    )

    nodes = splitter.get_nodes_from_documents(
        [document]
    )

    return nodes

# code to run the experiment on warmup data 
def run_warmup():
    document = load_document(WARMUP_PATH)
    embed_model = load_embedding_model()

    Settings.embed_model = embed_model

    query = "What does Romeo say about love?"

    techniques = {
        "token": create_token_nodes(document),
        "semantic": create_semantic_nodes(
            document,
            embed_model,
        ),
        "sentence-window": create_sentence_window_nodes(
            document
        ),
    }

    for technique_name, nodes in techniques.items():
        print(f"\nCreating {technique_name} chunks...")
        print("Number of chunks:", len(nodes))

        retrieve_chunks(
            nodes=nodes,
            embed_model=embed_model,
            query=query,
            top_k=5,
        )


def main():
    # Temporary warm-up run while we finish the refactor.
    run_warmup()


if __name__ == "__main__":
    main()
