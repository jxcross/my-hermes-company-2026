# 07. 설계 다이어그램 (Diagrams)

> 작성일: 2026-08-02 · 렌더: GitHub Mermaid (```mermaid 코드펜스)
> 관련: [`02`](./02_company_design.md) · [`03`](./03_mission_pipeline_and_workflow.md) · [`04`](./04_mvp_research_trend_report_spec.md) · [`08`](./08_agent_specialization_and_governance.md) · [`09`](./09_mission_board_and_visibility.md)

이 문서는 지금까지의 설계를 시각화한다. 각 다이어그램은 관련 설계 문서의 내용을 그림으로 옮긴 것이다.

---

## 1. 시스템 아키텍처 (Option B: Kanban + 전문 profile)

```mermaid
flowchart TB
    Sam(["👤 Sam (Founder)"])
    subgraph Slack["Slack"]
        C1["#ceo-office"]
        C2["#approvals"]
        C3["#mission-log"]
    end
    Solomon["🧠 Solomon (AI CEO)\n기획·오케스트레이션·검증총괄·보고\n(구현 안 함)"]
    Kanban["📋 Hermes Kanban\n워크플로우 관리자\n(task·의존·상태·코멘트·대시보드)"]

    subgraph Specialists["전문 profile (실무자, 전문성 누적)"]
        Scout["Scout\n검색·수집"]
        Reader["Reader\n분석"]
        FC["Fact-Checker\n교차검증(≠Reader)"]
        Syn["Synthesizer\n종합"]
        Writer["Writer\n집필"]
        Rev["Reviewer\n독립검토(≠Writer)"]
        Cur["Curator\n지식/Wiki"]
    end

    Wiki[("📚 LLM Wiki\n별도 Git repo\nraw→wiki→reflection")]
    Git[("🗂️ 회사 Git repo\n보고서·계획·이력")]

    Sam <-->|대화·브레인스토밍| Slack
    Slack <--> Solomon
    Solomon -->|미션→단계 task 생성·할당| Kanban
    Kanban -->|디스패치| Specialists
    Specialists -.->|단계 내 병렬| Specialists
    Cur --> Wiki
    Writer --> Git
    Specialists -->|근거 조회| Wiki
    Kanban -->|상태 알림| C3
    Solomon -->|승인 요청| C2
```

---

## 2. 미션 생명주기 상태 머신

```mermaid
stateDiagram-v2
    [*] --> PROPOSED
    PROPOSED --> PLANNING: Sam 승인(Scoping)
    PLANNING --> RESEARCHING
    RESEARCHING --> EXECUTING
    EXECUTING --> VERIFYING
    VERIFYING --> DELIVERING: 검증 통과
    VERIFYING --> EXECUTING: 검증 반려(재작업)
    DELIVERING --> COMPLETED: Sam 확인
    COMPLETED --> [*]

    PLANNING --> WAITING_APPROVAL
    EXECUTING --> WAITING_APPROVAL
    WAITING_APPROVAL --> EXECUTING: unblock
    EXECUTING --> BLOCKED
    BLOCKED --> EXECUTING: 해소
    EXECUTING --> FAILED
    FAILED --> [*]
```

---

## 3. 미션 A 파이프라인 (11노드) — `research-trend-report`

```mermaid
flowchart LR
    S1["1.Scoping\nSolomon+Sam"] --> S2["2.Search\nScout"]
    S2 --> S3["3.Collection\nScout"]
    S3 --> S4["4.Dedup·Relevance\nCurator"]
    S4 --> S5["5.Deep Analysis\nReader"]
    S5 --> S6["6.Cross-Verify\nFact-Checker≠Reader"]
    S6 --> S7["7.Synthesis\nSynthesizer"]
    S7 --> S8["8.Report Draft\nWriter"]
    S8 --> S9["9.Independent Review\nReviewer≠Writer"]
    S9 -->|반려| S8
    S9 --> S10["10.Wiki Update\nCurator+Lint"]
    S10 --> S11["11.Deliver\nSolomon"]

    S1 -.Sam 승인.-> G1{{"🔒 승인"}}
    S11 -.외부공개 시 Sam 승인.-> G2{{"🔒 승인"}}
```

---

## 4. 파이프라인 노드 ↔ Kanban 매핑

```mermaid
flowchart TB
    subgraph Pipeline["워크플로우(파이프라인)"]
        P0["미션(프로젝트)"]
        PA["단계 A 산출물"]
        PB["단계 B 산출물(검증)"]
    end
    subgraph KanbanModel["Hermes Kanban"]
        K0["부모 task = 미션"]
        KA["자식 task A (assignee=profile)"]
        KB["자식 task B (parents=[A])"]
        KC["task_comment / task_runs\n= 에이전트 기록"]
        KE["task_events = 상태전이 감사"]
        KS["status: todo→ready→running→done\n/ blocked"]
    end

    P0 --> K0
    PA --> KA
    PB --> KB
    KA -->|의존(게이트)| KB
    KA --> KC
    KA --> KE
    KA --> KS
    KB --> KC
```

---

## 5. 에이전트 상호작용 시퀀스 (미션 A 축약)

```mermaid
sequenceDiagram
    actor Sam
    participant Sol as Solomon
    participant KB as Kanban
    participant Sc as Scout
    participant Rd as Reader
    participant FC as Fact-Checker
    participant Wr as Writer
    participant Rv as Reviewer
    participant Cu as Curator

    Sam->>Sol: 주제 제시 (Slack)
    Sol->>Sam: 미션 스펙 제안(목표·완료조건)
    Sam-->>Sol: 승인
    Sol->>KB: 미션+11단계 task 생성·할당
    KB->>Sc: Search/Collection 디스패치
    Sc-->>KB: raw 수집 완료(comment)
    KB->>Rd: Deep Analysis
    Rd-->>KB: 분석 완료
    KB->>FC: Cross-Verify(≠Reader)
    FC-->>KB: 검증표 완료
    KB->>Wr: Report Draft
    Wr-->>KB: 초안 완료
    KB->>Rv: Independent Review(≠Writer)
    Rv-->>KB: 승인/반려
    KB->>Cu: Wiki Update
    Cu-->>KB: raw→wiki 반영
    KB->>Sol: 전 단계 done
    Sol->>Sam: 보고서 링크 + Slack 요약
```

---

## 6. 사람(Sam) 승인 게이트 흐름

```mermaid
flowchart TD
    A["에이전트가 위험경계 작업 도달\n(개인정보·보안·비용·외부공개·파괴적)"] --> B{승인 필요?}
    B -->|No| E["자율 진행"]
    B -->|Yes| C["Kanban task = blocked\n#approvals에 요청\n(행동·이유·영향·위험·복구)"]
    C --> D{Sam 판단}
    D -->|승인| F["unblock → 진행"]
    D -->|거부| G["중단·대안 모색"]
    D -->|수정요청| C
```

---

## 7. 복리 성장 루프 (회사가 시간이 지날수록 좋아지는 이유)

```mermaid
flowchart LR
    M["미션 수행"] --> R["Reflection\n무엇이 통했나/실패했나"]
    R --> SK["Skill 추출·개정\n(파이프라인·체크리스트 개선)"]
    R --> WK["LLM Wiki 축적\n(재사용 지식)"]
    R --> PM["profile 메모리 성장\n(역할 전문성)"]
    SK --> M2["다음 미션"]
    WK --> M2
    PM --> M2
    M2 -->|소요시간↓ 재작업↓ 재사용률↑ 품질↑| M2
    M2 --> R
```

---

## 8. 미션 게시판 계층 (Sam이 보는 진행 현황)

```mermaid
flowchart TB
    Board["🗂️ Kanban 웹 대시보드 / Slack #mission-log / Git 미션 저널"]
    Mission["📌 미션(프로젝트) 게시글 = 부모 task\n예: M-2026-001 Agentic AI 동향"]
    Board --> Mission
    Mission --> E1["① Scout: 검색·수집 기록"]
    Mission --> E2["② Reader: 분석 기록"]
    Mission --> E3["③ Fact-Checker: 검증 기록"]
    Mission --> E4["④ Writer: 초안 기록"]
    Mission --> E5["⑤ Reviewer: 검토 기록"]
    Mission --> E6["⑥ Curator: Wiki 반영 기록"]
    E1 -.실행 순서(코멘트/task_runs 시간순).-> E2 -.-> E3 -.-> E4 -.-> E5 -.-> E6
```

---

## 9. 전문화 스택 (에이전트-스킬-메모리-지식)

```mermaid
flowchart TB
    subgraph Profile["전문 profile (1 역할)"]
        SOUL["SOUL.md\n좁은 역할 정체성"]
        Skill["역할 한정 Skill\n(표준 방법론 절차)"]
        Mem["역할 누적 Memory\n(경험·교훈)"]
    end
    Knowledge[("공유 Knowledge\nLLM Wiki")]

    SOUL --> Skill --> Mem
    Mem -->|성장| SOUL
    Profile -->|조회·기여| Knowledge
    Knowledge -->|선행 지식 제공| Profile

    Bad["❌ 잡다한 일 투입\n= 역할 오염 → 전문성 저하"]
    Good["✅ 좁은 역할 유지\n= 투입할수록 전문화(복리)"]
    Bad -.대비.-> Good
```
