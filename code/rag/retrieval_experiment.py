from pathlib import Path

from llama_index.core import Document
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

if __name__ == "__main__":
    document = load_document(WARMUP_PATH)

    print("Loaded file:", WARMUP_PATH)
    print("Character count:", len(document.text))
    print("Source:", document.metadata["source"])
    print("\nPreview:")
    print(document.text[:500])
    print("\nLoading embedding model...")
    embed_model = load_embedding_model()

    test_embedding = embed_model.get_text_embedding(
        "What does Romeo say about love?"
    )

    print("\nEmbedding dimension:", len(test_embedding))
    print("First 8 embedding values:", test_embedding[:8])