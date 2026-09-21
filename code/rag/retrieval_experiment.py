import time
from pathlib import Path
import yaml
import numpy as np
from bs4 import BeautifulSoup
import json
from llama_index.core import (
    Document,
    Settings,
    SimpleDirectoryReader, # supports loading a local directory and explicitly supports PDFs
    VectorStoreIndex,
)
from llama_index.core.node_parser import (
    HTMLNodeParser,
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser,
    TokenTextSplitter,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[2]

WARMUP_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "warmup"
    / "tinyshakespeare.txt"
)
CORPUS_DIR = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "corpus"
)

QUESTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "questions.yaml"
)

RAW_DIR = (
    PROJECT_ROOT
    / "reports"
    / "hw03"
    / "raw"
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

def load_pdf_document(file_path: Path):
    reader = PdfReader(str(file_path))
    page_text = []

    for page in reader.pages:
        layout_text = page.extract_text(
            extraction_mode="layout"
        ) or ""

        default_text = page.extract_text() or ""

        layout_length = len(
            " ".join(layout_text.split())
        )
        default_length = len(
            " ".join(default_text.split())
        )

        if default_length > layout_length:
            page_text.append(default_text)
        else:
            page_text.append(layout_text)

    return Document(
        text="\n".join(page_text),
        metadata={
            "file_name": file_path.name,
            "file_path": str(file_path),
        },
    )

def load_html_document(file_path: Path):
    html = file_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for tag in soup(
        ["header", "nav", "footer", "script", "style"]
    ):
        tag.decompose()

    text = soup.get_text(
        "\n",
        strip=True,
    )

    return Document(
        text=text,
        metadata={
            "file_name": file_path.name,
            "file_path": str(file_path),
        },
    )

def load_corpus(directory: Path):
    pdf_files = sorted(directory.glob("*.pdf"))
    html_files = sorted(directory.glob("*.html"))

    pdf_documents = [
        load_pdf_document(file_path) for file_path in pdf_files
    ]

    html_documents = [
        load_html_document(file_path)
        for file_path in html_files
    ]
    return pdf_documents + html_documents

    # html_parser = HTMLNodeParser.from_defaults()

    # cleaned_html_documents = []

    for document in raw_html_documents:
        html_nodes = html_parser.get_nodes_from_node(
            document
        )

        for node in html_nodes:
            cleaned_html_documents.append(
                Document(
                    text=node.get_content(),
                    metadata={
                        **document.metadata,
                        **node.metadata,
                    },
                )
            )

    return pdf_documents + cleaned_html_documents

def load_embedding_model():
    return HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

# token splitter 
def create_token_nodes(documents):
    splitter = TokenTextSplitter(
        chunk_size=256,
        chunk_overlap=40,
        separator=" ",
    )

    nodes = splitter.get_nodes_from_documents(
        documents
    )

    return nodes

# index to retreive top chunks
def build_retriever(nodes, top_k=5):
    index = VectorStoreIndex(nodes)

    return index.as_retriever(
        similarity_top_k=top_k
    )


def retrieve_chunks(
    nodes,
    retriever,
    embed_model,
    query,
    technique_name,
):
    start_time = time.perf_counter()

    results = retriever.retrieve(query)

    latency_ms = (
        time.perf_counter() - start_time
    ) * 1000

    query_vector = np.asarray(
        embed_model.get_query_embedding(query),
        dtype=float,
    )

    rows = []
    document_vectors = []

    for rank, result in enumerate(results, start=1):
        node_text = result.node.get_content()

        document_vector = np.asarray(
            embed_model.get_text_embedding(node_text),
            dtype=float,
        )

        document_vectors.append(document_vector)
        source = result.node.metadata.get(
            "file_name", 
            result.node.metadata.get("source", "unknown")
        )

        rows.append(
            {
                "rank": rank,
                "source": source,
                "store_score": result.score,
                "cosine_similarity": (
                    calculate_cosine_similarity(
                        query_vector,
                        document_vector,
                    )
                ),
                "chunk_length": len(node_text),
                "preview": " ".join(node_text.split())[:160],
            }
        )

    document_matrix = np.vstack(document_vectors)

    return {
        "technique": technique_name,
        "query": query,
        "node_count": len(nodes),
        "average_chunk_length": float(
            np.mean(
                [
                    len(node.get_content())
                    for node in nodes
                ]
            )
        ),
        "latency_ms": latency_ms,
        "query_vector_shape": list(
            query_vector.shape
        ),
        "query_vector_first_8": (
            query_vector[:8].tolist()
        ),
        "document_vector_shape": list(
            document_matrix.shape
        ),
        "results": rows,
    }
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

def create_semantic_nodes(documents, embed_model):
    splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=embed_model,
    )

    nodes = splitter.get_nodes_from_documents(
        documents
    )

    return nodes

def create_sentence_window_nodes(documents):
    splitter = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_sentence",
    )

    nodes = splitter.get_nodes_from_documents(
        documents
    )

    return nodes

def load_questions(file_path: Path):
    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    return data["questions"]

# code to run the experiment on warmup data 
def run_warmup():
    document = load_document(WARMUP_PATH)
    embed_model = load_embedding_model()

    Settings.embed_model = embed_model

    query = "What does Romeo say about love?"

    techniques = {
        "token": create_token_nodes([document]),
        "semantic": create_semantic_nodes(
            [document],
            embed_model,
        ),
        "sentence-window": create_sentence_window_nodes(
            [document]
        ),
    }

    for technique_name, nodes in techniques.items():
        print(f"\nCreating {technique_name} chunks...")
        print("Number of chunks:", len(nodes))

        retrieve_chunks(
            nodes=nodes,
            embed_model=embed_model,
            query=query
        )

def save_raw_result(result, question_id):
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_name = (
        f"{question_id}_{result['technique']}.json"
    )

    output_path = RAW_DIR / file_name

    output = {
        "question_id": question_id,
        **result,
    }

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
        )

def main():
    # run_warmup()
    questions = load_questions(QUESTIONS_PATH)
    documents = load_corpus(CORPUS_DIR)

    print("Loaded graded questions:", len(questions))
    print("Loaded corpus documents:", len(documents))

    embed_model = load_embedding_model()
    Settings.embed_model = embed_model

    techniques = {
        "token": create_token_nodes(documents),
        "semantic": create_semantic_nodes(
            documents,
            embed_model,
        ),
        "sentence-window": create_sentence_window_nodes(
            documents
        ),
    }

    for technique_name, nodes in techniques.items():
        print(
            f"Created {technique_name} chunks:",
            len(nodes),
        )

    retrievers = {
        technique_name: build_retriever(nodes)
        for technique_name, nodes
        in techniques.items()
    }

    for question in questions:
        question_id = question["id"]
        query = question["question"]

        print(f"\nQuestion: {question_id}")

        for technique_name, nodes in techniques.items():
            result = retrieve_chunks(
                nodes=nodes,
                retriever=retrievers[technique_name],
                embed_model=embed_model,
                query=query,
                technique_name=technique_name,
            )

            save_raw_result(
                result=result,
                question_id=question_id,
            )

            print(
                technique_name,
                "latency:",
                f"{result['latency_ms']:.2f} ms",
                "top-1 cosine:",
                f"{result['results'][0]['cosine_similarity']:.4f}",
            )

if __name__ == "__main__":
    main()
