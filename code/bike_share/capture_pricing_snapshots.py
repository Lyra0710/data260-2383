"""Save Capital Bikeshare pricing text, provenance, and hashes for both cases."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from tools import HTTP_HEADERS, pricing_text

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "reports" / "hw07" / "raw" / "bike_share"
POLICY_URLS = {
    "pricing": "https://capitalbikeshare.com/pricing",
    "30_day_membership": (
        "https://help.capitalbikeshare.com/hc/en-us/articles/360039401111-30-Day-Membership"
    ),
}
SCENARIOS = ("membership_wins", "pay_per_use_wins")


def capture(url: str) -> dict[str, str]:
    """Fetch one official policy page and return its visible text and metadata."""

    response = httpx.get(
        url,
        follow_redirects=True,
        headers=HTTP_HEADERS,
        timeout=30.0,
    )
    response.raise_for_status()
    text = pricing_text(response.text)
    return {
        "source_url": str(response.url),
        "accessed_at": datetime.now(timezone.utc).isoformat(),
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    captures = {name: capture(url) for name, url in POLICY_URLS.items()}
    for scenario in SCENARIOS:
        scenario_dir = RAW_DIR / scenario
        scenario_dir.mkdir(exist_ok=True)
        metadata = {}
        for name, result in captures.items():
            text_path = scenario_dir / f"{name}.txt"
            text_path.write_text(result["text"] + "\n", encoding="utf-8")
            metadata[name] = {
                key: value for key, value in result.items() if key != "text"
            }
        (scenario_dir / "pricing_snapshot_metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"Saved pricing snapshots for {len(SCENARIOS)} scenarios in {RAW_DIR}")


if __name__ == "__main__":
    main()
