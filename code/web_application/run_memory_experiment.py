"""Run the fixed HW6 conversation and memory probes against the local API."""

import argparse
import json
import os
import time
from pathlib import Path

import requests
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
PROBES_PATH = REPO_ROOT / "reports" / "hw06" / "memory_probes.yaml"

CONVERSATION = [
    "My name is Ananya, and I organize a community sports league.",
    "I prefer tennis matches on weekday evenings.",
    "I need the tennis schedule to avoid Monday evenings.",
    "My preferred venue is Spartan Tennis Complex.",
    "I am planning a pickleball fundraiser on November 20.",
    "I want the fundraiser to start at 6 PM.",
    "Players need to bring water to the fundraiser.",
    "My favorite color for event flyers is blue.",
    "I expect about 40 attendees at the fundraiser.",
    "Please remember the fundraiser details for later.",
    "The league needs a volunteer sign-up reminder next month.",
    "I want beginner-friendly tennis clinics in the spring.",
    "Please keep the tennis and fundraiser details separate.",
    "The fundraiser will use the main court at the venue.",
    "I need a checklist for volunteer setup.",
    "The tennis clinics should have small groups.",
    "I prefer concise event-update emails.",
    "The fundraiser should include a welcome table.",
    "Please track the expected attendance for the fundraiser.",
    "The volunteer reminder should mention the event date.",
    "I want the beginner clinics to be welcoming.",
    "The main court needs a sound-system check.",
    "Please keep blue as the flyer color.",
    "The welcome table needs two volunteers.",
    "I will confirm the venue availability later.",
    "The event checklist should include water supplies.",
    "The tennis schedule must still avoid Monday evenings.",
    "I want a final reminder for the 40 expected attendees.",
    "Please prepare a concise summary of the event plan.",
    "I may add more volunteer details after this conversation.",
]


def post_chat(
    base_url: str,
    user_id: str,
    session_id: str,
    message: str,
    experiment_id: str,
    experiment_phase: str,
) -> dict:
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "experiment_id": experiment_id,
            "experiment_phase": experiment_phase,
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--short-term-n", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--base-url",
        default=os.getenv("HW6_BASE_URL", "http://127.0.0.1:8583"),
    )
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    probes = yaml.safe_load(PROBES_PATH.read_text(encoding="utf-8"))["probes"]
    user_id = f"hw6-{arguments.run_id}"
    session_id = f"session-{arguments.run_id}"
    results = {
        "run_id": arguments.run_id,
        "short_term_n": arguments.short_term_n,
        "user_id": user_id,
        "session_id": session_id,
        "conversation": [],
        "probes": [],
    }

    for turn, message in enumerate(CONVERSATION, start=1):
        response = post_chat(
            arguments.base_url,
            user_id,
            session_id,
            message,
            arguments.run_id,
            "conversation",
        )
        results["conversation"].append(
            {"turn": turn, "message": message, "reply": response["reply"]}
        )
        print(f"Conversation turn {turn}/30 complete")

    for probe in probes:
        response = post_chat(
            arguments.base_url,
            user_id,
            session_id,
            probe["question"],
            arguments.run_id,
            "probe",
        )
        results["probes"].append(
            {
                "id": probe["id"],
                "question": probe["question"],
                "expected_answer_criteria": probe["expected_answer_criteria"],
                "reply": response["reply"],
            }
        )
        print(f"Probe {probe['id']} complete")

    results["completed_at"] = time.time()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Saved results to {arguments.output}")


if __name__ == "__main__":
    main()
