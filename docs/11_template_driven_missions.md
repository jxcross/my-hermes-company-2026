# 11. 템플릿 기반 미션 시스템 — 설계

> 작성일: 2026-08-03 · 상태: **설계 승인(구현 전)** · 성격: design spec
> 관련: [`04_mvp_research_trend_report_spec.md`](./04_mvp_research_trend_report_spec.md)(아키타입 A 11단계) · [`10_stage1_plan.md`](./10_stage1_plan.md)(§4.4 게이트키퍼) · 참고 소스: 형제 repo `other_projects/harness-templates`(28개 파이프라인 템플릿)
> 후속: 이 문서는 "무엇을·왜·어떤 구조로"를 고정한다. 구현은 §7 phasing에 따라 **phase별 별도 계획**으로 진행한다.

## 0. 왜 이 설계인가 (Context)
현재 파이프라인은 아키타입 A(동향보고서) 11단계가 `scripts/build_pipeline.sh`에 **하드코딩**돼 있다. 그러나
미션마다 파이프라인이 다르다 — **아키타입 간 구조 차이**(동향보고서 vs 논문 vs 웹개발)와 **아키타입 내 가변성**(같은 유형도
깊이·단계 수·병렬성이 다름). 하드코딩은 **불변식**(작성자≠검증자·게이트·감사추적)과 **가변 단계**를 한 덩어리로 섞어,
미션 유형이 늘 때마다 스크립트를 고쳐야 하고, Solomon의 자율분해가 불변식을 깨는 사고([`10 §4.3`](./10_stage1_plan.md) 개선점 2)를 낳았다.

형제 repo `other_projects/harness-templates`를 정밀 분석한 결과, 우리가 설계하려던 **"템플릿 층 + 미션→템플릿 매칭"이 이미
검증된 형태로 존재**했고, 우리 백로그 아키타입과 그대로 겹친다(trendforge≈A · specflow≈D · paperforge/reviewforge≈B).
**목표:** 그 선언적 템플릿 모델을 **Hermes 런타임(Kanban·profile·gate_keeper)으로 번역**해, "미션 → 템플릿 선택 →
워크플로우 구성 → task 분배"를 시스템이 수행하게 한다.

## 1. 핵심 통찰 (분석 근거)
1. **런타임은 대부분 이미 있다.** harness의 상태머신/큐(`sources_state.py`·`runs_state.py`·`step_state.py`)는 우리 **Kanban이 네이티브로 수행**(claim/done/blocked/link). → 이식 불필요. **없는 층은 둘뿐: ① 선언적 템플릿+매처, ② 객관 게이트.**
2. **게이트는 상보적.** harness = **객관 Python**(최신성·출처균형·통계·PRISMA; `--policy --sources --draft`, exit 0/1/2, 우회불가). 우리 = **LLM 검증자**(의미 판단, `gate_keeper.py`의 VERDICT). 합치면 기계적 결함은 싸게·결정적으로, 의미적 결함은 LLM이. 서로의 빈틈을 정확히 메운다.
3. **템플릿 스키마 80% 재사용.** 웹 팩토리 `SpecInput`(Zod, `harness-templates/web/lib/spec/schema.ts`)이 거의 그대로 우리 포맷. **4필드만 보강**(§3.A).
4. **trendforge에서 배울 것:** `source_type` 4분류 + `source_balance.py`, 병렬 팬아웃(수집·분석·작성·검토), 스코프에 정책 선언. **우리가 나은 것(유지):** 검증자 분리 깊이(Fact-Checker≠Reader, Reviewer≠Writer), wiki 복리(재사용률), gate_keeper 반려 루프(자유서술 지시).

