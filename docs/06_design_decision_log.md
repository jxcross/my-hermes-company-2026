# 06. 설계 의사결정 기록 (Design Decision Log / ADR)

> 작성일: 2026-08-02 · 성격: ADR(Architecture Decision Record) — "왜 이렇게 설계했는가"의 근거 보존
> 배경: Sam과 Solomon(Claude) 간 브레인스토밍 협의 결과. 관련 문서: [`02`](./02_company_design.md)·[`03`](./03_mission_pipeline_and_workflow.md)·[`04`](./04_mvp_research_trend_report_spec.md)·[`05`](./05_stage0_setup_guide.md)

각 결정은 **맥락 → 검토한 대안 → 결정 → 근거 → 영향** 순으로 기록한다.

---

## ADR-001. 스코프를 "모든 일"이 아니라 미션 A로 좁힘
- **맥락**: "소프트웨어 개발 기업이 할 수 있는 모든 일"은 방향이지 설계 스코프가 아님. Sam의 실제 담당 업무는 4가지(A 동향보고서 / B 논문 / C 시뮬레이션 플랫폼 / D 웹개발).
- **대안**: (a) 4개 동시 구축 (b) 소프트웨어 생산(C/D) 먼저 (c) 지식 생산(A) 먼저.
- **결정**: **미션 A(동향 보고서) 1개를 먼저 완주.** (a)는 반드시 실패(전 부서 동시 창업), C/D는 인프라·배포·승인 범위가 커 첫 MVP로 부적합.
- **근거**: A는 위험 낮고 반복성 높아 **복리 루프(Skill·Wiki 축적)** 증명에 최적. LLM Wiki 가치를 가장 자연스럽게 보여줌.
- **영향**: Stage 1 = 미션 A. B/C/D는 Stage 5+에서 동일 골격 재사용.

## ADR-002. LLM Wiki를 "수요 기반 복리 자산"으로 재정의
- **맥락**: Sam이 "24시간 지식 축적"의 정당성을 요구. 목적 없는 상시 웹 탐색은 알려진 안티패턴(비용·드리프트·자료창고화).
- **대안**: (a) idle 시 자유 웹 탐색 (b) 수요 기반 축적만.
- **결정**: **(b) 수요 기반만.** 축적 대상 = ①과거 미션 지식공백 ②Sam 관심주제 신규 논문 ③노후 사실 재검증.
- **근거**: 축적 지식은 *미래 미션이 실제 소비*할 때만 가치. 재사용으로 속도↑, grounding으로 정확도↑, 미션마다 쌓여 뒤로 갈수록 저렴·정확 = "성장하는 회사"의 실체.
- **영향**: 24시간 학습(Stage 3)은 도메인 allowlist·일일 상한 하에 수요 기반으로만. "심심하면 웹서핑" 금지.

## ADR-003. Solomon = 기획·오케스트레이션·검증총괄·보고 (구현 안 함)
- **맥락**: Sam이 "Solomon은 기획자다. 직접 구현에 참여하는가?"라고 확인.
- **대안**: (a) Solomon이 기획+구현 (b) Solomon은 기획·관리만, 구현은 위임.
- **결정**: **(b).** 실제 회사 CEO처럼 Solomon은 회의실(기획)·관제실(오케스트레이션·검증)에, 구현은 전문 에이전트가.
- **근거**: 개념 문서 SOUL 원칙 #3(조사·구현·검토를 동일 에이전트가 단독 완료 금지)과 일치. 역할 분리가 품질·감사·확장에 유리.
- **영향**: 파이프라인에서 Solomon은 Scoping·Deliver·게이트 검증만 소유. 단계 산출물은 전문 profile이 생산.

## ADR-004. 전문 에이전트 = profile (subagent 아님) — Option B
- **맥락**: subagent(delegate) vs 별도 profile 중 무엇이 맞는지 검토 요청.
- **조사 사실**: subagent=일시적·0컨텍스트·부모권한 상속·**종료 시 메모리 소멸**·병렬(기본3). profile=독립 메모리/skill/cron·**권한 스코프 profile 단위**·Git 패키징·전문성 누적.
- **대안**: (A) 단일 profile + subagent (B) Kanban + 전문 profile.
- **결정**: **(B) 전문 profile.** subagent는 **단계 내부 병렬 팬아웃**으로만 사용.
- **근거**: ①**전문성 누적**(profile 메모리) = 성장 요구 충족 ②**권한 스코프가 profile 단위**뿐 → 보안 격리·역할별 도구 제한을 profile로만 강제 가능 ③**코드 구현≠검증**을 권한 분리로 강제하려면 별도 profile 필수(ADR-006).
- **영향**: Scout·Reader·Fact-Checker·Synthesizer·Writer·Reviewer·Curator를 profile로. 설정↑ 부담은 감수.

