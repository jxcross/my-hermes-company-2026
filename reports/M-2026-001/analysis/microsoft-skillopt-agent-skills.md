# SkillOpt: Agent skills as trainable parameters — 분석 노트

## 자료 식별
- 자료: raw/microsoft-skillopt-agent-skills.md
- 원문 URL: https://www.microsoft.com/en-us/research/blog/skillopt-agent-skills-as-trainable-parameters/
- 발행일/수집일: 2026-06-30 / 2026-08-02 (raw/microsoft-skillopt-agent-skills.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: agent skill file을 frozen target model 외부의 trainable parameter로 다루면 model weights 변경 없이 reliability를 높일 수 있다.
   - 근거: SkillOpt가 “skill file as a trainable parameter outside a frozen target model”이라고 설명 (raw/microsoft-skillopt-agent-skills.md:18-20,24-25).
2. 주장: SkillOpt는 52 evaluation cells 모두에서 best 또는 tied-best였다.
   - 근거: 6 benchmarks, 7 target models, 3 execution modes에 걸친 52 cells 결과를 제시 (raw/microsoft-skillopt-agent-skills.md:20,31).
3. 주장: bounded edits, validation gating, rejected-edit feedback, slow/meta updates가 uncontrolled prompt drift를 막는다.
   - 근거: 해당 구성요소와 strict validation gate, rejected-edit buffer, epoch-wise slow/meta update 설명 (raw/microsoft-skillopt-agent-skills.md:21,27-29).
4. 주장: optimized skills는 model scale, harness, related task 전이를 보인다.
   - 근거: cross-harness transfer 사례: Codex에서 훈련한 spreadsheet skill을 Claude Code에 적용해 22.1→81.8(+59.7), 직접 Claude Code 훈련 80.4보다 약간 높다고 제시 (raw/microsoft-skillopt-agent-skills.md:34-35).

## 핵심 수치·정의·방법론
- 평가 매트릭스: 6 benchmarks(SearchQA, SpreadsheetBench, OfficeQA, DocVQA, LiveMathematicianBench, ALFWorld), 7 target models, 3 execution modes(direct chat, Codex, Claude Code), 총 52 cells (raw/microsoft-skillopt-agent-skills.md:31).
- GPT-5.5 direct chat 평균: 58.8→82.3, +23.5점; oracle 대비 +5.4점 (raw/microsoft-skillopt-agent-skills.md:31).
- 절차 benchmark gains: SpreadsheetBench 41.8→80.7, OfficeQA 33.1→72.1, LiveMathematicianBench 37.6→66.9 (raw/microsoft-skillopt-agent-skills.md:31).
- agentic loops: GPT-5.5 Codex +24.8, Claude Code +19.1 over no skill (raw/microsoft-skillopt-agent-skills.md:31).
- compactness: median final skill length 약 920 tokens, accepted edits 1~4개, OfficeQA +39.0은 single accepted edit (raw/microsoft-skillopt-agent-skills.md:36).

## 상충·불일치 표시
- LangChain Deep Agents v0.7은 base prompt/tool descriptions/todos를 줄여도 성능 유지 가능하다고 주장한다 (raw/langchain-deep-agents-v0-7.md:18,24-29,35). SkillOpt는 skill 파일을 별도 최적화해 성능을 크게 높인다고 주장한다. 둘 다 “불필요한 prompt/token 증가”를 경계하지만 한쪽은 축소, 한쪽은 검증된 skill 추가/최적화에 초점이 있어 직접 판정하지 않음.
