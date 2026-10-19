# AI Use for HW6

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant to help interpret the homework requirements, plan the implementation, draft small code changes, and explain terminal commands. I personally ran the application, reviewed the raw outputs, captured the screenshots, updated the run log, and committed and pushed each incremental change.

## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

During the MongoDB memory demonstration, the local model incorrectly changed the fundraiser plan by suggesting alternative non-Monday dates even though the user had stated November 20. It also sometimes applied a fundraiser detail, such as bringing water, to unrelated tennis events.

## 3. How I detected the problem or verified the result

I reviewed the saved conversation and memory JSON instead of relying only on a fluent response. The generated summary and reply text showed the unsupported date change and the inappropriate transfer of fundraiser details to tennis scheduling.

## 4. What I changed and why it works now

I strengthened the extraction, summary, and response prompts to preserve stated dates, times, venues, and preferences exactly, not infer missing details, and report conflicts rather than silently resolve them. I also added fixed probes and deterministic scoring. The final experiment replies retained the stated fundraiser date, time, and venue, and the saved probe scores make remaining omissions visible.