## ADR-005. 워크플로우 관리 = Hermes 네이티브 Kanban (Git issue는 코드 미션만)
- **맥락**: 파이프라인/워크플로우 관리가 필요. Hermes 내장 Kanban vs Git issue 검토 요청.
- **조사 사실**: Hermes에 **네이티브 Kanban**(task·task_links·comment·events·block/unblock·gateway 알림, 협업패턴 P1~P8) 존재. task는 **profile에 할당**되고 디스패처가 worker 실행. GitHub 연동은 내장 없음(MCP로 가능).
- **대안**: (a) Kanban (b) Git issue (c) 커스텀 관리 시스템.
- **결정**: **Kanban을 모든 미션의 워크플로우 관리자로**(= Mission Pipeline Framework의 실행 엔진). **Git issue/PR은 코드 생산 미션(C/D)에만** 병행(PR 리뷰 게이트).
- **근거**: Kanban이 파이프라인 단계·게이트·사람개입·감사추적·Slack알림을 **내장 제공** → 커스텀 재개발 불필요. task=단계, task_links=게이트로 정확히 매핑. Kanban이 profile 할당 기반이라 ADR-004(profile)와 자연 결합.
- **영향**: 미션 A는 Kanban+Git 저장으로 충분(issue 미사용). **리스크**: Kanban 신기능(v01, 2026-04) → Stage 0에서 소규모 검증 후 사용.

## ADR-006. 코드 구현 에이전트 ≠ 코드 검증 에이전트 (권한 분리)
- **맥락**: Sam이 "코드 구현과 검증 에이전트는 분명히 달라야 한다"고 지시.
- **결정**: 코드 미션(C/D)에서 **Implementer profile**(코드 쓰기·실행 권한)과 **Reviewer profile**(읽기·판단만)을 **권한 분리된 별도 profile**로. Git **PR 리뷰**가 코드 레벨 게이트.
- **근거**: 권한 스코프가 profile 단위이므로(ADR-004), 진짜 권한 분리는 별도 profile로만 가능. subagent는 부모 권한 상속이라 분리 불가.
- **영향**: Stage 5+ C/D에서 구현/검증 profile 도입 + Git issue/PR.

## ADR-007. 파이프라인은 표준·안전한 방법론 Skill로 구성
- **맥락**: Sam이 "관련된 유명하고 안전한 스킬을 보유·활용하면 좋겠다".
- **결정**: 파이프라인을 발명하지 않고 **표준 방법론을 Skill로 채택**: 동향보고서=PRISMA+근거등급, 논문=IMRaD+인용검증, 웹개발=PRD·사용자스토리·ERD·보안리뷰, 지식=karpathy-llm-wiki. agentskills.io 표준, Git 버전관리.
- **근거**: 검증된 절차 재사용 → 품질·재현성↑. Skill 개정(Reflection 기반)이 복리 성장 엔진.
- **영향**: Skill Library를 Git으로 버전관리·거버넌스.

## ADR-008. 인프라 결정: llm-wiki 별도 repo · Docker 로컬 · Slack/키는 Sam 수행
- **맥락**: Sam의 명시 결정.
- **결정**: ①**llm-wiki = 별도 Git repo**(지식 자산을 코드와 분리) ②**Docker 호스트 = 로컬** ③**Slack 연결·API 키 발급은 Sam이** [05 가이드](./05_stage0_setup_guide.md)를 따라 단계별 수행.
- **영향**: Stage 0 산출물이 Sam 실행용 가이드 형태.

---

## 미해결 / 후속 확정 항목
- 비용 상한 구체 수치, 사용할 상용 모델 조합(Claude/OpenAI/OpenRouter).
- MCP 툴 목록 및 profile별 권한 매핑(arXiv·검색·GitHub·Slack).
- Hermes Kanban 성숙도 실사용 검증(Stage 0-E).
- profile 수 증가에 따른 운영 부담 관찰 → 필요 시 통폐합.
