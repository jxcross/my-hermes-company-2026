# 04. MVP SPEC — 미션 A: `research-trend-report`

> 작성일: 2026-08-02 · 상태: SPEC 확정본 (Stage 1에서 구현)
> 관련: [`02_company_design.md`](./02_company_design.md) · [`03_mission_pipeline_and_workflow.md`](./03_mission_pipeline_and_workflow.md)

이 문서는 회사의 **1호 미션**(최신 연구·기술 동향 분석 보고서)을 처음부터 끝까지 완주시키기 위한
파이프라인·체크리스트·검증 게이트·완료 조건을 정의한다. 목적은 **시스템이 실제로 돌아감**을 증명하고,
LLM Wiki 복리 루프의 씨앗을 심는 것이다.

---

## 1. 미션 개요

| 항목 | 내용 |
|------|------|
| Mission ID | 예: `M-2026-001` |
| 유형 | `research-trend-report` |
| 요청자 | Sam (Founder) |
| 목표 | 지정 주제(예: 최근 3개월 Agentic AI/LLM 동향)의 핵심 자료를 조사·검증·종합해 보고서 생산 |
| 산출물 | **Markdown 보고서(Git)** + **Slack 요약** + **LLM Wiki 반영** |
| 방법론 | PRISMA식 체계적 문헌조사 + 근거등급 (Skill) |
| 오케스트레이션 | Hermes Kanban (task=단계, task_links=게이트) |

### 완료 조건 (Completion Criteria) — "무엇을 했나"가 아니라 이 조건 충족으로 종료
- [ ] 주요 자료 N편 이상 검토 (미션별 지정, 예: 논문/공식문서 20편+)
- [ ] 핵심 주장은 **독립 출처로 교차검증**됨
- [ ] 적용 후보/시사점 도출 + **불확실성·반대근거** 명시
- [ ] **모든 주장에 출처** 포함
- [ ] LLM Wiki에 raw→wiki 반영 및 index/log 갱신
- [ ] Reviewer 독립 검토 통과

### 제약 (constraints)
- 공개 자료만 사용, 유료 자료 무단 접근 금지, robots/allowlist 준수
- 출처 없는 주장 제외
- 비용 상한 준수(초과 시 Sam 승인)

---

## 2. 파이프라인 (11단계)

표기: **소유**=산출물 생산 profile, **검증**=게이트 판정 주체. 체크리스트 미충족 시 Kanban `blocked`.

| # | 단계 | 소유 | 산출물 | 체크리스트(요지) | 검증 게이트 |
|---|------|------|--------|------------------|-------------|
| 1 | **Scoping** | Solomon+Sam | 미션 스펙(목표·완료조건·제약·N) | 완료조건 측정가능? 제약 명시? 주제 범위 합의? | **Sam 승인**(브레인스토밍) |
| 2 | **Search Strategy** | Scout | 검색식·소스 목록·기간 | 관심범위 커버? 최근성 필터? allowlist? | Solomon |
| 3 | **Collection** | Scout | `raw/`에 원자료+메타데이터(URL·수집일·발행일) | 원문 보존? 출처·날짜 기록? robots 준수? | 자동/Solomon |
| 4 | **Dedup·Relevance** | Curator | 선별 목록(중복 제거·관련성 점수) | 중복 제거? 관련성 기준 적용? 제외 사유 기록? | Solomon |
| 5 | **Deep Analysis** | Reader | 자료별 핵심 분석(주장·근거 분리) | 주장/근거 분리? 핵심 수치·정의 추출? | Solomon |
| 6 | **Cross-Verify** | **Fact-Checker (≠Reader)** | 검증표(주장별 독립출처 대조) | 핵심 주장 교차검증? 상충 표시? | Fact-Checker 판정 + Solomon |
| 7 | **Synthesis** | Synthesizer | 기술 분류·성숙도·적용 후보 | 불확실성·반대근거 포함? 후보 근거? | Solomon |
| 8 | **Report Draft** | Writer | Markdown 보고서(출처 포함) | 모든 주장에 출처 링크? 구조 완결? | Solomon |
| 9 | **Independent Review** | **Reviewer (≠Writer)** | 리뷰 결과(수정 요청/승인) | 반증 검토? 완료조건 충족? 출처 정확? | Reviewer 판정 |
| 10 | **Wiki Update** | Curator | raw→wiki 컴파일 + reflection + index/log | grounding 불변식? Lint 통과? 상충 반영? | Lint(자동)+Solomon |
| 11 | **Deliver** | Solomon | Slack 요약 + Git 커밋 링크 | 완료조건 전체 충족? | **Sam**(외부공개 시 승인) |

