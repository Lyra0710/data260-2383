# HW3 — Retrieval Metrics

## Metric definitions

- **Top-1 cosine:** mean explicit cosine similarity between each question and the highest-ranked retrieved chunk.
- **Mean @5 cosine:** mean of the five explicit cosine similarities for each question, averaged across the five questions.
- **Recall @5:** proportion of questions for which the question's expected source appears among the top five retrieved results.
- **Mean latency:** mean recorded retrieval latency in milliseconds across the five questions. This is retrieval latency as recorded by the experiment; it is not an end-to-end application latency measurement.

## Results

| Technique | Nodes | Average chunk length (characters) | Top-1 cosine | Mean @5 cosine | Recall @5 | Mean latency (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Semantic | 21 | 2,213.95 | 0.6267 | 0.5579 | 5/5 (100%) | 9.37 |
| Sentence-window | 254 | 183.04 | 0.5962 | 0.5634 | 5/5 (100%) | 12.96 |
| Token | 120 | 461.91 | 0.6339 | 0.5844 | 5/5 (100%) | 17.72 |

## Recorded observations

- All three techniques retrieved the expected source within the top five for all five graded questions.
- Token chunking had the highest mean top-1 cosine, highest mean @5 cosine, and highest mean latency among the three techniques in this run.
- Semantic chunking had the lowest mean latency in this run.
- The results cover five questions and one recorded run per technique/question combination. They do not establish that one chunking method will perform best on other corpora or query sets.

## Reproduction

Run the retrieval experiment and then regenerate the aggregate CSV:

```bash
python code/rag/retrieval_experiment.py
python code/rag/summarize_results.py
```

The raw JSON files and the aggregation script are the source for the values in the results table.
