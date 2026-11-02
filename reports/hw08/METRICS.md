# HW8 Results

## Part 3 Failure Behavior

| Failure scenario | Before fix | After fix | Evidence |
| --- | --- | --- | --- |
| Duplicate delivery | Replaying one correlation ID produced two draft side effects. | The first replay produced one draft; the duplicate was skipped. | `raw/failure_results.json`; `RUN_LOG.txt` |
| Consumer killed mid-work | Writer was stopped during its processing delay, before it sent a draft or committed its offset. | After restart, Writer received the same correlation ID and completed the draft. | `raw/failure_results.json`; `RUN_LOG.txt` |
| Poison message | A forced-failure task needed explicit handling to avoid stopping later work. | Writer retried three times, sent the task to `s2383_dead_letter`, then completed the later valid task. | `raw/failure_results.json`; `RUN_LOG.txt` |
| Two partitions/two consumers | Unkeyed related messages used partitions 0 and 1 and completed out of input order: `1, 2, 4, 3, ...`. | With key `fixture-ordering-2383`, all 20 messages used partition 1 and completed in order 1–20. | `raw/ordering_unkeyed_summary.json`; `raw/ordering_keyed_summary.json` |

## Part 3 Comparison With HW2

Kafka provided independent processes that can scale or restart separately, and durable topic buffers that decouple a sender from downstream processing. Unlike the HW2 in-process graph, this design also requires explicit idempotency and offset/retry handling for duplicate or failed delivery, plus deliberate partition-key choices when related messages must remain ordered.
