# S09 — LangChain ReviewBench (wiki 재사용)

- 원자료: `raw/langchain-reviewbench.md`; canonical 보존본: `/work/llm-wiki/raw/mission-m-2026-001/langchain-reviewbench.md`
- 성격: LangChain 자체 코드베이스의 real PR feedback 기반 benchmark. 일반 소프트웨어 전반으로의 대표성은 입증하지 않는다.

## 핵심 주장과 근거
1. **주장:** 실제 reviewer가 잡은 issue를 평가하려면 synthetic bug가 아니라 real PR history에서 substantive·verifiable finding을 curate해야 한다. [원문 L20–30]
   - **근거:** trusted reviewer comment를 후보로 삼고 LLM gate 뒤 human review를 거쳐, change가 도입한 실제 issue이면서 verifier로 판정 가능한 comment만 유지했다. [L21–26]
2. **주장:** ReviewBench는 frozen context와 local GitHub stub을 사용해 live GitHub 의존 없이 재현성을 확보한다. [L31–35]
   - **근거:** agent는 seeded repository를 inspect해 location/title/explanation 구조의 finding을 제출하며 hidden LLM-as-judge verifier가 curated baseline과 대조한다. [L31–35]
3. **주장:** basic common harness에서 현재 agent는 real-code-review finding의 다수를 놓친다. [L36–40]
   - **근거/수치:** 59 tasks, 64 baseline issues, task당 3 attempts; strongest run이 baseline issue 약 30%를 recover했다고 보고한다. [L31, L36–37]
4. **주장:** 모델·도구 추가뿐 아니라 review process를 안내하는 prompt가 성능에 영향을 줄 수 있다. [L38–40]
   - **근거:** tuned Luna는 새 도구 없이 PR change→surrounding dependency→caller/test/related implementation 검증을 지시한 prompt만 추가했다. [L38–40]

## 정의·방법론
- coverage는 같은 code path의 같은 underlying problem 식별 여부; wording 자체가 scoring target은 아니다. [L34–35]
- score는 coverage와 precision. [L34]

## 사용 경계·상충 표시
- LLM-as-judge hidden verifier 및 LangSmith mono-repo 기준선이므로 judge calibration·domain transfer는 독립 검증 필요.
- `S01`의 standardized harness가 common baseline에는 적절하나 maximum elicitation을 뜻하지 않는다는 구분과 일치한다.
