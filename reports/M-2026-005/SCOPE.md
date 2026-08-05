---
recency_policy:
  cutoff_year_offset: -3
  recent_ratio: 0.5
  hard_block_year_offset: -15
  seminal_exceptions: true
source_balance_policy:
  categories: [peer_reviewed, preprint, survey, dataset_code, standards, web]
  min_per_category:
    peer_reviewed: 6
    preprint: 2
    survey: 1
    dataset_code: 0
    standards: 0
    web: 0
  hard_block_if_missing: false
---

# M-2026-005 — 이중 게이트 설계 학술 논문 스코프

> 유형: `academic-paper` (아키타입 B, 11단계) · 주제: **LLM 에이전트 파이프라인에서 객관적 규칙 기반 게이트와 LLM 검증자의 이중 게이트 설계 및 역할 분담**

## 연구 목적과 연구 질문

### 목적
객관적으로 재현 가능한 규칙 기반 게이트와 의미·맥락 판단을 수행하는 LLM 검증자를 같은 LLM 에이전트 파이프라인에 배치할 때, 두 계층의 책임·판정 순서·실패 처리·독립성을 명확히 하는 학술 논문 초고를 작성한다. 핵심은 한 계층이 다른 계층을 대체하지 않도록 하면서, 검증 가능성과 판단 유연성 사이의 설계 근거를 제시하는 것이다.

### 연구 질문 (RQ)
- **RQ1.** LLM 에이전트 파이프라인에서 규칙 기반 객관 게이트와 LLM 검증자는 각각 어떤 검증 주장과 실패 유형을 담당해야 하는가?
- **RQ2.** 두 게이트를 어떤 순서와 의존관계로 배치해야 규칙 준수, 사실·인용 검증, 논증·문체 검토를 혼동 없이 분리할 수 있는가?
- **RQ3.** 작성자와 검증자를 분리하고 독립 검토를 두는 구조가 자기검증·확증 편향·검증 누락 위험을 어떻게 줄이는가?
- **RQ4.** 이중 게이트 설계의 한계(규칙의 불완전성, LLM 판정의 비결정성·설명 가능성 한계, 재검토 비용)는 무엇이며, 어떤 경우에 사람 승인 게이트가 필요한가?

## 예상 기여

1. 규칙 기반 게이트와 LLM 검증자를 **대체 관계가 아닌 상호보완적 이중 게이트**로 정의하는 설계 프레임을 제시한다.
2. 객관 게이트의 역할을 정책 준수의 기계 판정으로, LLM 검증자의 역할을 주장·근거 정합성과 논증 품질의 독립 판정으로 구분한 책임 매트릭스를 제시한다.
3. 집필 전 `Cross-Verify`와 집필 후 `Independent Review`의 두 검증 지점, 그리고 작성자·검증자 분리 원칙을 논문 구조와 파이프라인 구조 양쪽에서 명시한다.
4. 이중 게이트 설계의 **한계와 적용 조건**을 체계화한다. 규칙의 불완전성, LLM 판정의 비결정성·설명 가능성 한계, 재검토 비용, 그리고 사람 승인 게이트가 필요한 지점을 정리하여 RQ4에 답한다.

## 범위

### 포함
- LLM 에이전트 연구·집필 파이프라인에서의 이중 게이트 개념, 역할 분담, 순서, 의존관계 및 반려·수정 루프의 문헌 기반 분석.
- 규칙 기반 객관 게이트와 LLM 검증자의 장점·한계·상호보완 관계에 관한 학술적 논의.
- 객관 게이트 유형이 담당할 검증 주장과 설계 선택을 문헌 기반으로 분석한다. `recency_check`와 `source_balance`는 본 파이프라인에서 사용하는 사례로 언급하되, 논문의 범위를 이 두 유형으로 한정하지 않는다.
- `Cross-Verify`에서의 사실·인용·출처 정합성 검토와 `Independent Review`에서의 논증 구조·주장-근거 정합·문체·용어 일관성 검토.
- 학술 논문 초고의 연구 질문, 관련 연구, 설계/분석, 논의, 결론 및 한계.


### 제외
- 실제 에이전트 런타임 실행, 모델 호출, 프롬프트 최적화, 모델 벤치마크, 코드 변경 또는 게이트 스크립트 수정.
- 외부 데이터 수집·업로드, 외부 API 호출, 계정·권한·환경설정 변경, 배포, 결제, 커밋·푸시, Slack/이메일 전송 등 외부 부수 효과.
- 특정 LLM 제공자·모델의 우열 또는 실제 운영 파이프라인의 성능·안전성에 관한 실증적 보장.

