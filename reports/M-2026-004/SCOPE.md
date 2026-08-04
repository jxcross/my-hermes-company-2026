---
recency_policy:
  cutoff_year_offset: -2
  recent_ratio: 0.6
  hard_block_year_offset: -5
  seminal_exceptions: true
source_balance_policy:
  categories: [academic, vendor, research_org, standards, news]
  min_per_category:
    academic: 2
    vendor: 2
    research_org: 1
    standards: 0
    news: 0
  hard_block_if_missing: false
---

# M-2026-004 — 미션 스펙 (1단계 Scoping 산출물)

> 유형: `trend-report` (full 11단계) · 요청자: Sam · 승인: 2026-08-03
> 파이프라인: Scoping → Search Strategy(scout) → Collection(scout) → Dedup·Relevance(curator) → Deep Analysis(reader) → **Cross-Verify(fact-checker, ≠reader)** → Synthesis(synthesizer) → Report Draft(writer) → **Independent Review(reviewer, ≠writer)** → Wiki Update(curator) → Deliver(Solomon+Sam)

## 주제
**온디바이스 LLM 추론 최적화 동향** — 스마트폰·PC·엣지 장치 등 자원 제약 환경에서 LLM을 실행하기 위한 모델 압축·양자화·추론 런타임·하드웨어 가속·메모리/전력 최적화의 최근 연구와 제품화 동향.

범위에는 저비트 양자화·KV cache/메모리 관리·speculative decoding·컴파일러/런타임·NPU/GPU/모바일 가속 및 실제 배포 성능 평가를 포함한다. 단순 클라우드 서빙 최적화, 학습·파인튜닝만을 위한 기법, 출처로 검증할 수 없는 벤치마크 주장은 범위 밖이다.

## 목표
공개 자료를 우선 llm-wiki에서 재사용 가능 여부를 확인한 뒤 조사·교차검증·종합하여, 온디바이스 LLM 추론의 기술적 메커니즘과 실제 배포 선택 기준을 구분한 **출처 포함 Markdown 동향 보고서**를 생산한다. 보고서는 AI-Native Company가 지연시간·메모리·전력·품질·지원 하드웨어의 trade-off를 근거 기반으로 판단할 수 있게 해야 한다.

## 완료 조건 (Completion Criteria)
- [ ] llm-wiki를 먼저 query하여 관련 기존 지식을 식별하고, 재사용 항목·부족분·재사용률을 기록한다.
- [ ] 선별된 공개 자료 **10편 이상**(재사용+신규)을 검토하고, 각 항목의 URL·발행일/연도·수집일·출처 유형·선별 상태를 `raw/sources.yaml`에 기록한다.
- [ ] 최소 출처 분배를 충족한다: academic 2편 이상, vendor 2편 이상, research_org 1편 이상. 특정 벤더의 홍보성 주장만으로 핵심 결론을 만들지 않는다.
- [ ] 양자화/압축, 메모리·KV cache 최적화, 런타임·하드웨어 가속, 품질·성능·전력 평가를 각각 다루고, 각 영역의 성숙도와 적용상 trade-off를 명시한다.
- [ ] 최소 3개 대표 배포 경로(예: 모바일/PC/엣지 또는 서로 다른 런타임·하드웨어 조합)를 비교하되, 비교 가능한 측정 조건과 비교 불가능한 조건을 구분한다.
- [ ] 핵심 주장마다 1차 출처를 연결하고, 독립 출처로 확인 가능한 핵심 주장은 Fact-Checker가 확인/상충/미검증으로 판정한다.
- [ ] 보고서는 출처 없는 사실 주장을 포함하지 않으며, 모델 크기·정밀도·하드웨어·프롬프트/시퀀스 길이 등 성능 수치의 전제와 불확실성·벤치마크 한계를 명시한다.
- [ ] Writer와 독립된 Reviewer가 완료조건·인용 정확성·정책 준수를 검토하여 `VERDICT: PASS`를 낸다.
- [ ] Curator가 가치 있는 원자료와 정제 지식을 llm-wiki에 반영하고 reflection 및 재사용률을 갱신한다.
- [ ] Deliver 단계에서 Sam에게 보고서 요약·핵심 권고·검증 결과를 제시한다.

## 제약
- 공개적으로 접근 가능한 자료만 사용한다. 유료벽 우회, 무단 접근, robots 정책 위반은 금지한다.
- 1차 출처(논문·공식 기술문서·런타임/하드웨어 문서·시스템 카드)를 우선하며, 뉴스는 발견 보조 또는 시장 맥락용으로만 사용한다.
- 성능 주장은 원문에 명시된 모델·정밀도·장치·측정 조건을 함께 기록한다. 조건이 다른 결과를 직접 순위화하거나 일반화하지 않는다.
- 개인정보, 비공개 프롬프트/대화, API 키를 수집·보고서·wiki에 포함하지 않는다.
- 외부 공개, 유료 API/자원 증설, 계정·보안 설정 변경, 법적 약속, 운영 배포는 범위 밖이며 Sam의 별도 승인 없이는 수행하지 않는다.
- 온디바이스 제약과 직접 연결되지 않는 일반 LLM 연구·클라우드 전용 서빙 동향은 배경으로만 다루고, 결론의 근거 수에는 포함하지 않는다.

## Recency 정책
기준일: **2026-08-03**.

- recent는 **2024년 이후(포함)** 발행 자료로 정의하며, 선별·인용 자료의 **60% 이상**이어야 한다.
- **2021년 이전** 자료는 `seminal: true`로 명시된 기초/원전 예외가 아니면 선별하지 않는다.
- 2021–2023 자료는 최근 자료가 설명하지 못하는 개념적 계보·비교 기준에 한해 사용하고, 왜 필요한지 분석에 명시한다.
- 발행일을 확인할 수 없는 출처는 핵심 근거에서 제외한다.

## Source-balance 정책
| 범주 | 최소 선별 수 | 용도 |
|---|---:|---|
| academic | 2 | 방법론·실험·벤치마크 근거 |
| vendor | 2 | 런타임·하드웨어·제품화 및 운영 문서 |
| research_org | 1 | 독립 평가·재현성·효율성/리스크 관점 |
| standards | 0 | 모바일/엣지 관련 표준·호환성 기준 보강(선택) |
| news | 0 | 발견 보조·시장 맥락(선택) |

- 범주별 최소치 미달은 자동 차단은 아니나, Cross-Verify 및 Independent Review에서 사유와 영향이 명시된 예외 판정이 필요하다.
- 출처 유형은 `academic`, `vendor`, `research_org`, `standards`, `news` 중 하나로 기록한다.

## N
최소 **10편**, 권장 **12–15편**(신규+재사용 합산). 위 최소 출처 분배와 recency 비율은 N 충족과 별도로 적용한다.

## 산출물 위치
- `/work/company/reports/M-2026-004/raw/` — 원자료, 검색전략, `sources.yaml`
- `/work/company/reports/M-2026-004/analysis/` — 자료별 주장/근거 분석
- `/work/company/reports/M-2026-004/verify/` — Fact-Checker 교차검증표
- `/work/company/reports/M-2026-004/synthesis/` — 종합·분류·적용 판단
- `/work/company/reports/M-2026-004/review/` — 독립 검토
- `/work/company/reports/M-2026-004/report.md` — 최종 보고서
- `/work/llm-wiki` — 재사용 지식 및 reflection (curator 담당)