## 2. 설계 원리 — 계층형(불변식 / 아키타입 / 미션별 적응)
- **Layer 0 — 불변식(Sam 소유, 협상 불가):** Scoping+Sam 게이트(시작) · Deliver+Sam 게이트(끝) · 모든 산출 단계엔 별도 검증자 · 검증 fail→반려 루프 · 모든 주장 출처 · 감사추적. → **템플릿 린터가 강제**(위반 템플릿 거부).
- **Layer 1 — 아키타입 템플릿(Solomon 선택):** 선언적 스펙(데이터). trendforge/specflow/paperforge를 소스로.
- **Layer 2 — 미션별 적응(Solomon이 Scoping에서, 가드레일 안):** 선택 단계 가감 · N · 병렬성 · 정책값. **불변식 게이트는 못 뺌.**

즉, "누가 결정하나"의 답: **Sam=불변식, Solomon=아키타입 선택+제약 내 적응, 시스템(린터·게이트키퍼)=불변식 강제.**

## 3. 컴포넌트

### A. 선언적 템플릿 스키마 — `templates/<archetype>.yaml`
`SpecInput` 채택 + **4필드 보강**(①profile 매핑 ②parallel_merge ③명시적 upstream DAG ④게이트 선언).
```yaml
name: trend-report            # 아키타입 id
category: research            # research | domain | cli
goal_kr: "..."
invariants: [scoping_gate, deliver_gate, writer_ne_reviewer, revision_loop]  # Layer0 (린터 검증)
stages:
  - id: 3
    name: Collection
    profile: scout            # ← 보강① sub-agent→Hermes profile
    parallel: true
    workers: [academic, industry, patents, news]
    parallel_merge: {strategy: union, key: source_type}   # ← 보강②
    artifact: raw/
    upstream: [2]             # ← 보강③ 명시적 DAG(순서 암묵추론 제거)
    gate: null
  - id: 6
    name: Cross-Verify
    profile: fact-checker
    verifier: true            # 작성자≠검증자 불변식 대상
    gate:                     # ← 보강④ 이중 게이트
      objective: [recency_check, source_balance]   # Python
      llm: fact_checker_verdict                     # gate_keeper 경유
    upstream: [5]
```

### B. 템플릿 → Kanban 번역기 — `scripts/instantiate_template.py`
템플릿 yaml + 미션 파라미터(주제·N·정책) → Kanban task 그래프:
- stage → `hermes kanban create --assignee <profile> --workspace dir:/work/company/reports/<MID>`
- `upstream` → `link`(부모→자식). **verifier 단계의 downstream은 `--initial-status blocked`** (게이트키퍼가 PASS시 unblock — 기존 패턴 재사용).
- Sam 게이트(scoping/deliver) → `block --kind needs_input`.
- 병렬 워커 → **스테이지 task 1개 유지 + 본문에 subagent 팬아웃 프로토콜 주입**. (당초 "N개 형제 task"안은 폐기 — 조사 결과 Hermes는 동일 profile의 여러 ready task를 **순차 실행**(워커풀 없음)해 형제 task는 속도 이득이 없다. 정석은 "단계 내 병렬=subagent"(CLAUDE.md)로, 실행 profile이 `delegation` 도구의 배치(parallel) 위임으로 worker를 동시 디스패치→worker별 shard 기록→오케스트레이터가 병합. 스테이지가 1 task라 gate_keeper 검증자 매핑도 무손상. [2026-08-03 Phase 2-① 구현])
- **DAG 미리보기**: `--dry-run --render mermaid` → 실제 카드 생성 없이 템플릿(±미션 파라미터)의 DAG를 mermaid/ASCII로 출력. Solomon이 Scoping 협상 시 Slack에 붙여 제시(§3.F). 비파괴이므로 협상 반복에 안전.
현 `scripts/build_pipeline.sh`(하드코딩 11단계)를 이 번역기로 대체/위임.

### C. 미션 → 템플릿 매처 — `scripts/match_template.py` + `templates/manifest.json`
harness의 manifest + 의사결정트리 패턴(경량). 미션 설명 → 후보 템플릿(카테고리·키워드) → **Solomon이 최종 선택**. MVP는 의사결정트리+Solomon 판단(BM25는 후순위). manifest 필드: id·category·keywords·stages·gates.

