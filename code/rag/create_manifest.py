from pathlib import Path
import hashlib
import json
# this generates CORPUS_MANIFEST.json automatically so the byte sizes and hashes are accurate.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = PROJECT_ROOT / "reports" / "hw03" / "corpus"
OUTPUT_PATH = PROJECT_ROOT / "reports" / "hw03" / "CORPUS_MANIFEST.json"


def sha256_file(file_path):
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def main():
    files = []

    for file_path in sorted(CORPUS_DIR.iterdir()):
        if file_path.is_file():
            files.append(
                {
                    "filename": file_path.name,
                    "bytes": file_path.stat().st_size,
                    "sha256": sha256_file(file_path),
                }
            )

    manifest = {
        "corpus_directory": "reports/hw03/corpus",
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
    }

    OUTPUT_PATH.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()