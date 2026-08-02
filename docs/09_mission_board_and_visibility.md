# 09. 미션 게시판 & 워크플로우 가시성

> 작성일: 2026-08-02 · 상태: 설계 확정본
> 관련: [`03`](./03_mission_pipeline_and_workflow.md) · [`04`](./04_mvp_research_trend_report_spec.md) · [`07`](./07_diagrams.md) §4·§8 · [`hermes_agent_조사.md`](./hermes_agent_조사.md)

Sam의 요구:
> "미션 수행 전 과정에서 모든 AI 에이전트가 무엇을 하는지 Sam이 볼 수 있는 게시판이 필요하다.
> 새 미션이 주어지면 미션(프로젝트) 이름으로 게시글이 하나 생기고, 그 하위에 실행 순서대로 에이전트들이 기록한다.
> 워크플로우 각 노드 구성과 현재 실행 상태도 보고 싶다."

---

## 1. 결론 — 대부분 Hermes 네이티브 Kanban으로 해결

커스텀 게시판을 새로 만들지 않는다(MVP). Hermes Kanban이 다음을 **기본 제공**한다(조사: [`hermes_agent_조사.md`](./hermes_agent_조사.md), 결정: [`06` ADR-010](./06_design_decision_log.md)):
- **웹 대시보드**: 상태 컬럼(Todo/Ready/Running/Blocked/Done), **profile별 레인**(어느 에이전트가 무엇을), 카드 클릭 시 **코멘트 스레드 드로어**, 실시간 업데이트, 의존선.
- **CLI**: `hermes kanban list / show <id>`.
- **SQLite**(`~/.hermes/kanban.db`, 외부 읽기 개방) → 후속 커스텀 뷰 가능.

여기에 두 가지를 더해 사람 친화적으로 만든다:
- **Slack `#mission-log`**: 상태 변경 자동 알림(gateway watcher).
- **Git 미션 저널(Markdown)**: 미션별로 사람이 읽기 좋은 **영구 기록**을 자동 생성.

---

## 2. 게시판 구조 (미션 → 실행 순서 에이전트 기록)

그림: [`07`](./07_diagrams.md) §8.

```
📌 미션(프로젝트) 게시글          = Kanban 부모 task  (예: M-2026-001)
   ├─ ① Scout   : 검색·수집 기록   = 자식 task + comment/task_runs
   ├─ ② Reader  : 분석 기록         = 자식 task (parents=[①])
   ├─ ③ Fact-Checker : 검증 기록    = 자식 task (parents=[②])
   ├─ ④ Writer  : 초안 기록         = ...
   ├─ ⑤ Reviewer: 검토 기록
   └─ ⑥ Curator : Wiki 반영 기록
   (실행 순서 = task_links 의존 + comment/task_runs 시간순)
```

- **새 미션 = 부모 task 1개 생성**(미션 이름). Solomon이 생성.
- **각 단계 = 자식 task**(담당 profile assignee, 앞 단계에 의존).
- **에이전트 기록 = task_comment**(시간순) + **task_runs**(시도별 summary·metadata) + **task_events**(상태전이 감사).
- 사람은 **부모 카드**를 열면 하위 진행과 각 에이전트 기록을 순서대로 본다.

---

## 3. 워크플로우 노드 ↔ Kanban 매핑 (상세)

| 워크플로우(파이프라인) 개념 | Hermes Kanban | 사람 열람 |
|-----------------------------|---------------|-----------|
| 미션(프로젝트) | **부모 task** | 대시보드 카드 / 저널 제목 |
| 파이프라인 노드(단계) | **자식 task** (assignee=profile) | 컬럼 카드 / 저널 섹션 |
| 노드 순서·전제조건 | **task_links** (parents) = 게이트 | 의존선 |
| 노드 담당 에이전트 | task.assignee (profile) | **profile 레인** |
| 노드 산출물·근거 | comment 첨부 / Git 경로 | 카드 드로어 / 저널 링크 |
| 노드 실행 상태 | status(todo/ready/running/blocked/done) | 컬럼 위치 / 실시간 타이머 |
| 체크리스트·검증 결과 | comment(판정) + task_events | 드로어 스레드 |
| 사람 승인 | **blocked ↔ unblock** | #approvals + 카드 상태 |
| 재시도 이력 | **task_runs**(attempt별) | 사후분석 |

