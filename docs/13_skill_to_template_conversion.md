# 13. harness 스킬 → 템플릿 YAML 변환 — 작업 절차서

> 작성일: 2026-08-04 · 상태: **작업 중(6/20 — A·B·B'·D·E·F 전부 실행가능, 라이브 미션은 A만)** · 성격: working doc(재개 가능)
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
`gate.draft`로 지정한다. **이식한 게이트는 반드시 일부러 깨뜨린 픽스처로 검증하라**(§5).

현재 보유 게이트(10종): `recency_check` · `source_balance` · `doc_consistency` · `test_run` ·
`prisma_counts` · `prisma_checklist` · `seen_dedup` · `digest_shape` · `claim_consistency` ·
`patent_format`.
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
| `default` (Solomon) | clarify · scope-interview · finalize · deliver · orchestrate | `AskUserQuestion` | `paperforge-clarify-topic` · `paperforge-finalize` · `trendforge-clarify-scope` · `trendforge-finalize` · `reviewforge-{clarify-question,finalize}` · `litmonitor-seed-config` · `patentforge-{clarify-application,finalize}` |
| `scout` | gather · ingest · collect · scan · search · survey | `WebSearch` `WebFetch` | `paperforge-scope-survey` · `paperforge-gather-{arxiv,web,recent}` · `trendforge-landscape-survey` · `trendforge-gather-{academic,industry,patents,news}` · `reviewforge-{search-protocol,search-database}` · `litmonitor-scan-{arxiv,scholar,openreview}` · `patentforge-prior-art-{academic,patent}-scan` |
| `reader` | read-extract · analyze · classify · appraise · ingest | — | `paperforge-read-extract` · `trendforge-read-extract` · `reviewforge-{data-extract,quality-appraise}` · `patentforge-ingest-invention` |
| `curator` | dedup · filter · screen · normalize · cite-pack · cross-link | — | `reviewforge-prisma-screening` · `litmonitor-relevance-filter` · *(다른 스킬엔 대개 없어 우리가 보강)* |
| `synthesizer` | synthesize · outline · structure · summarize · gap-analysis | — | `paperforge-synthesize-outline` · `trendforge-synthesize-trends` · `reviewforge-synthesize` · `litmonitor-action-suggest` · `patentforge-gap-analyzer` |
| `writer` | draft · write · compose · section · adapt | — | `paperforge-draft-section` · `trendforge-draft-section` · `litmonitor-summarize` · `patentforge-{specification-writer,jurisdiction-adapter}` |
| `fact-checker` | fact-check · verify · evidence · recency · citation | `Bash`(게이트 스크립트 실행) | `paperforge-fact-check` · `trendforge-{evidence-critic,recency-check}` · `reviewforge-evidence-coverage-check` · `patentforge-{claim-consistency-check,novelty-comparison-check}` |
| `reviewer` | review · critic · clarity · logic · style · bias | — | `paperforge-{logic-critic,style-edit}` · `trendforge-{clarity-check,bias-check}` · `reviewforge-{prisma-compliance-check,bias-balance-check,clarity-check}` · `patentforge-format-compliance-check` · `specflow` **Design Review(신설)** |
| `architect` ⚠신규 | architect · erd · diagram · wireframe · style-design | `Read,Write,Grep,Glob`(쓰기만·실행 없음) | `specflow-{architect,erd-designer,diagrammer,wireframer,style-designer}` |
| `developer` ⚠신규 | backend-dev · frontend-dev · implement · build | **`Edit`** + `Bash` | `specflow-{backend-dev,frontend-dev}` |
| `tester` ⚠신규 | e2e-test · run · regression · verify-by-execution | **`mcp__playwright__*`** + `Bash` | `specflow-e2e-tester` |

⚠신규 = **아직 생성되지 않은 profile**. 템플릿은 `requires_profiles:`로 선언하고, `instantiate_template.py`가 미등록을 감지하면 **미리보기는 경고만·실제 인스턴스화는 중단**한다.

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
| 7 | policyforge | domain | 9-stage · agents 14 | ⬜ **다음** | — | 0 예상 |
| 8 | legalforge | domain | 8-stage · agents 13 | ⬜ | — | ? |
| 9 | docforge | domain | 8-stage · agents 13 | ⬜ | — | 예상 있음(코드 읽기) |
| 10 | lectureforge | domain | 9-stage · agents 15 | ⬜ | — | ? |
| 11 | migrateforge | domain | 8-stage · agents 13 | ⬜ | — | 예상 있음(개발·테스트) |
| 12 | secforge | domain | 8-stage · agents 13 | ⬜ | — | 예상 있음(스캐너) |
| 13 | agentforge | research | 9-stage · agents 12 | ⬜ | — | 예상 있음(평가 실행) |
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

**새 후속 과제** (다음 세션 이후)
- `test_run.py`는 테스트를 **실행하지 않는다** — Tester가 남긴 `results.json`을 검사할 뿐이다. 게이트키퍼가 미션 코드를 임의 실행하면 임의 코드 실행 통로가 되기 때문. 자기보고 신뢰 구간이 남아 있으므로, CI 연동 등 **독립 실행 경로**가 생기면 교체 검토
- `webapp-build`는 아직 **라이브 미션 미실행**(`maturity: draft`) — 실미션 1회로 `tested` 승격 필요

## 8. 다음 세션 재개 방법

### 8.0 현재 상태 스냅샷 (2026-08-04 세션 종료 시점)

| 항목 | 값 |
|---|---|
| HEAD | `562f1c0` (patentforge → F) · 그 앞: litmonitor→E · reviewforge→B' · profile 3종 · specflow→D · paperforge→B |
| 변환 | **6/20** · 다음 = **policyforge**(§6 대장 #7) |
| 미커밋 | 없음 (push 완료) |
| 컨테이너 | `hermes-solomon` · `hermes-gatekeeper` 2개 Up |
| Slack | **정상**(오전 도달 불가 → 오후 복구. 호스트 200 · 컨테이너 `ok=true` · 게이트키퍼 WARN 3시간38분째 없음) |
| Kanban | 전부 `done` · 활성 게이트 없음 · 잔여 테스트 카드 없음 |
| 테스트 | 83종 통과(27 템플릿 + 21 게이트키퍼 + 35 게이트) · 린터 6/6 |
| 라이브 미션 | **A(trend-report)만 실증**(M-2026-003·004). 나머지 5종은 `draft` — Sam 지시로 **전체 변환 후** 하나씩 실행 |

### 8.1 절차

1. **읽는다**: 이 문서 §6(다음 대상) → §2(레시피) → §5(함정) → 대상 스킬의 `SKILL.md`
2. **변환한다**: `templates/<name>.yaml` 작성. `templates/academic-paper.yaml`을 참고본으로 삼는다(주석에 변환 판단 근거가 남아 있다)
3. **검증한다**:
   ```bash
   # ① 불변식 린터(가장 빠른 피드백 — 협상 중에도 반복 호출)
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_template.py <name>'
   # ② DAG 미리보기(비파괴)
   docker exec hermes-solomon sh -c 'cd /work/company && \
     python3 scripts/instantiate_template.py <name> M-2026-TEST --dry-run --render mermaid'
   # ③ 회귀
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/test_instantiate_template.py'
   ```
   불변식 위반 0 · 테스트 통과 · `reports/M-2026-TEST/` 미생성 · 미등록 profile 경고가 뜨면
   템플릿의 `requires_profiles:`와 일치하는지 확인(§7에 후보로 등재)
4. **갱신한다**: §6 대장(상태·템플릿명·신규 profile) · §3 매핑 사전에 별칭 추가 · 새 함정이 있으면 §5
5. **커밋한다**: `feat(template): <name> 변환 — 아키타입 <X>` + `history.html` 기록

**한 세션에 2~3종이 적당하다.** 스킬 하나가 300줄 안팎이고, 변환 판단(§2②)은 원본을 실제로 읽어야 나온다.
