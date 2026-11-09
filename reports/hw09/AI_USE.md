# AI Use for HW9

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant to help interpret the homework requirements, inspect the
existing project and help debug the code. I personally ran the Redis, MySQL,
and application commands, ran the semantic-cache demo and threshold sweep,
reviewed the outputs, updated the related-item record, ran the multi-agent
evaluation, and reviewed the saved raw files and run log.

## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

I independently verified the semantic-cache threshold results rather than
relying only on an AI summary. In particular, I checked the false hits where
similar questions about fixture 1 and fixture 3 had different correct answers.

## 3. How I detected the problem or verified the result

I compared the fixed labels in `cache_cases.yaml` with the per-case results in
`threshold_sweep.json` and checked the total-cost calculation separately. I
also reviewed the multi-agent output to confirm that validation improved from
1 of 4 correct answers to 4 of 4 before the lessons were kept.

## 4. What I changed and why it works now

I used the measured threshold results in the metrics table and retained the
original case labels. I also kept the reusable lessons only after the
validation results showed improvement without changing the held-out test data.
