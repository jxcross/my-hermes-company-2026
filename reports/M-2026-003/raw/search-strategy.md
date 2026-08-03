# M-2026-003 — 검색 전략

- 작성일: 2026-08-03
- 단계: Search Strategy (원문 수집·분석은 이 단계의 범위 밖)
- 주제: AI 에이전트 메모리·컨텍스트 관리 동향
- 기준일: 2026-08-03
- 검색 우선순위: 공개 1차 자료(논문·공식 기술문서·독립 연구기관·표준) → 뉴스(발견 보조만)

## 적용 범위와 선별 정책

- 최근성: 2024년 이후 발행 자료를 우선하며, 최종 `selected` 자료 중 60% 이상이어야 한다.
- 2021년 이전은 기초/원전으로 필요하고 `seminal: true`가 명시된 경우만 후보로 남긴다.
- 발행 연도 또는 발행일을 원문에서 확인할 수 없으면 `raw/sources.yaml`에서 `selected`로 기록하지 않는다. 해당 후보는 `excluded` 처리하고 사유를 남긴다.
- 목표 수: 최종 12–15건(최소 10건).
- 최소 출처 분배: academic 2+, vendor 2+, research_org 1+. standards/news는 보강용이다.
- 동일 URL의 미러·재게시물·검색결과 요약은 원문 URL의 보조 발견 경로일 뿐, 별도 원자료로 수집하지 않는다.

## 검색식

| ID | 검색식 | 우선 대상 | 목적 범위 |
|---|---|---|---|
| Q1 | `site:arxiv.org/abs ("LLM agents" OR "AI agents") (memory OR "long-term memory") after:2023-12-31` | academic | 장기·에이전틱 메모리 아키텍처 |
| Q2 | `site:arxiv.org/abs ("memory benchmark" OR LongMemEval OR LoCoMo OR MemoryAgentBench) agent after:2023-12-31` | academic | 평가·신뢰성 |
| Q3 | `site:arxiv.org/abs "context compression" agents OR "context management" agents after:2023-12-31` | academic | 컨텍스트 압축·검색·갱신 |
| Q4 | `site:anthropic.com/engineering "context engineering" agents` | vendor | 공식 컨텍스트 엔지니어링 자료 |
| Q5 | `site:openai.com OR site:developers.openai.com agents (context OR state OR persistence)` | vendor | 공식 에이전트 상태·지속성 자료 |
| Q6 | `site:langchain.com OR site:docs.langchain.com (memory OR filesystem OR summarization) agents` | vendor | 프레임워크 구현·운영 문서 |
| Q7 | `site:microsoft.com/en-us/research (memory OR "evolving knowledge") agents` | vendor | 공식 연구·구현 자료 |
| Q8 | `site:metr.org agent (memory OR context OR state OR "prompt injection")` | research_org | 독립 평가·운영 리스크 |
| Q9 | `site:newamerica.org "AI agents" memory privacy` | research_org | 메모리·프라이버시·거버넌스 |
| Q10 | `site:nist.gov OR site:nvlpubs.nist.gov generative AI profile privacy prompt injection` | standards | 보안·프라이버시 기준 |
| Q11 | `site:ietf.org "agent security" (memory OR context)` | standards | 에이전트 메모리·공유 상태 보안 초안 |
| Q12 | `("agent memory" OR "context engineering") (benchmark OR privacy OR security) 2024..2026` | academic/research_org | 누락 영역 탐색 및 후보 확장 |

## 1차 수집 후보 목록

아래 URL은 수집 단계에서 원문 접근성·발행일·중복 여부를 다시 확인한다. `발행 연도`는 URL/검색 결과에서 확인된 연도만 기재했으며, 정확한 일자는 원문에서 검증한다.

