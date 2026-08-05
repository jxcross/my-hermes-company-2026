# 13. harness 스킬 → 템플릿 YAML 변환 — 작업 절차서

> 작성일: 2026-08-04(갱신 2026-08-05) · 상태: **작업 중(18/20 — A·B·B'·D·E·F·G·H·I·J·K·L·M·N·O·P·Q·R 전부 실행가능, 라이브 미션은 A만)** · 성격: working doc(재개 가능)
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

현재 보유 게이트(55종): `recency_check` · `source_balance` · `doc_consistency` · `test_run` ·
`prisma_counts` · `prisma_checklist` · `seen_dedup` · `digest_shape` · `claim_consistency` ·
`patent_format` · `evidence_grade` · `stakeholder_coverage` · `format_consistency` ·
`clause_completeness` · `law_citation` · `legal_safety` · `symbol_truth` · `api_coverage` ·
`doc_links` · `objective_coverage` · `bloom_distribution` · `course_consistency` ·
`content_accessibility` · `atomic_commit` · `test_pass_rate` · `behavior_diff` ·
`owasp_coverage` · `cve_remediation` · `finding_completeness` · `secret_redaction` ·
`eval_set_quality` · `stat_significance` · `repro_determinism` · `run_completeness` ·
`pii_presence` · `license_compat` · `schema_conformance` · `datasheet_completeness` ·
`result_tolerance` · `env_consistency` · `install_evidence` · `reproduce_doc` ·
`bit_exact` · `solver_pin` · `doe_completeness` · `analysis_integrity` ·
`proposal_format` · `budget_integrity` · `call_alignment` · `proposal_traceability` ·
`comment_fidelity` · `comment_coverage` · `change_consistency` · `response_quality`.
산출 도구는 `scripts/tools/`: `bib_export` · `monitor_state` · `relevance_score` · `budget_build`.
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
| `default` (Solomon) | clarify · scope-interview · finalize · deliver · orchestrate | `AskUserQuestion` | `paperforge-clarify-topic` · `paperforge-finalize` · `trendforge-clarify-scope` · `trendforge-finalize` · `reviewforge-{clarify-question,finalize}` · `litmonitor-seed-config` · `patentforge-{clarify-application,finalize}` · `policyforge-{clarify-issue,finalize}` · `legalforge-{clarify-doc,finalize}` · `docforge-{clarify-scope,finalize}` · `lectureforge-{clarify-course,finalize}` · `migrateforge-{clarify-migration,finalize}` · `secforge-{clarify-scope,finalize}` · `agentforge-{clarify-task,finalize}` · `datasetforge-{clarify-intent,finalize}` · `reproforge-{clarify-target,finalize}` · `simforge-{clarify-hypothesis,finalize}` · `proposalforge-{clarify-call,finalize}` · `rebuttalforge-{clarify-context,finalize}` |
| `scout` | gather · ingest · collect · scan · search · survey · **map(외부 사실 조사)** | `WebSearch` `WebFetch` | `paperforge-scope-survey` · `paperforge-gather-{arxiv,web,recent}` · `trendforge-landscape-survey` · `trendforge-gather-{academic,industry,patents,news}` · `reviewforge-{search-protocol,search-database}` · `litmonitor-scan-{arxiv,scholar,openreview}` · `patentforge-prior-art-{academic,patent}-scan` · `policyforge-context-mapping` · `legalforge-legal-research` · `secforge-dep-cve-scanner` · `agentforge-corpus-prep`(**수집 부분** — 정규화·청킹은 `curator` 로 갈랐다) · `proposalforge-{academic-scan,funded-scan,patent-scan}`(갈래가 달라도 '출처를 모은다' 는 계약은 같다 = 워커) |
| `reader` | read-extract · analyze · classify · appraise · ingest · **grade** | — | `paperforge-read-extract` · `trendforge-read-extract` · `reviewforge-{data-extract,quality-appraise}` · `patentforge-ingest-invention` · `policyforge-literature-ingest` · `legalforge-ingest-context` · `docforge-{ingest-codebase,parse-symbols}`(**코드를 읽는 것도 reader 다**) · `lectureforge-ingest-source` · `migrateforge-ingest-codebase` · `secforge-{ingest-target,owasp-scanner,cwe-scanner,secrets-scanner}`(**패턴 스캐너도 reader 다**) · `agentforge-eval-set-build`(코퍼스에서 gold Q-A 를 **추출**한다 — 지어내면 안 되는 것이 이 역할의 규율이다) · `datasetforge-{ingest-source,license-scan,pii-scan}`(**라이선스 등급 판정도 `grade` 다**) · `reproforge-{ingest-source,env-detect}` · `proposalforge-context-gather` · `rebuttalforge-parse-reviews`(리뷰어 원문을 코멘트로 **분해**한다) |
| `curator` | dedup · filter · screen · normalize · cite-pack · cross-link | — | `reviewforge-prisma-screening` · `litmonitor-relevance-filter` · `docforge-cross-linker`(동사 신호에 `cross-link` 가 이미 있었다) · `lectureforge-accessibility-pass`(읽고 마는 감사가 아니라 **정비**로 만들었다) · `agentforge-corpus-prep`(**정규화·중복제거·청킹 부분**) · `rebuttalforge-categorize`(분류에 더해 **리뷰어 간 중복 지적을 상호 연결**한다 — cross-link 가 이 profile 의 verb 다) · `datasetforge-clean-normalize`(dedup·normalize 가 이 profile 의 verb 집합 그대로다) · *(다른 스킬엔 대개 없어 우리가 보강)* |
| `synthesizer` | synthesize · outline · structure · summarize · gap-analysis · **options-design** | — | `paperforge-synthesize-outline` · `trendforge-synthesize-trends` · `reviewforge-synthesize` · `litmonitor-action-suggest` · `proposalforge-{gap-synthesizer,narrative-design}` · `simforge-analyze`(출력 통합 + 민감도 종합) · `patentforge-gap-analyzer` · `policyforge-{evidence-synthesize,options-design}` · `legalforge-{structure-design,risk-disclosure}` · `lectureforge-{learning-objectives,course-structure,assessment-design}` · `secforge-severity-classifier` |
| `writer` | draft · write · compose · section · adapt · **apply-changes** | — | `rebuttalforge-{address-comment,apply-changes,cover-letter}`(**원고에 수정을 반영하는 것도 `writer` 다** — 코드가 아니라 산문이므로 `developer` 가 아니다) · `proposalforge-section-writer` · `datasetforge-datasheet-writer` · `paperforge-draft-section` · `trendforge-draft-section` · `litmonitor-summarize` · `patentforge-{specification-writer,jurisdiction-adapter}` · `policyforge-{brief,report,memo,infographic}-writer` · `legalforge-{contract,opinion,advisory,terms}-writer` · `docforge-{api-ref,architecture,adr,tutorial}-writer` · `lectureforge-{syllabus,slides,assignments,quiz}-writer` |
| `fact-checker` | fact-check · verify · evidence · recency · citation · **grade-check** | `Bash`(게이트 스크립트 실행) | `paperforge-fact-check` · `trendforge-{evidence-critic,recency-check}` · `reviewforge-evidence-coverage-check` · `patentforge-{claim-consistency-check,novelty-comparison-check}` · `policyforge-{evidence-grade-check,source-diversity-check}` · `legalforge-law-citation-check` · `docforge-accuracy-check` · `lectureforge-{objective-coverage-check,bloom-distribution-check}` · `migrateforge-{test-pass-rate-check,regression-check}` · `secforge-{critical-zero-check,cve-patched-check}` · `agentforge-{evidence-critic,stat-significance-check,reproducibility-check,eval-quality-check}` · `datasetforge-pii-license-recheck` · `reproforge-result-tolerance-check` · `simforge-{bit-exact-check,environment-audit,evidence-critic}` · `proposalforge-{call-alignment,feasibility-check}`(자격 요건 대조와 자원↔계획 정합은 **사실 검증**이다) · `rebuttalforge-{coverage-check,change-consistency-check}` |
| `reviewer` | review · critic · clarity · logic · style · bias · **coverage·consistency** | — | `paperforge-{logic-critic,style-edit}` · `trendforge-{clarity-check,bias-check}` · `reviewforge-{prisma-compliance-check,bias-balance-check,clarity-check}` · `patentforge-format-compliance-check` · `policyforge-{stakeholder-coverage-check,format-consistency-check}` · `legalforge-{clause-completeness-check,tone-style-check}` · `docforge-{api-coverage-check,clarity-check}` · `lectureforge-{accessibility-check,format-consistency-check}` · `migrateforge-atomic-commit-check` · `secforge-{owasp-coverage-check,report-clarity-check}` · `specflow` **Design Review(신설)** · `datasetforge-{schema-consistency-check,datasheet-completeness-check}` · `reproforge-{env-completeness-check,doc-clarity-check}` · `simforge-output-completeness` · `proposalforge-{innovation-check,format-compliance}` · `rebuttalforge-{tone-polish,argument-strength}` |
| `architect` | architect · erd · diagram · wireframe · style-design · dependency-graph · **migration-plan** | `Read,Write,Grep,Glob`(쓰기만·실행 없음) | `specflow-{architect,erd-designer,diagrammer,wireframer,style-designer}` · `docforge-dependency-graph-builder` · `migrateforge-migration-planner` · `secforge-stride-modeler` · `proposalforge-timeline-build`(간트는 그림이 아니라 **연차 배치 결정**이다) · `simforge-{solver-pin,design-of-exp}`(솔버 고정과 실험계획은 **결정**이다) · `agentforge-{index-build,agent-design}`(검색 기반과 **비교 대상 집합을 결정**한다) · `datasetforge-schema-design`(없던 스키마를 **결정**한다 — docforge 의 architecture-writer 가 서술이라 writer 였던 것과 갈린다) |
| `developer` | backend-dev · frontend-dev · implement · build · **transform-execute** | **`Edit`** + `Bash` | `specflow-{backend-dev,frontend-dev}` · `migrateforge-transform-executor` · `agentforge-system-builder` · `datasetforge-{hf,parquet,csv}-converter`(변환 코드를 쓰고 돌린다) · `proposalforge-budget-build`(명세를 쓰고 산출 도구를 돌린다) · `reproforge-{docker,conda,pip}-builder`·`reproforge-script-builder` · `simforge-visualize`(그림을 그리는 **코드**를 쓴다) |
| `tester` | e2e-test · run · regression · verify-by-execution · **baseline-snapshot** | **`mcp__playwright__*`** + `Bash` | `specflow-e2e-tester` · `migrateforge-{baseline-snapshot,regression-test-runner,behavior-diff-checker,new-test-generator,type-check-runner}` · `agentforge-run-evaluator`(코드를 **돌려서** 지표를 낸다) · `reproforge-install-test`(실제로 설치·실행해 재측정한다) · `simforge-run-worker` |

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

> **[2026-08-05 여섯 번째 · agent-eval]** agentforge 는 평가셋 품질을 **전 시스템을 구현하고
> 전 run 을 돌린 뒤**(stage 8)에야 검사한다. 거기서 FAIL 이면 **LLM API 비용이 그대로 두 배**다.
> 재작업 비용이 사람의 시간이 아니라 **돈**인 아키타입에서는 이 판단이 더 분명해진다 —
> 평가셋 검증을 구현·실행 **전**(stage 6)으로 옮겼다.

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

### ⚠️ 게이트가 "다른가"를 재고 "더 나은가"를 재지 않는다 — 방향 없는 유의성 검정
**[발견: agent-eval 변환, 2026-08-05]** agentforge 의 GATE 2 는 제안 시스템이 기준보다 나은지를
증명하는 게이트다. 그런데 판정식이 이렇다:

```python
ci_excludes_zero = (ci_lo > 0) or (ci_hi < 0)     # 방향 무관
effect_ok = abs(d) >= args.min_effect             # 절댓값
```

**퇴보할수록 확실하게 통과한다.** 실측(50문항 · 제안이 30%p 하락):

```
mean diff (proposed - baseline): -0.2951
Cohen's d: -11.157  (threshold 0.2)  OK
bootstrap CI (95%): [-0.3023, -0.2882]  OK
verdict: PASS   exit=0
```

개선을 주장하려고 만든 논문 산출물이 **성능 퇴보를 통계적으로 입증한 채 finalize** 된다.
→ `higher_is_better` 축을 넣고 개선 방향의 CI 하한만 인정한다.

**교훈**: 비교 게이트를 이식할 때 **"어느 쪽이 이겨야 통과인가"가 코드에 있는지** 보라.
`abs()` 와 `or` 는 방향을 지우는 흔한 자리다. 통계 검정은 기본이 양측(two-sided)이라
**아무 생각 없이 옮기면 방향이 사라진다.**

### ⚠️ 이번엔 대조 대상을 담은 **변수조차 없었다**
`repro_check.py` 의 docstring 은 "raw.jsonl row count matches **gold set count**" 를 검증한다고
선언한다. 그런데 코드가 비교하는 것은 `metrics.n_items` — **그 run 이 스스로 적어 낸 숫자**다.
50문항 중 2문항만 돌리고 `n_items: 2` 라 쓰면 통과한다. 실측: 파일 전체에서 문자열 `gold` 는
**docstring 12행에 한 번 나오고 코드에는 없다**(`--gold` 인자 자체가 없다).

migrateforge 의 죽은 변수(§5)보다 한 단계 더 나아간 형태다 — 거기서는 `plan_text` 를 읽기라도
했는데 여기는 **읽는 시늉도 없다.** 그런데 docstring 만 보면 더 그럴듯하다.

**교훈**: docstring 이 "A 를 B 와 대조한다"고 하면 **B 가 어디서 오는지 인자 목록부터 보라.**
B 를 받을 통로가 없으면 그 대조는 존재하지 않는다.

### ⚠️ 해시를 **존재만** 확인하는 무결성 게이트 — 0 을 64자 적어도 통과한다
**[발견: sim-experiment 변환, 2026-08-05]** simforge 의 Gate 2(bit-exact)는 재현성의 핵심이다.
그런데 hash-only 모드에서 하는 일은 `runs/<id>/output.hash` **파일이 있는가**뿐이다. 실측:
실제 출력이 들어 있는 `outputs/` 옆에 `output.hash` 로 **`0` 을 64자** 적어 넣어도
`no hash-mode issues · PASS · exit=0`.

해시는 **무언가를 가리킬 때만** 무결성 장치다. 가리키는 대상을 확인하지 않으면 장식이다.

→ 우리는 `outputs/` 를 **실제로 읽어 같은 알고리즘으로 다시 계산해 대조**한다.
**파일을 읽는 것은 코드 실행이 아니므로 게이트가 해도 안전하다**(솔버 재실행과 다르다).
원본보다 강한 검사를 실행 없이 얻은 셈이다.

**교훈**: 체크섬·서명·지문을 다루는 게이트를 만나면 **그것을 다시 계산하는 코드가 있는지**
보라. 없으면 그 값은 아무나 적을 수 있는 문자열이다. 그리고 우리가 **읽기만 해서 다시 계산할
수 있는 것**은 자기보고에 맡기지 마라 — 실행 없이 검증할 수 있는 자리는 드물고 귀하다.

### ⚠️ CLI 옵션으로 광고까지 하는 죽은 검사
같은 게이트의 두 번째 결함. docstring 은 "run_inputs hash matches the input recorded in
03-doe.md (**no input drift**)" 라 하고, argparse 에도
`--doe`(`help="optional: 03-doe.md for input drift check"`)가 있다. 그런데 **`args.doe` 를
참조하는 코드가 한 줄도 없다.** 존재하지 않는 경로를 줘도 아무 말이 없다.

migrateforge 의 죽은 변수 · agentforge 의 죽은 gold-set 대조와 같은 계열인데 **가장
그럴듯하다** — `--help` 에까지 나오므로 쓰는 쪽은 그 검사가 있다고 믿는다.

**교훈**: docstring 다음으로 **argparse 옵션 목록과 코드 본문을 대조**하라. 받기만 하고 쓰지
않는 인자는 "이 검사는 없다"는 표시다.

### ⚠️ 표가 스스로를 선언하고 스스로를 만족시킨다 — 회계가 **내부적으로** 일관해질 때
**[자체 결함 · 픽스처가 잡았다]** `doe_completeness` 를 만들 때 "설계점 ↔ run 대조"만
넣었다. 그런데 픽스처에서 **설계점을 DOE 표에서도 지우고 run 도 지우니** 6→5 로 줄어든 채
**완벽히 일관**해져 PASS 했다.

파라미터 스윕에서 이것은 결과를 바꾼다 — 수렴하지 않는 구간을 통째로 없애면 그래프가 예뻐진다.
code-docs 의 '분모 자기결정'과 같은 계열이되 **한 단계 위**다: 거기서는 분모를 적게 세었고
여기서는 분모 자체를 다시 썼다.

→ `doe.md` 가 `n_design_points:` 를 **명시**하게 하고 블록 길이와 대조한다. 분모를 고정하는
선언을 따로 두면 나중에 조용히 줄일 수 없다.

**교훈**: "A 와 B 를 대조한다"는 게이트에서 **A 와 B 를 같은 주체가 같은 시점에 쓴다면**
그 대조는 성립하지 않는다. 둘 중 하나를 **더 이른 시점의 선언**에 묶어라.

### ⚠️ 검증 파이프라인이 **실패한 실행을 성공으로 판정**한다
**[발견: repro-package 변환, 2026-08-05]** reproforge 의 유일한 하드게이트는 재현된 수치가
허용오차 안인지 본다. 그런데 설치 테스트 보고서에서 `measurements:` 블록의 숫자만 읽는다.
실측 — 아래 보고서가 `overall: PASS · exit=0` 이다:

```
docker build: FAILED (base image not found)
smoke test: NOT RUN
measurements:
  accuracy: 0.873
```

**아무것도 재현되지 않았는데 재현됐다고 판정한다.** 재현 가능성을 증명하려고 만든
파이프라인에서 이보다 정확히 반대되는 결과는 없다.

→ `run_status:` 를 함께 읽어 성공이 아니면 반려하고, 실행 사실 자체를 요구하는
`install_evidence` 를 신설했다(방식·종료코드·소요·환경 지문·로그 발췌).

**교훈**: 게이트가 읽는 것이 **결과값**인지 **결과값 + 그 값이 나온 경위**인지 보라.
숫자만 읽는 게이트는 숫자를 적을 수 있는 누구에게나 통과된다. 특히 **그 숫자를 적는 주체가
검사 대상**일 때는 경위가 판정의 일부여야 한다.

### ⚠️ 필드 하나를 빼면 그 항목이 검사에서 사라진다 — 검사 대상이 검사 범위를 정한다
같은 게이트의 두 번째 결함. `parse_targets` 는 `expected:` 가 없는 항목을 `continue` 로
건너뛴다. 실측: `- metric:` 을 3개 선언하고 그중 2개에서 `expected:` 만 지우면

```
targets: 1, measured: 1, within: 1 · overall: PASS · exit=0
```

보고서에 **"targets: 1"** 로 찍혀 원래 3개였다는 사실조차 남지 않는다. code-docs 의
'분모 자기결정'과 같은 계열이되 더 은밀하다 — 거기서는 분모를 **적게 세었고**, 여기서는
분모가 **아예 없었던 것처럼** 보인다.

→ 선언된 `- metric:` **개수**와 파싱된 항목 수를 따로 세어 대조한다.

**교훈**: 파서에 `continue`·`skip`·`if not x: pass` 가 있으면 **건너뛴 것을 세는 코드가
있는지** 보라. 없으면 그 게이트의 검사 범위는 검사 대상이 정한다.

### ⚠️ 우리가 못 하는 검증은 **못 했다고 말하게** 만든다
우리 컨테이너에는 docker 데몬이 없다(실측: `docker info` 실패 · 소켓 부재). 그리고 붙이지
않는다 — **docker 소켓을 미션에 주는 것은 호스트 root 권한을 주는 것**이다. 그래서 이
아키타입의 설치 테스트는 `venv` 로만 하고 Dockerfile 은 정적 검토만 한다.

문제는 그것을 조용히 넘어가면 번들을 받는 사람이 "Docker 로 재현된다"고 읽는다는 것이다.
→ `install_evidence` 가 `docker_verified: false` 선언과 **release-notes 의 공시**를 함께
요구한다. 선언만 하고 공시하지 않으면 FAIL 이고, 검증하지 않은 것을 `true` 라고 적어도 FAIL 이다.

아키타입 N 의 "검사할 수 없는 형식은 검증되지 않은 산출물이다"의 짝이다. 거기서는 **막았고**
여기서는 **공시하게 했다** — 산출물의 성격이 다르기 때문이다(데이터의 개인정보는 새면
사고지만, Docker 미검증은 알리면 되는 한계다).

**교훈**: 환경 제약으로 검증하지 못하는 경로가 생기면 셋 중 하나를 골라라 —
**막거나**, **공시를 강제하거나**, **제약을 없애거나**. 조용히 넘어가는 네 번째 선택지는
"검증됐다"는 인상만 남긴다.

### ⚠️ 문서 제목이 절 별칭과 겹쳐 진짜 절을 가린다
**[자체 결함 · 픽스처가 잡았다]** `reproduce_doc` 의 절 매칭이 `# 재현 절차`(문서 H1 제목)를
'run' 절로 잡아 `## 실행` 절을 덮었다. 그래서 정상 REPRODUCE.md 가 "설명이 37자"로 반려됐다.
제목에 문서의 주제어가 들어가는 것은 **완전히 정상**인데, 별칭 매칭이 heading level 을 보지
않아 생긴 일이다. → 하위 제목(H2+)을 우선하도록 고쳤다.

**교훈**: 제목 기반으로 절을 찾는 게이트는 **문서 제목도 제목이라는 것**을 계산에 넣어야
한다. lecture-course 의 `week: 1` 필드형 미인식과 같은 계열 — 정상 입력의 흔한 형태를
픽스처에 넣지 않으면 드러나지 않는다.

### ⚠️ 샘플링하는 게이트는 게이트가 아니다 — 첫 샤드만 스캔했다
**[발견: dataset-release 변환, 2026-08-05]** datasetforge 의 유일한 하드게이트는 최종 데이터에서
개인정보를 다시 찾는 것이다. 그런데 대상을 이렇게 고른다:

```python
shards = sorted((formats_dir / "parquet").glob("data-*.parquet"))
if shards:
    return shards[0]          # ← 첫 샤드 하나
```

샤드 100개짜리 데이터셋이면 **1%만 검사하고 PASS** 한다. 게다가 대상은 parquet(또는 HF 샤드)
**한 갈래뿐**이라 같은 파이프라인이 만드는 CSV·JSONL 산출물은 아예 보지 않는다. 세 포맷으로
내보내면서 두 포맷이 미검사다.

**교훈**: 게이트가 **무엇을 대상으로 고르는지**를 반드시 읽어라. `[0]`·`next(...)`·`first`·
`sample` 이 보이면 그 게이트는 전수 검사가 아니다. 개인정보·비밀값처럼 **한 건이면 사고**인
도메인에서 샘플링은 검사가 아니라 요행이다.

### ⚠️ 검사할 수 없는 형식을 산출하면 게이트가 아니라 신뢰가 된다
같은 자리의 우리 쪽 문제. 우리 컨테이너에는 pandas·pyarrow 가 없어 **parquet 을 읽을 수 없다.**
읽지 못한 파일을 조용히 건너뛰면 원본의 샤드 함정을 형태만 바꿔 되풀이하게 된다.

→ `pii_presence` 는 **읽을 수 없는 데이터 파일이 있으면 FAIL** 한다. 그리고 템플릿의 기본
산출 포맷을 stdlib 로 읽히는 `.jsonl`/`.csv` 로 정했다(parquet 을 내보내려면 `pyarrow` 를 먼저
설치하라는 뜻이다).

**교훈**: 도구가 확인할 수 없는 산출물은 **검증되지 않은 산출물**이다. "우리 환경에서 검사
가능한 형식"이 아키타입의 산출 규격을 정하는 일이 있다 — 그것을 템플릿에 명시하라.

### ⚠️ `# safe default` 주석이 달린 자리가 정확히 구멍이었다
같은 하드게이트의 라이선스 절반:

```python
license_severity = license_report.get("verdict", "red")   # safe default
```

방어적으로 보인다. 그런데 `parse_license_report` 는 파일이 없을 때
`{"verdict": "missing"}` 를 돌려준다 — **키가 있으므로 기본값 `red` 는 절대 쓰이지 않는다.**
실측: 라이선스 보고서가 아예 없으면 `severity="missing"` → `missing != "red"` → **PASS**.
게다가 원본 CLAUDE.md 가 선언한 "`unknown` 이면 `red` 로 취급" 도 코드에 없어
`verdict: unknown` 역시 통과한다(실측).

**교훈**: **fallback 이 실제로 도달 가능한지 확인하라.** `.get(k, safe)` 앞에서 `k` 를 항상
채워 넣는 코드가 있으면 그 안전장치는 죽어 있다. 주석은 의도를 말하지 보증하지 않는다.

### ⚠️ "아무 데도 선언하지 않으면 일관됨" — 공집합이 통과하는 자리
같은 게이트의 세 번째 결함:

```python
license_consistent = len(declared_set) <= 1   # all same or all missing
```

주석이 스스로 밝히듯 **"all missing" 도 통과**다. 라이선스 전파를 검증하는 게이트가
**라이선스가 전무할 때** 통과한다. 실측으로 확인했다.

**교훈**: 집합의 크기로 일관성을 재는 코드를 보면 **빈 집합에서 무슨 일이 일어나는지** 물어라.
`len(s) <= 1` · `all(...)` · `not any(...)` 는 전부 공집합에서 참이다. 이 계열은 이번이
세 번째다(secforge 의 빈 블록, agentforge 의 0 runs).

### ⚠️ 커밋되는 것이 문서만이 아닌 아키타입 — 비밀값 검사의 확장자를 넓혀야 한다
아키타입 L 의 `secret_redaction` 은 `.md` 만 훑는다. 보안 감사의 산출물이 문서뿐이라 그것으로
충분했다. 그런데 agent-eval 은 **코드와 설정을 커밋한다** — `src/<system>/config.yaml` 이나
`runs/<id>/config.json` 에 API 키가 남으면 문서를 아무리 검사해도 잡히지 않는다.

→ 확장자를 `scan_extensions` 정책으로 뺐다(**기본값 `[".md"]` 이므로 L 의 동작은 그대로**).
고지 문구는 코드 파일마다 요구할 수 없으므로 `disclaimer_files` 로 대상을 좁히되, **선언한
파일이 없으면 FAIL** 이다(§5 '선언 목록 대비 존재').

**교훈**: 게이트를 재사용할 때 **"이 아키타입이 커밋하는 것의 종류"** 를 먼저 세어라. 같은
게이트라도 산출물의 형태가 달라지면 검사 범위가 달라진다. 새 게이트를 만드는 것보다
기존 게이트에 **정책 축을 하나 여는 편**이 낫다 — 이름이 겹치는 쌍둥이 게이트가 생기지 않는다.

### ⚠️ 중간 Sam 게이트의 승인 요약이 부실하다 → **[2026-08-04 해소]**
`gate_keeper.gate_summary()`는 `upstream` 유무로 **진입/산출** 두 갈래만 나눴고, 산출 갈래는 `report.md`를 찾았다. 그래서 academic-paper의 중간 승인(stage 8, 대상=`outline.md`)은 산출 게이트로 오분류돼 요약이 파일 목록 나열로 떨어졌다.

**해결**: 템플릿이 `approval_artifact:`로 **승인 대상 파일을 선언**하고, `gate_summary`가 **3분기**(진입 / 중간 / 산출)로 갈리도록 고쳤다. 산출 갈래도 아키타입별 파일명(`report.md`·`draft.md`·`paper.md`)을 탐색한다. 새 템플릿에 중간 Sam 게이트를 둘 때는 **반드시 `approval_artifact`를 함께 선언하라** — 없으면 Sam이 무엇을 승인하는지 모른 채 승인하게 된다.

### ⚠️ 상한만 재는 규격 게이트는 **빈 산출물을 가장 안전하게 통과**시킨다
**[발견: research-proposal 변환, 2026-08-05]** proposalforge 의 Gate 1 은 제출 규격을
지키는 하드게이트다 — 페이지 한도·필수 절·예산 상한. 그런데 셋 다 **위쪽만** 잰다.
실측: 섹션 파일 5개를 **전부 빈 파일**로 두고 gantt 를 ````mermaid\ngantt\n```` 한 줄로
두면

```
page_count           PASS — 0.0 / 30 pages (0 words)
section_completeness PASS — all present
timeline_format      PASS — mermaid gantt block present
overall              PASS   exit=0
```

**아무것도 쓰지 않은 제안서가 가장 안전하게 통과한다.** `is_file()` 은 파일이 있다는 뜻이지
쓰였다는 뜻이 아니고, "한도 이하"는 0 에서 가장 잘 만족된다. 공집합이 통과하는 자리의
여덟 번째이되 **모양이 새롭다** — 앞의 일곱은 검사 대상이 없어서 통과했지만 여기는
검사 대상이 있고 **측정값이 0** 이라 통과한다.

→ 상한마다 **하한을 짝으로** 뒀다(절 분량 하한 · 페이지 하한 비율 · gantt task 개수 하한 ·
번들 조립 비율). **분량을 재는 게이트를 만나면 0 을 넣어 보라.**

### ⚠️ 도구가 만든 표를 도구의 규칙으로 검사하면 언제나 맞는다 — 분모를 **두 곳**에 고정했다
예산표는 `tools/budget_build.py` 가 만든다. 그 표의 행 합계와 열 합계를 검사하면 도구가
계산한 값을 도구의 산식으로 확인하는 것이라 **틀릴 수가 없다**(sim-experiment 의 '표가
스스로를 선언하고 스스로를 만족시킨다' 와 같은 자리). 그래서 `budget_integrity` 는 분모를
표 밖에서 가져온다:

- **연차 수·연차 상한·간접비율** → `SCOPE.md`(stage 1 · **Sam 이 승인한 값**)
- **인력·장비의 근거** → `plan.md`(stage 9 · 예산보다 **먼저** 쓰인다)

연차 열을 5→3 으로 줄여 상한 검사를 헐겁게 만드는 것도 이것으로 막힌다. 그리고 양방향으로
본다 — 계획한 자원이 예산에 0 이면 FAIL, 계획에 없는 비목에 돈이 잡혀도 FAIL.

**교훈**: 게이트가 검사할 값을 **누가 언제 썼는지** 물어라. 검사 대상과 같은 주체가 같은
시점에 썼다면 대조가 아니라 자기확인이다.

### ⚠️ 같은 fail-open 이 세 번째다 — '모르면 통과' 는 도메인을 가리지 않는다
`call_alignment_check.py` 의 자격 검사:

```python
else:
    ok = True   # unknown program — eligibility not auto-checked
```

실측: 사업명을 `기본연구` 로 쓰면 **박사 30년차가 신진연구자 사업에 PASS · exit=0** 이다.
secforge 의 빈 블록 · datasetforge 의 `verdict: unknown` 과 같은 모양이다. 우리는 정책에
없는 사업명을 **FAIL** 로 뒤집었다(새 사업이면 자격창을 정책에 추가하라 — 게이트를 고치는
것이 아니라 정책을 채우는 일이다).

### ⚠️ 국문 분량 규격은 **어절만이 아니라 글자 수도** 다시 계산해야 한다
**[자체 결함 · 정상 픽스처가 잡았다]** 평가지표 대응 근거의 하한을 영문 감각으로 60자로
뒀더니, 정상 픽스처의 실제 근거 문장이 전부 반려됐다:

```
FAIL: '창의성' 의 evidence 가 56자 — 하한 60자
```

그 문장은 "기존 계열은 공개 벤치마크에 그쳤다 본 연구는 국내 산업 데이터에 대한 검증 체계를
처음으로 제시한다" 로, **내용상 아무 문제가 없다.** 국문은 정보 밀도가 높아 완결된 한
문장이 40~55자다. policy-brief 에서 **어절** 기준을 재보정한 것(§5)의 **글자 수 판**이다.
→ 40자로 낮췄다('창의적이다'=5자 · '본 연구는 창의적이고 우수하다'<30자 는 여전히 걸린다).

**교훈**: 한국어 도메인에서 길이를 재는 모든 상수를 의심하라 — 경계(`\b`)·토큰·어절·**글자**.
그리고 이것은 **정상 픽스처로 PASS 를 확인하지 않았다면 실미션에서야 드러났을 것**이다.

### ⚠️ 문서와 코드가 **서로 다른 형식**을 말하면 규약을 지킨 쪽이 반려된다
**[발견: reviewer-response 변환, 2026-08-05]** rebuttalforge 의 CLAUDE.md 는 변경 표시
규약을 이렇게 문서화한다:

```
| Change-marking convention | `[CHANGE-r1: ...]` inline tags + 05-change-log.md | Stage 5 |
```

그런데 게이트가 찾는 것은 `\[CHANGE-(R\d+\.\d+):` 다. 실측: 문서를 그대로 따라
`[CHANGE-r1: 실험 추가]` 로 쓰면 **태그 0건 · 전건 FAIL**. 지금까지의 함정은
**docstring 과 코드**의 불일치였고 결과가 거짓 PASS 였는데, 이것은 **상위 문서와 코드**의
불일치이고 결과가 **거짓 FAIL** 이다. 규약을 성실히 따를수록 막힌다.

같은 파일의 두 번째 형태: 변경기록 파서가 `^\s*(R\d+\.\d+):\s` 라 **마크다운 목록**
(`- R1.1: 3.2절에 실험 추가`)을 한 건도 읽지 못한다. 목록으로 쓰는 것이 오히려 자연스러운데
그러면 전건 "변경기록에 항목 없음" 으로 반려된다(legalforge 의 '항상 FAIL' 과 같은 계열).

**교훈**: 형식을 요구하는 게이트를 이식할 때는 **그 형식을 말하는 문서를 모두 찾아 대조**하고,
**정상적인 마크다운 관용구**(목록·번호·들여쓰기)로 쓴 픽스처를 반드시 넣어라.
우리는 형식을 템플릿 policy 한 곳에 못박고 본문 지시와 게이트가 같은 곳을 보게 했다.

### ⚠️ 비율 하한은 **짧은 항목의 누락**을 잡지 못한다 — 구조가 있으면 구조를 세라
**[자체 결함 · 정상 픽스처가 잡았다]** `comment_fidelity` 의 '원문 포착률' 하한을 0.4 로
뒀더니, 리뷰어 지적 **5건 중 1건을 통째로 빠뜨려도 72%** 라 통과했다. 짧은 지적("Minor:
Table 2 caption has a typo.")은 글자 비율을 거의 움직이지 않기 때문이다. 비율만으로
누락을 재면 **가장 빠뜨리기 쉬운 것을 가장 못 잡는다.**

→ 리뷰어 원문의 **번호 매긴 항목 수**를 함께 센다(`1.` `2.` `3.` — 대부분의 리뷰가 이렇게
쓴다). 구조가 있는 곳에서는 개수를 직접 세고, 번호 없는 산문형 리뷰에서는 비율로 돌아간다.
하한도 0.75 로 올렸다.

**교훈**: 커버리지를 **연속량**(글자·바이트·비율)으로 재는 게이트를 만나면 **셀 수 있는
단위가 입력에 이미 있는지** 보라. 있으면 그것을 세는 편이 언제나 낫다.

### ⚠️ 게이트가 도는 시점과 산출물이 만들어지는 시점을 맞춰라
**[자체 결함 · 정상 픽스처가 잡았다]** 아키타입 R 의 공개 범위 정책에 `bundle` 을 본문
목록으로 넣었는데, 번들은 **Deliver(stage 12)에서 조립**되고 그 검사는 **Final Review
(stage 10)에서** 돈다. 결과: 정상 미션이 "선언한 산출물의 부재" 로 반려된다.

**선언 목록 대비 존재**(§5)는 강력한 패턴이지만 **그 시점에 이미 존재해야 하는 것만**
넣어야 한다. 아키타입 O 의 '설치 증거' 나 N 의 '데이터 위치' 처럼 산출 시점이 명확한
것과 달리, 번들 조립은 파이프라인의 **마지막** 행위다.

**교훈**: 정책에 파일 목록을 선언할 때 **그 파일이 몇 번 stage 에서 생기는지**와 **게이트가
몇 번 stage 에 걸려 있는지**를 나란히 확인하라. 픽스처는 이것을 즉시 드러낸다.

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
| 13 | agentforge | research | 9-stage · agents 12 | ✅ **draft (M)** | `agent-eval.yaml` | 0 (**예상 빗나감**) |
| 14 | datasetforge | research | 9-stage · agents 14 | ✅ **draft (N)** | `dataset-release.yaml` | 0 (**예상 빗나감**) |
| 15 | reproforge | research | 8-stage · agents 12 | ✅ **draft (O)** | `repro-package.yaml` | 0 (**예상 빗나감**) |
| 16 | simforge | research | 8-stage · agents 11 | ✅ **draft (P)** | `sim-experiment.yaml` | 0 |
| 17 | proposalforge | research | 9-stage · agents 15 | ✅ **draft (Q)** | `research-proposal.yaml` | 0 (**예상 적중**) |
| 18 | rebuttalforge | research | 8-stage · agents 11 | ✅ **draft (R)** | `reviewer-response.yaml` | 0 (**예상 적중**) |
| 19 | outreachforge | research | 8-stage · agents 12 | ⬜ **다음** | — | ? |
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

**agent-eval 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/stat_significance.py`(원본 GATE 2 이식 — **방향**·**분모 커버리지**·**축퇴 방어**·
  seed 집계) · `gates/repro_determinism.py`(원본 GATE 3 이식 — fail-open 3곳 봉합 + **실제
  gold set 대조** + 버전 핀 규칙 교체 + **run.sh 를 실행하지 않는 replay 증거 검사**)
- ✅ **`gates/eval_set_quality.py` 신설 — 원본 GATE 1 은 스크립트가 아예 없었다**(LLM 크리틱
  하나). 모든 수치의 **분모가 되는 평가셋**을 객관 게이트 없이 두면 뒤의 통계·재현성 게이트는
  부실한 측정을 정밀하게 재는 일이 된다. 환각 `gold_context` 를 실제 chunk 목록과 대조한다
  (원본 CLAUDE.md 가 "Never invent a gold context" 라고 **선언만** 하던 것)
- ✅ **`gates/run_completeness.py` 신설** — 선언한 시스템 × seed 매트릭스가 전부 돌았는지.
  원본은 실패 run 을 **집계에서 빼고 남은 것으로 게이트를 통과**시킨다("gates may still pass
  with remaining runs"). seed 를 여러 개 돌리는 이유가 사라진다
- ✅ `secret_redaction` 에 `scan_extensions`·`disclaimer_files` 정책 축 추가(§5) —
  **기본값은 L 의 동작 그대로**이고 sec 하네스 22/22 로 회귀 없음을 확인
- **원본 게이트 2종에서 결함 5건 — 전부 실측으로 확인했다**(§5):
  방향 없는 유의성 검정(30%p 퇴보가 PASS) · 분모 자기결정(6문항만 채점해도 PASS) ·
  축퇴 시 Cohen's d = +inf · `runs/` 가 비면 PASS · `raw.jsonl`·`metrics.json` 부재 시 건너뜀.
  여기에 **반대 방향의 고장** 1건 — 버전 핀 휴리스틱이 agentforge **자신의 문서화된 기본값**
  `text-embedding-3-small` 을 반려했다(실측 `exit=1`)
- **신규 profile 0개 — 대장의 "예상 있음(평가 실행)"은 빗나갔다.** `system-builder` 는 tools 가
  `developer`(specflow backend-dev)와 동일하고, `run-evaluator` 는 **실행 결과로 산출·판정**
  하므로 `tester` 다(migrateforge 의 `baseline-snapshot` 과 같은 판정). **아키타입 D 때 만든
  3종이 D·K·M 을 모두 받쳤다** — profile 을 계약 단위로 자른 판단이 값을 했다
- ⚠️ **병렬 판단이 아키타입 K 와 갈린다.** K 는 git 인덱스가 공유 자원이라 병렬을 **제거**했지만,
  M 의 stage 7 은 시스템마다 `src/<id>/` 로 트리가 겹치지 않고 **여기서 커밋을 하지 않는다**
  (커밋은 Deliver 한 번). 같은 "코드를 쓰는 병렬"이라도 **공유 자원이 무엇인지**로 갈린다
- ⚠️ **비용이 있는 아키타입** — stage 9 는 LLM API 를 수십~수백 회 호출한다. 그래서 stage 8
  (Run Plan)에서 호출 수·비용을 산정하고 **그 직전에 Sam 승인 게이트**를 뒀다(K 의 '코드 변경
  직전 승인'과 같은 계열 — 되돌리기 어렵거나 돈이 드는 행위 앞에는 사람을 둔다)
- ⚠️ **공개 범위 분리**(L 의 규율을 이 도메인 형태로): `_private/` 에 **코퍼스 원문·청크**
  (제3자 문서 — 저작권·라이선스)와 run 의 **예측 원본**(`raw.jsonl` — 코퍼스 발췌를 담는다).
  커밋 대상은 코드·설정·지표·보고서. 코퍼스 `license:` 기재를 stage 2 가 강제한다
- ✅ **깨뜨린 픽스처 43케이스 E2E**(정상 6 + 결함 31 + **원본 결함 회귀방어 6** + 설계
  회귀방어 3 + L 회귀방어 1) — 지금까지 하네스 중 가장 크다
- **미이식**: `eval_metrics.py`·`latex_export.py`(**판정하지 않는다 = 산출 도구** — Tester·Writer
  가 미션 안에서 만들어 쓴다) · `runs_state.py`(Kanban 이 대체) · `statistical_test.py` 의
  Wilcoxon 옵션(scipy 의존 · 우리 bootstrap 으로 충분)
- **연결**: 이 아키타입의 `report/paper-artifacts/` 는 **아키타입 B(academic-paper)의 입력**이다.
  원본이 의도한 `agentforge → paperforge` 사슬이 우리 쪽에서도 성립한다

**dataset-release 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/pii_presence.py`(원본 pii_scan+하드게이트 이식 — **전 포맷·전 파일 스캔** ·
  Luhn 창 수정 · 전화번호 과검출 수정 · 마스킹 허용 · **공개 범위 준수 검사**) ·
  `gates/license_compat.py`(원본 license_check 이식 — **제한 조항 우선 판정** · unknown=red ·
  선언 부재 FAIL · **소스 LICENSE 를 직접 다시 읽는다**)
- ✅ **`gates/schema_conformance.py`·`gates/datasheet_completeness.py` 신설** — 원본 크리틱
  2종은 **스크립트가 없다**(LLM 서술뿐). 원본 CLAUDE.md 가 선언만 하던 규칙("3 포맷 동일
  row count + 동일 schema" · "모든 column 은 실제 column 에서 유래")을 코드로 옮겼다
- **원본 게이트 3종에서 결함 6건 — 전부 실측**(§5): 첫 샤드만 스캔 · 라이선스 보고서 부재 시
  PASS(`# safe default` 가 죽은 코드) · unknown 통과 · 선언 전무를 '일관됨'으로 통과 ·
  분류 순서가 뒤집혀 독점 조건이 덧붙은 Apache 헤더가 green · Luhn 고정 창이 카드번호를 놓침.
  **반대 방향** 1건 — `phone_kr` 선두 0 이 선택이라 `측정값 1012345678` 을 HIGH 로 잡는다
  (숫자 id 를 가진 정상 데이터셋이 영영 배포되지 않는다)
- ⚠️ **공개 범위를 정책으로 못박고 게이트가 강제한다** — `publication_policy.mode` 가
  `local_only`(기본)면 데이터는 `_private/bundle/` 에만 두고, **커밋 대상에 데이터 파일이
  있으면 FAIL**. `repo_commit` 은 Sam 이 Scoping 과 Deliver 에서 **두 번** 승인해야 한다.
  L·M 의 `_private/` 규율이 여기서 **정책 축**으로 승격했다 — 산출물이 곧 데이터인
  아키타입에서는 "무엇이 커밋되는가"가 미션마다 달라지기 때문이다
- ⚠️ **정본 포맷을 `.jsonl`/`.csv` 로 정했다** — 컨테이너에 pandas·pyarrow 가 없어 게이트가
  parquet 을 읽지 못한다. 읽지 못한 파일을 건너뛰면 원본의 샤드 함정과 같아지므로
  **읽을 수 없는 데이터 파일이 있으면 FAIL**(§5)
- ⚠️ **양립성 표를 정책으로 넓힐 수 있게 뒀다**(`extra_compatible`) — 이식한 표는 코드
  라이선스 기준이라 보수적이고(Apache-2.0 → CC-BY-4.0 이 INCOMPATIBLE), 닫아 두면
  legalforge 의 '어떤 입력에도 FAIL' 과 같은 자리에 이른다. 넓히는 것은 Sam 의 결정이다
- **신규 profile 0개 — 대장의 "예상 있음(변환·빌드)"은 빗나갔다.** 정제는 `curator`
  (dedup·normalize 가 그 verb 집합이다), 포맷 변환은 `developer`(변환 코드를 쓰고 돌린다).
  **"예상 있음"이 4연속으로 빗나갔다**(I·K·L·M·N) — profile 11종이 사실상 포화인 듯하다
- ✅ **깨뜨린 픽스처 42케이스 E2E**(정상 5 + 공개범위 4 + 결함 26 + **원본 결함 회귀방어 7**).
  **정상 픽스처가 내 판정 기준 2건을 잡았다** — 데이터시트 절 하한(60자)에 픽스처 본문이
  못 미쳤고, 라이선스 조합을 INCOMPATIBLE 로 골라 뒀다(§2⑧ '정상 픽스처로 PASS 확인'이
  또 작동했다)
- **미이식**: `croissant_build.py`(JSON-LD 생성 = 산출 도구) · `bundle_export.py` · `runs_state.py`

**repro-package 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/result_tolerance.py`(원본 하드게이트 이식 — **실행 성공 확인** · 선언↔파싱 개수
  대조 · 0건 방어 · 허용오차 기본값 적용) · `gates/env_consistency.py`(원본 env_diff 이식 —
  **버전 대조 신설** · Dockerfile 의 COPY+RUN 실체 확인 · 이름 정규화 · 공집합 방어)
- ✅ **`gates/install_evidence.py` 신설** — 원본에 이 자리가 통째로 비어 있다. 실행 방식·
  종료코드·소요·환경 지문·로그 발췌를 요구하고, **미검증 경로(Docker)의 공시를 강제**한다
- ✅ **`gates/reproduce_doc.py` 신설** — 원본 `doc-clarity-check` 는 스크립트가 없다.
  필수 절·명령 블록·**명령이 가리키는 파일의 실재**(`doc_links` 가 링크에 하는 일을 명령의
  인자에 한다)·예상 소요를 본다
- ✅ **기존 게이트 2종을 재사용했다** — `license_compat`(N)은 원본 CLAUDE.md 의 "02-ingest
  라이센스 검토 · GPL incompatible 은 release-notes 에 명시"와 하는 일이 같고,
  `secret_redaction`(L)은 번들 스크립트의 토큰 박힌 URL 을 잡는다(`scan_extensions` 를 M 에서
  정책으로 뺀 것이 여기서 값을 했다). **"만들기 전에 가진 것과 겹치는지 보라"(§2④)가 처음으로
  두 건이나 성립한 변환**이다
- **원본 게이트 2종에서 결함 6건 — 전부 실측**(§5): 빌드 실패 보고서를 PASS · `expected:` 를
  빼면 검사가 사라짐 · key_results 0건이면 PASS · py_packages 공집합이면 PASS · 주석의
  `requirements.txt` 를 전 패키지 커버로 셈 · **버전을 한 번도 비교하지 않음**
- ⚠️ **docker 데몬이 없다**(실측). 소켓을 붙이지 않는다 — 호스트 root 권한을 미션에 주는
  일이다. 설치 테스트는 `venv`, Dockerfile 은 정적 검토. 그리고 **그 사실을 공시하게** 했다(§5)
- **신규 profile 0개 — "예상 있음"이 6연속 빗나갔다**(I·K·L·M·N·O). 환경 파일 3종을 쓰는 것은
  `developer`, 실제로 돌려 보는 것은 `tester` 다. **profile 11종은 포화로 봐도 되겠다**
- ✅ **깨뜨린 픽스처 41케이스 E2E**(정상 6 + 결함 27 + **원본 결함 회귀방어 6** + 설계
  회귀방어 2). **픽스처가 자체 결함 1건을 잡았다** — 문서 H1 제목이 절 별칭과 겹쳐 진짜
  절을 가렸다(§5)
- **미이식**: `bundle_export.py`·`release_notes_build.py`(산출 도구) · `runs_state.py`(Kanban)

**sim-experiment 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/bit_exact.py`(원본 Gate 2 이식 — **해시를 다시 계산해 대조** · `--doe` 가 광고만
  하던 **입력 드리프트 검사를 실제로 구현** · run 0건 방어 · 재실행은 기록만 검사)
- ✅ **`gates/solver_pin.py`·`gates/doe_completeness.py` 신설 — 원본 Gate 1·Gate 3 은
  스크립트가 아예 없다**(LLM 크리틱뿐). 원본 CLAUDE.md 가 규약으로만 적어 둔 것
  ("02-solver.md 가 source of truth" · "No silent failures" · "Output schema consistent")을
  코드로 옮겼다. `solver_pin` 은 **계획/실행 두 모드**로 돈다(아키타입 K 의 `atomic_commit` 방식)
- ✅ **`gates/analysis_integrity.py` 신설** — Sobol 불변식(`0 ≤ S_i ≤ S_Ti ≤ 1`) · 선언 변수
  커버리지 · 인용 CSV 실재 · **근사 한계와 그림 미생성의 공시 강제**
- **원본 결함 3건 실측**(§5): 해시를 존재만 확인(0 을 64자 적어도 PASS) · **`--doe` 를
  `--help` 에까지 내놓고 코드에서 한 번도 참조하지 않음** · run 0건이면 PASS(공집합 여섯 번째)
- ⚠️ **`run_completeness`(M)를 재사용하지 않았다.** 이름과 목적이 비슷해 보이지만 **선언의
  모양이 다르다**(M=시스템×seed 행렬 · P=DOE 설계점 목록). 합치면 미션마다 절반만 쓰이는
  게이트가 되고 어느 도메인의 규칙인지 흐려진다. **재사용은 '하는 일'이 같을 때지 '이름'이
  비슷할 때가 아니다** — O 에서 `license_compat`·`secret_redaction` 을 재사용한 판단의 짝이다
- ⚠️ **환경 제약이 또 하나 드러났다** — **matplotlib·numpy 가 없다**(실측). 그림을 만들 수
  없어 `plot.py` + CSV 를 내고 `figures_generated: false` 를 **공시**하게 했다(O 의
  `docker_verified: false` 와 같은 계열 · 세 번째 적용)
- ✅ **깨뜨린 픽스처 43케이스 E2E**(정상 5 + 결함 33 + **원본 결함 회귀방어 3** + 설계
  회귀방어 2). **픽스처가 자체 결함 1건을 잡았다** — 설계점을 표에서도 지우면 회계가
  내부적으로 일관해져 통과했다(§5). `n_design_points:` 선언으로 분모를 고정해 막았다
- **신규 profile 0개** — 이번엔 대장도 "예상 있음(실행)"이었지만 `tester` 로 충족됐다.
  **7연속**(I·K·L·M·N·O·P)
- **미이식**: `runs_state.py`(Kanban) · `doe_generate.py`·`hash_outputs.py`·
  `sensitivity_analysis.py`·`latex_export.py`(**판정하지 않는 산출 도구** — 미션이 만들어 쓴다)

**research-proposal 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/proposal_format.py`(원본 Gate 1 형식부 이식 — **분량 하한 신설** · gantt task 실체 ·
  **영문 초록 검사 신설** · 번들 조립 비율) · `gates/budget_integrity.py`(원본 Gate 1 예산부 이식 —
  Sum 열 강제 · **파싱 실패 행을 FAIL** · 음수 차단 · 간접비율 대조 · **계획 근거 대조**) ·
  `gates/call_alignment.py`(원본 Gate 2 이식 — **키워드 세기를 구조화 대응 선언으로 교체** ·
  미상 사업명 fail-closed · 대표논문을 `representative` 블록 안에서만 셈)
- ✅ **`gates/proposal_traceability.py` 신설** — 원본에 스크립트가 없다. CLAUDE.md 가
  "Gantt 는 methods 활동과 **1:1 매칭**" 이라 선언하지만 코드는 gantt 블록의 존재만 본다.
  공백→세부목표→활동→일정→방법 사슬을 id 로 대조하고 **역방향**(고아 공백·활동 없는 목표·
  계획 밖 일정)까지 본다. **이 아키타입의 핵심 불변식**이다
- ✅ **기존 게이트 3종 재사용 — 지금까지 중 가장 많다**(§2④): `source_balance`·`recency_check`
  (지형 조사의 갈래 균형·최신성은 아키타입 A·G 와 하는 일이 같다 — 원본에는 이 검사가 없다) ·
  `legal_safety`(고지 + 개인정보). **새 게이트를 만드는 대신 `legal_safety` 에
  `publication_policy` 축을 열었다**(M 의 `scan_extensions` 교훈 두 번째 적용 — 선언하지
  않으면 돌지 않으므로 아키타입 H 는 16/16 그대로다)
- **원본 게이트 2종에서 결함 8건 — 전부 실측**(§5): 빈 제안서가 PASS(섹션 5개가 전부 빈
  파일 + 빈 gantt) · Sum 열을 빼면 산술 검사가 사라짐 · 짧은 행의 9억이 증발 · 음수 조정
  행으로 상한 우회 · 미상 사업명이면 자격 검사 꺼짐 · 키워드 나열 한 줄로 평가지표 5종 통과 ·
  대표논문을 남의 인용 bibkey 로 셈 · 간접비율 17% 를 CLAUDE.md 에 선언만 하고 미검사
- ⚠️ **공개 범위가 이 아키타입의 최대 위험이다** — 제안서는 **심사 전에 공개되면 아이디어를
  선점당한다**. `publication_policy.mode` 기본값 `local_only`(본문·예산·PI 정보는
  `_private/`, 커밋되는 것은 `report/summary.md` 뿐) · `repo_commit` 은 **Scoping·Deliver
  두 번 승인**. 아키타입 N 의 규율을 문서 산출물에 적용한 것이다
- ⚠️ **검증을 앞으로 당겼다(일곱 번째)** — 원본은 집필·예산·일정을 **다 만든 뒤** stage 8 에서
  자격과 정합을 본다. 자격 미달이면 그 전부가 버려진다. 우리는 설계 검증(stage 8)을
  **집필 전**에 두고 `call_alignment` 를 **plan/final 두 모드**로 만들었다(K 의
  `atomic_commit`, P 의 `solver_pin` 과 같은 방식)
- ⚠️ **stage 수가 15로 가장 길다** — 원본 9단계에 우리 불변식(curator dedup·wiki·검증 4지점)이
  더해졌다. 예산·일정을 **집필 전**에 두어(9→10→11) Sam 승인이 "이 계획·이 예산으로 집필을
  시작한다" 가 되게 했다(게이트 겹침을 피하면서 승인의 내용을 키운 배치)
- **신규 profile 0개 — 대장의 "예상 0" 이 이번엔 맞았다**(I·K·L·M·N·O·P 는 "예상 있음"이
  빗나간 경우였다). 간트는 `architect`(연차 배치 **결정**), 예산표는 `developer`(명세를 쓰고
  산출 도구를 돌린다)
- ✅ `tools/budget_build.py` 이식 — **판정하지 않으므로 게이트가 아니다**(`bib_export` 와 같은
  판정). 원본의 cap 위반 exit 1 은 **경고로 낮췄다** — 판정은 게이트의 일이다
- ✅ **깨뜨린 픽스처 62케이스 E2E**(정상 7 + 결함 44 + **원본 결함 회귀방어 8** + 설계
  회귀방어 3). **정상 픽스처가 자체 결함 1건을 잡았다** — 근거 서술의 글자 수 하한을 영문
  감각으로 60자로 잡아 **정상 국문 문장(56자)을 반려**했다(§5)
- **미이식**: `bundle_export.py`(Deliver 의 파일 작업) · `runs_state.py`(Kanban) ·
  `format_check.py` 의 페이지 환산(국문 어절로 재보정해 정책으로 옮겼다)

**reviewer-response 변환에서 나온 것 (2026-08-05)**
- ✅ `gates/comment_coverage.py`(원본 Gate 1 이식 — orphan·duplicate·untagged 양방향 검사는
  **원본이 이미 잘 하고 있어 그대로 유지**했고, **응답 실체**(분량 하한)와 공집합 차단을 더했다) ·
  `gates/change_consistency.py`(원본 Gate 2 이식 — 목록형 변경기록 인식 · 태그 형식 통일 ·
  **원본 원고 대조 신설**)
- ✅ **`gates/comment_fidelity.py` 신설 — 원본에 이 자리가 통째로 비어 있다.**
  커버리지의 **분모(코멘트 목록)를 파이프라인 자신이 만들고**, 게이트의 인자 목록에 리뷰어
  원문이 아예 없다. 8건 중 5건만 파싱하면 커버리지 100% 다 → 원문을 직접 읽어 verbatim
  실재·포착률·번호 항목 수·리뷰어 부재를 본다. **`comment_coverage` 와 짝으로만 의미가
  있다**(`api_coverage`↔`symbol_truth` 와 같은 배치)
- ✅ **`gates/response_quality.py` 신설 — 크리틱 2종(tone-polish·argument-strength)은
  스크립트가 없다.** 그런데 규칙은 이미 기계적으로 쓰여 있었다("근거 없는 반박 = HIGH,
  automatically" · "금지 표현 = HIGH, no exceptions"). 판정자를 LLM 하나로 두면 이 규칙은
  매번 다시 판단되지만 게이트로 올리면 매번 같다
- ✅ **재사용 1종**: `legal_safety` — 아키타입 Q 에서 연 `publication_policy` 축이 **바로 다음
  변환에서 값을 했다**(리뷰어 코멘트는 저널 비밀유지 관행상 대외비 · 심사 중 원고는 미발표
  저작물). 축을 여는 판단이 옳았다는 실증이다
- **원본 게이트 2종에서 결함 6건 — 전부 실측**(§5). ⚠️ **원본은 지금까지 이식한 것 중 가장
  잘 만들어져 있었다**(양방향 검사·역방향 대조·verdict 누락 FAIL). 그런데도 6건이 나왔다:
  빈 응답 파일에 커버리지 PASS · 코멘트 0건에 커버리지 100% · 분모 자기결정 · 태그만 붙여도
  PASS · **목록형 변경기록을 반려**(거짓 FAIL) · **문서가 말하는 태그 형식을 따르면 반려**(거짓 FAIL)
- ⚠️ **거짓 FAIL 이 2건**이다. 지금까지는 대개 느슨한 쪽(거짓 PASS)이었는데 이 하네스는
  **양쪽이 반반**이다 — 정상 픽스처로 PASS 를 확인하는 절반이 없었다면 "이식 완료" 로
  기록해 놓고 파이프라인을 막아 놓았을 것이다(legalforge 에 이은 두 번째)
- **신규 profile 0개 — 대장의 "예상 0" 이 적중**. **원고에 수정을 반영하는 것도 `writer` 다**
  (코드가 아니라 산문이므로 `developer` 가 아니다 — code-migration 의 `transform-executor`
  와 갈리는 자리를 §3 에 적어 뒀다)
- ✅ **깨뜨린 픽스처 43케이스 E2E**(정상 5 + 결함 33 + **원본 결함 회귀방어 5** —
  그중 **정상 입력이 통과하는지** 확인하는 것이 2건이다). **정상 픽스처가 자체 결함 2건을
  잡았다** — 아직 조립되지 않은 번들의 위치를 요구한 것과 포착률 하한이 낮아 지적 누락을
  놓친 것(§5)
- **미이식**: `diff_export.py`(원본↔수정 diff — **판정하지 않는 산출 도구**. 우리는 게이트
  안에서 직접 대조한다) · `bundle_export.py`(Deliver 의 파일 작업) · `comments_state.py`(Kanban)
- **연결**: 아키타입 B(academic-paper) → 투고 → **R** → 재투고. 리뷰어가 추가 실험을 요구하면
  M(agent-eval)·P(sim-experiment)로 갔다가 근거를 들고 돌아온다

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
| HEAD | rebuttalforge → R · 그 앞: proposalforge→Q · simforge→P · reproforge→O · datasetforge→N |
| 변환 | **18/20** · 다음 = **outreachforge**(§6 대장 #19) |
| 미커밋 | 없음 (push 완료 · `question_history.md` 는 이 작업과 무관한 기존 변경) |
| 컨테이너 | `hermes-solomon` · `hermes-gatekeeper` 2개 Up |
| Slack | ⚠️ **현재 도달 불가(재발 · 2026-08-05 세션 종료 시점)**. `docs/10 §4.3` 1순위 진단 실측: 호스트·컨테이너 모두 `slack.com` **HTTP 000**(타임아웃)인데 `google.com`·`github.com` 은 **HTTP 200** → **네트워크성이며 토큰·설정 문제 아님**(2026-08-03·08-04 와 같은 증상, 그때는 와이파이 변경으로 복구됐다). 게이트키퍼 WARN 6시간 107건(= `conversations.history` 폴링 실패). **Kanban 이 전부 done 이고 활성 게이트가 없어 실무 영향은 없다** — 승인 대기 중인 미션이 없기 때문. 실미션 재개 전에 도달성부터 확인할 것 |
| Kanban | 전부 `done`(54/54) · 활성 게이트 없음 · 잔여 테스트 카드 없음 |
| 테스트 | **226종 통과**(29 템플릿 + 21 게이트키퍼 + 176 게이트) · 린터 18/18 · **E2E 하네스 12종 377케이스 전건 통과**(`scripts/tests/fixtures/run_all.py`) |
| 라이브 미션 | **A(trend-report)만 실증**(M-2026-003·004). 나머지 17종은 `draft` — Sam 지시로 **전체 변환 후** 하나씩 실행 |
| ⚠️ 신규 | 저장소가 **PUBLIC** 임을 전제한 개인정보 게이트(`legal_safety`) 도입 · `.gitignore` 에 `_personal/` |

### 8.1 절차

1. **읽는다**: 이 문서 §6(다음 대상) → §2(레시피) → §5(함정) → 대상 스킬의 `SKILL.md`
2. **변환한다**: `templates/<name>.yaml` 작성. `templates/academic-paper.yaml`을 참고본으로 삼는다(주석에 변환 판단 근거가 남아 있다)
3. **게이트를 이식한다** — 이 단계에서 결함이 나온다(16건 변환에서 16건 모두).
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
   함께 돌린다. 기존 하네스(`policy`·`legal`·`docs`·`lecture`·`migrate`·`sec`·`agent`·`dataset`·`repro`·`sim`·`proposal`·`rebuttal`)를 본으로 삼아
   새 파일을 만들고 `run_all.py`의 `HARNESSES`에 등록하라. 상세는
   [`scripts/tests/fixtures/README.md`](../scripts/tests/fixtures/README.md).

   불변식 위반 0 · 테스트 통과 · 하네스 전건 통과 · `reports/M-2026-TEST/` 미생성 ·
   미등록 profile 경고가 뜨면 템플릿의 `requires_profiles:`와 일치하는지 확인(§7에 후보로 등재)
5. **갱신한다**: §6 대장(상태·템플릿명·신규 profile) · §3 매핑 사전에 별칭 추가 · 새 함정이 있으면 §5
6. **커밋한다**: `feat(template): <name> → 아키타입 <X>` + `history.html` 기록

**한 세션에 2~3종이 적당하다.** 스킬 하나가 300줄 안팎이고, 변환 판단(§2②)은 원본을 실제로 읽어야 나온다.
