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

**[2026-08-03 Phase 2-① 병렬화 구현]** 메커니즘 = **subagent 스테이지 내 팬아웃**(형제 task 아님 — §3.B 참조). 범위 = **Stage 3 수집(source_type 5워커 고정분할)·5 분석(자료별 동적분할)·8 집필(섹션별 동적분할)**. 번역기(`instantiate_template.py`)가 템플릿의 `parallel` 블록(`mode: workers|per_item`, `shard`, `merge_to`)을 읽어 각 스테이지 task **본문에 delegation 배치 위임 프로토콜을 주입**한다(스테이지 카드 1개 유지). 경합 회피: worker/항목별 개별 shard 파일 → 오케스트레이터가 스테이지 끝에서 canonical(`raw/sources.yaml`·`analysis/_index.md`·`report.md`)로 병합·dedup. **선행 확인**: `delegation`(👥) 도구셋이 scout 포함 전 profile에 enabled, `delegate` 배치(parallel) 지원(`max_concurrent_children` 기본 3, `MAX_DEPTH=1`). dry-run(불변식·주입본문·pipeline.json 메타·mermaid 표기) 검증 통과.

**[2026-08-04 `parallel.batch_size` 추가 — 배치 상한 명시]** Hermes `delegate_task`는 한 배치가 `delegation.max_concurrent_children`(현 설정 **3**)을 넘으면 **큐잉하지 않고 `Too many tasks…` tool_error 로 거절**한다(근거: `hermes-home/skills/…/delegate-task-concurrency-diagnosis.md` — 캡 경로 3종). 즉 stage 3의 워커 5개는 반드시 라운드로 나뉘어야 하는데, 기존 주입 문구는 "**한 번에** 위임하라"만 말해 분할을 **모델의 자체 판단에 의존**했다(M-2026-004 로그에 `Too many tasks`·`Truncated` 0건 = scout 가 알아서 3+2로 나눠 성공했으나 보장이 아님). → 템플릿에 `parallel.batch_size`(기본 3, 하한 1) 선언 + 번역기가 **"최대 N개씩, 이 단계는 5=3+2 총 2라운드"**를 본문에 못박고 거절 동작까지 경고. 렌더 라벨도 `⇉5워커/배치3×2R`로 노출. `pipeline.json`에 `batch_size` 기록. 테스트 `scripts/tests/test_instantiate_template.py` 17종. **컨테이너 config 의 `max_concurrent_children`를 올릴 경우 템플릿 `batch_size`도 함께 올릴 것**(둘은 독립 — 템플릿 값이 크면 tool_error, 작으면 동시성 손해).