> 즉 "워크플로우 각 노드 구성"과 "현재 실행 상태"는 **Kanban 대시보드의 컬럼·레인·의존선·카드 상태**로 지금도 볼 수 있다.

---

## 4. 사람 열람 3계층

| 계층 | 수단 | 성격 | 시점 |
|------|------|------|------|
| **실시간 관제** | Kanban **웹 대시보드** | 상태·레인·의존·타이머 | 진행 중 |
| **알림·개입** | Slack `#mission-log`(알림) / `#approvals`(승인) | 푸시 + 사람 개입(block/unblock) | 이벤트 발생 시 |
| **영구 기록** | Git **미션 저널**(Markdown) | 리뷰·감사·재사용 | 완료 후에도 |

### 미션 저널(Markdown) 형식 (Git 자동 생성)
경로 예: `reports/M-2026-001/JOURNAL.md`
```markdown
# 미션 M-2026-001 — Agentic AI 동향 (상태: COMPLETED)
- 요청: Sam / 완료조건: ... / 파이프라인: research-trend-report

## 진행 기록 (실행 순서)
### [2026-08-xx 10:00] Scout — Search/Collection ✅
- 산출물: raw/ 23건 수집 (링크)
- 체크리스트: allowlist 준수 ✓ / 출처·날짜 기록 ✓
### [.. 10:40] Reader — Deep Analysis ✅
...
### [.. 11:20] Fact-Checker — Cross-Verify ✅ (반려 1회 → 보완)
...
## 결과
- 보고서: reports/M-2026-001/report.md
- Wiki 반영: llm-wiki repo (raw/wiki/reflections)
```
> 저널은 Kanban의 comment/task_runs/task_events를 사람이 읽기 좋게 정리한 미러다.

---

## 5. 실행상태 고급 뷰 (후속 — Control Plane)

Sam의 "나중에는 워크플로우 각 노드 구성과 현재 실행 상태를 보고 싶다"는 요구 중,
**전체 DAG 그래프·임계경로·통계**는 Kanban 기본 대시보드가 부분적으로만 제공한다(의존선 수준).

→ **Stage 4+에서 AI Company Control Plane(웹뷰)**을 별도 SPEC으로 개발한다:
- 데이터 소스: `~/.hermes/kanban.db`(읽기 전용). 스키마: `tasks · task_links · task_comments · task_events · task_runs`.
- 기능: 미션별 **워크플로우 DAG 렌더**(노드=단계, 엣지=의존), **노드별 상태·담당·소요시간**, 임계경로, 비용·성장지표 집계.
- 원칙: 쓰기는 Hermes CLI/도구 경유, 커스텀 뷰는 **읽기 전용**.

> MVP에서는 개발하지 않는다. 네이티브 대시보드 + Slack + 미션 저널로 충분.

---

## 6. 데이터 모델 (참조)

| 테이블 | 핵심 필드(요지) | 용도 |
|--------|------------------|------|
| `tasks` | id, title, body, assignee(profile), status, parents | 미션/단계 노드 |
| `task_links` | parent_id, child_id | 노드 의존(게이트) |
| `task_comments` | task_id, profile, text, created_at | 에이전트 순서 기록 |
| `task_runs` | task_id, attempt, summary, metadata, outcome | 시도·handoff·사후분석 |
| `task_events` | task_id, kind, details, created_at | 상태전이 감사추적 |

> 필드 상세·스키마는 Hermes 버전에 따라 다를 수 있으므로 Stage 0에서 실제 `kanban.db`로 확인한다.

---

## 7. 적용 (설계 반영)
- [`04`](./04_mvp_research_trend_report_spec.md) §3(Kanban 구성)과 일치: 미션=부모 task, 11단계=자식 task.
- [`05`](./05_stage0_setup_guide.md): Stage 0-E에 **웹 대시보드 활성화·접속** 및 미션 저널 규약 검증 추가.
- Control Plane은 Stage 4+ 별도 SPEC.
