# 02. AI-Native Company 설계 — Solomon

> 작성일: 2026-08-02 · 상태: 설계 확정본(Stage 0 착수 전)
> 관련: [`ai_native_company_개념.md`](./ai_native_company_개념.md) · [`hermes_agent_조사.md`](./hermes_agent_조사.md) · [`llm_wiki_조사.md`](./llm_wiki_조사.md)
> 함께 볼 것: [`03_mission_pipeline_and_workflow.md`](./03_mission_pipeline_and_workflow.md) · [`04_mvp_research_trend_report_spec.md`](./04_mvp_research_trend_report_spec.md) · [`06_design_decision_log.md`](./06_design_decision_log.md)

---

## 1. 목적과 비전

Sam(창업자, CS 박사, 1인 기업)이 AI의 도움으로 **기획→제안→설계→구현→배포**까지
소프트웨어 개발 기업의 일을 수행하는 **AI-Native Company**를 만든다.

- 사람은 **Sam 혼자**(Founder). AI 총괄 대표는 **Solomon(AI CEO)**. 소통 채널은 **Slack**.
- Sam은 Solomon과 **브레인스토밍 협의 후 실행**한다.
- 회사는 **시간이 지날수록 결과물 품질·개발 속도·성능이 좋아지는(복리 성장)** 조직이어야 한다.

**초기 회사 업무(Sam의 실제 담당 업무)**
- (A) 최신 연구·기술 동향 분석 보고서 (AI·LLM 등) ← **1호 미션**
- (B) 학술 논문 작성 (AI 활용 등)
- (C) 웹 기반 시뮬레이션 플랫폼 개발
- (D) 최신 웹 기술 프로그램 개발

> (A)(B)는 **지식 생산**, (C)(D)는 **소프트웨어 생산**. 한 번에 다 만들지 않고 **미션 A부터 완주**해
> 시스템을 증명한 뒤 동일 골격으로 확장한다.

---

## 2. 설계 원칙

1. **미션 중심**: 대화가 아니라, 완료 조건이 충족될 때 종료되는 "미션" 단위로 일한다.
2. **파이프라인 + 검증**: 모든 미션은 정의된 파이프라인을 흐르고, 단계마다 **산출물·체크리스트·검증 게이트**를 가진다.
3. **작성자 ≠ 검증자**: 산출물을 만든 주체와 검증하는 주체를 분리한다(특히 **코드 구현 ≠ 코드 검증**).
4. **복리 성장을 구조로**: Skill 추출 · LLM Wiki 축적 · Reflection · profile 전문성 누적 · 파이프라인 개선.
5. **사람 개입은 위험 경계에만**: 개인정보·보안·비용·외부공개·파괴적 작업·법적약속·전략변경만 Sam 승인.
6. **과설계 금지**: 최소 구성으로 시작하고, 반복이 증명되면 확장한다.

---

## 3. 아키텍처 (Option B: Hermes Kanban + 전문 profile)

```
Sam ──Slack──> Solomon (대표 profile: 기획·디스패처·검증총괄·보고)
                     │  (직접 구현 ❌ — 실무는 위임)
                     ▼
              Hermes Kanban   = 파이프라인 / 워크플로우 관리자
              · task           = 파이프라인 단계
              · task_links     = 단계 게이트(부모 done → 자식 ready)
              · block/unblock  = 사람 개입 지점(Sam 승인)
              · comment/events = 체크리스트·검증 감사추적(영구)
              · gateway watcher= 상태 변경 시 Slack 알림
                     │  디스패처가 담당 profile을 worker로 실행
   ┌─────────────────┼─────────────────┬─────────────────┐
   ▼                 ▼                 ▼                 ▼
 Scout            Reader          Fact-Checker      Writer / Reviewer ...
 (전문 profile — 각자 SOUL·skill·누적 메모리)   단계 내부 병렬 = subagent 팬아웃
                     │
                     ▼
            LLM Wiki (별도 Git repo: raw → wiki → reflection)
```

### 3.1 Solomon (AI CEO) — 역할 경계
- **한다**: Sam과 브레인스토밍 → 미션 설계(목표·완료조건·파이프라인 선택·제약) → Kanban에 단계 task 생성·할당 → **게이트 검증·승인** → 최종 취합·Sam 보고 → 진행·비용·위험 관리.
- **안 한다**: 조사·분석·집필·코딩 등 **단계 산출물 직접 생산 ❌**.
- Sam과의 소통 창구는 **Solomon만**(전문 profile은 Sam과 직접 대화하지 않음).

### 3.2 전문 profile (실무자)
- 미션 A 초기 세트: **Scout**(검색) · **Reader**(논문/문서 분석) · **Fact-Checker**(교차검증) · **Synthesizer**(종합) · **Writer**(집필) · **Reviewer**(독립검토) · **Curator**(지식/Wiki 관리).
- 각 profile은 독립 SOUL.md(역할 정체성)·skill·**누적 메모리**를 가져 **전문성이 시간에 따라 축적**된다(= 성장 엔진).
- 별도 Slack 봇 **불필요** — 대표 gateway 하나가 Kanban 디스패치로 각 profile을 worker로 실행.
- 권한/도구 스코프는 **profile 단위**로 제한(보안 격리).

