
## (1) What I used an AI assistant for and what I did myself
I used an AI assistant (specifically ChatGPT) to help create index.css (as I tried to focus more on understanding the backend code), verify script and the seed script (since it needed to be automated). I also used it to help with understanding the homework instructions (to make sure I follow the intended pipeline). The assistant also helped with code-review, debugging, and polishing some sentences in the report. This homework was on the learning curve for me, and the assistant helped me understand where everything fits in the bigger picture. The analysis and observations were primarily my own. I also had some fun with the RAG section!

## (2) One AI-produced output that was wrong/unsuitable, or one thing I independently verified
The initial draft for the call_llm() function, which was AI-assisted, used Qwen’s default reasoning behavior and allowed a long response. For this local RAG task, the first generation request timed out after 180 seconds, so the configuration was unsuitable for this setting. 

## (3) How I detected the problem or verified the result
The retrieval step completed and printed the top retrieved chunk, but the program stopped during the LLM request with:
```
TimeoutError: timed out
```
The traceback showed that the timeout occurred at urlopen() inside call_llm(), not during PDF indexing or ChromaDB retrieval.

## (4) What I changed and why it works now
I updated the Ollama request to include:
```
"think": False,
"options": {
    "temperature": 0,
    "num_predict": 256,
},
```
I also increased the request timeout from 180 to 300 seconds. Disabling extended reasoning and limiting the maximum answer length made the responses appropriate for the short RAG questions. After this change, the k = 1, k = 3, and k = 5 sweep and the full six-question comparison completed and saved their JSON outputs.