# Changelog

이 프로젝트의 주요 변경 이력. 형식은 [Keep a Changelog](https://keepachangelog.com/) 및
[Semantic Versioning](https://semver.org/)을 따른다.

## [v0.3.0] - 2026-08-05

**실미션 테스트 착수** — 변환된 아키타입을 라이브로 돌리기 시작했고, **첫 미션이 배선·운영
층의 결함 7건을 냈다.** 그중 6건은 E2E 픽스처 510케이스가 **원리적으로 볼 수 없는** 종류다.

### Fixed — 라이브가 잡은 것 (M-2026-005 · 아키타입 B)
- **인스턴스화가 디스패처와 경합**: 카드 N장을 모두 만든 뒤 block·link 하는 순서라 그 사이
  카드가 *부모 없는 `ready`* 로 노출돼 **상류 산출물 없이 워커 6개가 동시 실행**됐다.
  Hermes CLI 제약을 실측(`create --parent`→`todo`=창 0 · `block` 은 `ready` 에서만 ·
  `--initial-status blocked` 는 실제로 blocked 를 만들지 않는다)하고 **stage 마다
  생성→게이트→링크를 한 번에** 끝내도록 재배치.
- **`block` 실패(`rc=-7`)를 WARN 으로 넘겨 게이트가 빠진 파이프라인이 남던 것** →
  1회 재시도 후 **중단 + 롤백**. 게이트 하나 빠진 그래프는 없는 것보다 나쁘다.
- **`gate_keeper.VERIFIERS` 하드코딩** → `pipeline.json` 이 선언한 검증자를 읽는다.
  `webapp-build` 의 `tester` 검증자를 게이트키퍼가 아예 보지 못해 downstream 이 영구
  정지하던 문제(로그도 남지 않는다).
- **선별에서 버린 자료(`status: rejected`)가 정책 카운트에 잡히던 것** — 템플릿은 curator 에게
  `selected/rejected` 판정을 지시하는데 게이트는 `("failed","excluded")` 두 단어만 걸렀다.
  게이트가 *선별한 것*이 아니라 *수집한 것*을 재고 있었다. 접두 deny-list + 정책화.

### Added — 운영 도구
- **`scripts/match_template.py`** — 미션→템플릿 3-way 매처(docs/12 §5). 근거 낱말을 함께
  내고, `maturity` 를 점수에 반영하며 `draft` 선택 시 경고한다. **관계없는 요청에는 '낮음'을
  내고 억지로 고르지 않는다.** `manifest.json` 은 템플릿에서 생성한다(손으로 유지하면 어긋난다).
- **`scripts/usage_report.py`** — 사용량·한도 리포트. **LLM 을 호출하지 않는다**(한도를
  확인하려고 한도를 쓸 수 없다). `exit 1` = 소진 중 → 미션 착수 전 점검용.
- 템플릿 20종에 **`keywords:`** 선언 · `trend-report` 에 **`maturity: proven`** 명시
  (실미션 2회 완주 실적은 있는데 필드가 없었다).

### Notes — 운영 규약 두 가지 (코드로 못 막는 것)
- **게이트 승인의 `--reason` 은 다음 워커가 읽는다.** 승인하며 남긴 "골격 검증 미션·게이트
  변수를 배제하고 골격만 본다"가 **논문의 스코프**로 SCOPE.md 에 들어갔다(RQ1 과 모순되는
  범위 제외까지). 승인 사유는 **파이프라인에 대한 지시**로 쓰고, 운영 메모는
  `[운영 메모 · 산출물 지시 아님]` 접두를 붙인다.
- **`archive`·`reclaim` 은 실행 중인 워커를 죽이지 않는다.** 폐기한 카드의 워커가 8분 41초째
  살아서 **새 미션의 `raw/` 에 20파일을 썼다.** 폐기·재시작 시 `ps | grep 'kanban task'` 로
  프로세스를 확인하고 죽여라.

### Known issues
- **M-2026-005 는 stage 4 에서 정지 중** — 원인은 파이프라인이 아니라 **LLM 사용량 한도
  소진**(`HTTP 429` · plan=team · 리셋 **2026-08-09 14:07**). 미션은 깨끗이 세워져 있고
  stage 1~3 산출물은 온전하다. 재개 절차는 `CLAUDE.md`.
- **실패의 표면 증상과 근본 원인이 두 층 떨어져 있다** — 카드에는
  `protocol violation` 만 남고 429 는 세션 로그에만 있다. 환경성 실패를 카드에 남기는 것이
  후속 과제(`usage_report.py` 가 임시로 그 간극을 메운다).
- 미완 백로그: **성장 지표 대시보드**(재작업률·wiki 재사용률·소요시간).
- Slack 도달 불가(네트워크성) 지속 · `SLACK_BOT_TOKEN` rotate 미결.

## [v0.2.0] - 2026-08-05

두 번째 마일스톤 — **Stage 1 파이프라인 실동작 + 템플릿 기반 미션 시스템 + 아키타입 20종 확보**.

사람이 목표·경계조건을 정하고 AI가 계획·조사·검증·정리를 수행하는 파이프라인이 실제로
돌기 시작했다. 미션 4건을 11단계 전 구간 완주했고, 미션을 **선언적 템플릿**으로 기술하면
Kanban 그래프로 번역되는 시스템을 만들었으며, 외부 하네스 스킬 20종을 우리 아키타입으로
변환해 실행 가능한 상태로 적재했다.

### Added — Stage 1 파이프라인 운영
- **전문 profile 11종**(default·scout·reader·writer·synthesizer·curator·architect·developer
  = `gpt-5.6-terra` / fact-checker·reviewer·tester = `gpt-5.6-sol`). **작성자≠검증자** 불변식을
  프로필 경계로 강제.
- **미션 4건 완주**: M-2026-001(슬라이스) · M-2026-002(full 11단계) ·
  M-2026-003(템플릿+이중 게이트) · M-2026-004(병렬화 라이브 파일럿).
- 인프라: `HERMES_WRITE_SAFE_ROOT` 워커 직접쓰기 · **Tavily 웹검색** · `WIKI_PATH`(LLM Wiki) ·
  컨테이너 `git push` 자격(`GITHUB_TOKEN` + `GIT_CONFIG_*` credential helper).

### Added — 템플릿 기반 미션 시스템
- **선언적 템플릿 → Kanban 번역기**(`scripts/instantiate_template.py`) + 불변식 린터
  (`scripts/lint_template.py`) + 협상용 비파괴 미리보기(`--dry-run --render mermaid`).
- **이중 게이트**: 객관 게이트(Python · exit 0/1/2 fail-closed) + LLM 검증자(VERDICT).
- **스테이지 내 병렬화**: 템플릿 `parallel` 선언(`workers`/`per_item` + `batch_size`)을
  번역기가 delegation 배치 위임 프로토콜로 task 본문에 주입.
- 설계 문서 `docs/11`(템플릿 미션) · `docs/12`(파이프라인 협상) · `docs/13`(변환 절차서).

### Added — 반려·승인 게이트 자동화
- 사이드카 컨테이너 **`hermes-gatekeeper`**(`scripts/gate_keeper.py`):
  검증 task 가 `VERDICT: FAIL` 이면 **재작업 루프(리비전→재검증) 자동 생성** + downstream 보류.
- **Sam 승인 게이트 자동화**(`approval_poll`, Slack Web API): 활성 승인 게이트를
  **판단 내용과 함께** `#approvals` 에 게시 → Sam 의 `승인`/`승인 <task_id>` 감지 →
  `kanban unblock`(`SLACK_ALLOWED_USERS` 만).

### Added — 미션 아키타입 20종 (A~T)
`templates/*.yaml` — trend-report(A · **proven**) · academic-paper(B) · systematic-review(B') ·
webapp-build(D) · lit-monitor(E) · patent-spec(F) · policy-brief(G) · legal-draft(H) ·
code-docs(I) · lecture-course(J) · code-migration(K) · security-audit(L) · agent-eval(M) ·
dataset-release(N) · repro-package(O) · sim-experiment(P) · research-proposal(Q) ·
reviewer-response(R) · outreach-content(S) · conference-slides(T).
**A 외 19종은 `maturity: draft`**(라이브 미션 미실행).

- **객관 게이트 62종**(`scripts/gates/`) · **산출 도구 4종**(`scripts/tools/`).
- **공개 범위 규율**: 저장소가 PUBLIC 이고 Deliver 가 `reports/` 를 push 하므로,
  민감 산출물은 `_private/`(gitignore)에 두고 `publication_policy.mode` 를 게이트가 강제한다
  (아키타입 L·M·N·Q·R). 되돌리기 어렵거나 비용이 드는 행위(코드 변경·LLM API 호출·
  외부 패키지 실행·계산 자원) 앞에는 **Sam 승인 게이트**를 뒀다(K·M·O·P).

### Verified
- **깨뜨린 픽스처 E2E 하네스 14종 510케이스**(`scripts/tests/fixtures/run_all.py`) —
  정상 픽스처(PASS 기대) + 고의 결함(FAIL 기대) + **원본 결함 회귀 방어**를 함께 돌린다.
- 단위 테스트 **251종**(29 템플릿 + 21 게이트키퍼 + 201 게이트) · 템플릿 린터 **20/20**.

### Fixed
- `gate_keeper` **fail-open 결함**: 자식 task 의 transient 조회 실패(None)를 종단으로 오인해
  downstream 을 고아화하던 것 → `classify_children` + defer.
- 아키타입 S 의 stage 7·8 이 `--draft` 규약이 다른 객관 게이트를 한 stage 에 묶어
  **실미션에서 게이트 3종이 `exit 2` 로 파이프라인을 막던 것** → walk-up `mission_root`.
- 렌더러가 `sam_gate` + `parallel` 동시 stage 에서 팬아웃 표식을 숨기던 표시 버그.
- Slack 아웃바운드 진단 오진 정정 — 근본 원인은 **네트워크의 `slack.com` 도달 불가**
  (`status` 의 `configured` 는 토큰 존재만 의미). 1순위 진단은 `docs/10 §4.3`.

### Notes
- **변환 20건에서 20건 모두 원본 게이트에 결함이 있었다** — fail-open(공집합 통과 11회) ·
  docstring 이 선언한 검사를 코드가 하지 않음 · 죽은 변수·인자 · 한국어 정규식·분량 기준 붕괴 ·
  **어떤 입력에도 FAIL 하는 게이트**까지. 교훈은 `docs/13 §5` 에 함정 사전으로 축적했다.
- **미결**: Slack 네트워크 도달 불가(재발 · 네트워크성) · `SLACK_BOT_TOKEN` 재발급 권장 ·
  템플릿 매처(C) · 성장 지표 대시보드 · 미션 진행상황 Slack 실시간 보고.
- 다음: **실미션** — `draft` 19종을 하나씩 라이브로 돌려 `tested`→`proven` 승격.

## [v0.1.0] - 2026-08-02

첫 마일스톤 — **설계 확정 + Stage 0 인프라 구축 완료**.

### Added — 설계
- AI-Native Company 설계 문서 세트(`docs/02`~`docs/09`):
  회사 설계, 미션 파이프라인↔Kanban, 1호 미션 SPEC(11단계), Stage 0 가이드,
  의사결정 기록(ADR 11건), 다이어그램(Mermaid 9종), 에이전트 전문화·거버넌스, 미션 게시판·가시성.
- Hermes Agent·LLM Wiki 기반 기술 조사 문서.
- 핵심 결정: Option B(Hermes 네이티브 **Kanban + 전문 profile**), Solomon=기획·검증(구현 위임),
  작성자≠검증자, 전문화 4계층 스택, 수요 기반 LLM Wiki, 미션 아키타입 A/B/D.

### Added — Stage 0 인프라
- `docker-compose.yml`: 공식 이미지 `nousresearch/hermes-agent`로 **격리 컨테이너 `hermes-solomon`**
  (호스트 `~/.hermes`와 분리, 포트 8652/9129, llm-wiki·회사 repo 마운트).
- `solomon-profile/`(SOUL·USER), `.env.example`, `.gitignore`(hermes-home·.env).

### Verified — Stage 0 동작
- **OAuth(ChatGPT) 인증, 기본 모델 `gpt-5.5`**(provider `openai-codex`).
- Solomon 정체성 로컬 대화 검증(기획·검증 역할, 구현 안 함).
- **Slack** 인바운드·아웃바운드 동작(봇명 Solomon, 채널 #ceo-office/#approvals/#mission-log).
- **Kanban** create/list/archive + **웹 대시보드(게시판)** `localhost:9129`.

### Notes
- 별도 지식 저장소: `my-hermes-company-llm-wiki-2026`.
- 다음: **Stage 1** — 1호 미션(연구·기술 동향 보고서) 파이프라인 완주.

[v0.3.0]: https://github.com/jxcross/my-hermes-company-2026/releases/tag/v0.3.0
[v0.2.0]: https://github.com/jxcross/my-hermes-company-2026/releases/tag/v0.2.0
[v0.1.0]: https://github.com/jxcross/my-hermes-company-2026/releases/tag/v0.1.0
