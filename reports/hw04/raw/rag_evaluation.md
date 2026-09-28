# HW4 Part 4 Evaluation

## Per-question results

| Question | Configuration | Correct retrieval | Correct answer | Grounded | Refused when needed | Notes |
|---|---|---|---|---|---|---|
| Q1 | No RAG | N/A | Yes | N/A | N/A | Correct general definition, but no document evidence was provided to the model. |
| Q1 | Basic RAG | Yes | Yes | Partial | N/A | Correct answer, but it added “stateless” beyond the retrieved chunk text. |
| Q1 | ContextRAG | Yes | Yes | Partial | N/A | Cited Sources 1 and 2, but added unsupported details such as specific HTTP methods. |
| Q2 | No RAG | N/A | Yes | N/A | N/A | Correct general knowledge answer, with no supplied evidence. |
| Q2 | Basic RAG | Yes | Yes | Partial | N/A | Retrieved both Pydantic and Uvicorn evidence, but added an unstated `uvicorn main:app --reload` command. |
| Q2 | ContextRAG | Yes | Yes | Yes | N/A | Correctly combined Pydantic validation from Source 3 with Uvicorn from Source 1. |
| Q3 | No RAG | N/A | Yes | N/A | N/A | Correct general answer, but no retrieved evidence was used. |
| Q3 | Basic RAG | Yes | Yes | Yes | N/A | Correctly described FastAPI as a backend framework. |
| Q3 | ContextRAG | Yes | Yes | Yes | N/A | Used consistent FastAPI evidence from two course documents. |
| Q4 | No RAG | N/A | No | N/A | N/A | Interpreted “session” as a class meeting instead of the course’s technical usage. |
| Q4 | Basic RAG | Yes | Yes | Yes | N/A | Identified the database-model and LLM-model meanings. |
| Q4 | ContextRAG | Yes | Yes | Yes | N/A | Clearly distinguished the two supported meanings with sources. |
| Q5 | No RAG | N/A | No | N/A | No | Hallucinated a typical soccer-team size instead of refusing. |
| Q5 | Basic RAG | Expected: no relevant evidence | Yes | Yes | Yes | Correctly said the context did not contain the answer. |
| Q5 | ContextRAG | Expected: no relevant evidence | Yes | Yes | Yes | Used the exact required refusal sentence. |
| Q6 | No RAG | N/A | No | N/A | No | Gave a general Bitcoin prediction disclaimer instead of a document-based refusal. |
| Q6 | Basic RAG | Expected: no relevant evidence | Yes | Yes | Yes | Correctly identified that the context had no relevant information. |
| Q6 | ContextRAG | Expected: no relevant evidence | Yes | Yes | Yes | Used the exact required refusal sentence. |

## Configuration summary

| Configuration | Answer accuracy | Faithfulness / grounding | Format compliance | Robustness on Q5 and Q6 |
|---|---:|---|---|---|
| No RAG | 3/6 | No document grounding | No citations | 0/2 refusals |
| Basic RAG | 6/6 | Mostly grounded; Q1 and Q2 added unsupported details | Raw-context answers; no source citations required | 2/2 refusals |
| ContextRAG | 6/6 | Strongest grounding; Q1 still added some unsupported REST details | Source citations and exact refusal format | 2/2 refusals |