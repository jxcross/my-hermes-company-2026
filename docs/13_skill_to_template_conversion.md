# 13. harness 스킬 → 템플릿 YAML 변환 — 작업 절차서

> 작성일: 2026-08-04 · 상태: **작업 중(2/20 완료)** · 성격: working doc(재개 가능)
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

### ⑤ 불변식을 보강한다 (§4 체크리스트)
원본에는 우리 불변식이 대개 없다. 빠진 단계를 채운다.

### ⑥ 원본의 사람 승인 지점을 보존한다
`wait for explicit approval`·`surface to the user` 같은 구절이 있으면 그 지점에 `sam_gate: true`. 다만 **§5의 게이트 겹침 함정**을 반드시 확인한다.

### ⑦ `policy` 블록을 도메인에 맞게 쓴다
`recency_policy`·`source_balance_policy`는 **정책 주도**다(`scripts/gates/source_balance.py`가 템플릿 선언을 읽는다 — 카테고리 하드코딩 없음). 도메인마다 taxonomy를 새로 정의하라.

### ⑧ 검증하고 대장을 갱신한다
```bash
docker exec hermes-solomon sh -c 'cd /work/company && \
  python3 scripts/instantiate_template.py <name> M-2026-TEST --dry-run --render mermaid'
```
불변식 위반 0 + mermaid DAG 확인 + **`reports/M-2026-TEST/`가 생성되지 않았는지**(비파괴) 확인 → §6 대장 갱신 → 커밋.

## 3. agent → profile 매핑 사전 (누적 자산 — 변환할 때마다 추가)

**3신호로 판정한다**: ⓐ 동사(name·description) ⓑ 판별력 있는 tools ⓒ 역할 표지(`parallel worker`/`critic`/`orchestrator`). 셋 중 **2개 이상 합의** 시 매핑, 아니면 §7 보류.

| 우리 profile | 동사 신호 | tools 신호 | 확인된 별칭 |
|---|---|---|---|
| `default` (Solomon) | clarify · scope-interview · finalize · deliver · orchestrate | `AskUserQuestion` | `paperforge-clarify-topic` · `paperforge-finalize` · `trendforge-clarify-scope` · `trendforge-finalize` |
| `scout` | gather · ingest · collect · scan · search · survey | `WebSearch` `WebFetch` | `paperforge-scope-survey` · `paperforge-gather-{arxiv,web,recent}` · `trendforge-landscape-survey` · `trendforge-gather-{academic,industry,patents,news}` |
| `reader` | read-extract · analyze · classify · appraise | — | `paperforge-read-extract` · `trendforge-read-extract` |
| `curator` | dedup · filter · screen · normalize · cite-pack · cross-link | — | *(원본에 대개 없음 — 우리가 보강)* |
| `synthesizer` | synthesize · outline · structure · summarize | — | `paperforge-synthesize-outline` · `trendforge-synthesize-trends` |
| `writer` | draft · write · compose · section | — | `paperforge-draft-section` · `trendforge-draft-section` |
| `fact-checker` | fact-check · verify · evidence · recency · citation | `Bash`(게이트 스크립트 실행) | `paperforge-fact-check` · `trendforge-{evidence-critic,recency-check}` |
| `reviewer` | review · critic · clarity · logic · style · bias | — | `paperforge-{logic-critic,style-edit}` · `trendforge-{clarity-check,bias-check}` |

**신규 profile 후보 신호**: `Edit`(코드 수정) · `mcp__playwright__*`(브라우저 E2E) · 스캐너·빌더 계열. → §7에 쌓고 Sam 승인 전까지 만들지 않는다.

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

### ⚠️ 중간 Sam 게이트의 승인 요약이 부실하다 (미해결)
`gate_keeper.gate_summary()`는 `upstream` 유무로 **진입 게이트/산출 게이트**만 구분하고, 산출 게이트는 `report.md`를 찾는다. academic-paper의 중간 승인(stage 8)은 `outline.md`가 대상이라 요약이 산출물 목록 나열로 떨어진다. **후속 개선 대상**(§7).

## 6. 진행 대장 (재개 지점 — 새 세션은 여기서 다음 대상을 고른다)

| # | 스킬 | 카테고리 | 원본 | 상태 | 템플릿 | 신규 profile |
|---|---|---|---|---|---|---|
| 1 | trendforge | domain | 8-stage · agents 14 | ✅ **proven** (A) | `trend-report.yaml` | 0 |
| 2 | paperforge | research | 8-stage · agents 12 | ✅ **draft** (B) | `academic-paper.yaml` | 0 |
| 3 | specflow | domain | 12-step · agents 12 | ⬜ **다음** | — | 예상 있음(개발) |
| 4 | reviewforge | research | 9-stage · agents 12 | ⬜ | — | 0 예상 |
| 5 | litmonitor | research | 5-stage · agents 7 | ⬜ | — | 0 예상 |
| 6 | patentforge | domain | 8-stage · agents 11 | ⬜ | — | ? |
| 7 | policyforge | domain | 9-stage · agents 14 | ⬜ | — | 0 예상 |
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
| *(아직 없음 — trendforge·paperforge 모두 0)* | | | | |

**후속 과제**
- `bib_export.py` 이식 — BibTeX 산출(게이트 아님). academic-paper Deliver 단계에 붙일지 판단
- `gate_keeper.gate_summary()` — 중간 Sam 게이트(진입도 산출도 아닌 경우) 요약 개선(§5)
- `lint_template.py` 분리 — 현재 불변식은 `instantiate_template.check_invariants`에 인라인([`docs/12 §7`](./12_pipeline_negotiation.md))

## 8. 다음 세션 재개 방법

1. **읽는다**: 이 문서 §6(다음 대상) → §2(레시피) → §5(함정) → 대상 스킬의 `SKILL.md`
2. **변환한다**: `templates/<name>.yaml` 작성. `templates/academic-paper.yaml`을 참고본으로 삼는다(주석에 변환 판단 근거가 남아 있다)
3. **검증한다**:
   ```bash
   docker exec hermes-solomon sh -c 'cd /work/company && \
     python3 scripts/instantiate_template.py <name> M-2026-TEST --dry-run --render mermaid'
   docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/test_instantiate_template.py'
   ```
   불변식 위반 0 · 테스트 통과 · `reports/M-2026-TEST/` 미생성
4. **갱신한다**: §6 대장(상태·템플릿명·신규 profile) · §3 매핑 사전에 별칭 추가 · 새 함정이 있으면 §5
5. **커밋한다**: `feat(template): <name> 변환 — 아키타입 <X>` + `history.html` 기록

**한 세션에 2~3종이 적당하다.** 스킬 하나가 300줄 안팎이고, 변환 판단(§2②)은 원본을 실제로 읽어야 나온다.