| 우선 | 후보 ID / 예상 원문 파일명 | URL | 발행 연도 | 정규화 출처유형 | 검색식 | 주제 범위 | 상태 |
|---:|---|---|---:|---|---|---|---|
| 1 | `locomo-evaluating-very-long-term-conversational-memory` | https://arxiv.org/abs/2402.17753 | 2024 | academic | Q2 | 메모리 평가 | 수집 대기 |
| 2 | `longmemeval-benchmarking-chat-assistants` | https://arxiv.org/abs/2410.10813 | 2024 | academic | Q2 | 장기 상호작용 메모리 평가 | 수집 대기 |
| 3 | `a-mem-agentic-memory-for-llm-agents` | https://arxiv.org/abs/2502.12110 | 2025 | academic | Q1 | 메모리 아키텍처·갱신 | 수집 대기 |
| 4 | `memoryagentbench-incremental-multi-turn-interactions` | https://arxiv.org/abs/2507.05257 | 2025 | academic | Q2 | 메모리 평가 | 수집 대기 |
| 5 | `anthropic-effective-context-engineering-for-ai-agents` | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 2025* | vendor | Q4 | 컨텍스트 엔지니어링 | 수집 대기 |
| 6 | `anthropic-effective-harnesses-for-long-running-agents` | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | 2025 | vendor | Q4 | 세션 간 상태·핸드오프 | 수집 대기 |
| 7 | `microsoft-evolib-evolving-knowledge` | https://www.microsoft.com/en-us/research/blog/evolib-turning-experience-into-evolving-knowledge/ | 2026 | vendor | Q7 | 경험·지식 갱신 | wiki 재사용 후보 |
| 8 | `langchain-deep-agents-v0-7` | https://www.langchain.com/blog/deep-agents-v0-7 | 2026 | vendor | Q6 | 파일시스템 기반 컨텍스트 관리 | wiki 재사용 후보 |
| 9 | `metr-frontier-risk-report` | https://metr.org/blog/2026-05-19-frontier-risk-report | 2026 | research_org | Q8 | 에이전트 실행 환경·보안 | wiki 재사용 후보 |
| 10 | `new-america-ai-agents-and-memory` | https://www.newamerica.org/insights/ai-agents-and-memory | 미확인 | research_org | Q9 | 메모리·프라이버시 | 수집 대기; 발행일 확인 필수 |
| 11 | `nist-ai-600-1-generative-ai-profile` | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf | 2024 | standards | Q10 | 프라이버시·정보보안 위험 관리 | 수집 대기 |
| 12 | `ietf-agent-security-benchmark-00` | https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html | 2026 | standards | Q11 | 공유 메모리·무결성·보안 평가 | wiki 재사용 후보 |
| 13 | `openai-for-developers-2025` | https://developers.openai.com/blog/openai-for-developers-2025 | 2025* | vendor | Q5 | 지속 상태·대화 상태 | 수집 대기 |

`*` 수집 단계에서 원문에 표시된 날짜/연도를 재검증한다. 재검증 불가 시 `raw/sources.yaml`에는 `status: excluded`로 기록한다.

## 위키 선조회 결과 및 재사용 지시

`/work/llm-wiki`의 `SCHEMA.md`, `log.md`, 전수 키워드 검색을 먼저 수행했다. 직접 재사용 후보 4건이 확인되었다.

| 후보 | 위키 원자료 경로 | 확인된 메타데이터 |
|---|---|---|
| Microsoft EvoLib | `/work/llm-wiki/raw/mission-m-2026-001/microsoft-evolib-evolving-knowledge.md` | URL, 발행일 2026-07-30, 수집일 2026-08-02 |
| LangChain Deep Agents v0.7 | `/work/llm-wiki/raw/mission-m-2026-001/langchain-deep-agents-v0-7.md` | URL, 발행일 2026-07-29, 수집일 2026-08-02 |
| METR Frontier Risk Report | `/work/llm-wiki/raw/mission-m-2026-002/metr-frontier-risk-report.md` | 위키 원자료 존재; 이번 단계에서 URL 원문·발행일 재검증 필요 |
| IETF Internet-Draft | `/work/llm-wiki/raw/mission-m-2026-002/ietf-agent-security-benchmark.md` | URL, 2026-07(일자 미확인), 수집일 2026-08-02 |

수집 단계는 재사용 원자료를 수정하지 않는다. 필요한 경우 원문을 M-2026-003 `raw/`에 새 사본으로 보존하고, 재사용 사실·기존 경로·수집일을 `raw/sources.md`에 기록한다.

## 수집 실행 순서

1. 후보 1–4의 arXiv abstract/HTML 또는 PDF 원문을 수집한다. arXiv의 발행일과 실제 열람한 버전 URL을 보존한다.
2. 후보 5–8·13의 공식 벤더 원문을 수집한다. 페이지 날짜가 없는 지속 갱신 문서는 날짜 미확인으로 표시하고 핵심 근거 후보에서 제외한다.
3. 후보 9–10의 독립 연구기관 원문을 수집한다. 후보 10은 발행일 확인 실패 시 대체 research_org 후보를 Q8/Q9로 추가 탐색한다.
4. 후보 11–12의 표준/초안 원문을 수집한다. IETF 항목은 Internet-Draft임을 유지하고 확정 표준으로 표기하지 않는다.
5. 각 원문을 `raw/<id>.md`에 보존하고 URL·발행일·수집일·출처유형·수집 상태를 기록한다. 이어 `raw/sources.yaml`에 동일 ID로 `selected`/`failed`/`excluded` 상태를 작성한다.
6. 선정 판단이나 중복 제거는 수행하지 않고, 수집 불가·날짜 불명·미러·중복 가능성만 표시해 Curator 단계로 넘긴다.

## 목표 출처 분배(수집 후 선별 전)

| source_type | 목표 후보 수 | 후보 |
|---|---:|---|
| academic | 4 | 1–4 |
| vendor | 5 | 5–8, 13 |
| research_org | 2 | 9–10 |
| standards | 2 | 11–12 |
| news | 0 | 필요 시 발견 보조로만 추가 |

총 13건이며, 각 후보의 발행 연도가 확인되면 모두 2024년 이후여야 한다. 날짜 미확인 후보는 최종 selected 수 및 recent 비율 계산에서 제외한다.