### D. 이중 게이트 모델 — 객관 Python(신규) + 기존 gate_keeper
- **객관 게이트(신규):** `scripts/gates/*.py`. harness의 `recency_check.py` 이식(policy 필드명 정합), `source_balance.py`는 우리 출처분류로 재작성. 규약 유지: `--policy --sources --draft`, exit 0/1/2.
- **통합점:** 검증자 stage에서 객관 게이트를 먼저 실행(FAIL시 즉시 반려), PASS면 LLM 검증자 판정. **gate_keeper가 두 신호를 합쳐 VERDICT 결정**(객관 FAIL이면 자동 FAIL).
- 기존 `gate_keeper.py`의 반려 루프·활성게이트 가드·fail-closed는 그대로 재사용.

### E. 불변식 린터 — `scripts/lint_template.py`
템플릿(및 인스턴스화 직전 미션 그래프)이 Layer0 불변식을 만족하는지 검증. 위반(검증자 누락·게이트 제거·Sam 게이트 빠짐)시 거부 → Solomon 자율분해 사고 원천 차단.

### F. Scoping = 파이프라인 협상 (Sam ↔ Solomon 상호작용)
미션 시작 시 **Scoping은 곧 "어떤 파이프라인으로 갈지"를 Sam과 Solomon이 협상하는 단계**다. 위 컴포넌트들이 이 대화를 뒷받침한다. 4단계 흐름:

1. **질의** — Sam이 Slack `#ceo-office`에서 미션 제시 + "어떤 파이프라인?" 질의(또는 Solomon이 먼저 제안). Scoping은 Solomon 소유(docs/03 §1.2·§5.1).
2. **제시(DAG)** — Solomon이 `match_template`(C)로 아키타입 선택 → `instantiate_template --dry-run --render mermaid`(B)로 **템플릿 DAG를 mermaid로 Slack에 미리보기 제시**. 후보가 여럿이면 함께 제시. (인스턴스화 전이라 비파괴.)
3. **협상(Layer 2, 가드레일 내)** — Sam↔Solomon이 선택 단계 가감·N·병렬성·정책값을 조정. **매 조정마다 `lint_template`(E)가 Layer 0 불변식 검증** → 검증자 제거·Sam 게이트 누락 등 위반은 거부. **합의가 불변식을 못 깬다.**
4. **승인·실행** — 합의 확정 → Sam이 **Scoping 게이트 승인**(`#approvals`에서 `unblock`) → 번역기(B)가 **합의된 템플릿을 결정적으로 인스턴스화** → daemon dispatch. ⇒ **"승인한 것 = 실제 도는 것"** (Solomon 자율분해 이탈 차단; `hermes kanban decompose` 자율분해가 수동 카드와 충돌하던 docs/10 §4.3 개선점 2를 원천 해소).

> 실행 시작 후 DAG는 Kanban 대시보드(:9129)의 컬럼·레인·**의존선**으로 관찰(docs/09 — 부분 DAG). 완전한 그래프 렌더는 후속 Control Plane(docs/09 §5).
>
> **Sam의 세 질문 대응:** (Q1 "어떤 워크플로우?" = 1·2단계) · (Q2 "DAG로 제시?" = 2단계 mermaid 미리보기 + 실행 후 대시보드) · (Q3 "그대로 진행?" = 4단계 승인→결정적 인스턴스화). 셋 다 지금도 부분 가능하나, 이 설계로 **신뢰 가능(승인=실행)**해진다.

## 4. 재사용 / 비재사용 (경계 명확화)
- **재사용:** SpecInput 스키마(+4필드) · 객관 게이트 스크립트(recency 등) · manifest/의사결정트리 개념 · 아키타입 콘텐츠(trendforge≈A · specflow≈D · paperforge/reviewforge≈B).
- **비재사용:** harness의 Python 상태머신/큐(**Kanban이 대체**) · Claude-Code 로컬 파일 런타임 전체(우리는 Kanban+profile+reports).

