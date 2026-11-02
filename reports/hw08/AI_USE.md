# AI Use for HW8

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant to help interpret the homework requirements, inspect the existing project, suggest small Kafka code changes, and explain terminal commands. I personally started the Docker, Kafka, and Ollama services, created the required topics, ran the request/response tests, ran the Planner-Writer-Reviewer pipeline, ran the failure experiments, captured screenshots, reviewed the terminal output, updated the run log. I also used the assistant to improve the text grammar and clarity of the report.


## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

An early AI suggestion assumed that the existing MySQL Fixture database should be reused for Part 1. That was unsuitable because the HW8 instructions explicitly require the Kafka worker to store fixtures in a plain Python dictionary for this exercise.


## 3. How I detected the problem or verified the result

I reread the instructions and compared the proposed storage approach with the requirements instead of relying on the existing HW7 application structure. I also independently verified the final worker behavior by running CREATE_FIXTURE, GET_FIXTURE, validation-error tests, the Planner-Writer-Reviewer pipeline, and the Kafka smoke test.

## 4. What I changed and why it works now

I changed the Part 1 worker to store fixtures in a plain Python dictionary and generate UUID entity IDs in the worker. The final implementation preserves correlation IDs, returns clean validation errors, and passed the Kafka round-trip smoke test. I also independently ran the duplicate-delivery, consumer-restart, poison-message/dead-letter, and two-partition ordering experiments. The final logs and raw files show the expected results.
