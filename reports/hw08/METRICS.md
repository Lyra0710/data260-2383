# HW8 Results Tables

## Personal Configuration

| Value | Result |
| --- | --- |
| SID4 | 2383 |
| PORT_BASE | 8583 |
| PREFIX | s2383 |
| SEED | 2383 |
| VERIFY_SEED | 262383 |
| DOMAIN_ID | 7 |

## Part 1 — Kafka Request/Response Results

| Check | Result | Evidence |
| --- | --- | --- |
| CREATE_FIXTURE | Passed; Worker generated a UUID entity ID and stored the Fixture in its in-memory dictionary. | `RUN_LOG.txt`; `verification.json` |
| GET_FIXTURE | Passed; Worker returned the exact created Fixture. | `RUN_LOG.txt`; `verification.json` |
| Correlation ID | Preserved unchanged across CREATE_FIXTURE and GET_FIXTURE. | `RUN_LOG.txt`; `verification.json` |
| Validation/error behavior | Passed for missing field, empty values, invalid values, unknown operation, missing entity ID, and unknown entity ID. | `RUN_LOG.txt` |
| Docker services | Kafka, Worker, and FastAPI ran together; FastAPI was available at `http://127.0.0.1:8583`. | `RUN_LOG.txt` |

## Part 2 — Three-Agent Pipeline Results

| Stage | Input topic | Output topic | Result |
| --- | --- | --- | --- |
| Planner | `s2383_inbox` | `s2383_tasks` | Created a three-step plan. |
| Writer | `s2383_tasks` | `s2383_drafts` | Produced a fixture-management draft. |
| Reviewer | `s2383_drafts` | `s2383_final` | Returned `status: approved` and a final answer. |

## Part 3 — Failure Behavior

| Failure scenario | Before fix | After fix | Matching evidence |
| --- | --- | --- | --- |
| Duplicate delivery | Replaying correlation ID `12b64d45-1e4a-42d2-b3c7-90ef1f61585d` produced two draft side effects. | Replaying correlation ID `23ccf642-7d4f-410b-b11a-0fc23ff65cb9` produced one draft; Writer logged `duplicate skipped`. | `RUN_LOG.txt`; `raw/failure_results.json` |
| Consumer killed mid-work | Writer was stopped during a 30-second processing delay, before it sent a draft or committed the offset. | After restart, Writer received correlation ID `8b3c54b3-300c-4d7f-a49a-23e01f920b36` again and completed the draft. | `RUN_LOG.txt`; `raw/failure_results.json` |
| Poison message | The baseline Writer had no bounded retry or dead-letter path for a forced failure. | Writer retried three times, sent the poison message to `s2383_dead_letter`, and then completed the later valid task. | `RUN_LOG.txt`; `raw/failure_results.json` |
| Two partitions/two consumers | The unkeyed run used partitions 0 and 1; related messages completed out of order: `1, 2, 4, 3, ...`. | The keyed run used partition 1 only; all 20 related messages completed in order 1–20. | `raw/ordering_unkeyed_summary.json`; `raw/ordering_keyed_summary.json` |

## Kafka Compared With the HW2 In-Process Graph

### Benefits

1. Planner, Writer, and Reviewer run as separate processes, so a stage can scale or restart independently.
2. Kafka topics buffer messages between stages, so a sender and downstream consumer are decoupled in time.

### New Responsibilities

1. The application must make side effects idempotent and deliberately control when offsets are committed.
2. The application must handle retries, dead-letter messages, and partition keys when related-message order matters.