**[2026-08-04 라이브 파일럿 M-2026-004 완주 — 병렬화 실증]** 주제 "온디바이스 LLM 추론 최적화 동향". **stage 3**: scout가 `delegation` 배치로 source_type별 **병렬 subagent 디스패치**(deleg 배치 라이브 transcript 확인) → worker shard 5개(academic·vendor·research_org·standards·news) → curator 병합 15건. **stage 5**: 자료별 `analysis/<id>.md` **12 shard** 병렬. **stage 8**: `report.<섹션>.md` **7 shard** 병렬 → report.md 조립. 이중 게이트(6·9) 리비전 루프·gate_keeper 자동 unblock 정상. 보고서 품질 순차본(M-2026-003)과 동등(조건부 trade-off·성숙도 분류·확인25/상충0/미검증13 공개). Deliver=Sam 승인→보고서 커밋(b585526, 55파일)+Slack #mission-log 게시로 **11/11 완주**(컨테이너 자격 부재분은 호스트 폴백 push·hermes-solomon Slack — Phase 2 항목 #2/#3 잔존). **파일럿이 발견·수정한 결함**: gate_keeper **fail-open**(자식 상태 transient 조회실패(None)를 종단으로 오인→검증자 영구 processed→downstream 고아화; stage 10 정지로 발현). 수정 `classify_children`+unknown시 fail-closed defer, 단위테스트 4종(`scripts/tests/test_gate_keeper.py`). **잔여 미소 결함**: 리비전 링크 생성 시 간헐 `kanban link` returncode -7 WARN(루프는 정상 형성 — 링크 등록됨). → gate_keeper `run()` 재시도 보강 후속.

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
   - ~~**컨테이너 GitHub push 자격증명 없음**~~ → **[해소 2026-08-04]** `.env`에 `GITHUB_TOKEN`(Fine-grained PAT, Contents:write) + docker-compose가 `GIT_CONFIG_*`로 github.com HTTPS credential helper 주입(토큰 파일 저장 없이 env 런타임 조회, `.git/config` 신원은 보존). 검증: 컨테이너 `git push` 인증 성공(API push=True). `.env.example`에 슬롯.
   - ~~**Deliver Slack 게시 실패**~~ → **[해소 2026-08-04]** 원인은 자격 아님 — Slack **Socket Mode(인바운드) 만성 flapping**에 에이전트 slack 도구가 의존. Deliver 게시를 **`hermes send`(Web API)** 경로로 고정(템플릿 stage11 body). Web API 아웃바운드는 정상.
   - ~~**Slack 승인→Kanban unblock 미배선**~~ · ~~**pre-blocked Sam 게이트 무알림**~~ → **[해소 2026-08-04, 커밋 예정]** gate_keeper에 **Sam 승인 게이트 자동화**(Web API 폴링, Socket Mode 비의존) 추가: **#4** 활성 Sam-게이트(상위 done·blocked)를 `#approvals`에 **판단 내용 포함 자동 승인요청 게시**(1회, 멱등; `task_id` + `gate_summary` — 진입 게이트=주제·파이프라인 계획·정책, 산출 게이트=보고서 요약·검증 결과·공개 대상) · **#3** `SLACK_ALLOWED_USERS`(Sam)의 승인 메시지 감지→해당 게이트 `kanban unblock`(바레 `승인`=단일 대기 게이트, `승인 <task_id>`=명시; 부정형/타인 스킵; 기동 시 과거 메시지 baseline seen 처리로 소급 방지). 단위테스트 10종 + 라이브 E2E(요청 게시→Sam `승인`→unblock) 검증. `scripts/gate_keeper.py` `approval_poll`.
   - **[잔여] Slack Socket Mode 인바운드 flapping** — 2026-08-02부터 15초마다 "transport disconnected"(2085+회, WebSocket 전송 타임아웃=네트워크성; app/bot 토큰은 유효). **force-recreate 후 재연결·현재 안정**이나 재발 가능. 승인 흐름은 Web API 폴링이라 이에 **비의존**. 대화형 인바운드(Solomon chat)만 영향 → 네트워크·중복연결 모니터.
   - ~~**속도** — 순차 실행·병렬화 미구현이 최대 병목.~~ → **[해소 2026-08-03 Phase 2-①]** subagent 스테이지 내 팬아웃(3·5·8) 구현. 메커니즘·검증은 §5·§3.B. 잔여: 라이브 파일럿 M-2026-004 실행으로 실측 속도 이득·shard 병합 확인, `max_concurrent_children`(기본3)를 수집 5워커에 맞춰 튜닝(선택, hermes-home/config 로컬).

   **[2026-08-05 실미션 재개 — 아키타입 B(M-2026-005) 착수에서 나온 결함 3건]**
   변환 20/20 이후 `draft` 19종을 하나씩 라이브로 돌리는 단계에서, **첫 인스턴스화 한 번에**
   배선·운영 층의 결함이 세 개 나왔다. 셋 다 **E2E 픽스처로는 잡을 수 없는 종류**다 —
   게이트의 판정이 아니라 **카드가 만들어지는 방식**과 **프로세스의 수명**에 관한 것이기 때문이다.

   - **① 인스턴스화가 디스패처와 경합한다(가장 심각).** 번역기는 카드 N장을 **모두 만든 뒤**
     block·link 했다. 그 사이 카드들은 **부모 없는 `ready`** 라 게이트웨이 디스패처가 집어간다.
     실측: 상류 산출물이 하나도 없는 상태에서 **워커 6개(2·3·5·6·9·10)가 동시에 실행**됐다
     (Wiki Update 가 수집보다 먼저 돌기 시작했다). Hermes CLI 제약을 실측으로 확인하고 배치를
     바꿨다 — `create --parent <미완료 부모>` 는 **`todo` 로 태어나고**(창 0), `block` 은
     **`ready` 에서만** 걸리며(`todo` 면 "cannot block"), `--initial-status blocked` 는
     **실제로 blocked 를 만들지 않는다**. → stage 마다 생성→(게이트)→링크를 한 번에 끝낸다.
   - **② `block` 실패를 WARN 으로 넘겨 게이트가 빠진 파이프라인이 남았다.** 같은 실행에서
     `block ... --kind needs_input` 이 `rc=-7` 로 죽었는데 번역기가 계속 진행했다.
     **게이트가 하나 빠진 그래프는 없는 것보다 나쁘다** — 있는 줄 알고 돌린다.
     → 1회 재시도 후 **중단**하고 이미 만든 카드를 **롤백(archive)** 한다.
   - **③ `archive`·`reclaim` 은 실행 중인 워커 프로세스를 죽이지 않는다.** 폭주한 scout 를
     reclaim 하고 카드를 archive 했는데도 그 프로세스는 **8분 41초째 살아서** 자료를 수집했고,
     미션 디렉터리를 지우고 재인스턴스화하자 **새 미션의 `raw/` 에 그대로 쓰기 시작**했다
     (20파일 · 워커 shard `sources.peer_reviewed.yaml` 까지). 폐기된 그래프의 워커가
     **검증 사슬 밖에서** 새 미션의 증거를 만든다 — 게이트는 파일의 **출처**를 묻지 않으므로
     이것은 게이트로 잡을 수 없다. → 미션을 폐기·재시작할 때는 카드 archive 만으로 부족하다:
     `docker exec hermes-solomon ps -eo pid,args | grep 'kanban task <archived_id>'` 로
     **프로세스를 확인하고 죽여라.**
   - **⑤ 게이트 승인의 `--reason` 은 다음 워커가 읽는다 — 메타 지시가 산출물의 주제로 샌다.**
     Scoping 을 승인하며 운영자가 남긴 말("아키타입 B **골격 검증 미션**", "**게이트 변수를
     배제하고 골격만 본다**")이 카드 코멘트로 남았고, Solomon 이 그것을 **논문의 스코프**로
     받아 `SCOPE.md` 에 옮겨 적었다 — `미션 성격: skeleton-validation` · 기여 #4 "스켈레톤
     검증 미션의 경계를 문서화한다" · 범위 제외에 "게이트 변수 평가"와 **"새로운 객관 게이트
     유형의 설계·구현 논의"**. 마지막 것은 **RQ1("각 계층이 어떤 검증 주장을 담당해야 하는가")과
     정면으로 모순**된다 — 논문이 자기 연구질문에 답하지 못하게 된다.
     → **규약**: 승인 사유는 *우리끼리의 메모*가 아니라 **파이프라인에 대한 지시**로 쓴다.
     테스트 성격·운영 사정처럼 산출물과 무관한 말은 넣지 말고, 넣어야 하면
     **`[운영 메모 · 산출물 지시 아님]`** 접두를 붙인다. 승인은 "통과" 버튼이 아니라
     **다음 워커에게 말을 거는 행위**다.
     → **조치**: 산출물을 손으로 고치지 않고 게이트키퍼와 같은 형태로 `1R Revision` 카드를
     만들어 downstream 앞에 링크했다(검증 사슬 밖의 편집은 ③에서 문제 삼은 것과 같은 일이다).

   - **⑥ 선별에서 버린 자료(`status: rejected`)가 정책 카운트에 잡힌다 — 게이트가 '수집한 것'을 잰다.**
     `academic-paper` stage 4 는 curator 에게 **"`status=selected/rejected` 판정"**을 지시하는데
     `source_balance`·`recency_check` 는 `("failed","excluded")` **두 단어만** 걸렀다.
     이번 미션은 scout 가 `peer_reviewed` 를 **하한(6)에 정확히 맞춰** 수집했으므로, curator 가
     중복 한 건만 버려도 **실제 5편인데 PASS** 가 났을 것이다(실측: rejected 1건 → 6→5 FAIL).
     아키타입 R 의 '문서와 코드가 서로 다른 형식을 말한다' 와 같은 계열이되 **방향이 거짓 PASS** 다.
     → 접두 deny-list(`failed`·`excluded`·`rejected`·`dropped`·`duplicate`·`skipped`)로 넓히고
     `policy.status_excluded_prefixes` 로 뺐다. **모르는 단어는 포함으로 둔다** —
     M-2026-003 이 `new`·`reuse_existing_wiki` 를 정상 값으로 썼으므로 allow-list 로 뒤집으면
     그 미션들이 조용히 0건이 된다.
     > **부수 관찰**: 수집이 하한을 **정확히** 맞추면 그 다음 선별 단계가 하한을 깨뜨린다.
     > 수집 목표는 하한이 아니라 **하한 + 여유**여야 한다(템플릿 지시 보강 후보).
   - **⑦ 실패의 표면 증상과 근본 원인이 두 층 떨어져 있다 — 카드만 봐서는 왜 멈췄는지 모른다.**
     stage 4 가 4회 연속 크래시했고 카드에 남은 것은
     `worker exited cleanly (rc=0) without calling kanban_complete — protocol violation` 뿐이었다.
     실제 원인은 **LLM 사용량 한도 소진**(`HTTP 429 usage_limit_reached` · plan=team ·
     `resets_at` 2026-08-09)이었고, 그것은 **세션 로그에만** 있다(`hermes kanban log`).
     디스패처는 429 재시도 실패로 조용히 끝난 세션을 '프로토콜 위반' 으로 읽는다.
     → 게이트키퍼/디스패처가 429·인증 실패 같은 **환경성 실패를 카드에 남기게** 해야 한다.
     그러지 않으면 다음 세션이 "워커가 규약을 안 지킨다"를 디버깅하게 된다(후속 과제).

   - **⑧ 작성자가 "시뮬레이션했다"고 자백한 산출물을 게이트 3종이 전부 통과시켰다
     (2026-08-05 · M-2026-005 · 지금까지 중 가장 심각).**
     stage 5 분석 11편 중 **7편이 날조**였고, 본문이 스스로 그렇게 적고 있었다:

     ```
     analysis/{gokhale2025,kim2024,li2024,manakul2023,wang2024,wu2024,yamauchi2025}.md
       ### Claim 1: [Synthesized from relevance note]
       - **Evidence:** [Simulated deep analysis based on relevance impacts.]
     ```

     `raw/` 에는 **원문이 다 있었다**(35KB~384KB, 11편 전부). reader 는 원문을 가지고 있으면서
     읽지 않고 `curated.md` 의 관련성 메모를 재서술했다. 파일 크기가 증언한다 — 실물 3편은
     4.1K·8.6K·14.4K, 날조 7편은 1.0K~1.7K.

     **창 크기 탓이 아니다.** `li2024`(384KB≈96k토큰)는 131072 창에 안 들어가지만
     `yamauchi2025`(35KB≈9k토큰)는 여유가 많은데도 똑같이 날조됐다. 창은 기여 요인이지
     원인이 아니다.

     세 겹의 방어가 모두 뚫렸다:
     - **객관 게이트가 검사 대상이 아닌 파일을 보고 있었다.** stage 6 의 `recency_check`·
       `source_balance` 는 `raw/sources.yaml` **메타데이터만** 읽는다. 산출물을 아예 열지
       않으므로, 분석이 비어 있든 날조든 판정이 달라지지 않는다.
     - **LLM 검증자가 표본만 보고 전체를 통과시켰다.** `verify/verification.md` 는 11편 중
       **5편만 표에 올렸고**, 그중 2건을 스스로 `unverified` 로 적어놓고 결론에
       `VERDICT: PASS` 를 썼다. 근거는 *"모순의 징후가 없다"* 였다 — **읽지 않은 것에
       모순이 없는 것은 당연하다.** 검증자가 "무엇을 검증하지 *못했는지*"를 판정에
       반영하지 않으면, 커버리지 부족이 곧 PASS 가 된다.
     - **stage 7 Synthesis 가 그 위에 논지를 쌓았다.** 날조는 하류로 전파되며, 전파된
       뒤에는 출처가 지워진다.

     > **핵심 교훈: 객관 게이트가 검사 대상이 아닌 파일을 보고 있으면 그 stage 에는
     > 사실상 게이트가 없다.** `docs/13 §5` 의 "동작하는 척하는 게이트"가 한 층 위로
     > 올라온 것이다 — 게이트가 아니라 **파이프라인이** 동작하는 척한다.
     > 그리고 `docs/14 §7` 이 예고한 것이 이걸로 측정됐다:
     > *"이 프로브가 재지 않는 것은 검증의 깊이다."* 결과는 **깊이 없음**이다.

     → 조치: **`analysis_substance` 게이트 신설**(자가선언 시뮬레이션 문구 탐지 ·
     샤드 개수 == `sources.yaml` 의 `selected` 개수 항등 · 분량 상하한 쌍).
     객관 게이트가 `sources.yaml` 만 읽는 stage 전부에 배선한다.
     ⚠️ 이 게이트를 넣으면 stage 의 공유 `--draft` 가 바뀐다 — `docs/13 §5` 의 `exit 2`
     조합을 반드시 먼저 확인하라.
     → **미해결 후속**: 검증자 프롬프트가 **커버리지를 판정에 반영하게** 해야 한다
     (N건 중 M건만 대조했으면 PASS 를 낼 수 없어야 한다).

     **⑧-b 그 잘못된 판정이 사람에게 가는 승인 요청문의 근거로 재사용된다 (같은 날 실증).**
     13:15 에 stage 8 이 `#approvals` 에 게시됐고 22:04 에 Slack `승인` 이 감지돼 워커가
     떴다. 승인 요청문은 **검증자의 판정을 그대로 옮긴다** — 그리고 그 판정이 `PASS` 였다.
     즉 알림은 *"검증 통과했으니 집필 시작할까요"* 라고 물었고, 분석 11편 중 8편이
     껍데기라는 사실은 어디에도 없었다.
     > **사람이 최종 방어선인데, 그 사람에게 가는 정보가 이미 오염돼 있다.**
     > 게이트가 틀리면 사람도 같이 틀리게 만드는 구조다 — 방어선이 둘이 아니라 하나였다.
     → 조치: `gate_keeper.artifact_inspection()` — 승인문에 판정만이 아니라 **산출물
     실측치**(파일 수·크기 중앙값·2KB 미만 목록·의심 문구 원문)를 함께 싣는다.
     M-2026-005 로 검증: *파일 21개 · 중앙값 1,740B · 2KB 미만 12개 · 의심 문구 7건*.
     ⚠️ 이것은 **게이트가 아니다**(판정하지 않는다). 게이트가 못 본 것을 사람이 볼
     기회를 줄 뿐이다. 판정과 실측이 어긋나면 그 자체가 신호다.

     **⑧-c 그리고 이 결함을 고치면서 같은 실수를 한 번 더 했다 — 기록해 둔다.**
     ① `analysis_substance` 에 주기 모니터의 '조용한 회차' 를 위한
     `allow_empty_when_no_sources` 예외를 넣었다가, 신설한 `preflight_gates.py` 가
     **"빈 미션을 PASS 시킨다"** 로 잡아냈다. 다시 보니 같은 stage 의 다른 게이트도 빈
     입력을 반려하므로 그 예외로 구제되는 경우가 실제로 없었다 — **얻는 것 없이 게이트만
     약해졌다.** 지웠다.
     ② `lint_gate_drafts.py` 의 첫 파서가 픽스처 4종의 `expect()` 시그니처를 못 읽어
     게이트 15종을 "한 번도 안 돌린다" 로 **오탐**했다. 린터가 대상을 덜 읽으면 조용히
     통과시킨다 — ⑧ 본문의 "검사 대상이 아닌 파일을 보는 게이트" 와 같은 계열이다.
     > **검사하는 쪽도 검사받아야 한다.** 게이트·린터·프리플라이트 전부 그렇다.

   - 부수 수정: `gate_keeper.VERIFIERS` 하드코딩 → **`pipeline.json` 이 선언한 검증자**를 읽는다.
     `webapp-build` stage 8 의 검증자가 `tester` 라 게이트키퍼가 그 stage 를 아예 보지 않았다
     (downstream 이 blocked 인 채 영구 정지 · 로그도 남지 않는다).

2. **일반화** — 린터·매처·manifest. B/D 템플릿 추가.
3. **매칭 자동화** — Solomon이 미션→템플릿 선택.

> **[2026-08-04] 위 2·3과 §3.C·§3.E·§3.F의 협상 설계는 [`12_pipeline_negotiation.md`](./12_pipeline_negotiation.md)로 확장·구체화됐다.** 핵심 발견: **현행 구조에는 협상이 들어갈 자리가 없다**(인스턴스화가 협상보다 먼저 일어나 stage 1 본문에 "카드를 새로 만들지 마라" 방어 문구가 박힘). docs/12는 협상을 **Phase 0(카드 생성 전, 비파괴)**으로 앞당기고, 논의 단위를 **단계→의도**로 바꾸며, 3층 구조(`_base.yaml`/아키타입/미션 오버레이)·매칭 3-way 판정·maturity 등급·축적 루프를 제안한다.

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