## 5. 아키타입 A 개선 (trendforge에서 흡수 — 병행 가능)
scout를 `academic/industry/patents/news` **4워커로 분화** + `source_type` 필드 + `source_balance` 객관 게이트 + 수집·분석·작성 **병렬화** + `01-scope`에 recency/source_balance **정책 선언**. (지식 복리·검증자 분리는 유지.)

**[2026-08-03 Phase 2-① 병렬화 구현]** 메커니즘 = **subagent 스테이지 내 팬아웃**(형제 task 아님 — §3.B 참조). 범위 = **Stage 3 수집(source_type 5워커 고정분할)·5 분석(자료별 동적분할)·8 집필(섹션별 동적분할)**. 번역기(`instantiate_template.py`)가 템플릿의 `parallel` 블록(`mode: workers|per_item`, `shard`, `merge_to`)을 읽어 각 스테이지 task **본문에 delegation 배치 위임 프로토콜을 주입**한다(스테이지 카드 1개 유지). 경합 회피: worker/항목별 개별 shard 파일 → 오케스트레이터가 스테이지 끝에서 canonical(`raw/sources.yaml`·`analysis/_index.md`·`report.md`)로 병합·dedup. **선행 확인**: `delegation`(👥) 도구셋이 scout 포함 전 profile에 enabled, `delegate` 배치(parallel) 지원(`max_concurrent_children` 기본 3, `MAX_DEPTH=1`). dry-run(불변식·주입본문·pipeline.json 메타·mermaid 표기) 검증 통과. 라이브 파일럿(M-2026-004)은 Sam Scoping 승인 후 실행 예정.

## 6. 파일 (생성/수정) — 구현 시
- **신규:** `templates/<archetype>.yaml`(A/B/D), `templates/manifest.json`, `scripts/instantiate_template.py`, `scripts/match_template.py`, `scripts/lint_template.py`, `scripts/gates/recency_check.py`·`source_balance.py`.
- **수정:** `scripts/build_pipeline.sh`(→번역기로 위임), `scripts/gate_keeper.py`(객관 게이트 신호 통합), `profiles-src/scout/SOUL.md`(4워커·source_type), `docs/04`·`docs/10` 갱신, `CLAUDE.md`.

