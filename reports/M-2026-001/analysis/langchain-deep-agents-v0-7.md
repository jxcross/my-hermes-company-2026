# Deep Agents v0.7 — 분석 노트

## 자료 식별
- 자료: raw/langchain-deep-agents-v0-7.md
- 원문 URL: https://www.langchain.com/blog/deep-agents-v0-7
- 발행일/수집일: 2026-07-29 / 2026-08-02 (raw/langchain-deep-agents-v0-7.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: Deep Agents v0.7은 base harness를 단순화해 comparable performance에서 base input tokens를 65% 줄였다.
   - 근거: release summary와 “~6k → ~2k” 설명 (raw/langchain-deep-agents-v0-7.md:18,24-29).
2. 주장: 현대 모델에서는 good tool schemas가 few-shot examples보다 낫고, 반복 instruction은 유의미한 reinforcement를 제공하지 않는다.
   - 근거: Anthropic guide와 v0.7 관찰의 공통 finding으로 제시 (raw/langchain-deep-agents-v0-7.md:20-23).
3. 주장: TodoListMiddleware 기본 포함은 필요하지 않아 opt-in으로 전환했다.
   - 근거: evals에서 planning prompt/write_todos tool이 성능을 유의미하게 개선하지 않았고, todos disabled가 slightly better rewards/lower cost였다고 설명 (raw/langchain-deep-agents-v0-7.md:27,37).
4. 주장: configurability 요청을 반영해 middleware/default harness stack 변경 가능성을 높였다.
   - 근거: FilesystemMiddleware override, SummarizationMiddleware thresholds, base prompt override 요청과 v0.7 변경 설명 (raw/langchain-deep-agents-v0-7.md:39-44).

## 핵심 수치·정의·방법론
- token 감소: default-agent turn base input tokens 65%, 약 6k→2k (raw/langchain-deep-agents-v0-7.md:28-29).
- tool descriptions trimming: builtin tool descriptions 43% 감소 (raw/langchain-deep-agents-v0-7.md:25-26).
- 평가 suite: Autonomous, Conversational, Long-context 3 categories (raw/langchain-deep-agents-v0-7.md:30-33).
- 모델 매트릭스: gpt-5.6-luna, gemini-3.6-flash, claude-sonnet-4-6, claude-opus-4-8 (raw/langchain-deep-agents-v0-7.md:34).
- 결과 예: gpt-5.6-luna tokens -34%, cost -15%, reward +4%; claude-sonnet-4-6는 일부 autonomous tasks로 cost increase exception (raw/langchain-deep-agents-v0-7.md:35).

## 상충·불일치 표시
- 이 자료는 fewer base tokens와 opt-in todos를 주장한다. Kanban/장기작업 운영에서는 별도 작업관리(todo/board)가 여전히 필요할 수 있으나, 자료 자체는 Deep Agents harness 평가 맥락에 한정된다. 다른 운영문맥과 직접 충돌로 판정하지 않음.
