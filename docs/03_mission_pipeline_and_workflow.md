# 03. Mission Pipeline & Workflow Management

> 작성일: 2026-08-02 · 상태: 설계 확정본
> 관련: [`02_company_design.md`](./02_company_design.md) · [`04_mvp_research_trend_report_spec.md`](./04_mvp_research_trend_report_spec.md) · [`hermes_agent_조사.md`](./hermes_agent_조사.md) · [`llm_wiki_조사.md`](./llm_wiki_조사.md)

---

## 1. Mission Pipeline Framework (일급 개념)

소프트웨어 개발이 `도메인정의→PRD→시나리오→ERD→BE→FE→...`처럼 단계별 설계·검증을 거치듯,
**모든 미션은 자신만의 파이프라인을 갖고, 파이프라인을 따라 산출물과 체크리스트를 검증한다.**

### 1.1 Stage 정의
```
Stage = { 입력 → 산출물(deliverable, 소유 profile) → 체크리스트 → 검증 게이트 }
```
- **산출물**: 그 단계가 반드시 만들어야 하는 것 (예: 검색식, 검증표, PRD, ERD, 보고서 초안)
- **체크리스트**: 다음 단계로 넘어가기 전 충족해야 할 조건 (통과해야 진행)
- **검증 게이트**: 통과 판정. **작성자 ≠ 검증자**(다른 profile) + 일부 단계는 **Sam 승인**
- 체크리스트 미충족 → **진행 차단**(되돌아가 보완)

### 1.2 역할 배치
- **Solomon**: Scoping(미션 설계)·Deliver(취합·보고)를 소유 + **모든 단계 게이트 검증·승인**. 산출물 직접 생산 ❌.
- **전문 profile**: 각 단계 산출물을 소유·생산.
- **검증자 분리**: 예) Reader가 분석 → Fact-Checker가 검증 / Writer가 초안 → Reviewer가 리뷰.

---

## 2. Workflow Manager = Hermes 네이티브 Kanban

별도 대시보드·커스텀 관리 시스템을 만들지 않는다. Hermes가 제공하는 **Kanban**이 곧 워크플로우 관리자다.
(근거·조사: [`hermes_agent_조사.md`](./hermes_agent_조사.md), 결정: [`06_design_decision_log.md`](./06_design_decision_log.md))

### 2.1 파이프라인 ↔ Kanban 매핑

| 파이프라인 개념 | Hermes Kanban 기능 |
|-----------------|--------------------|
| 파이프라인 단계 | **task** (제목·본문·할당 profile·상태) |
| 단계 순서·의존 | **task_links** (부모 done → 자식 ready) = **게이트** |
| 산출물 소유자 | task의 **assignee(profile)** — 디스패처가 worker로 실행 |
| 체크리스트·검증 기록 | **task_comment + task_events** (영구 감사추적) |
| 사람(Sam) 승인 | **block / unblock** (human-in-the-loop, 패턴 P5) |
| 검증자 분리 | 산출물 task와 검증 task를 **다른 profile**에 할당 |
| 병렬 단계 | **task fan-out** (패턴 P1) — 형제 task 동시 실행 |
| 진행 알림 | **gateway watcher** → Slack `#mission-log` |

### 2.2 상태 머신 (Kanban 표준)
```
todo → ready → running → done → archived
              ↓
           blocked → (Sam unblock) → ready
```
- 체크리스트 미충족/검증 반려 → 해당 task를 **blocked**로 두고 comment에 사유 기록 → 보완 후 재개.

### 2.3 활용 협업 패턴 (Hermes Kanban 제공)
- **P1 Fan-out**: 병렬 검색·병렬 분석
- **P2 Pipeline**: scout→reader→writer 같은 단계 체인
- **P3 Voting/Quorum**: 다수 검증자 → 집계(중요 주장 교차검증에 활용 가능)
- **P5 Human-in-the-loop**: block→comment→unblock (Sam 승인 게이트)

---

## 3. Skill Library — 표준·안전한 방법론 채택

