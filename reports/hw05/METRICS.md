# Part 5 Metrics

Model: `qwen3:8b`  
Provider: Local Ollama  
Maximum steps: 3

| Scenario | Steps | Stop reason | Tool calls |
|---|---:|---|---:|
| What fixtures are scheduled at venue 1? | 2 | normal_completion | 1 |
| Give me details for fixture 1. | 2 | normal_completion | 1 |
| Search for fixtures containing SJSU. | 2 | normal_completion | 1 |
| What is the total number of available slots at venue 2? | 2 | normal_completion | 1 |

All four Ollama scenarios completed normally within the maximum step limit. Each scenario used one domain-tool call followed by a final response.