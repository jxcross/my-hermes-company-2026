# Evaluating code review agents with ReviewBench — 분석 노트

## 자료 식별
- 자료: raw/langchain-reviewbench.md
- 원문 URL: https://www.langchain.com/blog/evaluating-code-review-agents-with-reviewbench
- 발행일/수집일: 2026-07-31 / 2026-08-02 (raw/langchain-reviewbench.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: 코드 리뷰 에이전트 평가는 내부 review standards를 반영하는 benchmark가 부족해 어렵다.
   - 근거: “Code review is hard to evaluate… benchmarks… don’t incorporate our internal review standards” (raw/langchain-reviewbench.md:19).
2. 주장: ReviewBench는 실제 PR feedback에서 curated reviewer findings를 만들어 substantive defects 회복 능력을 평가한다.
   - 근거: trusted reviewers의 merged PR comments에서 candidate findings 수집, LLM gate와 manual review로 concrete/verifiable findings만 유지 (raw/langchain-reviewbench.md:20-25).
3. 주장: 현재 models + basic harness는 curated reviewer findings 대부분을 놓친다.
   - 근거: strongest runs recover about 30% of baseline issues (raw/langchain-reviewbench.md:35-36).
4. 주장: prompt/review 방법 변경만으로도 성능 개선 가능성이 있다.
   - 근거: Luna tuned configuration은 새 tools 없이 structured review prompt/high reasoning effort를 사용했고, agent review 방식 변경이 중요하다고 설명 (raw/langchain-reviewbench.md:37-39).

## 핵심 수치·정의·방법론
- benchmark 규모: 59 tasks, 64 baseline issues (raw/langchain-reviewbench.md:30).
- task format: Harbor format; frozen PR context, local GitHub stub로 frozen PR metadata/diff 제공, live GitHub 의존 제거 (raw/langchain-reviewbench.md:30-32).
- 제출 형식: issue location, title, explanation의 structured list (raw/langchain-reviewbench.md:32).
- scoring: coverage와 precision. coverage는 same underlying problem in same code path를 식별하면 covered; LLM-as-judge hidden verifier 사용 (raw/langchain-reviewbench.md:33-34).
- 실행: 59 tasks에서 동일 base Deep Agents harness, task당 3 attempts; custom review-specific prompt 제외 (raw/langchain-reviewbench.md:35).
- matched comparison: 20 tasks, task당 3 attempts (raw/langchain-reviewbench.md:37).

## 상충·불일치 표시
- Microsoft SkillOpt는 skill/prompt layer 최적화가 큰 성능 향상을 낸다고 주장한다 (raw/microsoft-skillopt-agent-skills.md:31). LangChain ReviewBench도 “new prompt”만으로 개선 가능성을 언급하지만, 기본 harness는 여전히 약 30% baseline issue 회복에 그친다고 한다 (raw/langchain-reviewbench.md:36-39). 세부 benchmark가 달라 직접 비교 판정하지 않음.
