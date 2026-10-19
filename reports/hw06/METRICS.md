# HW6 Part 3 Metrics

## Method

Each setting used the same 30-message conversation and five fixed probes in fresh sessions. Means below use the 30 conversation requests only; the deterministic criterion checks and per-probe results are in `raw/probe_scores.json`. Token components are character/4 estimates, while total prompt and completion tokens are returned by the local model response metadata.

## Short-term Memory Comparison

| Setting | Mean prompt tokens/turn | Mean completion tokens/turn | Mean latency (ms) | Mean probe quality (1–5) |
| --- | ---: | ---: | ---: | ---: |
| SHORT_TERM_N=4 | 518.0 | 48.9 | 9244.7 | 4.6 |
| SHORT_TERM_N=12 | 710.9 | 45.0 | 10057.1 | 4.6 |
| SHORT_TERM_N=30 | 1086.2 | 45.2 | 11804.7 | 4.8 |
| Summary-aware compaction (N=30 to 4 after summary) | 496.4 | 41.8 | 8779.7 | 4.8 |

## Mean Prompt Component Tokens per Conversation Turn

| Setting | System primer | Long-term summary | Short-term window | Episodic facts |
| --- | ---: | ---: | ---: | ---: |
| SHORT_TERM_N=4 | 73.0 | 265.2 | 140.3 | 55.4 |
| SHORT_TERM_N=12 | 73.0 | 261.8 | 342.7 | 55.4 |
| SHORT_TERM_N=30 | 73.0 | 256.4 | 743.0 | 55.4 |
| Summary-aware compaction (N=30 to 4 after summary) | 73.0 | 262.0 | 122.0 | 55.4 |

## Compaction Effect vs. N=30

The compaction policy reduced mean prompt tokens by 54.3% and mean latency by 25.6%. Mean probe quality changed from 4.8 to 4.8.

## Estimated Cost for 10,000 30-turn Conversations

Input tokens are priced at $1/million and output tokens at $5/million. The best setting is compaction because it has the lowest measured cost while retaining a 4.8/5 probe score. The worst setting is N=30 because it has the highest measured cost.

| Setting | Input cost | Output cost | Total cost |
| --- | ---: | ---: | ---: |
| Summary-aware compaction (N=30 to 4 after summary) | $148.92 | $62.70 | $211.62 |
| SHORT_TERM_N=30 | $325.86 | $67.85 | $393.71 |

## Probe Scores

| Run | Identity | Tennis | Fundraiser details | Fundraiser logistics | Memory boundaries | Mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SHORT_TERM_N=4 | 5 | 5 | 5 | 4 | 4 | 4.6 |
| SHORT_TERM_N=12 | 5 | 5 | 5 | 4 | 4 | 4.6 |
| SHORT_TERM_N=30 | 5 | 5 | 5 | 4 | 5 | 4.8 |
| Summary-aware compaction (N=30 to 4 after summary) | 5 | 5 | 5 | 5 | 4 | 4.8 |
