# M-2026-003 Independent Review

## 판정

**수정요청(changes-requested)**

`VERDICT: FAIL`

보고서는 핵심 주장과 불확실성의 연결은 대체로 양호하지만, SCOPE 완료조건의 영역별 성숙도 명시가 최종 보고서에서 불완전하고, 출처 메타데이터 원장에 상호 모순되는 발행연도 기록이 남아 있다. 이 두 항목은 승인 전 수정이 필요하다.

## 완료조건 대조

| SCOPE 완료조건 | 판정 | 검토 결과 |
|---|---|---|
| llm-wiki 선행 query·재사용 항목·부족분·재사용률 기록 | 충족 | `raw/curated.md:6-17,44-46`에 query 대상, 재사용 4건, 신규/부족분, 공식 재사용률 4/13(30.8%)을 기록했다. |
| 공개 자료 10편 이상 및 URL·발행연도·수집일·유형·상태 기록 | 부분 충족 | selected 12건은 필수 필드가 있고 `raw/sources.md`와 `raw/sources.yaml`에 기록됐다. 다만 제외 자료 OpenAI 항목의 발행연도가 두 원장 사이에서 모순된다(차단 사유 2). |
| 출처 분배 academic≥2, vendor≥2, research_org≥1 | 충족 | `sources.yaml` selected 기준 academic 4, vendor 4, research_org 2, standards 2. |
| 최근 자료 60% 이상, 2021년 이전 제한 | 충족 | selected 12/12가 2024년 이후다. |
| 메모리 아키텍처·컨텍스트 최적화·평가/신뢰성·보안/프라이버시 각각의 성숙도와 trade-off | **미충족** | 네 영역은 모두 다루지만 최종 보고서에서 성숙도 표기가 일관되지 않는다. 구조화·진화형 memory만 `연구 단계`로 명시되고(`report.md:25`), 평가/신뢰성(`:17-23`), context(`:31-35`), 보안·프라이버시(`:37-43`)에는 해당 영역의 성숙도 판정이 없다. trade-off·한계는 대체로 공개됐다. |
| 핵심 주장별 1차 출처 및 Fact-Checker 판정 | 충족 | 핵심 문단과 수치표가 1차 출처 및 `verify/verification.md` ID에 연결된다. 검증표는 확인 20·상충 0·미검증 14로 분류했다. |
| 출처 없는 사실 주장 금지, 불확실성·반대근거·벤치마크 한계 공개 | 충족 | `report.md:74-84`가 미검증 14건, MemoryAgentBench 버전 차이, MCP authorization 범위, 벤치마크 층위, NIST/IETF 지위 차이를 공개한다. 미검증 자체를 실패 사유로 삼지 않았다. |
| Writer와 독립된 Reviewer 검토 | 충족(본 단계) | `pipeline.json:117-143`에서 Writer=`writer`, Reviewer=`reviewer`로 분리돼 있다. 판정은 FAIL이다. |
| Wiki Update 및 Deliver | 후속 단계 | 각각 10·11단계의 완료조건이므로 현재 9단계 보고서 품질 판정의 선행 차단 사유로 삼지 않는다. |

## 출처 정확성 표본 감사

| 보고서 주장 | 표본 출처 대조 | 결과 |
|---|---|---|
| LongMemEval 5개 능력·500개 질문(`report.md:21,50`) | ICLR 2025 공식 페이지가 다섯 능력과 500개 질문을 명시한다. 30% 하락·기법 우위는 저자 평가임도 보고서가 분리했다. | 적합 |
| Anthropic의 context 정의·고신호 context(`report.md:33`) | Anthropic 원문이 context를 inference 시 포함되는 전체 token 집합으로 정의하고 작은 고신호 token 집합을 원칙으로 제시한다. 보고서는 제공자 운영 패턴으로 한정했다. | 적합 |
| Deep Agents 6K→2K, 65%, tool description 43%, reward CI(`report.md:35,53`) | LangChain 원문과 ExplainX·daily.dev가 수치·변경점을 재기술하며, 원문은 모든 모델 reward CI가 0을 포함한다고 명시한다. 보고서는 성능 동등/향상 입증으로 승격하지 않았다. | 적합 |
| persistent memory poisoning 위험(`report.md:39`) | Unit 42는 장기 메모리에 간접 prompt injection이 저장되고 후속 세션에서 대화 이력을 유출하는 PoC를 공개한다. | 적합 |
| New America의 dashboard·retention·memory-free mode·compartment·purpose tag·audit 권고(`report.md:39`) | 원문이 해당 권고를 실제로 나열한다. 보고서는 효과가 검증된 통제가 아닌 정책 제안으로 제한했다. | 적합 |
| NIST AI 600-1의 위험관리 지위(`report.md:41,84`) | NIST 공식 RMF 페이지는 600-1을 조직 목표·우선순위에 맞춘 GAI risk-management action profile로 설명한다. | 적합 |
| IETF draft 4개 1차원·55개 2차 metric 및 비표준 지위(`report.md:43,54,72,84`) | Datatracker는 수치와 함께 `Active Internet-Draft (individual)`, `not endorsed by the IETF`, `no formal standing`을 명시한다. | 적합 |
| MemoryAgentBench 용어 차이(`report.md:23,51,78`) | ICLR/OpenReview 보존 문서는 `selective forgetting`, 현행 GitHub와 고정 HF README는 `Conflict Resolution`을 사용한다. 보고서는 version/commit 고정을 요구한다. | 적합 |

링크 구조 점검: Markdown 링크 125개, 고유 외부 링크 31개, 고유 로컬 링크 5개이며 로컬 대상 누락은 0개였다.

## 차단 사유 및 구체적 수정 지시

1. **네 필수 영역의 성숙도 판정을 최종 보고서에 명시하라.** `report.md:15-43` 또는 별도 요약표에서 메모리 아키텍처, 컨텍스트 최적화, 평가/신뢰성, 보안/프라이버시 각각에 일관된 성숙도 척도와 판정을 부여하고, 각 판정의 근거 및 적용 trade-off를 같은 행/문단에서 추적 가능하게 연결해야 한다. `synthesis/synthesis.md:12-21`의 분류를 단순 참조만 하지 말고 최종 보고서가 완료조건을 자체 충족하도록 해야 한다.
2. **OpenAI 제외 항목의 발행연도 메타데이터 모순을 해소하라.** `raw/sources.yaml:113-121`은 `published_year: 2025`를 기록하면서 `dedup_status: excluded_missing_published_year`라고 하고, `raw/sources.md:21`은 원문에서 발행일을 확인하지 못했으며 URL의 연도를 근거로 쓰지 않았다고 명시한다. 확인 불가 값을 확정 연도로 기록하지 않도록 기계 원장 표현을 수정하고 두 원장을 일치시켜라. 수정 후 selected 12건의 recency·분배 집계를 다시 검증하라.
3. **수정 후 재검토용 검증 증거를 남겨라.** 보고서의 네 영역 성숙도 표기 위치, 수정된 OpenAI 메타데이터 필드, selected 자료 수·유형 분포·recency 재계산 결과를 변경 내역에 명시해야 한다.

위 사항을 수정하기 전에는 승인할 수 없다.