### 3.3 subagent (단계 내부 병렬)
- 한 단계 안에서의 **병렬 팬아웃**에 사용(예: Scout profile이 N개 소스를 subagent로 동시 검색).
- 일시적·0-컨텍스트, 종료 시 소멸(메모리 없음). 기본 병렬 3, 필요 시 상향.

### 3.4 코드 미션(C/D)의 구현 ≠ 검증
- **Implementer profile**(코드 쓰기·실행 권한)과 **Reviewer profile**(읽기·판단만)을 **권한 분리된 별도 profile**로 둔다.
- Git **PR 리뷰**가 코드 레벨의 작성자≠검증자 게이트 역할.

---

## 4. 핵심 서브시스템 (요약)

| 서브시스템 | 정의 | 상세 문서 |
|-----------|------|-----------|
| **Mission Pipeline Framework** | 미션 = 단계별(산출물·체크리스트·게이트) 파이프라인. Hermes Kanban으로 구현 | [03](./03_mission_pipeline_and_workflow.md) |
| **Skill Library** | 표준 방법론(PRISMA·IMRaD·PRD/ERD·karpathy-llm-wiki)을 Skill로 보유 | [03](./03_mission_pipeline_and_workflow.md) |
| **Workflow Manager** | Hermes **네이티브 Kanban** 사용(커스텀 관리시스템 미개발) | [03](./03_mission_pipeline_and_workflow.md) |
| **LLM Wiki** | **별도 Git repo**. 수요 기반 복리 지식자산(raw→wiki→reflection) | [llm_wiki_조사](./llm_wiki_조사.md) |
| **Memory/Skill/MCP 거버넌스** | 고정사실/절차/외부툴 구분 + 생성·갱신·폐기 관리 | [03](./03_mission_pipeline_and_workflow.md) |

### LLM Wiki를 두는 이유 (수요 기반 복리 자산)
- **정당한 축적만**: ①과거 미션의 지식 공백 보완 ②Sam 관심주제(AI·LLM) 신규 논문 추적 ③노후 사실 재검증. "심심하면 웹서핑" ❌.
- **근거**: 축적된 지식은 *미래 미션이 실제로 소비*한다 → 재조사 감소로 **속도↑**, 근거 고정으로 **정확도↑**, 미션마다 쌓여 **뒤로 갈수록 저렴·정확**. 이것이 "성장하는 회사"의 물리적 실체.

---

## 5. 인간 승인 범위 (개념 문서 §4 계승)

| 자율 결정(승인 불필요) | 사람(Sam) 승인 필요 |
|------------------------|---------------------|
| 공개 웹 검색·논문 요약·기술 비교·문서 초안·로컬 테스트·Git 브랜치/커밋·내부 Wiki 갱신·재시도·하위 에이전트 선택 | 개인정보 사용 · 보안(계정/키) · **유료 API·비용** · **외부 공개**(논문 제출·GitHub 공개·이메일) · 파괴적 작업(운영 배포·대량 삭제) · 법적 약속 · 전략 변경 |

승인 요청은 **행동·이유·영향·위험·복구 방법**을 함께 제시한다(막연한 질문 금지).

---

## 6. 성장 지표 (측정 가능하게)

"시간이 지날수록 더 좋아진다"를 희망이 아니라 숫자로 관리한다.

- 보고서 **소요 시간 ↓**
- **Wiki 재사용률 ↑** (보고서 근거 중 기존 Wiki에서 온 비율)
- **재작업률 ↓** (검증 게이트 반려 횟수)
- **Skill / 재사용 컴포넌트 수 ↑**
- **profile 전문성 누적** (역할별 메모리·skill 성장)

---

## 7. 단계별 로드맵

| Stage | 목표 | 핵심 산출 |
|-------|------|-----------|
| **0 — 기반(로컬)** | 로컬 Docker에 Hermes, Slack(Socket Mode), Solomon profile, Kanban, Git repo 2개(회사 / 별도 llm-wiki), 상용 API 키·비용상한 | 동작하는 Solomon + Slack 대화 |
| **1 — 1호 미션 MVP** | Kanban에 `research-trend-report` 파이프라인 + 최소 전문 profile 세트 + subagent 팬아웃 → 보고서 완주 | Markdown 보고서(Git) + Slack 요약 + Wiki 시딩 |
| **2 — 복리 루프** | `/research-trend` Skill 추출, Reflection, Wiki 재사용, profile 메모리 성장 | 성장 지표 최초 측정 |
| **3 — 24시간 학습** | Cron 수요기반 축적(도메인 allowlist·일일 상한) | idle 지식 축적 |
| **4 — 부서 확장** | profile fleet 확대 + profile distribution, Kanban 다중 보드 | research-lab 등 부서화 |
| **5+ — 미션 B/C/D** | 논문(IMRaD)·시뮬레이션 플랫폼·웹개발. C/D는 구현≠검증 profile + Git issue/PR | 지식·소프트웨어 생산 확장 |

> **현재 위치**: Stage 0 착수 전. Stage 0 구축은 Sam이 [05 가이드](./05_stage0_setup_guide.md)를 따라 수행한다.

---

## 8. 열린 사항 (후속 확정)
- 비용 상한 구체 수치, 사용할 상용 모델 조합(Claude/OpenAI), MCP 툴 목록(arXiv·검색·GitHub).
- Hermes Kanban 성숙도(신기능 v01, 2026-04) — Stage 0에서 소규모 검증 후 본격 사용.
