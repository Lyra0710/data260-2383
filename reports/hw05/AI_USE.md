# AI Use

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant for explanations, debugging guidance, code structure suggestions, and help interpreting the homework requirements. I also used it to create automated scripts for verify and reproducible instructions file. I entered the code, ran the commands, tested the API and MCP tools, reviewed the outputs, and made the final decisions about the implementation.

## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

An initial MCP setup used the MCP 1.x `FastMCP` import while the development command installed MCP 2.x. This caused the server to fail to start.

## 3. How I detected the problem or verified the result

I read the terminal traceback, which identified the MCP version mismatch. I then pinned the MCP dependency to a version below 2 and confirmed that all tools appeared in MCP Inspector.

## 4. What I changed and why it works now

I used the MCP 1.x-compatible dependency constraint and tested all four tutorial tools and all three domain tools. I also verified the retry behavior, offline tests, local Ollama agent loop, safety rule, and final test results.