## 이중 게이트와 역할 분리

| 층위 | 담당 | 판정 대상 | 논문에서의 분석 관점 |
|---|---|---|---|
| 객관 게이트 | 규칙 기반 검사 | 정책 형식과 출처 집합의 기계 판정 | 재현 가능한 규칙 판정이 맡을 수 있는 검증 주장, 적용 조건 및 한계를 분석한다. `recency_check`, `source_balance`는 파이프라인 사례다. |
| LLM 검증자 1 | Fact-Checker | 원자료-노트-주장의 사실·인용 정합성 | 사실·인용 정합성의 의미 판단과 독립 교차검증의 역할을 분석한다. |
| 작성자 | Writer | outline에 따른 섹션 초고 | 작성과 검증 책임의 분리가 자기검증 위험을 줄이는 방식을 분석한다. |
| LLM 검증자 2 | Reviewer | 초고의 논증, 주장-근거 정합, 문체, 완료조건 | 논증·문체 검토의 의미 판단, 재검토 비용 및 사람 승인 필요 조건을 분석한다. |

- **명시적 Writer/Verifier 분리:** Writer는 `writer` 프로필이며, Fact-Checker는 `fact-checker`, Reviewer는 `reviewer` 프로필이다. Writer는 자신의 초고에 대한 최종 검증자일 수 없고, `reviewer ≠ writer`를 유지한다. 또한 Fact-Checker는 분석 작성자인 `reader`와 분리한다.
- 객관 게이트는 LLM 판정의 근거를 보조하는 정책 검사이지 LLM 검증자의 의미 판단을 대체하지 않는다. 반대로 LLM의 `VERDICT: PASS|FAIL`은 객관 게이트의 결과를 무시하거나 우회할 수 없다.


## 완료 기준 (Measurable Completion Criteria)

- [ ] `SCOPE.md`의 YAML frontmatter가 본 미션의 `pipeline.json` 정책과 정확히 일치한다.
- [ ] RQ 4개가 본문에서 각각 답해지고, 예상 기여 4개가 역할 분담, 배치, 독립성, 한계·적용 조건을 각각 다룬다.
- [ ] 핵심 설계 주장마다 1차 학술 출처 또는 검증 가능한 원출처 인용이 연결된다.
- [ ] 포함/제외 범위가 학술적 논의 범위와 실증·운영 작업의 경계를 명확히 구분한다.
- [ ] 수집·분석·검증·집필·검토 산출물 경로가 아래 경로 계약에 선언된다.
- [ ] Writer, Fact-Checker, Reviewer의 역할과 `Writer ≠ Reviewer`, `Reader ≠ Fact-Checker` 분리가 명시된다.
- [ ] 선택된 문헌의 최소 N과 출처 분배, 최신성 기준이 아래 정책을 충족하도록 검색·선별 계획에 반영된다.
- [ ] 연구 범위의 한계가 명시되고, 설계 논증과 후속 실증 평가의 관계가 구분된다.
- [ ] 결과 문서는 UTF-8 일반 Markdown으로 저장되며, 요구된 연구 질문·기여·범위·제약·정책·경로 계약을 일관되게 제시한다.

## 제약

- 공개적으로 접근 가능한 학술 자료와 공식 공개 자료만 사용한다. 유료벽 우회, 무단 접근, robots 정책 위반은 금지한다.
- 핵심 설계 주장은 1차 학술 출처 또는 검증 가능한 원출처에 연결한다. 웹 자료는 선택적 맥락·발견 보조이며 핵심 결론의 단독 근거가 될 수 없다.
- 모든 선별 자료는 `id`, 제목, 저자, `published_year`, venue, DOI/URL, `source_type`, `collected_at`, `status`를 `raw/sources.yaml`에 기록한다. 발행 연도가 없는 자료는 선별하지 않는다.
- 논문 초고의 사실 주장에는 인용 식별자를 붙이고, 불확실성·상충 결과·검증 불가능한 주장을 구분한다.
- 외부 입력은 0개이며, 이 명세가 허용하는 것은 지정된 경로의 문서 산출물뿐이다. 외부 시스템 변경 및 외부 부수 효과는 0개여야 한다.
- 사람 승인 게이트는 파이프라인의 승인 절차일 뿐 자동 실행 권한이 아니다. 특히 집필 개시 전 outline 승인과 최종 Deliver 승인은 별도로 다룬다.

