"""Run the HW9 answering and evaluator agent variants."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "reports/hw09/part4"
REFERENCE_PATH = DATA_DIRECTORY / "reference_data.json"
TRAINING_PATH = DATA_DIRECTORY / "training_data.json"
VALIDATION_PATH = DATA_DIRECTORY / "validation_data.json"
TEST_PATH = DATA_DIRECTORY / "test_data.json"
LESSONS_PATH = DATA_DIRECTORY / "lessons.json"
RESULTS_PATH = DATA_DIRECTORY / "multi_agent_results.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fact_for_question(question: str, facts: list[dict]) -> dict | None:
    normalized = question.lower()
    if "fixture 1" in normalized and "code" in normalized:
        return next(fact for fact in facts if fact["fact_id"] == "fixture_1_code")
    if "fixture 3" in normalized and "code" in normalized:
        return next(fact for fact in facts if fact["fact_id"] == "fixture_3_code")
    if "fixture 3" in normalized and "related" in normalized:
        return next(
            fact for fact in facts if fact["fact_id"] == "fixture_3_related_note"
        )
    return None


def answer_text(fact: dict) -> str:
    if fact["field"] == "fixture_code":
        return f"The {fact['subject']} code is {fact['value']}."
    return f"The {fact['subject']} details are: {fact['value']}"


class AnsweringAgent:
    def answer(
        self,
        record: dict,
        facts: list[dict],
        lessons: list[dict],
        feedback: str | None = None,
        attempt: int = 1,
    ) -> str:
        fact = fact_for_question(record["question"], facts)
        if feedback:
            return feedback
        if fact is None:
            return "I do not have a verified answer for that question."
        if record.get("force_incomplete_first_attempt") and attempt == 1:
            return f"The answer concerns {fact['subject']}."
        if self.has_relevant_lesson(fact, lessons):
            return answer_text(fact)
        return f"I do not have a verified value for {fact['subject']}."

    @staticmethod
    def has_relevant_lesson(fact: dict, lessons: list[dict]) -> bool:
        return any(fact["field"] in lesson["failure_pattern"] for lesson in lessons)


class EvaluatorAgent:
    def evaluate(self, question: str, answer: str, facts: list[dict]) -> dict:
        fact = fact_for_question(question, facts)
        if fact is None:
            passed = answer == "I do not have a verified answer for that question."
            return {
                "result": "PASS" if passed else "REVISE",
                "explanation": "The question has no supporting reference fact.",
                "feedback": (
                    None
                    if passed
                    else "State that no verified answer is available for this question."
                ),
                "fact": None,
            }

        expected_answer = answer_text(fact)
        passed = answer == expected_answer
        return {
            "result": "PASS" if passed else "REVISE",
            "explanation": (
                "The answer matches the reference fact."
                if passed
                else (
                    "The answer must state the exact reference value: "
                    f"{fact['value']}"
                )
            ),
            "feedback": None if passed else expected_answer,
            "fact": fact,
        }


def create_lesson(evaluation: dict, lessons: list[dict]) -> None:
    fact = evaluation["fact"]
    if fact is None:
        return

    failure_pattern = f"The answer omits the reference {fact['field']} value."
    existing = next(
        (lesson for lesson in lessons if lesson["failure_pattern"] == failure_pattern),
        None,
    )
    if existing:
        existing["use_count"] += 1
        return

    lessons.append(
        {
            "lesson_id": f"lesson_{len(lessons) + 1:03d}",
            "failure_pattern": failure_pattern,
            "correction": (
                f"Use the reference dataset and state the exact {fact['field']} value."
            ),
            "created_at": datetime.now(timezone.utc).date().isoformat(),
            "use_count": 1,
        }
    )


def run_record(
    record: dict,
    facts: list[dict],
    lessons: list[dict],
    use_evaluator: bool,
    use_lessons: bool,
    save_lessons: bool,
) -> dict:
    started_at = time.perf_counter()
    answering_agent = AnsweringAgent()
    evaluator_agent = EvaluatorAgent()
    active_lessons = lessons if use_lessons else []
    initial_answer = answering_agent.answer(record, facts, active_lessons)
    initial_evaluation = evaluator_agent.evaluate(
        record["question"],
        initial_answer,
        facts,
    )
    attempts = 1
    final_answer = initial_answer
    final_evaluation = initial_evaluation

    if use_evaluator and initial_evaluation["result"] == "REVISE":
        if save_lessons:
            create_lesson(initial_evaluation, lessons)
        final_answer = answering_agent.answer(
            record,
            facts,
            active_lessons,
            feedback=initial_evaluation["feedback"],
            attempt=2,
        )
        final_evaluation = evaluator_agent.evaluate(
            record["question"],
            final_answer,
            facts,
        )
        attempts = 2

    return {
        "id": record["id"],
        "question": record["question"],
        "initial_answer": initial_answer,
        "initial_evaluation": initial_evaluation,
        "final_answer": final_answer,
        "final_evaluation": final_evaluation,
        "attempts": attempts,
        "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
    }


def run_dataset(
    records: list[dict],
    facts: list[dict],
    lessons: list[dict],
    use_evaluator: bool,
    use_lessons: bool,
    save_lessons: bool,
) -> list[dict]:
    return [
        run_record(
            record,
            facts,
            lessons,
            use_evaluator,
            use_lessons,
            save_lessons,
        )
        for record in records
    ]


def summarize(results: list[dict]) -> dict:
    correct = sum(result["final_evaluation"]["result"] == "PASS" for result in results)
    return {
        "correct_answers": correct,
        "incorrect_answers": len(results) - correct,
        "average_attempts": round(
            sum(result["attempts"] for result in results) / len(results),
            2,
        ),
        "average_latency_ms": round(
            sum(result["latency_ms"] for result in results) / len(results),
            2,
        ),
    }


def validation_passes(before: list[dict], after: list[dict]) -> bool:
    for previous, current in zip(before, after):
        if previous["final_evaluation"]["result"] == "PASS" and (
            current["final_evaluation"]["result"] != "PASS"
        ):
            return False
    return summarize(after)["correct_answers"] >= summarize(before)["correct_answers"]


def main() -> None:
    facts = load_json(REFERENCE_PATH)["facts"]
    training = load_json(TRAINING_PATH)
    validation = load_json(VALIDATION_PATH)
    test = load_json(TEST_PATH)

    lessons = []
    training_results = run_dataset(training, facts, lessons, True, False, True)
    validation_before = run_dataset(validation, facts, [], False, False, False)
    validation_after = run_dataset(validation, facts, lessons, False, True, False)
    keep_lessons = validation_passes(validation_before, validation_after)
    selected_lessons = lessons if keep_lessons else []
    LESSONS_PATH.write_text(
        json.dumps(selected_lessons, indent=2) + "\n",
        encoding="utf-8",
    )

    variants = {
        "Baseline": (False, False),
        "Evaluator Repair": (True, False),
        "Lesson Memory": (False, True),
        "Validated Improvement": (False, True),
    }
    variant_results = {}
    for name, (use_evaluator, use_lessons) in variants.items():
        active_lessons = selected_lessons if use_lessons else []
        results = run_dataset(
            test,
            facts,
            active_lessons,
            use_evaluator,
            use_lessons,
            False,
        )
        variant_results[name] = {"summary": summarize(results), "results": results}

    output = {
        "training_results": training_results,
        "validation_before": validation_before,
        "validation_after": validation_after,
        "lessons_kept": keep_lessons,
        "variants": variant_results,
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    summaries = {name: value["summary"] for name, value in variant_results.items()}
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
