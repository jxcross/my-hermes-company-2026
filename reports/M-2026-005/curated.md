# M-2026-005 · 선별목록 (Stage 4 Dedup·Relevance 판정)

> 작성: 2026-08-05 / Curator / t_b62286c9

## 판정 요약을 줄 요약

11건 수집 → 11건 선택(selected), 0건 제외(rejected). 중복 없음.

| 분류 | 최소 요건 | 현재 selected | 판정 |
|---|---:|---:|---|
| peer_reviewed | ≥6 | 6 | 유지(6/6 정족수; reject 시 역전) |
| preprint | ≥2 | 3 | 유지(all relevant_q 매핑) |
| survey | ≥1 | 2 | 유지(all relevant_q 매핑) |
| dataset_code | — | 0 | (scope 외부; stage6에서 재검토 가능) |
| standards | — | 0 | (scope 외부; stage6에서 재검토 가능) |
| 웹/검색결과 | — | 0 | 원문 후보 아님(운영 원칙 준수) |

- **총 N=11** (/≥9 / recent=full=100%)
- **reject 불가 사유:** peer_reviewed가 정족수 6과 동일하므로, 어떤 항목을 제거해도 연구질문 매핑 관련성 판단이 달란 경우 stage6에서 peer_reviewed 부족으로 역전됨. preprint 3/ survey 2는 모두 2개 이상 RQ와 직접 관련되므로 추가 여유분 유지.

## 상세 판정표

| ID | 제목 | source_type | relevant_q | dedup status | relevance |
|---|---|---|---:|---|---|
| dhuliawala2024 | Chain-of-Verification Reduces Hallucination in LLMs | peer_reviewed | Q1-2, Q2-1 | unique / no overlap | CoVe 검증자 독립 질문/검토 순서의 핵심 사례 |
| gao2023 | RARR: Researching and Revising What LM Say Using LMs | peer_reviewed | Q1-2, Q3-1 | unique (Luyu Gao shared with madaan2023 but different paper) | 자기 검토 루프 + factual ground-truth 기준 |
| min2023 | FActScore: Fine-grained Atomic Evaluation of Factuality | peer_reviewed | Q1-2 | unique / distinct metric | 원자적 사실 정합성 측정 프레임워크 |
| madaan2023 | Self-Refine: Iterative Refinement with Self-Feedback | peer_reviewed | Q1-3, Q3-1 | unique (different from gao2023 despite shared author) | 도구 외부 자기 피드백 기반 수정의 대표 사례 |
| manakul2023 | SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection | peer_reviewed | Q1-2, Q2-1, Q3-1 | unique / distinct from FActScore | 외부 참조 없는 자기 정합성 검출 |
| wu2024 | Large Language Models Can Self-Correct with Key Condition Verification | peer_reviewed | Q1-2, Q3-1 | unique / executable verification approach | 실행 가능 조건 검증(symoblic gate)으로 self-correct 판정 |
| gokhale2025 | LogicGuard: Temporal Logic based Critics for Embodied Agents | preprint | Q1-1, Q2-3 | unique / novel temporal logic approach | time-logic 기반 rules-based gate — rules vs LLM 책임 경계 핵심 |
| yamauchi2025 | Empirical Study of LLM-as-a-Judge: Design Choices Impact Reliability | preprint | Q3-2, Q4-1 | unique / direct to SCOPE targets | judge 설계 선택지(비교방식·순서)의 신뢰도 영향 측정 |
| kim2024 | Can LLMs Produce Faithful Explanations For Fact-checking? (Multi-Agent Debate) | preprint | Q1-2, Q2-2 | unique / distinct from single-agent self-reflection | multi-agent debate의 메시지 경계·역할 분담 사례 |
| li2024 | Survey: LLM-based Multi-Agent Systems (workflow/infrastructure/challenges) | survey | Q2-1, Q2-2, Q3-3 | unique scope vs wang2024 | multi-agent workflow/infra 구조 서베이 |
| wang2024 | A Survey on Large Language Model Based Autonomous Agents | survey | Q3-1, Q4-3 | unique (broader scope than li2024) | 자율 에이전트 self-reflection/correction/evaluation 광범위 서베이 |