## 최신성 정책 (Recency)

기준 연도는 파이프라인 실행 시점의 현재 연도로 해석한다.

- `cutoff_year_offset: -3`: **현재 연도 - 3 이상** 발행된 자료를 recent로 정의한다.
- `recent_ratio: 0.5`: 선별·인용 자료 중 **50% 이상**이 recent여야 한다.
- `hard_block_year_offset: -15`: **현재 연도 - 15 미만**의 자료는 원칙적으로 선별하지 않는다.
- `seminal_exceptions: true`: 위 hard block보다 오래된 자료는 기초적·원전적 필요성을 `seminal: true`로 명시한 경우에만 예외로 사용할 수 있다.
- 발행 연도 미상 자료는 핵심 근거 및 선별 N에서 제외한다.

## 출처 균형 정책 (Source Balance)

| 출처 유형 | 최소 선별 수 | 주된 용도 |
|---|---:|---|
| `peer_reviewed` | 6 | 방법·이론·실험·검증 근거 |
| `preprint` | 2 | 최신 연구와 아직 정식 출판 전인 논의 |
| `survey` | 1 | 개념 계보와 연구 지형 정리 |
| `dataset_code` | 0 | 필요 시 구현·재현 맥락 |
| `standards` | 0 | 필요 시 정책·표준 맥락 |
| `web` | 0 | 발견 보조 또는 제한적 맥락 |

- 허용된 출처 범주는 정확히 `peer_reviewed`, `preprint`, `survey`, `dataset_code`, `standards`, `web`이다.
- `hard_block_if_missing: false`이므로 범주 최소치 미달은 자동 차단하지 않는다. 다만 미달 사유와 연구질문·결론에 미치는 영향을 Cross-Verify와 Independent Review에서 기록한다.
- 같은 조직 또는 같은 주장 계열의 자료만으로 핵심 결론을 확정하지 않으며, 출처 유형과 근거의 독립성을 검토한다.

## N 목표

- **N = 최소 9편, 목표 9편 이상**의 `status=selected` 문헌을 선별한다.
- 최소 N=9는 필수 최소 분배 `peer_reviewed` 6편 + `preprint` 2편 + `survey` 1편의 합계다.
- N 충족은 최신성 비율 및 출처별 최소치 충족과 별개로 확인한다. `dataset_code`, `standards`, `web`은 선택 항목이므로 N의 필수 하한을 늘리지 않는다.

## 산출물 경로 계약

- `/work/company/reports/M-2026-005/SCOPE.md` — 본 스코프 및 정책 명세
- `/work/company/reports/M-2026-005/raw/search-strategy.md` — 검색식, DB, 기간, 출처 유형 분배
- `/work/company/reports/M-2026-005/raw/sources.yaml` — 병합된 선별 자료 목록과 정책 판정 입력
- `/work/company/reports/M-2026-005/analysis/<id>.md` — 자료별 구조화 분석 노트
- `/work/company/reports/M-2026-005/analysis/_index.md` — 분석 노트 색인
- `/work/company/reports/M-2026-005/verify/verification.md` — Fact-Checker의 교차검증, 객관 게이트 결과, `fact_checker_verdict`
- `/work/company/reports/M-2026-005/synthesis/` — 논지, 주장-근거 매핑, 용어집을 포함한 종합 자료
- `/work/company/reports/M-2026-005/outline.md` — 승인 대상 논문 목차와 섹션별 claim→evidence 매핑
- `/work/company/reports/M-2026-005/draft.<section>.md` — Writer의 섹션별 초고
- `/work/company/reports/M-2026-005/draft.md` — 병합된 학술 논문 초고
- `/work/company/reports/M-2026-005/review/review.md` — Reviewer의 독립 검토와 `reviewer_verdict`
- `/work/company/reports/M-2026-005/references.bib` — `draft.md`에서 실제 인용된 항목의 BibTeX 내보내기

## 연구 범위의 한계

본 논문은 이중 게이트 설계의 역할 분담, 배치, 독립성 및 적용 조건에 관한 설계 논증과 문헌 기반 분석을 제시한다. 실제 에이전트 런타임에서의 성능, 비용, 안전성 또는 LLM 판정 품질을 실증적으로 평가하지 않으며, 이러한 평가는 다양한 과업·모델·조직적 승인 절차를 포함한 후속 연구 과제다.