> 단계 6·9는 **작성자와 다른 profile**이 검증한다(핵심: 작성자 ≠ 검증자). 필요 시 6단계는 Kanban P3(다수 검증자→집계)로 강화 가능.

### 2.1 템플릿·이중 게이트 (2026-08-03, docs/11 Pilot 반영)
이 11단계는 이제 **선언적 템플릿** `templates/trend-report.yaml`로 정의되고 `scripts/instantiate_template.py`가 Kanban 그래프로 번역한다(하드코딩 `build_pipeline.sh` deprecated). 검증 게이트(6·9)는 **이중**이다:
- **객관 게이트(Python, `scripts/gates/`)**: `recency_check`(인용 최신성 비율) · `source_balance`(출처 taxonomy 균형). LLM 없이 exit 0/1, 우회 불가.
- **LLM 검증자**(Fact-Checker/Reviewer의 `VERDICT: PASS|FAIL`): 의미적 판정. `gate_keeper.py`가 두 신호를 결합(객관 FAIL이면 자동 FAIL).
- **`raw/sources.yaml` 계약**(Scout 방출): 각 소스 `id·title·url·published_year·source_type·collected_at·status·seminal?`. `source_type` taxonomy = `academic·vendor·research_org·standards·news`(정책은 template의 `source_balance_policy`, 미션별 조정). 인간용 `raw/sources.md` 표와 병행.
- 정책(`recency_policy`·`source_balance_policy`)은 Scoping이 `SCOPE.md`에 명시하고 `reports/<MID>/pipeline.json`에도 기록됨.

---

## 3. Kanban 구성 (task 매핑)

- 미션 1건 = Kanban **task 11개**(단계별), `task_links`로 1→2→…→11 의존 연결.
- 병렬 가능 구간: 3(Collection)·5(Deep Analysis)는 자료별 **subagent 팬아웃**으로 내부 병렬.
- **게이트 = task_links**: 앞 단계 `done` 전에는 다음 task `ready` 안 됨.
- **Sam 승인(1·11) = block**: 해당 task를 blocked로 두고 `#approvals`에 승인 요청 → unblock 시 진행.
- **검증 반려**: 검증 task가 실패 판정 → 대상 산출물 task를 `blocked` + comment 사유 → 보완 후 재개.
- 진행 상태 변경은 **gateway watcher가 Slack `#mission-log`에 알림**.

---

## 4. 에이전트(profile) 구성

| profile | 역할 | 주요 도구(MCP/도구) |
|---------|------|---------------------|
| **Solomon** | 기획·디스패치·게이트 검증·보고 | Kanban, Slack, 메모리 |
| **Scout** | 검색·수집 | 웹 검색, 브라우저 |
| **Reader** | 논문/문서 심층 분석 | 브라우저, PDF, 파일 |
| **Fact-Checker** | 교차검증(≠Reader) | 웹 검색 |
| **Synthesizer** | 종합·분류·후보 도출 | 파일, 코드실행(표 정리) |
| **Writer** | 보고서 집필 | 파일 |
| **Reviewer** | 독립 검토(≠Writer) | 파일, 웹 검색 |
| **Curator** | 중복제거·Wiki 관리 | karpathy-llm-wiki skill, Git(wiki repo) |

> 단계 내부 병렬은 각 profile이 **subagent**로 팬아웃. profile은 미션을 거치며 **역할 메모리가 누적**되어 다음 미션에서 더 잘 수행(성장).

---

## 5. 저장 위치

| 산출물 | 위치 |
|--------|------|
| 보고서(Markdown) | 회사 Git repo (예: `reports/M-2026-001/report.md`) |
| 원자료·컴파일 지식 | **별도 llm-wiki repo** (`raw/`, `wiki/`, `reflections/`) |
| 미션 상태·검증 이력 | Hermes Kanban (SQLite, 영구) |
| 요약·승인·알림 | Slack `#ceo-office`·`#approvals`·`#mission-log` |

---

## 6. 성장 지표 연결 (이 미션에서 수집)
- 소요 시간, 검증 반려 횟수(재작업률), 최종 보고서의 출처 중 **기존 Wiki 재사용 비율**(1호 미션은 0에서 시작 → 이후 미션에서 상승 관찰).

---

## 7. 검증(이 SPEC이 완료되었다고 볼 조건)
- Slack에서 Sam이 주제를 던지면 Solomon이 미션 스펙을 제시(1단계) →
  Kanban 파이프라인이 돌아 →
  출처 포함 Markdown 보고서가 Git에 커밋되고 Slack 요약이 오며 →
  llm-wiki repo에 raw/wiki/reflection이 반영됨 →
  완료 조건 체크리스트가 모두 충족됨.
