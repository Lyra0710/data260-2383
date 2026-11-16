# AI Use for HW10

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant to help interpret the Homework 10 requirements, inspect
the existing Kafka and semantic cache implementation, suggest small code
changes, and draft documentation. I personally ran the DeepEval judge
validation, started Kafka, Redis, and the four workers, ran the cache-miss,
cache-hit, and failure traces, ran the 50-request latency experiment, reviewed
the raw JSON evidence, and captured the report screenshots.

## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

I independently verified that the first latency summary incorrectly treated
the runner's Kafka-client startup time as queue wait. I also verified that a
full GEval evaluator worker was still consuming messages when the first
linkage-only latency test unexpectedly reported a full evaluation.

## 3. How I detected the problem or verified the result

I compared the per-trace timestamps in `raw/traces.jsonl`. The approximately
9-second gap was consistently between cache lookup and inbox publication,
which showed that it was runner setup rather than Kafka stage-to-stage wait.
For the evaluator-mode issue, I compared the requested mode with the
`observed_evaluation_modes` field produced by the latency runner.

## 4. What I changed and why it works now

I separated `runner_setup` from actual queue wait and regenerated the latency
summary from the already captured 50 traces, without rerunning the experiment.
I also added a mode-consistency check and restarted the evaluator worker in
`linkage_only` mode. The final evidence records 50 confirmed cache misses,
explicitly identifies `linkage_only` evaluation mode, and preserves the full
DeepEval GEval validation as a separate Part 2 result.
