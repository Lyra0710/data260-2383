# AI Use

## 1. What I used an AI assistant for and what I did myself

I used an AI assistant for help interpreting the homework requirements, designing the materiality policy and golden test cases, writing Muse prompts, debugging test behavior, and organizing the report. I edited the files, ran the commands, performed the Muse tests, reviewed the outputs, collected the screenshots, and made the final decisions about the policy and evaluation.

## 2. One AI-produced output that was wrong/unsuitable, or one thing I independently verified

An initial adversarial fixture used a credential-request link on `example-newswire.example`, which was already an approved host in `sources.json`. Because of this, `watch.py fetch` did not block the link at the allowlist step.

## 3. How I detected the problem or verified the result

I checked the Muse output after running `watch.py fetch`. It showed that the host was allowlisted and that the request failed only because the fictional site was unreachable, not because it was blocked by the source policy.

## 4. What I changed and why it works now

I changed the adversarial fixture link to `desk.example-newswire.example/priority`, which is not an approved source. I reran the test and verified that `watch.py fetch` returned `blocked: true`. I also independently verified the restart recovery, duplicate suppression, prompt-injection handling, HIGH-alert trace, golden-set results, and final metrics.