# M-2026-003 · 4 Dedup·Relevance 선별

- 선별일: 2026-08-03
- 범위: AI 에이전트의 메모리·컨텍스트 관리(장·단기 메모리, 컨텍스트 최적화, 멀티에이전트 상태, 평가·신뢰성, 보안·프라이버시) 동향.
- 입력: `sources.yaml`의 원자료 13건. 미션 내부의 canonical URL 중복은 0건이다.
- 기존 지식 query: `/work/llm-wiki/SCHEMA.md`, `index.md`, 최근 `log.md`, 그리고 `[[evolving-knowledge]]`, `[[langchain]]`, `[[metr]]`, `[[agent-governance]]`를 대조했다.
- 판정 원칙: (1) 발행 연도 확인·recency 정책, (2) 미션 주제의 직접성, (3) 기존 wiki와 동일 canonical URL은 신규 근거로 이중 계상하지 않고 재사용 표시, (4) 연도 미확인 자료는 핵심 근거에서 제외한다.
- 이 문서는 중복·관련성·재사용 기록이며, 자료별 주장 종합이나 사실 검증을 수행하지 않는다.

## 결과

- 입력 13건 → 선별 12건(신규 8, 기존 wiki 재사용 4) → 제외 1건.
- 미션 내부 URL 중복: 0건.
- 기존 wiki 원문과 동일 canonical URL의 재사용: 4건. HTML/Markdown/XML 보존 형식이나 수집 시점이 달라 byte hash가 동일하지 않은 경우에도 URL과 원문 제목을 기준으로 같은 출처로 판정했다.
- 공식 재사용률(스키마 분모=새 미션 원자료 전체): **4/13 = 30.8%**.
- 참고: 선별 집합 기준 재사용률은 **4/12 = 33.3%**. 제외된 자료는 신규 수집물이므로 공식 수치와 구분한다.
- 최신성: 선별 12건 모두 2024년 이후(12/12=100%)이며, 최소 출처 분배는 academic 4, vendor 4, research_org 2, standards 2로 충족한다.

## 선별 목록

| ID | 원자료 | 구분 | 관련성 | 근거/후속 사용 경계 |
|---|---|---|---:|---|
| S01 | `locomo-evaluating-very-long-term-conversational-memory.xml` | 신규 | 5/5 | 장기 대화·다중 세션 memory 평가의 학술 원자료. 학술 preprint의 abstract 보존본 범위에서 사용한다. |
| S02 | `longmemeval-benchmarking-chat-assistants.xml` | 신규 | 5/5 | 추출·다중 세션·시간 추론·지식 갱신·abstention을 다루는 장기 memory 평가의 학술 원자료. |
| S03 | `a-mem-agentic-memory-for-llm-agents.xml` | 신규 | 5/5 | 동적 indexing·linking 기반 agentic memory 설계의 학술 원자료. preprint이며 독립 재현 여부는 다음 단계에서 구분한다. |
| S04 | `memoryagentbench-incremental-multi-turn-interactions.xml` | 신규 | 5/5 | incremental multi-turn memory의 retrieval·learning·long-range understanding·forgetting 평가 자료. |
| S05 | `anthropic-effective-context-engineering-for-ai-agents.html` | 신규 | 5/5 | context를 유한 자원으로 보고 구성·관리하는 공식 엔지니어링 자료. 제공자 운영 권고로 취급한다. |
| S06 | `anthropic-effective-harnesses-for-long-running-agents.html` | 신규 | 5/5 | 다수 context window를 넘는 장기 실행의 상태 전달·작업 진행 관리 공식 자료. 제공자 구현 사례로 취급한다. |
| S07 | `microsoft-evolib-evolving-knowledge.html` | 재사용:wiki | 5/5 | raw experience를 reusable knowledge로 정제·재가중하는 memory/knowledge 접근. canonical raw: `/work/llm-wiki/raw/mission-m-2026-001/microsoft-evolib-evolving-knowledge.md`; `[[evolving-knowledge]]`를 우선 참조한다. |
| S08 | `langchain-deep-agents-v0-7.md` | 재사용:wiki | 5/5 | context-engineering 기반 harness 경량화의 공식 제품 자료. canonical raw: `/work/llm-wiki/raw/mission-m-2026-001/langchain-deep-agents-v0-7.md`; `[[langchain]]`을 우선 참조한다. |
| S09 | `metr-frontier-risk-report.html` | 재사용:wiki | 3/5 | 메모리 자체의 설계·성능 근거는 아니나 agent 위험 평가·신뢰성 경계의 독립 보조 자료. canonical raw: `/work/llm-wiki/raw/mission-m-2026-002/metr-frontier-risk-report.md`; `[[metr]]`을 우선 참조한다. |
| S10 | `new-america-ai-agents-and-memory.html` | 신규 | 5/5 | MCP era의 agent memory privacy·power를 다루는 독립 연구기관 자료. 정책 분석이며 구현 효과의 실증 근거로 일반화하지 않는다. |
| S11 | `nist-ai-600-1-generative-ai-profile.pdf` | 신규 | 4/5 | generative AI risk management의 표준·거버넌스 보강 자료. memory-specific 실험 근거는 아니므로 privacy·risk 통제 맥락으로 제한한다. |
| S12 | `ietf-agent-security-benchmark-00.html` | 재사용:wiki | 5/5 | memory/context read-write, shared memory, privacy, poisoning을 포괄하는 agent security evaluation 초안. canonical raw: `/work/llm-wiki/raw/mission-m-2026-002/ietf-agent-security-benchmark.md`; Internet-Draft로만 인용한다. |

## 제외 목록

| 원자료 | 구분 | 제외 사유 |
|---|---|---|
| `openai-for-developers-2025.html` | 신규 | 원문 페이지에서 발행일·연도를 확인할 수 없다. URL의 `2025`는 메타데이터 근거가 아니며 SCOPE의 발행일 확인 요건에 따라 핵심 근거·정량 집계에서 제외한다. |

## 전달 경계

- 다음 단계는 S01–S12만 검토 대상으로 삼는다. S07–S09·S12는 위 canonical wiki raw를 우선 참조하고, 새 수집 사본을 별도 독립 근거로 이중 계상하지 않는다.
- 제외 E01은 발행일이 원문에서 확인되거나 미션의 날짜 제약이 변경될 때에만 재선별한다.
- 재사용 지식은 `[[evolving-knowledge]]`, `[[langchain]]`, `[[metr]]`, `[[agent-governance]]`이며, 공식 재사용률은 4/13(30.8%)이다.
- 이 선별은 주장 정확성·상호 일치·보고서 인용 적합성을 보증하지 않는다. 이는 Deep Analysis 및 Cross-Verify의 책임이다.
