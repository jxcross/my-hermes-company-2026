# 13. harness 스킬 → 템플릿 YAML 변환 — 작업 절차서

> 작성일: 2026-08-04(갱신 2026-08-05) · 상태: **작업 중(12/20 — A·B·B'·D·E·F·G·H·I·J·K·L 전부 실행가능, 라이브 미션은 A만)** · 성격: working doc(재개 가능)
> 관련: [`12_pipeline_negotiation.md`](./12_pipeline_negotiation.md)(§8 phasing 2b) · [`11_template_driven_missions.md`](./11_template_driven_missions.md)(템플릿 스키마 §3.A·§3.B) · 소스: 형제 repo `other_projects/harness-templates`
>
> **⚠️ 이 문서는 여러 세션에 걸쳐 이어서 작업하기 위한 것이다.** 새 세션은 **§6 진행 대장**에서 다음 대상을 고르고 → **§2 레시피**대로 변환하고 → **§6 갱신 + 커밋**하면 된다. 재개 방법은 §8.

## 1. 범위와 원칙

**대상**: `harness-templates`의 **20종**(domain 9 + research 11). `cli-harnesses` 8종은 코딩도구 하네스라 **제외**.

**가져오는 것은 스킬이다.**

| harness | 우리 |
|---|---|
| `.claude/skills/<name>/SKILL.md` (오케스트레이터 — 단계·병렬·게이트 선언) | **`templates/<name>.yaml`** ← 변환 대상 |
| `.claude/agents/*.md` (단계 수행자 — 격리 컨텍스트·제한된 tools·입출력 계약) | `profiles-src/<name>/SOUL.md` ← **참조만**(profile 매핑 판단용) |

agents는 템플릿으로 옮기는 것이 아니다. harness의 agent는 **하네스 전용 일회용**이지만 우리 profile은 **미션을 가로질러 재사용되며 Memory가 누적되는 영속 자산**이다. 그래서 1:1 이식이 아니라 **정규화**한다.

**신규 템플릿은 항상 `maturity: draft`로 적재한다.** 변환됐다는 것과 우리 Kanban·이중 게이트에서 동작한다는 것은 다르다. 실미션 1회 완주 → `tested`, 2회 → `proven`([`docs/12 §6`](./12_pipeline_negotiation.md)).

## 2. 변환 레시피 (스킬 1개 기준 · 8단계)

### ① 파이프라인 골자를 뽑는다
`SKILL.md`의 **`## Pipeline at a Glance`** 코드블록 하나에 필요한 것이 거의 다 있다 — stage 번호·이름, **★ 병렬 표시**, 산출물 경로, 리비전 루프. 여기서 시작한다.

### ② stage별 sub-agent를 세 갈래로 분류한다 (가장 중요한 판단)

| 원본 형태 | 판정 | 우리 표현 |
|---|---|---|
| **같은 계약의 워커 N개** (`gather-arxiv`/`gather-web`/`gather-recent`, 자료당 `read-extract`, 섹션당 `draft-section`) | **profile 아님** | stage **1개** + `parallel: {mode: workers\|per_item}` |
| **축이 다른 비평가 N개** (`logic-critic`/`fact-check`/`style-edit`) | 별개 역할 | 우리 **두 검증 지점**으로 재배치 |
| 단독 수행자 | profile 1개 | stage 1개 |

**"별개 profile인가"는 병렬 여부가 아니라 계약이 다른가로 갈린다.** arXiv를 뒤지든 웹을 뒤지든 "출처를 수집한다"는 계약은 같다.

### ③ agent → profile 매핑 (§3 사전)

### ④ 객관 게이트를 추출한다
`SKILL.md`가 실행하는 `scripts/*.py` 중 **exit code로 통과/불통을 판정하는 것만** `gate.objective`다.
**산출 도구는 게이트가 아니다** — `bib_export.py`(BibTeX 생성)는 판정하지 않으므로 게이트가 아니라 산출 단계의 도구다.

이식 시 우리 CLI 규약으로 맞춘다: `--policy <pipeline.json> --sources <sources.yaml> --draft <검사대상>`
(gate_keeper가 항상 이 셋을 넘긴다. 안 쓰는 인자도 받아만 두면 된다). 판정 대상 파일은 템플릿의
`gate.draft`로 지정한다. **이식한 게이트는 반드시 일부러 깨뜨린 픽스처로 검증하라**(§5) —
하네스는 `scripts/tests/fixtures/`에 아키타입별로 둔다(`run_all.py`로 일괄 실행).

**이식 전에 우리가 이미 가진 게이트와 겹치지 않는지 먼저 보라.** policyforge 의 하드게이트
3종 중 하나(`diversity_check.py` = 카테고리별 최소 건수 + 최근 5년 60%)는 우리
`source_balance` + `recency_check` 와 **하는 일이 같았다.** 스크립트를 늘리지 않고 템플릿
`policy` 블록으로 흡수했다 — 게이트를 정책 주도로 만들어 둔 보상이다(§2⑦).

**그리고 이식한 게이트가 애초에 동작했다고 가정하지 마라.** legalforge 의 게이트 2종은 **둘 다
어떤 입력에도 FAIL 하는 상태**였다(§5). 정상 픽스처로 **PASS 가 나오는지부터** 확인하라 —
"깨뜨린 픽스처로 FAIL 확인"의 짝이다.

현재 보유 게이트(30종): `recency_check` · `source_balance` · `doc_consistency` · `test_run` ·
`prisma_counts` · `prisma_checklist` · `seen_dedup` · `digest_shape` · `claim_consistency` ·
`patent_format` · `evidence_grade` · `stakeholder_coverage` · `format_consistency` ·
`clause_completeness` · `law_citation` · `legal_safety` · `symbol_truth` · `api_coverage` ·
`doc_links` · `objective_coverage` · `bloom_distribution` · `course_consistency` ·
`content_accessibility` · `atomic_commit` · `test_pass_rate` · `behavior_diff` ·
`owasp_coverage` · `cve_remediation` · `finding_completeness` · `secret_redaction`.
산출 도구는 `scripts/tools/`: `bib_export` · `monitor_state` · `relevance_score`.
회귀 테스트는 `scripts/tests/test_gates.py`.

### ⑤ 불변식을 보강한다 (§4 체크리스트)
원본에는 우리 불변식이 대개 없다. 빠진 단계를 채운다.

### ⑥ 원본의 사람 승인 지점을 보존한다
`wait for explicit approval`·`surface to the user` 같은 구절이 있으면 그 지점에 `sam_gate: true`. 다만 **§5의 게이트 겹침 함정**을 반드시 확인한다.

### ⑦ `policy` 블록을 도메인에 맞게 쓴다
`recency_policy`·`source_balance_policy`는 **정책 주도**다(`scripts/gates/source_balance.py`가 템플릿 선언을 읽는다 — 카테고리 하드코딩 없음). 도메인마다 taxonomy를 새로 정의하라.

### ⑧ 검증하고 대장을 갱신한다
```bash
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_template.py <name>'
docker exec hermes-solomon sh -c 'cd /work/company && \
  python3 scripts/instantiate_template.py <name> M-2026-TEST --dry-run --render mermaid'
```
불변식 위반 0 + mermaid DAG 확인 + **`reports/M-2026-TEST/`가 생성되지 않았는지**(비파괴) 확인 → §6 대장 갱신 → 커밋.

## 3. agent → profile 매핑 사전 (누적 자산 — 변환할 때마다 추가)

**3신호로 판정한다**: ⓐ 동사(name·description) ⓑ 판별력 있는 tools ⓒ 역할 표지(`parallel worker`/`critic`/`orchestrator`). 셋 중 **2개 이상 합의** 시 매핑, 아니면 §7 보류.

| 우리 profile | 동사 신호 | tools 신호 | 확인된 별칭 |
|---|---|---|---|
| `default` (Solomon) | clarify · scope-interview · finalize · deliver · orchestrate | `AskUserQuestion` | `paperforge-clarify-topic` · `paperforge-finalize` · `trendforge-clarify-scope` · `trendforge-finalize` · `reviewforge-{clarify-question,finalize}` · `litmonitor-seed-config` · `patentforge-{clarify-application,finalize}` · `policyforge-{clarify-issue,finalize}` · `legalforge-{clarify-doc,finalize}` · `docforge-{clarify-scope,finalize}` · `lectureforge-{clarify-course,finalize}` · `migrateforge-{clarify-migration,finalize}` · `secforge-{clarify-scope,finalize}` |
| `scout` | gather · ingest · collect · scan · search · survey · **map(외부 사실 조사)** | `WebSearch` `WebFetch` | `paperforge-scope-survey` · `paperforge-gather-{arxiv,web,recent}` · `trendforge-landscape-survey` · `trendforge-gather-{academic,industry,patents,news}` · `reviewforge-{search-protocol,search-database}` · `litmonitor-scan-{arxiv,scholar,openreview}` · `patentforge-prior-art-{academic,patent}-scan` · `policyforge-context-mapping` · `legalforge-legal-research` · `secforge-dep-cve-scanner` |
| `reader` | read-extract · analyze · classify · appraise · ingest · **grade** | — | `paperforge-read-extract` · `trendforge-read-extract` · `reviewforge-{data-extract,quality-appraise}` · `patentforge-ingest-invention` · `policyforge-literature-ingest` · `legalforge-ingest-context` · `docforge-{ingest-codebase,parse-symbols}`(**코드를 읽는 것도 reader 다**) · `lectureforge-ingest-source` · `migrateforge-ingest-codebase` · `secforge-{ingest-target,owasp-scanner,cwe-scanner,secrets-scanner}`(**패턴 스캐너도 reader 다**) |
| `curator` | dedup · filter · screen · normalize · cite-pack · cross-link | — | `reviewforge-prisma-screening` · `litmonitor-relevance-filter` · `docforge-cross-linker`(동사 신호에 `cross-link` 가 이미 있었다) · `lectureforge-accessibility-pass`(읽고 마는 감사가 아니라 **정비**로 만들었다) · *(다른 스킬엔 대개 없어 우리가 보강)* |
| `synthesizer` | synthesize · outline · structure · summarize · gap-analysis · **options-design** | — | `paperforge-synthesize-outline` · `trendforge-synthesize-trends` · `reviewforge-synthesize` · `litmonitor-action-suggest` · `patentforge-gap-analyzer` · `policyforge-{evidence-synthesize,options-design}` · `legalforge-{structure-design,risk-disclosure}` · `lectureforge-{learning-objectives,course-structure,assessment-design}` · `secforge-severity-classifier` |
| `writer` | draft · write · compose · section · adapt | — | `paperforge-draft-section` · `trendforge-draft-section` · `litmonitor-summarize` · `patentforge-{specification-writer,jurisdiction-adapter}` · `policyforge-{brief,report,memo,infographic}-writer` · `legalforge-{contract,opinion,advisory,terms}-writer` · `docforge-{api-ref,architecture,adr,tutorial}-writer` · `lectureforge-{syllabus,slides,assignments,quiz}-writer` |
| `fact-checker` | fact-check · verify · evidence · recency · citation · **grade-check** | `Bash`(게이트 스크립트 실행) | `paperforge-fact-check` · `trendforge-{evidence-critic,recency-check}` · `reviewforge-evidence-coverage-check` · `patentforge-{claim-consistency-check,novelty-comparison-check}` · `policyforge-{evidence-grade-check,source-diversity-check}` · `legalforge-law-citation-check` · `docforge-accuracy-check` · `lectureforge-{objective-coverage-check,bloom-distribution-check}` · `migrateforge-{test-pass-rate-check,regression-check}` · `secforge-{critical-zero-check,cve-patched-check}` |
| `reviewer` | review · critic · clarity · logic · style · bias · **coverage·consistency** | — | `paperforge-{logic-critic,style-edit}` · `trendforge-{clarity-check,bias-check}` · `reviewforge-{prisma-compliance-check,bias-balance-check,clarity-check}` · `patentforge-format-compliance-check` · `policyforge-{stakeholder-coverage-check,format-consistency-check}` · `legalforge-{clause-completeness-check,tone-style-check}` · `docforge-{api-coverage-check,clarity-check}` · `lectureforge-{accessibility-check,format-consistency-check}` · `migrateforge-atomic-commit-check` · `secforge-{owasp-coverage-check,report-clarity-check}` · `specflow` **Design Review(신설)** |
| `architect` | architect · erd · diagram · wireframe · style-design · dependency-graph · **migration-plan** | `Read,Write,Grep,Glob`(쓰기만·실행 없음) | `specflow-{architect,erd-designer,diagrammer,wireframer,style-designer}` · `docforge-dependency-graph-builder` · `migrateforge-migration-planner` · `secforge-stride-modeler` |
| `developer` | backend-dev · frontend-dev · implement · build · **transform-execute** | **`Edit`** + `Bash` | `specflow-{backend-dev,frontend-dev}` · `migrateforge-transform-executor` |
| `tester` | e2e-test · run · regression · verify-by-execution · **baseline-snapshot** | **`mcp__playwright__*`** + `Bash` | `specflow-e2e-tester` · `migrateforge-{baseline-snapshot,regression-test-runner,behavior-diff-checker,new-test-generator,type-check-runner}` |

⚠신규 = **아직 생성되지 않은 profile**(현재 표에는 없다 — 11종 모두 생성 완료). 템플릿은 `requires_profiles:`로 선언하고, `instantiate_template.py`가 미등록을 감지하면 **미리보기는 경고만·실제 인스턴스화는 중단**한다.

**신규 profile 후보 신호**: `Edit`(코드 수정) · `mcp__playwright__*`(브라우저 E2E) · 스캐너·빌더 계열. → §7에 쌓고 Sam 승인 전까지 만들지 않는다.

**tools가 같으면 같은 계약일 가능성이 높다** — specflow에서 `backend-dev`/`frontend-dev`가 `Read,Write,Edit,Bash,Grep,Glob`로 **완전히 동일**했고, `architect`/`erd-designer`/`wireframer`도 `Read,Write,Grep,Glob`로 동일했다. tools 단독으로는 판별력이 낮지만(246개 중 112개가 `Read,Write,Bash`), **한 스킬 안에서 tools가 일치하는 agent들**은 대개 같은 profile의 샤드다.

**절대 병합 금지**: `fact-checker` ≠ `reviewer`. "둘 다 검증"이라고 합치면 작성자≠검증자 불변식이 얕아진다.

## 4. 불변식 보강 체크리스트

원본을 그대로 옮기면 대개 아래가 빠져 있다. 변환할 때마다 확인한다.

- [ ] **시작 Sam 게이트** — stage 1 `sam_gate: true`
- [ ] **끝 Sam 게이트** — 마지막 stage `sam_gate: true`
- [ ] **검증 지점 2곳** — 산출 전(사실·인용) + 산출 후(품질·완료조건), 각각 `verifier: true`
- [ ] **작성자≠검증자** — 검증자 profile ≠ 직전 producer profile
- [ ] **반려·리비전 루프** — `verifier: true`만 선언하면 `gate_keeper`가 자동 생성(템플릿에 쓸 것 없음)
- [ ] **Dedup·Relevance** (curator) — 원본은 오케스트레이터가 즉석 병합만 하는 경우가 많다
- [ ] **Wiki Update** (curator) — 복리 성장. 원본엔 없다
- [ ] **`sources.yaml` 계약** — 모든 주장에 출처
- [ ] **`profile ∈ 등록된 profile`** — 없는 profile을 쓰면 존재하지 않는 assignee로 카드가 생성된다
- [ ] **`parallel` 스테이지마다 `batch_size`** — 미선언 시 기본 3
- [ ] **중간 Sam 게이트에는 `approval_artifact`** — 승인 대상 파일을 선언해야 요약이 실린다(§5)
- [ ] **객관 게이트 선언** — `gate.objective`가 비어 있으면 이중 게이트가 반쪽(LLM 판정만)이다. 도메인에 맞는 게이트가 없으면 **만든다**(`doc_consistency`·`test_run`이 그렇게 생겼다)

> 위 항목은 `python3 scripts/lint_template.py <name>`이 기계적으로 잡아준다(불변식 위반=exit 1, 미등록 profile=경고).

## 5. 함정 사례 (실제로 걸린 것만)

### ⚠️ 게이트 겹침 — 한 stage에 `sam_gate` + 검증자 downstream
**[발견: academic-paper 변환, 2026-08-04]** paperforge는 outline 확정 후 사용자 승인을 기다린다. 그래서 Synthesis(=outline 산출) stage에 `sam_gate: true`를 달았는데, 이 stage는 **동시에 검증자(Cross-Verify) downstream**이었다.

번역기는 **카드당 block을 하나만** 걸고 `sam_gate`가 우선하므로(`instantiate_template.py` 2절 `if sam_gate: ... elif is_gated_downstream:`), **검증 게이트가 조용히 사라졌다** — 검증이 FAIL이어도 Sam 승인만으로 진행되는 **불변식 우회**다.

**해결**: 승인 지점을 인접 stage로 내린다(Synthesis→Draft Sections). 의미도 더 정확하다 — "목차 확정 후 **집필 개시** 승인".
**재발 방지**: `check_invariants`에 겹침 검사를 추가했다. 이제 dry-run이 자동으로 거부한다.

### ⚠️ 수집 워커는 "검색 전략"이 아니라 "산출 taxonomy"로 나눈다
paperforge의 `gather-recent`(최신성 가중 검색)를 워커로 그대로 옮기면 `source_type`이 나오지 않아 `source_balance` 게이트가 워커 산출을 검사하지 못한다. **최신성은 워커가 아니라 `recency_policy`로 흡수**해 전 워커가 함께 지키게 했다.

### ⚠️ 병렬 워커를 profile로 만들면 증식이 시작된다
`gather-arxiv`/`gather-web`/`gather-recent`를 profile 3개로 만들 뻔했다. 계약이 같으므로 `parallel: workers` 하나로 흡수 — **paperforge 12 agent → 신규 profile 0개**.

### ⚠️ 산출 도구를 게이트로 오분류
`bib_export.py`는 BibTeX를 **생성**할 뿐 판정하지 않는다. 게이트가 아니다.

### ⚠️ 검증자가 아예 없는 스킬이 있다
**[발견: webapp-build 변환, 2026-08-04]** specflow에는 critic·fact-check 계열이 **하나도 없다**. 완료 판정이 "체크박스가 다 찼는가 + e2e가 green인가"뿐이다. 그대로 옮기면 우리 불변식(검증 2지점·작성자≠검증자)을 통째로 위반한다.

**해결**: 검증 단계를 **신설**했다 — 5 Design Review(reviewer: PRD 요구사항 커버리지·시나리오 추적·ERD/구조/화면 상호 모순)와 8 Test & Verify(tester: 시나리오 전건 실행 검증). 원본에 없다고 빼면 안 된다. **없으면 만든다**가 원칙이다.

부수 효과로 작성자≠검증자가 자연스럽게 성립했다 — `developer`가 짜고 `tester`가 검증한다.

### ⚠️ 코드 병렬은 task 단위가 아니라 "겹치지 않는 디렉터리" 단위로 나눈다
specflow는 task별(`/backend-task <N>`)로 구현한다. 이를 `per_item`으로 옮기면 **여러 subagent가 같은 디렉터리를 동시에 고쳐 충돌**한다. 문서 샤드(`analysis/<id>.md`)와 달리 코드는 상호 참조가 많다.

**해결**: `workers: [backend, frontend]`로 **버킷 분할**(서로 겹치지 않는 트리)하고, 각 워커가 자기 버킷의 task를 선행관계 순서대로 **순차** 처리하게 했다. `merge_to: null` — 코드는 병합 대상이 아니다.

### ⚠️ 도메인이 다르면 policy 블록도 갈아끼운다
`recency_policy`·`source_balance_policy`는 조사·집필 아키타입(A·B)의 정책이다. 웹개발에는 의미가 없어 `completion_policy`(체크박스 강제·E2E green·시나리오 커버리지)로 대체했다. **정책은 템플릿 소유**이므로 도메인마다 새로 정의하면 된다.

### ⚠️ 이식한 게이트가 "동작하는 척"할 수 있다 — 깨뜨린 픽스처로만 드러난다
**[발견: patent-spec 변환, 2026-08-04]** patentforge의 `claim_consistency.py`를 이식했더니 **두 겹의 결함**이 나왔다.

1. **절 파싱이 즉시 잘렸다** — 종료 조건 `(?=^##|\Z)`가 하위 제목 `### 청구항 1`에도 걸려 `【청구범위】` 절이 빈 문자열이 됐다. 청구항을 **하나도 못 읽는다**. → `(?=^##[^#]|\Z)`로 수정.
2. **요소 추출이 한국어에서 무력했다** — `\S+\s*(?:모듈|부|…)\b` 패턴은 조사가 붙은 `모듈과`·`부를`에서 `\b`가 성립하지 않아 **놓치고**, 대신 동사구 `포함하는 시스템`을 요소로 잡았다. 그래서 본문에서 '캐시 부'를 통째로 지웠는데도 **커버리지 2/2 PASS**가 나왔다.

→ (수식어, 핵심명사)를 분리해 잡고 조사를 lookahead로 허용하며, 동사 어미로 끝나는 수식어를 배제하도록 재작성. 같은 픽스처가 이제 `커버리지 2/3 · exit=1`로 잡힌다.

**교훈**: 게이트가 PASS를 낸다고 동작하는 것이 아니다. **일부러 깨뜨린 입력에 FAIL을 내는지**까지 확인해야 비로소 게이트다. 특히 원문 언어가 한국어인 도메인에서는 영어 기준 정규식(`\b`, 공백 토큰화)이 조용히 무너진다.

### ⚠️ 안전·법적 고지는 지시가 아니라 게이트로 강제한다
patentforge는 finalize 단계에서 `usage-disclaimer.md`를 첨부하라고 **지시만** 한다. 특허 초안이 고지 없이 유통되면 변리사 자문으로 오인될 수 있으므로, 우리는 `patent_format` 게이트에 **고지 문구 존재 검사**를 넣어 자동 반려하게 했다. 원본에 없던 검사를 추가한 사례다 — 도메인에 법적·안전 요구가 있으면 게이트로 승격하라.

### ⚠️ 주기 실행 스킬은 "미션 간 지속 상태"를 요구한다
**[발견: lit-monitor 변환, 2026-08-04]** litmonitor는 다른 하네스와 달리 **주기 실행**용이다(`/loop weekly`). 우리 모델은 **미션 1건 = 파이프라인 1회 실행**이라 매 회차가 새 미션이 되는데, "이미 본 논문" 기억은 미션을 가로질러 살아야 한다. 미션 디렉터리(`reports/<MID>/`)에 두면 다음 회차가 못 읽는다.

**해결**: `monitors/<monitor_id>/`에 지속 상태를 분리했다(watchlist·`_seen.tsv`·history). git 추적 대상이라 PC 간에도 이어진다. `monitor_id`는 **Scoping이 SCOPE.md frontmatter에 선언**하고 게이트가 그 값으로 상태를 찾는다. 주기 실행 아키타입을 또 만들 때는 이 패턴을 재사용하라.

**부수 판단**: 원본 stage 1(seed-config)은 "첫 회차에만" 도는 조건부 단계다. **조건부 분기를 Kanban 그래프에 넣지 않았다** — gate_keeper의 단순한 순차 모델이 깨진다. 대신 Scoping이 "없으면 만들고 있으면 검토"하게 흡수했다.

### ⚠️ 이식한 게이트의 휴리스틱을 그대로 믿지 마라 — 픽스처로 때려봐야 안다
**[발견: systematic-review 변환, 2026-08-04]** reviewforge의 `prisma_audit.py`는 27항목 각각에 대해 `키워드 or 절힌트`가 맞으면 **PARTIAL**을 줬다. 그런데 절 힌트는 대부분 `methods`·`results` 같은 흔한 제목이라 **어느 원고에나 맞는다.** 결과적으로 PROSPERO 등록·연구비·이해상충·근거 확실성처럼 **가장 자주 누락되는 항목**이 키워드가 통째로 없는데도 PARTIAL로 살아남아 게이트를 통과했다(픽스처로 해당 문구를 전부 지웠는데 `exit=0`).

**해결**: `키워드가 없으면 NO`로 바꾸고, 절 힌트는 PARTIAL→YES로 **올리기만** 하게 했다. 같은 픽스처가 이제 `NO 6건 · exit=1`로 잡힌다.

**교훈**: 이식은 복사가 아니다. **원본이 통과시키던 것을 통과시켜선 안 되는 경우**가 있으므로, 게이트는 반드시 **일부러 깨뜨린 픽스처**로 검증하라 — PASS 케이스만 보면 느슨한 게이트를 발견할 수 없다.

### ⚠️ 수집 워커 분할 기준은 아키타입마다 다르다
trend-report는 **산출 taxonomy**(source_type)로 나눴고(§5 위), systematic-review는 **데이터베이스별**로 나눴다. 후자는 각 DB가 서로 다른 문헌 모집단이라 검색 전략 분할이 곧 산출 분할이기 때문이다. 원칙은 하나다 — **게이트가 워커 산출을 그대로 검사할 수 있게 나눈다.**

### ⚠️ 감사 도구의 하드게이트를 "취약점 0건"으로 두면 **게이트가 발견을 벌한다**
**[발견: security-audit 변환, 2026-08-05]** secforge 의 GATE 1 은 "Critical/High = 0 건" 이다.
그런데 secforge 는 스스로 **report-only**(자동 수정 없음)라고 선언한다. 즉 이 파이프라인이
할 수 있는 일은 보고서를 내는 것뿐인데, **취약점을 찾을수록 게이트가 FAIL 이 되어 그 보고서가
finalize 되지 않는다.** 심각한 취약점을 발견했을 때야말로 보고가 가장 빨리 사람에게 가야
하는데, 바로 그때 파이프라인이 막힌다.

→ 판정 방향을 뒤집었다. `finding_completeness` 는 **"몇 건이냐"가 아니라 "보고가 조치
가능한가"**(위치·근거·영향·조치)를 본다. 건수 상한은 정책(`max_critical`·`max_high`)으로
남겼지만 **기본값은 무제한**이다 — 릴리스 게이트로 쓰고 싶은 팀만 켠다.

**교훈**: 게이트를 이식하기 전에 **"이 게이트가 FAIL 을 낼 때 파이프라인이 하려던 일이
무엇인가"** 를 물어라. 발견이 목적인 파이프라인에서 발견을 막는 게이트는 목적과 싸운다.

### ⚠️ 보안 게이트가 fail-open 이면 게이트가 아니라 장식이다
같은 스킬의 게이트 3종이 **전부** 입력이 없거나 깨졌을 때 PASS 였다. 실측:

| 원본 게이트 | 입력 | 결과 |
|---|---|---|
| `severity_check`(GATE 1) | 빈 보고서(형식 깨짐) | `PASS · exit=0` — `parse_int` 가 키 없으면 0 |
| `owasp_coverage`(GATE 2) | "A01 … A10 은 **앞으로 점검할 예정**이다" 한 줄 | `covered 10/10 · PASS` |
| `cve_check`(GATE 3) | CVE 스캔을 아예 안 돌림 | `PASS · exit=0` — 블록 없으면 `""` |

특히 GATE 2 는 **글자의 존재**를 감사의 증거로 셌다. 우리 규약은 처음부터 fail-closed
(exit 2)였고 그 규약이 여기서 값을 했다 — 셋 다 뒤집고, 범주마다 **구조화된 항목**(status +
근거)을 요구하도록 바꿨다.

**교훈**: 보안 도메인에서 **"데이터가 없다"는 "문제가 없다"가 아니다.** 게이트를 이식할 때
`if not m: block = ""` 같은 줄을 보면 그 자리가 곧 구멍이다.

### ⚠️ 감사 산출물은 그 자체가 공격 안내서다 — 공개 범위를 파이프라인이 나눠야 한다
legal-draft 에서 배운 것(§5)의 두 번째 적용이자 더 날카로운 형태다. 이 저장소는 PUBLIC 이고
Deliver 가 `reports/` 를 push 하는데, 보안 감사의 산출물은 **취약점의 위치와 재현 방법**이고
secrets-scanner 는 **실제 키 값**을 찾아낸다. 그대로 push 하면 감사가 유출 사고가 된다.

→ 산출물을 둘로 나눴다: `_private/`(상세 · **gitignore**) 와 `report/`(공유용 요약 · 커밋).
`secret_redaction` 게이트는 **커밋 대상만** 검사하고 `_private/` 는 제외한다(거기엔 값이 있어야
하기 때문이다). 마스킹 표기(`AKIA****`·`<redacted>`)는 허용해야 한다 — 막으면 발견을 보고할
방법이 없어진다.

**교훈**: 산출물이 민감한 아키타입에서는 **"무엇을 만드는가"만이 아니라 "무엇이 커밋되는가"**
를 템플릿이 정해야 한다. 게이트는 그 경계를 지키는 도구지 경계 자체가 아니다.

### ⚠️ 미션 밖의 실제 코드를 바꾸는 아키타입은 **안전 규약이 설계의 일부**다
**[발견: code-migration 변환, 2026-08-05]** 지금까지의 아키타입은 `reports/<MID>/` 에 문서를
쌓을 뿐이었다. migrateforge 는 다르다 — **대상 저장소의 파일을 고치고 git 이력을 남긴다.**
그래서 템플릿에 안전 규약을 명시적으로 넣었다:

- 대상 저장소는 **`HERMES_WRITE_SAFE_ROOT` 안**이어야 워커가 쓸 수 있다.
- **`/work/company` 자신을 대상으로 삼지 않는다** — 파이프라인이 자기 코드를 고치게 되고,
  gate_keeper 가 도는 중에 gate_keeper 가 바뀐다.
- 대상 저장소는 **깨끗한 작업 트리**여야 한다(커밋 안 된 변경이 있으면 원자 커밋 검사가 무의미).
- **force push 금지** · 되돌리기는 `git revert` 로만.
- 코드 변경 개시 **직전에 Sam 승인 게이트**(`legal_safety` 가 개인정보를 막은 것과 같은 계열 —
  되돌리기 어려운 행위 앞에는 사람을 둔다).

### ⚠️ git 커밋은 병렬화할 수 없다 — 디렉터리를 나눠도 인덱스는 공유 자원이다
원본 stage 5 는 독립 배치를 병렬 subagent 로 돌리고 **각자 `git commit`** 한다. 같은 저장소에서
동시 커밋은 `.git/index.lock` 을 두고 경합해 실패하거나 커밋이 뒤섞인다. specflow 에서 얻은
"코드 병렬은 겹치지 않는 디렉터리 단위로"(§5)보다 **더 강한 제약**이다 — 파일이 겹치지 않아도
git 인덱스는 하나다. 게다가 이 아키타입의 하드게이트(원자 커밋)는 커밋 단위의 원자성을
요구하므로 병렬과 근본적으로 상충한다. → **`parallel` 선언을 아예 넣지 않았다.**

**교훈**: 원본의 ★(병렬) 표시를 기계적으로 옮기지 마라. **공유 자원이 무엇인지** 먼저 물어라.
문서 샤드는 독립이지만 git 인덱스·DB 트랜잭션·빌드 산출 디렉터리는 그렇지 않다.

### ⚠️ 회귀 게이트가 **기준선을 보지 않으면** 회귀를 못 잡는다
migrateforge 의 GATE 1 은 "테스트 통과율 ≥ 95%" 다. 그런데 **기준선과 비교하지 않는다.**
실측: 마이그레이션 **전 200/200(100%)** 이던 것이 **후 192/200(96%)** 가 돼도 `PASS · exit=0`.
8건이 깨졌는데 합격이다. 마이그레이션 게이트의 존재 이유가 회귀 탐지인데 회귀를 못 본다.

더구나 통과율의 **분모는 산출물이 적어 낸 값**이라, 깨진 테스트를 지우면 100% 가 된다
(code-docs 의 '분모 자기결정' 과 같은 계열). → 기준선 대비 **통과 건수 감소**와 **테스트 수
감소**를 각각 FAIL 로 만들었다.

**교훈**: "전후를 비교한다"는 게이트를 만나면 **'전'을 실제로 읽는 코드가 있는지** 확인하라.

### ⚠️ 계획을 읽어 변수에 담고 한 번도 쓰지 않는다 — 죽은 변수
`behavior_diff.py` 의 docstring 은 행동 차이가 "**03-plan 에 명시된 의도적 변경인지**"를
검증한다고 선언한다. 코드는 `plan_text = args.plan.read_text(...)` 로 읽어 놓고 **그 뒤로 한
번도 참조하지 않는다.** 실제 판정은 diff 보고서 자신이 적은 `acceptable: yes` 한 줄뿐이다 —
**바꾼 쪽이 스스로 '괜찮다'고 적으면 통과**한다. 실측으로 확인했다(`exit=0`).

lectureforge 의 `pass` 죽은 코드(§5)와 같은 계열이되 더 찾기 어렵다 — 변수가 있으니 읽는
것처럼 보인다. → 각 차이가 계획의 ```intentional``` 블록에 **선언된 id 를 참조**해야 인정하게
바꿨다.

**교훈**: docstring 이 "A 를 B 와 대조한다"고 하면, **B 를 담은 변수가 판정식에 등장하는지**
눈으로 확인하라.

### ⚠️ 게이트 이름이 겹치면 **먼저 있던 아키타입이 조용히 망가진다**
**[발견: lecture-course 변환, 2026-08-05]** lectureforge 에도 `format_consistency_check.py` 가
있다. 우리는 이미 `gates/format_consistency.py` 를 갖고 있다(아키타입 G — 정책 브리프의
포맷 간 권고 일치·분량). **이름만 같고 하는 일이 전혀 다르다**(강의 쪽은 LO id·주차 번호·성적
비중). 관성으로 같은 파일명에 이식했다면 policy-brief 가 **다른 도메인의 검사를 받으며 조용히
FAIL** 하게 됐을 것이다 — 그리고 그 사실은 아키타입 G 의 실미션을 돌릴 때에야 드러난다.

→ `course_consistency.py` 로 새로 만들었다. **이식 전에 `ls scripts/gates/` 로 이름 충돌을
확인하라.** 도메인 접두어를 붙이는 편이 안전하다.

### ⚠️ 죽은 코드가 게이트 행세를 한다 — 분기 본문이 `pass` 였다
같은 파일의 두 번째 결함. docstring 은 "Total grade weights sum to 100% (±0.1)" 를 검증한다고
선언하는데, 해당 분기의 **본문이 문자 그대로 `pass`** 다(원본 116~119행, 주석까지 달려 있다).
성적 비중이 60% 든 140% 든 아무 일도 일어나지 않는다.

docstring-vs-코드 함정(§5)의 가장 노골적인 형태다. **선언된 검사 항목마다 그것을 수행하는
코드 줄을 눈으로 짚어라.** 항목 수가 아니라 실행되는 판정문의 수를 세라.

### ⚠️ 원본이 **검증을 너무 늦게** 하고 있으면 앞으로 당겨라
lectureforge 는 4개 산출물(강의계획서·슬라이드 16주치·과제·퀴즈)을 **다 쓴 뒤에** 학습목표
커버리지와 Bloom 분포를 검사한다. 거기서 FAIL 이 나면 학습목표부터 다시 세우고 **16주치
슬라이드를 다시 써야** 한다.

우리는 설계 검증(stage 7)을 **집필 전**에 뒀다. patent-spec(관할 변환 전 청구항 검증) ·
policy-brief(옵션 설계 전 근거 검증) · legal-draft(집필 전 법령 검증) · code-docs(집필 전 심볼
검증)와 같은 판단이다. **다섯 번 반복된 패턴이므로 이제 기본값으로 삼는다** — 원본의 검증
지점을 그대로 옮기지 말고, **재작업 비용이 가장 크게 갈라지는 지점 앞**에 놓아라.

### ⚠️ 커버리지 게이트의 **분모를 파이프라인이 스스로 정하면** 게이트가 아니다
**[발견: code-docs 변환, 2026-08-05]** docforge 의 하드게이트는 "공개 API 의 90% 이상이
문서화됐는가" 를 잰다. 그런데 분모인 공개 심볼 목록은 **같은 파이프라인의 앞 단계(parse-symbols)가
만든 것**이다. 심볼 추출이 공개 함수 100개 중 3개만 적어 내면 그 3개만 문서화해도 **커버리지
100%** 다. 측정 대상이 자기 성적표의 분모를 정하는 구조라 게이트가 성립하지 않는다.

원본 CLAUDE.md 는 "03-symbols 의 모든 entry 는 실제 AST 분석 결과(**환각 금지**)" 라고
선언하지만 **이를 검사하는 코드는 없다**(§5 의 docstring-vs-코드 함정과 같은 계열).

→ `gates/symbol_truth.py` 를 **신설**했다. Python `ast` 로 코드베이스를 실제로 파싱해
① 선언한 심볼이 코드에 있는지(환각) ② 시그니처가 맞는지 ③ **AST 가 찾은 공개 심볼 대비 선언
비율이 하한 이상인지**(과소 선언)를 본다. `api_coverage` 와 `symbol_truth` 는 **짝으로만 의미가
있다** — 하나만 켜면 반쪽이다.

**교훈**: 비율을 재는 게이트를 만나면 **분모가 어디서 오는지** 물어라. 분모가 검사 대상 쪽에서
오면, 분모를 고정하는 게이트를 하나 더 세워야 한다.

### ⚠️ 부분 문자열 검사는 커버리지를 100%로 만든다
같은 게이트의 두 번째 결함. `keyword in api_text` — 문서 **전체에 대한 부분 문자열** 검사였다.
실측: 심볼 `run`·`get_config`·`parse_tree` 를 선언하고 본문에 "**running** 상태의 파이프라인에서
**get_configuration** 값을 **parse_tree_node** 로 넘긴다. 자세한 것은 추후 작성 예정" 만 써도
**3/3 = 100.0% PASS**. 아무것도 문서화하지 않았는데 하드게이트가 통과한다.

→ 심볼이 **제목으로 등장하고 본문이 일정 길이 이상**이어야 문서화로 인정한다(clause_completeness
의 "조항은 절 제목으로" 와 같은 규율). 목차 나열·"추후 작성" 은 문서가 아니다.

### ⚠️ 구조를 **결정**하는 것과 이미 있는 구조를 **서술**하는 것은 다르다
`docforge-architecture-writer` 를 `architect` 로 보낼 뻔했다. 이름이 같기 때문이다. 그러나
specflow 의 `architect` 는 **없던 구조를 결정**하고(설계), docforge 의 그것은 **이미 있는 코드의
구조를 서술**한다(문서). 후자는 `writer` 다. 반면 `dependency-graph-builder` 는 코드에서 구조를
**추출해 그린다** — §3 의 `diagrammer` 별칭이 이미 `architect` 이므로 그쪽이 맞다.

**교훈**: agent 이름의 명사가 아니라 **산출물에 대한 판단의 성격**으로 가른다.

### ⚠️ 이식 대상 게이트가 **애초에 고장나 있을 수 있다** — 정상 픽스처로 PASS 부터 확인하라
**[발견: legal-draft 변환, 2026-08-04]** legalforge 의 게이트 2종은 **둘 다 어떤 입력에도
FAIL** 하는 상태였다. 지금까지의 함정(느슨해서 통과시킨다)과 정반대다.

1. **`clause_completeness.py` — raw f-string 안의 정규식 수량자가 보간됐다.**
   `rf"^#{1,3}\s+…"` 에서 `{1,3}` 은 정규식 수량자가 아니라 **f-string 표현식**으로
   평가된다 → 튜플 `(1, 3)` → 실제 패턴 `^#(1, 3)\s+…`. **어떤 제목에도 맞지 않는다.**
   실측: `## 제1조 (당사자)` 가 명백히 있는 계약서에 `found=0/14`. 유일한 하드게이트가
   항상 FAIL 이므로 **finalize 가 영원히 차단**된다.
2. **`law_citation_check.py` — 탐욕 캡처 + WARN 이 곧 FAIL.**
   법령명 클래스 `[가-힣A-Za-z0-9\s·]+` 에 `\s` 가 있어 앞 문장을 삼킨다. 실측:
   "본 계약은 민법 제105조" → 법령명 **`본 계약은 민법`**. 화이트리스트는 당연히 빗나가고,
   docstring 이 "warns for unknowns; **doesn't fail**" 이라 했는데 코드는
   `return 0 if overall == "PASS" else 1` 이라 **WARN 도 exit 1** 이다. 둘이 겹쳐 정상
   문서도 반려된다.

→ 수량자를 f-string 밖으로 빼고, 법령명은 **조문 토큰 앞쪽에서 뒤로** 추출하며(화이트리스트
최장 접미사 매칭), WARN 을 실제로 WARN 이 되게 했다.

**교훈**: 검증은 양방향이다. **깨뜨린 픽스처가 FAIL 을 내는가**(느슨함 탐지)와 **정상
픽스처가 PASS 를 내는가**(고장 탐지)를 둘 다 확인하라. 후자를 건너뛰면 "게이트를 이식했다"고
기록해 놓고 실제로는 파이프라인을 막아 놓게 된다.

### ⚠️ 우리 운영 환경이 원본에 없던 게이트를 요구할 수 있다 — 저장소가 PUBLIC 이다
**[발견: legal-draft 변환, 2026-08-04]** legalforge 는 당사자 정보를 `_personal/` 에 두고
"commit 금지"를 **CLAUDE.md 에 지시**한다. 로컬 도구니까 그것으로 충분하다.

우리는 다르다. **Deliver 단계가 `reports/<MID>/` 를 커밋하고 `git push` 하며, 이 저장소는
PUBLIC 이다.** 계약서 초안에 당사자 주민등록번호·사업자등록번호가 남은 채 미션이 끝나면 그
순간 공개되고 **되돌릴 수 없다.**

→ `gates/legal_safety.py` 를 신설했다(고지 강제 + 개인정보 평문 차단). 초안은 플레이스홀더로
쓰고(`[갑의 사업자등록번호]`·`000-00-00000`) 실제 값은 저장소 밖에서 사람이 채운다.
`.gitignore` 에 `_personal/`·`reports/**/_personal/` 도 추가했다.

**교훈**: 원본의 위험 목록을 그대로 받지 말고 **우리 실행 환경에서 무엇이 달라지는지** 물어라.
같은 산출물이라도 로컬 파일과 공개 저장소 커밋은 위험의 종류가 다르다. patentforge 의 고지
승격과 같은 계열이다 — **도메인의 법적·안전 요구는 지시가 아니라 게이트로 올린다.**

### ⚠️ 원본이 "검사한다"고 선언한 것을 실제로는 검사하지 않는다 — docstring 과 코드를 대조하라
**[발견: policy-brief 변환, 2026-08-04]** policyforge 의 `evidence_grade.py` 는 docstring 과
CLAUDE.md 양쪽에서 "**모든 핵심 권고가 GRADE high/moderate 근거에서 유래**"함을 검증한다고
선언한다. 그런데 코드가 실제로 보는 것은 **"인용이 0건인가"** 뿐이다. low 근거 하나만 달고
유보 표현을 붙인 권고가 그대로 통과한다. 게이트 이름과 문서가 주는 안심이 가짜였다.

같은 파일에 **환각 인용 구멍**도 있었다 — `grades.get(eid)` 가 `None`(근거 목록에 없는 id)이면
low 도 very-low 도 아니므로 조용히 넘어간다. **`e99` 를 지어내도 PASS** 다.

→ 둘 다 FAIL 조건으로 승격했다(권고 절에 강근거 인용 1건 이상 · 미상 id 인용 금지). 픽스처로
확인: 권고 절이 low 근거만 인용 → `exit=1`, `e99` 인용 → `exit=1`.

**교훈**: 이식할 게이트는 **docstring 이 아니라 코드가 무엇을 세는지** 읽어라. 이름·주석·상위
문서가 모두 같은 말을 해도 그것이 구현됐다는 뜻은 아니다.

### ⚠️ 한국어 함정의 반대 얼굴 — 이번엔 정상 문서를 **반려**한다
patent-spec 에서는 영어 기준 정규식이 **놓쳐서**(거짓 PASS) 문제였다. policyforge 에서는 같은
원인이 **거짓 FAIL** 을 낸다.

- 인용·토큰 정규식 `\b(e\d+)\b` · `\bO\d+\b` · `\bs1\b` 은 조사가 붙은 `e1을`·`O2를`·`s1의`
  에서 전부 실패한다(`1`↔`을` 은 둘 다 `\w` 라 경계가 없다). 실측: 국문 문장에서 **인용을 한 건도
  못 읽는다.** 그 결과 ⓐ caveat·환각 검사가 통째로 무력화되고(거짓 PASS) ⓑ 동시에 "인용 0건"
  으로 정상 문서를 반려한다(거짓 FAIL). → lookaround `(?<![0-9A-Za-z])…(?![0-9A-Za-z])` 로 교체.
- **분량 규격도 마찬가지다.** 원본은 `brief: 1200~2400 words = 2~4쪽`인데 이는 영문 기준이다.
  국문 A4 1쪽은 **500~700 어절**(≈1,600자)이라 규격에 맞는 국문 브리프가 700~2,800 어절로
  나온다. 원본 하한을 그대로 쓰면 **잘 쓴 문서가 분량 미달로 반려**된다. → 국문 어절로 재보정하고
  기준을 템플릿 `policy` 로 옮겼다.

**교훈**: 원문 언어가 한국어면 **문자 단위 가정(경계·토큰·분량)을 전부 다시 계산하라.** 게이트가
느슨해지는 쪽만이 아니라 빡빡해지는 쪽으로도 무너진다.

### ⚠️ 병렬 워커가 통째로 실패하면 glob 기반 검사는 "검사할 것이 없어" 통과한다
`format_consistency_check.py` 는 `formats/*.md` 를 glob 해서 있는 파일만 검사했다. 워커 하나가
죽어 `memo.md` 가 아예 없으면 **검사 대상에서 빠지므로 PASS** 다. 산출물이 없는데 통과하는
게이트다. → SCOPE.md frontmatter 의 `formats:` 선언(없으면 정책값)과 대조해 **부재를 FAIL** 로.
patent_format 의 `jurisdictions` 검사와 같은 패턴이다 — **병렬 산출물은 "선언 목록 대비 존재"를
항상 확인하라.**

### ⚠️ 한 stage 가 Sam 게이트이면서 팬아웃일 수 있다 — 렌더러가 병렬을 숨겼다
policy-brief stage 9(Format Write)는 **집필 개시 승인 + 포맷 4워커**를 동시에 갖는 첫 stage다.
`render_mermaid`·`render_ascii` 가 표식을 `if sam_gate … elif parallel` 로 묶고 있어 **DAG 에서
병렬이 사라졌다**(본문 주입은 정상이라 동작에는 영향 없음 — 협상 중 Sam 이 보는 그림만 틀린다).
→ 표식을 누적하도록 고치고 회귀 테스트를 넣었다. 게이트 겹침(§5 첫 항목)과 달리 이것은
**정상 조합**이다 — 금지 대상이 아니라 표시 버그였다.

### ⚠️ 중간 Sam 게이트의 승인 요약이 부실하다 → **[2026-08-04 해소]**
`gate_keeper.gate_summary()`는 `upstream` 유무로 **진입/산출** 두 갈래만 나눴고, 산출 갈래는 `report.md`를 찾았다. 그래서 academic-paper의 중간 승인(stage 8, 대상=`outline.md`)은 산출 게이트로 오분류돼 요약이 파일 목록 나열로 떨어졌다.

**해결**: 템플릿이 `approval_artifact:`로 **승인 대상 파일을 선언**하고, `gate_summary`가 **3분기**(진입 / 중간 / 산출)로 갈리도록 고쳤다. 산출 갈래도 아키타입별 파일명(`report.md`·`draft.md`·`paper.md`)을 탐색한다. 새 템플릿에 중간 Sam 게이트를 둘 때는 **반드시 `approval_artifact`를 함께 선언하라** — 없으면 Sam이 무엇을 승인하는지 모른 채 승인하게 된다.

## 6. 진행 대장 (재개 지점 — 새 세션은 여기서 다음 대상을 고른다)

| # | 스킬 | 카테고리 | 원본 | 상태 | 템플릿 | 신규 profile |
|---|---|---|---|---|---|---|
| 1 | trendforge | domain | 8-stage · agents 14 | ✅ **proven** (A) | `trend-report.yaml` | 0 |
| 2 | paperforge | research | 8-stage · agents 12 | ✅ **draft** (B) | `academic-paper.yaml` | 0 |
| 3 | specflow | domain | 12-step · agents 12 | ✅ **draft (D) · 실행가능** | `webapp-build.yaml` | **3 생성완료**(architect·developer·tester) |
| 4 | reviewforge | research | 9-stage · agents 12 | ✅ **draft (B')** | `systematic-review.yaml` | 0 |
| 5 | litmonitor | research | 5-stage · agents 7 | ✅ **draft (E)** | `lit-monitor.yaml` | 0 |
| 6 | patentforge | domain | 8-stage · agents 11 | ✅ **draft (F)** | `patent-spec.yaml` | 0 |
| 7 | policyforge | domain | 9-stage · agents 14 | ✅ **draft (G)** | `policy-brief.yaml` | 0 |
| 8 | legalforge | domain | 8-stage · agents 13 | ✅ **draft (H)** | `legal-draft.yaml` | 0 |
| 9 | docforge | domain | 8-stage · agents 13 | ✅ **draft (I)** | `code-docs.yaml` | 0 (**예상 빗나감**) |
| 10 | lectureforge | domain | 9-stage · agents 15 | ✅ **draft (J)** | `lecture-course.yaml` | 0 |
| 11 | migrateforge | domain | 8-stage · agents 13 | ✅ **draft (K)** | `code-migration.yaml` | 0 (**기존 3종으로 충족**) |
| 12 | secforge | domain | 8-stage · agents 13 | ✅ **draft (L)** | `security-audit.yaml` | 0 (**예상 빗나감**) |
| 13 | agentforge | research | 9-stage · agents 12 | ⬜ **다음** | — | 예상 있음(평가 실행) |
| 14 | datasetforge | research | 9-stage · agents 14 | ⬜ | — | 예상 있음(변환·빌드) |
| 15 | reproforge | research | 8-stage · agents 12 | ⬜ | — | 예상 있음(환경 빌드) |
| 16 | simforge | research | 8-stage · agents 11 | ⬜ | — | 예상 있음(실행) |
| 17 | proposalforge | research | 9-stage · agents 15 | ⬜ | — | 0 예상 |
| 18 | rebuttalforge | research | 8-stage · agents 11 | ⬜ | — | 0 예상 |
| 19 | outreachforge | research | 8-stage · agents 12 | ⬜ | — | ? |
| 20 | slideforge | research | 8-stage · agents 10 | ⬜ | — | 예상 있음(시각화) |

**권장 순서**: 문서·조사 계열(4·5·7·17·18 — 신규 profile 0 예상)을 먼저 몰아서 하고, **개발·실행 계열(3·11·12·13·15·16)은 신규 profile 결정을 한 번에 모아서** 처리하는 편이 낫다. profile 신설은 Sam 승인 사항이라 왕복이 생기기 때문이다.

## 7. 신규 profile 후보 · 후속 과제 (쌓아두는 곳)

**신규 profile 후보** — Sam 승인 전까지 만들지 않는다. 발견될 때마다 여기에 추가:

| 후보명 | 근거 agent | 출처 스킬 | 왜 기존으로 안 되나 | 상태 |
|---|---|---|---|---|
| **`architect`** | `architect`·`erd-designer`·`diagrammer`·`wireframer`·`style-designer` (5종, tools 동일) | specflow | 설계는 집필(`writer`)도 종합(`synthesizer`)도 아니다 — 구조·스키마·화면을 **결정**한다. 산출이 문서지만 판단 성격이 다르다 | ✅ **생성 완료**(terra) |
| **`developer`** | `backend-dev`·`frontend-dev` (tools 동일) | specflow | **코드를 쓴다**(`Edit`). 기존 7종 중 파일을 수정하는 profile이 없다 | ✅ **생성 완료**(terra) |
| **`tester`** | `e2e-tester` | specflow | **실행 결과로 판정**한다(`Bash`+`playwright`). `reviewer`는 읽고 판단하지 구동하지 않는다. developer의 검증자 역할이라 분리 필수(작성자≠검증자) | ✅ **생성 완료**(**sol** — 검증자) |

> **[2026-08-04 Sam 승인·생성 완료]** `profiles-src/{architect,developer,tester}/`(SOUL·config) +
> `hermes profile create --clone-from {writer,writer,reviewer}` + `hermes-home/profiles/`에 배포.
> **profile 11종**(default 포함)으로 늘었고 `webapp-build.yaml`이 실행 가능해졌다.
> 검증자는 `gpt-5.6-sol`(fact-checker·reviewer·**tester**), 작성자 계열은 `gpt-5.6-terra`.
> 부트스트랩 목록은 [`profiles-src/README.md`](../profiles-src/README.md) 갱신됨.

**후속 과제 — [2026-08-04 전부 완료]**

| 과제 | 결과 |
|---|---|
| 신규 profile 3종 SOUL 작성 | ✅ 위 표. 원본 agent md를 재료로 삼되 **우리 역할 경계**(작성자≠검증자·범위 이탈 금지·게이트 신호)를 명시 |
| 객관 게이트 2종 신설 | ✅ `scripts/gates/doc_consistency.py`(R-id·S-id 추적 커버리지 + 비범위 누출 경고) · `scripts/gates/test_run.py`(results.json·시나리오 전건 pass·체크박스 완료). webapp-build의 `objective: []` → 채움. **이중 게이트 완성** |
| `bib_export.py` 이식 | ✅ `scripts/tools/bib_export.py` — **게이트가 아니라 산출 도구**라 `gates/`가 아닌 `tools/`에 뒀다(gate_keeper는 `gates/*.py`만 exit code로 판정). academic-paper Deliver body에서 호출 |
| `gate_summary()` 중간 게이트 | ✅ 템플릿이 `approval_artifact:`로 승인 대상을 선언하고 gate_summary가 3분기(진입/중간/산출)로 갈린다. 산출 게이트도 아키타입별 파일명(report/draft/paper.md) 탐색으로 일반화 |
| `lint_template.py` 분리 | ✅ 독립 CLI(`--all` 지원). 검사 로직은 `instantiate_template`에 두고 import — **단일 진실** 유지 |

**systematic-review 변환에서 나온 것 (2026-08-04)**
- ✅ `gates/prisma_counts.py`(PRISMA flow 카운트 항등식 + included 블록 수 + 배제사유 합계) ·
  `gates/prisma_checklist.py`(PRISMA 2020 27항목 커버리지, **국문 키워드 추가**) 이식
- ✅ `scripts/tests/test_gates.py` 신설(15종) — 게이트 판정이 조용히 느슨해지는 것을 막는다
- **미이식**: `meta_analysis.py`(효과크기 통합 — 판정 아닌 산출) · `latex_export.py`(LaTeX 변환) ·
  `papers_state.py`(큐 상태머신 — Kanban 이 대체). 메타분석은 필요해지면 `tools/`로 이식 검토

**lit-monitor 변환에서 나온 것 (2026-08-04)**
- ✅ `gates/seen_dedup.py`(멱등성 — 이미 본 논문 혼입·id 형식·워커 병합 중복) ·
  `gates/digest_shape.py`(항목 수·id 실재·요약 분량·행동 라벨)
- ✅ `tools/monitor_state.py`(미션 간 seen 로그) · `tools/relevance_score.py`(결정적 점수)
- ✅ `monitors/` 디렉터리 신설 + README(지속 상태 규약)
- **자체 발견**: `digest_shape.word_count`가 행동 줄의 **근거 부분을 요약 분량에 합산**해,
  한 줄 요약도 근거를 길게 쓰면 하한을 통과했다 → 행동 줄을 **줄 단위로 제거**하도록 수정
  (테스트가 먼저 잡았다)
- **미이식**: `history_archive.py`(Deliver 단계의 파일 이동으로 흡수 — 별도 스크립트 불요)

**patent-spec 변환에서 나온 것 (2026-08-04)**
- ✅ `gates/claim_consistency.py`(청구항 구성요소의 본문 뒷받침 + 종속항 참조 실재성·방향) ·
  `gates/patent_format.py`(관할별 필수 절 + **고지 문구 강제**)
- **이식 결함 2건 수정**(§5) — 절 파싱 조기 종료 · 한국어 요소 추출 무력화
- **미이식**: `bundle_export.py`(번들 조립 = Deliver 의 파일 작업) · `runs_state.py`(Kanban 이 대체) ·
  `prior_art_search_lib.py`(scout 의 검색 도구 — 우리는 Tavily 사용)
- **검증 순서 판단**: 청구항 정합성은 **관할 변환 전**에 잡는다. canonical 명세서가 틀린 채로
  4개 관할에 복제되면 재작업이 4배가 된다

**policy-brief 변환에서 나온 것 (2026-08-04)**
- ✅ `gates/evidence_grade.py`(근거 등급↔권고 정합 · 환각 인용 · 저근거 유보표현) ·
  `gates/stakeholder_coverage.py`(이해관계자 커버리지 + `interest`·`position` 기재 충실도) ·
  `gates/format_consistency.py`(포맷 간 권고 일치 + 국문 어절 분량 + 선언 포맷 부재)
- ✅ **원본 하드게이트 3종 중 1종은 이식하지 않았다** — `diversity_check.py` 는 우리
  `source_balance` + `recency_policy` 와 동일 기능이라 **템플릿 policy 블록으로 흡수**
- **이식 결함 5건 수정**(§5) — 환각 인용 통과 · 권고↔등급 미검사(선언만 있고 코드에 없음) ·
  한국어 조사에서 id/옵션 토큰 매칭 붕괴 · 영문 기준 분량 규격 · 병렬 산출물 부재 미검출
- ✅ 자체 도구 결함 1건 수정 — `render_mermaid`/`render_ascii` 가 `sam_gate` + `parallel`
  동시 stage 에서 팬아웃 표식을 숨겼다(표시 버그 · 동작 무영향)
- ✅ **깨뜨린 픽스처 14케이스 E2E 검증** — 정상 3 PASS + 고의 결함 11건 전부 `exit=1`
- **미이식**: `bundle_export.py`(번들 조립 = Deliver 의 파일 작업) · `runs_state.py`(Kanban 이 대체)
- **구조 판단**: 원본에 없는 **수집 단계를 신설**했다. policyforge 는 사용자가 문헌을 들고 오는
  전제(stage 2 가 곧바로 ingest)지만, 우리는 `sources_cited` 불변식과 카테고리 균형 게이트가
  있으므로 scout 가 발신 주체별로 모으고 curator 가 선별한 뒤 reader 가 읽는다

**legal-draft 변환에서 나온 것 (2026-08-04)**
- ✅ `gates/clause_completeness.py`(문서종류·도메인별 필수 조항이 **절 제목으로** 존재 +
  조항 명칭 별칭 + 선언 문서 부재) · `gates/law_citation.py`(법령 인용 형식·화이트리스트·
  조문 번호 타당성 + 자기 조항 참조 구별)
- ✅ **`gates/legal_safety.py` 신설** — 원본에 없다. 고지 강제 + **개인정보 평문 차단**.
  우리는 `reports/` 를 **PUBLIC 저장소에 push** 하므로 원본의 "`_personal/` commit 금지"
  지시로는 부족하다(§5). `.gitignore` 에 `_personal/`·`reports/**/_personal/` 추가
- **이식 결함 2건 수정 — 둘 다 "항상 FAIL"**(§5): raw f-string 안의 `{1,3}` 이 보간돼
  정규식이 깨진 하드게이트 · 법령명 탐욕 캡처가 앞 문장을 삼키고 WARN 이 exit 1
- ✅ 조항 taxonomy 를 `standard_clause_lib.py` 하드코딩에서 **템플릿 policy 로** 이관
- ✅ **깨뜨린 픽스처 16케이스 E2E 검증** — 정상 3 PASS + 고의 결함 10건 `exit=1` +
  **원본 결함 회귀 방어 3건**(별칭 조항명 · 문장 중간 법령 인용 · 플레이스홀더)
- **미이식**: `bundle_export.py`(번들 조립 = Deliver 의 파일 작업) · `runs_state.py`(Kanban)
- **검증 순서 판단**: 법령 인용 검증을 **구조 설계·집필 전**에 둔다(틀린 법령이 문서 종류
  수만큼 복제되면 재작업이 배가된다). Sam 중간 승인은 "조항 구성 확정 → 집필 개시"

**code-docs 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/api_coverage.py`(제목+본문 기준 커버리지 + 역방향 환각 경고) ·
  `gates/doc_links.py`(링크·앵커 무결성 + 상호 링크 하한)
- ✅ **`gates/symbol_truth.py` 신설** — Python `ast` 로 코드베이스를 실제 파싱해 대조.
  환각 심볼 · 시그니처 불일치 · **과소 선언**을 잡는다(§5). `api_coverage` 의 짝
- **이식 결함 4건 수정**(§5): 부분 문자열 검사로 100% PASS · 커버리지 분모의 자기결정 ·
  이미지가 깨진 링크로 잡힘 · 앵커 slug 가 GitHub 규칙과 달라 정상 앵커를 반려
- **신규 profile 0개 — 대장의 "예상 있음(코드 읽기)" 은 빗나갔다.** 코드를 **읽는** 것은
  여전히 `reader` 다(신규 후보 신호는 `Edit`·`playwright` 인데 docforge 에는 없다).
  §3 사전에 이 판정을 명시해 뒀다
- **이 아키타입만의 성질**: 근거가 웹 출처가 아니라 **코드**라 `sources_cited` 불변식과
  `source_balance`·`recency_check` 를 쓰지 않는다. 대신 AST 대조가 그보다 강하게 받친다 —
  **지금까지 변환한 것 중 사실성 검증이 가장 단단한 도메인**
- **미이식**: `bundle_export.py`(Deliver 의 파일 작업) · `runs_state.py`(Kanban) ·
  `symbol_extractor.py`(우리는 게이트 안에서 `ast` 로 직접 파싱)

**lecture-course 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/objective_coverage.py`(LO→주차·평가 양방향 + **빈 주차 검사** + LO 개수 범위) ·
  `gates/bloom_distribution.py`(교육 수준별 분포 · WARN/FAIL 분리 · 국문 단계 표기) ·
  `gates/course_consistency.py`(LO 정합 + 국문 주차 인식 + **성적 비중 합계**) ·
  `gates/content_accessibility.py`(대체 텍스트 + 불릿 단위 문장 길이)
- **원본 4종 전부에서 결함**(§5): 한국어 조사·국문 주차 표기 미인식 · 스치는 언급을 커버리지로
  셈 · 역방향(빈 주차) 미검사 · WARN 이 exit 1 · 선언 임계(≥10%)를 0% 일 때만 적용 ·
  **성적 비중 검사가 `pass` 죽은 코드** · 불릿을 문장 1개로 뭉쳐 슬라이드 오판
- ⚠️ **게이트 이름 충돌을 피했다** — 원본 `format_consistency_check.py` 는 우리 기존
  `format_consistency`(G 전용)와 이름만 같다. `course_consistency` 로 신설(§5)
- ✅ **깨뜨린 픽스처 18케이스 E2E 검증**(정상 4 + 결함 11 + 원본 회귀방어 3).
  **자체 결함 1건을 픽스처가 잡았다** — `units` 블록의 필드형 `week: 1` 을 주차로 인식하지
  못해 정상 입력이 FAIL 했다(§2⑧ '정상 픽스처로 PASS 확인'이 실제로 작동한 사례)
- **검증 위치 이동**: 설계 검증을 **집필 전**으로 당겼다(원본은 16주치 집필 후에 검사)
- **미이식**: `bundle_export.py`(Deliver) · `runs_state.py`(Kanban)

**code-migration 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/atomic_commit.py`(계획·실행 **두 모드** — 파일 겹침·롤백 선언·**실제 git log 대조**
  ·혼합 커밋) · `gates/test_pass_rate.py`(**기준선 대비 회귀** + 테스트 수 감소 차단) ·
  `gates/behavior_diff.py`(계획의 의도적 변경 id 참조 강제 + 지문 재실행 커버리지)
- **원본 3종 전부 결함**(§5) — 회귀를 못 잡는 회귀 게이트 · 계획을 읽고 안 쓰는 죽은 변수 ·
  커밋 메시지가 비면 형식 검사를 건너뜀. 앞의 둘은 **원본을 직접 돌려 실측 확인**했다
- ✅ **git log 대조 도입** — 원본은 "CI/sandbox 를 위해" 자기 신고만 봤지만, 우리는 대상
  저장소가 로컬에 있고 **`git log` 읽기는 읽기 전용이라 안전**하다(테스트 실행과 달리 임의
  코드 실행 통로가 아니다). 존재하지 않는 SHA·혼합 커밋을 잡는다
- ⚠️ **병렬을 의도적으로 제거**했다 — git 인덱스는 공유 자원이라 동시 커밋이 불가능하다(§5)
- ⚠️ **안전 규약을 템플릿에 명시** — 안전 루트·자기 저장소 금지·깨끗한 작업 트리·force push
  금지·코드 변경 직전 Sam 승인(§5)
- **신규 profile 0개** — 대장의 "예상 있음(개발·테스트)"은 아키타입 D 때 만든
  `architect`·`developer`·`tester` 로 충족됐다(§3 사전에 별칭 추가)
- ✅ **깨뜨린 픽스처 19케이스 E2E**(정상 4 + 결함 14 + 원본 회귀방어 1). 실제 git 저장소를
  만들어 SHA 대조·혼합 커밋까지 확인
- **미이식**: `migration_lint.py`(코드 스캔 보조 — reader 가 한다) · `bundle_export.py` ·
  `runs_state.py`

**security-audit 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/finding_completeness.py`(원본 GATE 1 을 **판정 방향을 뒤집어** 이식 — 건수가 아니라
  조치 가능성 + 선언 수치↔목록 대조) · `gates/owasp_coverage.py`(범주별 구조화 항목 + 근거) ·
  `gates/cve_remediation.py`(고위험 조치 명시 + **스캔 실행 증거**)
- ✅ **`gates/secret_redaction.py` 신설** — 커밋 대상 산출물의 비밀값 평문 차단 + 고지 강제.
  `legal_safety`(개인정보)와 같은 계열이나 패턴이 달라 **별도 게이트**로 뒀다(이름 충돌 교훈의 짝)
- **원본 3종 전부 fail-open**(§5) — 실측으로 확인했다. 특히 GATE 2 는 "A01…A10 은 앞으로
  점검할 예정" 한 줄에 **커버리지 10/10** 을 줬다
- ⚠️ **공개 범위 분리** — `_private/`(상세·gitignore) ↔ `report/`(요약·커밋). `.gitignore` 에
  `_private/`·`reports/**/_private/` 추가. Deliver 의 Sam 승인에 "무엇이 커밋되는가"를 명시
- **신규 profile 0개 — 대장의 "예상 있음(스캐너)"은 빗나갔다.** 이 하네스의 스캐너는
  `Grep`/`Glob` 로 소스를 읽어 분류한다 = `reader`(docforge 와 같은 판정). 실제 스캐닝 도구
  (semgrep·trivy)를 붙이면 그때는 **실행 결과로 판정하는** `tester` 계열이 될 것이다
- ✅ **깨뜨린 픽스처 22케이스 E2E**(정상 4 + fail-open 3 + 결함 12 + 설계 회귀방어 2 + 원본
  회귀방어 1). 픽스처가 **자체 결함 2건**을 잡았다 — 블록 부재 시 exit 1 을 내 문서화한
  계약(exit 2)과 어긋났다
- **미이식**: `bundle_export.py` · `runs_state.py`

**새 후속 과제** (다음 세션 이후)
- `test_run.py`는 테스트를 **실행하지 않는다** — Tester가 남긴 `results.json`을 검사할 뿐이다. 게이트키퍼가 미션 코드를 임의 실행하면 임의 코드 실행 통로가 되기 때문. 자기보고 신뢰 구간이 남아 있으므로, CI 연동 등 **독립 실행 경로**가 생기면 교체 검토
- `webapp-build`는 아직 **라이브 미션 미실행**(`maturity: draft`) — 실미션 1회로 `tested` 승격 필요
- `test_pass_rate`·`behavior_diff`는 **테스트를 실행하지 않는다** — Tester 가 남긴 보고를
  검사할 뿐이라 자기보고 신뢰 구간이 남는다(`test_run` 과 같은 한계 · docs/13 §7).
  `atomic_commit` 만 실제 git 과 대조한다(읽기 전용이라 안전). CI 연동 등 **독립 실행 경로**가
  생기면 교체 검토
- **아키타입 A~F 의 게이트에는 E2E 하네스가 없다** — 이 하네스 규율은 G(policy-brief)부터
  생겼다. `recency_check`·`source_balance`·`prisma_*`·`seen_dedup`·`digest_shape`·
  `claim_consistency`·`patent_format`·`doc_consistency`·`test_run` 은 단위 테스트만 있다.
  한가할 때 소급해 하네스를 만들면 좋다(우선순위 낮음 — 이미 라이브 미션으로 실증된 A 제외)
- **보안 스캐너를 실제 도구로 교체할 때** `tester` 계열 profile 이 필요해질 수 있다
  (semgrep·trivy 등 실행 결과로 판정). 지금은 `reader` 의 패턴 검토라 불필요 — 실제 도구를
  붙이는 미션이 생기면 §3 신호(실행 판정)로 재평가
- `symbol_truth`는 **Python 만 AST 파싱**한다. JS/TS·Java 코드베이스는 검증자(LLM)가 읽어야
  하므로 객관 게이트가 그만큼 얇아진다. 다국어 코드베이스 미션이 실제로 생기면 언어별 파서
  (tree-sitter 등) 도입을 검토 — 지금 넣으면 쓰지도 않을 의존성이 늘어난다

## 8. 다음 세션 재개 방법

### 8.0 현재 상태 스냅샷 (2026-08-04 세션 종료 시점)

| 항목 | 값 |
|---|---|
| HEAD | secforge → L · 그 앞: migrateforge→K · lectureforge→J · docforge→I · legalforge→H · policyforge→G |
| 변환 | **12/20** · 다음 = **agentforge**(§6 대장 #13 — 신규 profile 예상 있음(평가 실행)) |
| 미커밋 | 없음 (push 완료) |
| 컨테이너 | `hermes-solomon` · `hermes-gatekeeper` 2개 Up |
| Slack | **현재 정상**(컨테이너 Web API `ok=true` · team=my-hermes-company). 단 **간헐 재발 중** — 게이트키퍼 WARN(DNS 실패→타임아웃)이 하루 동안 산발했고 마지막 WARN 후 복구됨. 호스트·컨테이너 모두 `slack.com` HTTP 200. **네트워크성**이며 토큰·설정 문제 아님(진단 순서 `docs/10 §4.3`) |
| Kanban | 전부 `done`(54/54) · 활성 게이트 없음 · 잔여 테스트 카드 없음 |
| 테스트 | **159종 통과**(29 템플릿 + 21 게이트키퍼 + 109 게이트) · 린터 12/12 · **E2E 하네스 6종 103케이스 전건 통과**(`scripts/tests/fixtures/run_all.py`) |
| 라이브 미션 | **A(trend-report)만 실증**(M-2026-003·004). 나머지 11종은 `draft` — Sam 지시로 **전체 변환 후** 하나씩 실행 |
| ⚠️ 신규 | 저장소가 **PUBLIC** 임을 전제한 개인정보 게이트(`legal_safety`) 도입 · `.gitignore` 에 `_personal/` |

### 8.1 절차

1. **읽는다**: 이 문서 §6(다음 대상) → §2(레시피) → §5(함정) → 대상 스킬의 `SKILL.md`
2. **변환한다**: `templates/<name>.yaml` 작성. `templates/academic-paper.yaml`을 참고본으로 삼는다(주석에 변환 판단 근거가 남아 있다)
3. **게이트를 이식한다** — 이 단계에서 결함이 나온다(12건 변환에서 12건 모두).
   - 먼저 **이름 충돌 확인**: `ls scripts/gates/` — 같은 이름에 덮어쓰면 먼저 있던 아키타입이
     조용히 망가진다(§5).
   - **원본을 직접 돌려 보라.** `python3 <원본>.py <인자>` 로 정상 입력과 쓰레기 입력을 넣어
     본다. 지금까지 나온 결함의 절반은 이 한 번으로 드러났다(fail-open · 항상 FAIL ·
     회귀 미탐지).
   - **docstring 과 코드를 대조**하라. "A 를 B 와 대조한다"고 쓰여 있으면 **B 를 담은 변수가
     판정식에 등장하는지** 눈으로 확인한다(죽은 변수·`pass` 본문이 실제로 있었다).
4. **검증한다**:
   ```bash
   # ① 불변식 린터(가장 빠른 피드백 — 협상 중에도 반복 호출)
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_template.py <name>'
   # ② DAG 미리보기(비파괴)
   docker exec hermes-solomon sh -c 'cd /work/company && \
     python3 scripts/instantiate_template.py <name> M-2026-TEST --dry-run --render mermaid'
   # ③ 회귀(단위)
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/test_gates.py'
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/test_instantiate_template.py'
   # ④ ★ 깨뜨린 픽스처 E2E — 새 아키타입마다 하네스를 만든다
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'
   ```
   **④가 이 절차의 핵심이다.** `scripts/tests/fixtures/`에 아키타입별 하네스를 두고
   **정상 픽스처(PASS 기대) + 고의로 깨뜨린 픽스처(FAIL 기대) + 원본 결함의 회귀 방어**를
   함께 돌린다. 기존 하네스(`policy`·`legal`·`docs`·`lecture`·`migrate`·`sec`)를 본으로 삼아
   새 파일을 만들고 `run_all.py`의 `HARNESSES`에 등록하라. 상세는
   [`scripts/tests/fixtures/README.md`](../scripts/tests/fixtures/README.md).

   불변식 위반 0 · 테스트 통과 · 하네스 전건 통과 · `reports/M-2026-TEST/` 미생성 ·
   미등록 profile 경고가 뜨면 템플릿의 `requires_profiles:`와 일치하는지 확인(§7에 후보로 등재)
5. **갱신한다**: §6 대장(상태·템플릿명·신규 profile) · §3 매핑 사전에 별칭 추가 · 새 함정이 있으면 §5
6. **커밋한다**: `feat(template): <name> → 아키타입 <X>` + `history.html` 기록

**한 세션에 2~3종이 적당하다.** 스킬 하나가 300줄 안팎이고, 변환 판단(§2②)은 원본을 실제로 읽어야 나온다.