파이프라인을 맨땅에서 발명하지 않고, **유명하고 검증된 표준 방법론을 Skill로 보유·활용**한다.
Skill은 agentskills.io 표준(Hermes 호환)이며 Git으로 버전관리한다.

| 미션 유형 | 채택 방법론(Skill) | 핵심 |
|-----------|---------------------|------|
| 동향 보고서 (A) | **PRISMA식 체계적 문헌조사** + 근거등급(evidence grading) | 검색→선별→분석→교차검증의 재현 가능한 절차 |
| 학술 논문 (B) | **IMRaD** 구조 + 인용 검증 | Introduction·Methods·Results·Discussion + citation audit |
| 웹 개발 (C/D) | **PRD · 사용자 스토리 · ERD · 아키텍처 · 테스트/보안 리뷰** | 구현 전 설계·검증 파이프라인 |
| 지식 관리 | **karpathy-llm-wiki** (Ingest/Query/Lint) | raw→wiki→reflection 컴파일·검색·점검 |

> Skill은 **버전관리 대상**이다. 미션 실패/재작업 → Reflection → **체크리스트·파이프라인·Skill 개정(버전↑)** → 다음 미션 품질↑ (= 복리 성장 엔진).

---

## 4. Memory / Skill / MCP 거버넌스

| 종류 | 담는 것 | 관리 원칙 |
|------|---------|-----------|
| **Memory** | Sam 선호, 회사 원칙, 고정 환경 사실 (작고 항상 참조) | 소량 유지, 오래된 것 정리. profile별 분리 |
| **Skill** | 반복 가능한 업무 절차(방법론) | Git 버전관리, 추출(`/learn`)·리뷰·폐기 거버넌스 |
| **MCP Tool** | 외부 도구 연결(arXiv·검색·GitHub·Slack) | **profile 단위 권한 스코프** — 역할별 접근 제한 |
| **LLM Wiki** | 논문·기술지식·근거·출처·미션 이력 | 별도 repo, Lint로 무결성 점검 |
| **Mission (Kanban)** | 특정 미션의 단계·상태·검증 이력 | task_events 영구 보존 |

**핵심**: 권한 스코프가 **profile 단위**이므로, 도구 접근 제한(예: 코드 실행 권한은 Implementer만)은 **profile 설계로** 강제한다. "누가 만들고/갱신하고/폐기하는가"의 거버넌스가 성장의 관건.

---

## 5. 파이프라인 예시 (개요)

### 5.1 미션 A `research-trend-report` (상세: [04](./04_mvp_research_trend_report_spec.md))
`Scoping(Solomon+Sam)→Search(Scout)→Collection(Scout)→Dedup·Relevance(Curator)→Deep Analysis(Reader)→Cross-Verify(Fact-Checker)→Synthesis(Synthesizer)→Report Draft(Writer)→Independent Review(Reviewer)→Wiki Update(Curator)→Deliver(Solomon)`

### 5.2 미션 C/D `web-app` (Stage 5+, 개요)
`도메인정의→PRD→사용자시나리오→ERD→아키텍처→Backend→Frontend→테스트→보안검토→통합→문서화→배포승인→배포`
- 각 단계 산출물·체크리스트·게이트.
- **Implementer profile ≠ Reviewer profile**(권한 분리), Git **PR 리뷰**가 코드 게이트.
- Kanban으로 오케스트레이션 + **Git issue/PR**로 코드 작업 항목 추적.

---

## 6. 워크플로우 관리 범위 정리

| 용도 | 도구 |
|------|------|
| 미션·파이프라인 단계 오케스트레이션(모든 미션) | **Hermes Kanban** |
| 코드 작업 항목·코드 리뷰 게이트(미션 C/D) | **Git issue / PR** (Kanban과 병행) |
| 지식 축적·재사용 | **LLM Wiki**(별도 repo) |
| 반복 절차 | **Skill**(Git 버전관리) |

> 미션 A(보고서)는 Kanban + Git 저장으로 충분하며 Git issue는 사용하지 않는다.
