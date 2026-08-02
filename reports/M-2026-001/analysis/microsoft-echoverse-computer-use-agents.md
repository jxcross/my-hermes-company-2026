# Echoverse: Deep, evolving environments for computer-use agents — 분석 노트

## 자료 식별
- 자료: raw/microsoft-echoverse-computer-use-agents.md
- 원문 URL: https://www.microsoft.com/en-us/research/blog/echoverse-deep-evolving-environments-for-computer-use-agents/
- 발행일/수집일: 2026-07-30 / 2026-08-02 (raw/microsoft-echoverse-computer-use-agents.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: 컴퓨터-use 에이전트 훈련에는 단순한 환경 수보다 깊이, capability targeting, co-evolution이 핵심이다.
   - 근거: 세 레버로 Depth, Capability targeting, Co-evolution을 제시하고 “none of them raw environment count”라고 설명 (raw/microsoft-echoverse-computer-use-agents.md:33-34).
2. 주장: Echoverse는 12개 training worlds로 9B 모델 성능을 거의 두 배로 높였다.
   - 근거: 10개 deep domain worlds와 2개 capability worlds를 구축했고, 전체 12개로 훈련한 9B 모델이 36.5%에서 67.1%로 상승했다고 제시 (raw/microsoft-echoverse-computer-use-agents.md:19).
3. 주장: shallow worlds는 도움이 되지 않고 deep worlds가 개선을 만든다.
   - 근거: 같은 사이트의 shallow/deep builds 비교에서 shallow 훈련은 regress, deep 훈련은 improve라고 설명 (raw/microsoft-echoverse-computer-use-agents.md:20,45,50).
4. 주장: 날짜 선택기와 nested filters 같은 특정 UI control을 다양하게 훈련하면 미훈련 domain에도 전이된다.
   - 근거: datepicker ID 60.0%→82.6%, held-out 34.0%→54.0%; filter held-out 62.8%→84.1%; Online-Mind2Web 29.5%→34.3% (raw/microsoft-echoverse-computer-use-agents.md:43-47).
5. 주장: database-grounded verifier가 screenshot 기반 판정보다 조작·오판 가능성을 줄인다.
   - 근거: task answer key를 실제 DB SQL query에서 만들고, write는 before/after DB diff로 평가한다고 설명 (raw/microsoft-echoverse-computer-use-agents.md:36-39).

## 핵심 수치·정의·방법론
- 정의: world = environment + tasks + verifier (raw/microsoft-echoverse-computer-use-agents.md:32).
- 구성: 12 training worlds = 10 deep domain worlds + 2 capability worlds(date pickers, nested filters) (raw/microsoft-echoverse-computer-use-agents.md:19).
- 성능: 9B model 36.5%→67.1%, GPT-5.4와 14점 이내 (raw/microsoft-echoverse-computer-use-agents.md:19).
- workflow 깊이: EchoStay booking은 약 87 routes, 23 tables를 거치며 tasks는 종종 5~20 actions deep (raw/microsoft-echoverse-computer-use-agents.md:42).
- 공개 범위: 4개 worlds(EchoStay, EchoForge, datepicker, nested-filter) 코드·데이터·grounded graders 공개 (raw/microsoft-echoverse-computer-use-agents.md:24,59).

## 상충·불일치 표시
- LangChain의 “Agents need their own computer”는 production agent 실행환경의 microVM isolation과 보안을 강조한다 (raw/langchain-agents-own-computer.md:35,47-51). Echoverse는 훈련/평가용 합성 world와 DB-grounded grading을 강조한다. 초점 차이이며 직접 충돌로 판정하지 않는다.