## 7. 권장 단계 (phasing) — 각 phase는 별도 구현 계획
1. **Pilot: A를 템플릿화** — `trend-report.yaml` + 번역기로 아키타입 A를 재현(현 build_pipeline 대체), 객관 게이트(recency/source_balance)를 1개 미션에 적용. "템플릿→런타임" 경로 증명.
   **[2026-08-03 구현·검증(P0–P3)]**: `templates/trend-report.yaml` + `scripts/instantiate_template.py`(--dry-run --render mermaid, pipeline.json 기록, 인라인 불변식) — dry-run 그래프가 build_pipeline과 동형 확인. `scripts/gates/{recency_check,source_balance}.py`(harness 이식, 카테고리 정책화) — 픽스처 3종 정확 판정. `gate_keeper.py` 이중 게이트 통합(객관 FAIL→VERDICT FAIL, 재검증 카드 폴백) — 스크래치 3결합 검증. `scout/SOUL.md` sources.yaml 방출 계약. **게이트 통일 개선**: 모든 게이트(Sam+검증자 downstream)를 링크 전 `needs_input` block으로 통일 → auto-promote race·Deliver 게이트 버그 해소.

   **[2026-08-03 P4 실미션 M-2026-003 완주]** 주제 "AI 에이전트 메모리·컨텍스트 관리 동향". 11/11 단계 완주, report.md(출처12·전부2024+·확인20/상충0/미검증14 공개), 커밋 `b7ec055`. **라이브 검증**: Scoping 자율분해 안 함(분해금지 지시) · scout sources.yaml 정규화 taxonomy 방출 · **이중 게이트 실작동**(stage6 객관PASS+LLM FAIL→반려; stage9 객관PASS+LLM FAIL→writer수정→재검증 PASS) · Sam 게이트(Scoping·Deliver) 강제.

   **실미션이 발견·수정한 결함(P4 fixes)**:
   - **무한 리비전 루프** — 검증자가 본질적 미검증에 계속 FAIL → 비수렴. **수정**: gate_keeper `MAX_REVISION_ROUNDS`(2회→Sam 에스컬레이션) + fact-checker/reviewer SOUL 판정 정교화(미검증 '건수'만으로 FAIL 금지; 상충 없고 검증가능 주장 전수 확인 + 잔여 미검증 본질적·공개면 PASS, M-2026-002 선례).
   - **gate_keeper race** — 검증자 done 직후 VERDICT 코멘트 in-flight → 신호 없어 fail-closed 오판정. **수정**: `verdict_signal_present` 미확정 시 최대 `MAX_DEFER`회 재시도.
   - **stage_tag 버그** — 재검증 카드('G6R Re-Verify')가 태그 오추출('G'). **수정**: `·\s*G?(\d+)`.
   - notify 타임아웃 30→60s.

   **미해결(Phase 2 개선점)**:
   - **컨테이너 GitHub push 자격증명 없음** — Deliver가 로컬 커밋 후 push 실패로 self-block(정직). 현재 호스트 폴백 push. → 컨테이너에 GITHUB_TOKEN 프로비저닝 또는 Deliver=로컬커밋+별도 push 단계.
   - **Slack 승인→Kanban unblock 미배선** — Sam이 Slack 승인해도 Solomon(대화형)이 해당 task를 unblock 안 함(대화 응답만). → Solomon이 승인 메시지→`kanban unblock` 표준 처리, 또는 브리지.
   - **pre-blocked Sam 게이트 무알림** — Deliver가 인스턴스화때부터 blocked라 상위 완료 시 "승인 차례" 알림 없음. → 게이트키퍼가 상위 done 시 #approvals 자동 게시.
   - ~~**속도** — 순차 실행·병렬화 미구현이 최대 병목.~~ → **[해소 2026-08-03 Phase 2-①]** subagent 스테이지 내 팬아웃(3·5·8) 구현. 메커니즘·검증은 §5·§3.B. 잔여: 라이브 파일럿 M-2026-004 실행으로 실측 속도 이득·shard 병합 확인, `max_concurrent_children`(기본3)를 수집 5워커에 맞춰 튜닝(선택, hermes-home/config 로컬).
2. **일반화** — 린터·매처·manifest. B/D 템플릿 추가.
3. **매칭 자동화** — Solomon이 미션→템플릿 선택.

## 8. 검증 (설계 타당성 판정)
- Pilot에서 `instantiate_template.py trend-report M-2026-003`가 현 11단계와 **동등한 Kanban 그래프** 생성(수동 대비 diff 0).
- 객관 게이트가 스크래치 미션에서 recency 비율·source_type 균형을 정확히 FAIL/PASS 판정, gate_keeper와 합쳐 반려 루프 발동.
- 린터가 불변식 위반 템플릿(검증자 뺀 것)을 거부.
- 완료 미션 재처리·과거 그래프 오염 없음(기존 활성게이트 가드 유지).

## 9. 리스크·주의
- **비재사용 경계 유지:** harness 코드를 통째 끌어오지 말 것(Kanban 중복 상태머신 = 부채).
- **불변식 우선:** 자율 적응이 편해도 Layer0는 린터로 강제(사고 재발 방지).
- **스코프 억제:** 웹 팩토리·28개 이식은 범위 밖. 필요한 3~4 아키타입만.
- 별도 repo(`other_projects/harness-templates`)는 **참고 소스**일 뿐 — 필요한 스크립트만 우리 repo로 **선택 이식**(출처·라이선스 주석).
