# AI Use

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant to help me read the assignment requirements, review my project against the rubric, and format the results from my saved experiment data into Markdown tables. I ran the local model experiments and the five-turn client conversation myself. I also checked the raw files, terminal output, and final project files before adding anything to the report. I also used chatgpt and Claude as an assistant to help me code the agentic parts of the project.

## 2. One AI-produced output that was unsuitable

The AI assistant initially told me that I needed to refactor `agents_demo.py` so that it also used the Part 4 model adapter. That suggestion was too broad for the way the assignment is organized: `agents_demo.py` is used for Parts 2 and 3, while Part 4 specifically uses `src/model_client.py` with `hw1_client.py`.

## 3. How I detected the problem

I caught this by checking the section headings and deliverables in the assignment PDF. Part 2 asks for `agents_demo.py`, while Part 4 separately asks for a reusable adapter and a small command-line demo that imports it. I confirmed that `hw1_client.py` imports and calls `src/model_client.py`.

## 4. What I changed and why it works now

I did not make an unnecessary change to `agents_demo.py`. Instead, I kept the Part 4 work focused on `hw1_client.py` and `src/model_client.py`. This matches the Part 4 deliverable because the command-line client sends its model requests through the reusable adapter.

