# Evaluating code review agents with ReviewBench

## 메타데이터
- URL: https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench
- 발행일: 2026-07-31
- 수집일: 2026-08-02
- 출처유형: 공식 블로그/평가
- 수집상태: curl_exit=0; bytes=158745
- 원문 보존 파일: raw/_fetched/langchain-reviewbench.html

## 검색/선정 근거
- 최근 3개월(2026-05~2026-08) 범위 내 공식/1차 공개 자료이며, 에이전트·툴/컴퓨터 유즈·평가·신뢰성 중 하나 이상의 키워드와 관련되어 수집함.

## 원문 텍스트 추출(사실 확인용; 자동 추출)
- Evaluating code review agents with ReviewBench
- Build long-running agents for complex tasks
- Build reliable agents with low-level control
- Quick start agents with any model provider
- There are more code review agents now, and we’ve been building one internally. Code review is hard to evaluate. There aren’t many benchmarks we trust for measuring whether an agent is useful in our review workflow, because they don’t incorporate our internal review standards.
- We wanted a benchmark tied to the kinds of issues our reviewers catch in real PRs. So we built ReviewBench. It is built from real PR feedback in our LangSmith mono-repo. We started with comments from trusted reviewers, curated them into concrete review issues, and turned them into reproducible Harbor tasks.
- We wanted ReviewBench to measure the kinds of issues reviewers actually raise, so we started from real review history instead of writing synthetic bugs from scratch.
- We collected comments from trusted reviewers on merged PRs in our LangSmith codebase and treated them as candidate findings. Many of those comments depended on codebase-specific standards, such as missing tenant constraints on database queries or production crons that needed to follow existing locking patterns. For an agent to find these issues, it needs to reconstruct implicit system contracts from the surrounding code instead of just inspecting the changed lines in isolation.
- Our initial thought was to use raw review comments directly as ground truth labels, but those proved too noisy to use directly. Some are substantive findings, but many are nits or questions. We needed to turn the raw comments into a smaller set of concrete, verifiable findings.
- We only kept comments that identified a real issue introduced by the change and were specific enough for a verifier to evaluate. We passed the unfiltered PR reviews through an LLM gate to flag weak candidates, then manually reviewed each remaining comment.
- This curation is what makes ReviewBench useful as an eval. The benchmark does not ask agents to reproduce everything a trusted reviewer said. It measures whether an agent can recover the substantive defects represented by curated reviewer findings.
- Here are some concrete examples of what these tasks look like.
- One issue involves a database SQL query that fetched and deleted a resource by ID without also checking the tenant. To catch it, the agent needs to recognize a project-level safety rule and apply it to a specific code path.
- Another involves an endpoint migration that dropped a filter present in the original API, changing the endpoint’s behavior. Catching it requires comparing the two implementations and catching the API-parity regression.
- These are the kinds of issues we want ReviewBench to measure. They require more than scanning the changed lines for obvious bugs.
- ReviewBench currently has 59 tasks covering 64 baseline issues. The tasks are written in Harbor format. Harbor gives us a standard task format for the instruction, environment, and verifier. We turned the curated review issues into Harbor tasks using the same eval-engineering workflow described in Towards Automating Eval Engineering .
- At the start of a task, the agent receives the frozen PR context and instructions to review the PR. A local GitHub stub serves the frozen PR metadata and diff, so the task does not depend on live GitHub state.
- The agent can inspect the full seeded repository, then submits a structured list of findings containing each issue’s location, title, and explanation. After submission, the verifier compares those findings against the curated baseline issues.
- ReviewBench scores coverage and precision. Each task has a hidden verifier that uses an LLM-as-judge to compare the agent’s submitted review against the curated baseline.
- Coverage measures whether the agent found the baseline issue. A baseline issue counts as covered when the verifier determines that the agent identified the same underlying problem in the same code path. We score the underlying issue, not the wording of the comment.
- We ran each model with the same base Deep Agents harness across the 59 ReviewBench tasks with three attempts per task. We deliberately omitted a custom review-specific system prompt so the table would compare models under the same minimal scaffolding, providing a common baseline rather than measuring each model’s best tuned performance.
- The main result is that current models with a basic harness still miss most curated reviewer findings. The strongest runs recover about 30% of the baseline issues. Agents generally report valid issues, but they still miss many of the specific issues trusted reviewers caught in real PRs.
- We ran a matched comparison on 20 ReviewBench tasks with three attempts per task. The tuned Luna configuration used high reasoning effort and a structured review prompt. Opus 4.8 and Kimi K3 use the original review harness.
- The tuned configuration did not give Luna any new tools. Like the original configuration, it could read and search the repository but could not run code or shell commands. The only new part was a new prompt. The new prompt instructed Luna to identify what the PR changed, trace how the surrounding system depended on that behavior, and validate its findings against callers, tests, and related implementations.
- For code review agents, better performance can come from changing how the agent reviews, not only from changing the model or adding more tools.
- ReviewBench gives us a starting point for evaluating code review agents against real PR feedback. Next, we want to make it larger and broader.
- Over time, we want ReviewBench to measure whether code review agents can find substantive issues in real changes without adding unnecessary review noise.
- LangSmith, our agent engineering platform, helps developers debug every agent decision, eval changes, and deploy in one click.
- LangSmith Platform LangSmith Observability LangSmith Evaluation LangSmith Deployment LangSmith Fleet LangSmith Sandboxes Deep Agents LangChain LangGraph
