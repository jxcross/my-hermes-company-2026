# Changelog

이 프로젝트의 주요 변경 이력. 형식은 [Keep a Changelog](https://keepachangelog.com/) 및
[Semantic Versioning](https://semver.org/)을 따른다.

## [Unreleased]

### Added — 추론 백엔드를 갈아끼울 수 있게 했다 (`docs/14`)
- **`scripts/set_backend.py`** — 프로필 11종의 `model:` 블록을 **한 명령으로** 전환한다
  (`--backend codex|ollama` · `--show` · `--dry-run`). 배치표는 스크립트 상단 `TIERS`·`BACKENDS`
  **한 곳에만** 있고, `profiles-src/`(git 소스)와 `hermes-home/`(라이브) 양쪽을 함께 갱신한다.
  - **왜**: codex 주간 한도가 소진돼(리셋 2026-08-09 14:07) 실미션 M-2026-005 가 stage 4 에서
    멈췄고, 나흘 동안 파이프라인·게이트 62종·템플릿 20종을 **실행으로 검증할 수 없었다**.
    한 공급자의 한도가 회사 전체를 세우면 안 된다.
  - **로컬 배치**(M4 Max·64GB): 작성자 `qwen3.6-64k` · 검증자 **`glm-4.7-flash-64k`** ·
    코더 `qwen3-coder-64k`(64K 창에서 각각 22~24GB). **작성자≠검증자를 모델 *계열* 수준까지**
    지킨다 — 같은 계열은 같은 맹점을 공유해 독립검증이 성립하지 않는다. 테스트가 강제한다.
  - **`--build-models`** — 배치 모델은 Modelfile 로 창을 못박은 **파생본**이다.
    **실측으로 드러난 것**: Ollama 의 `/v1/chat/completions` 는 `options.num_ctx` 를 **무시한다**
    (`/api/chat` 은 지킨다). Hermes 는 `/v1` 로 말하므로 config 의 `ollama_num_ctx` 만으로는
    창이 안 잡히고, 모델이 최대 창으로 로드된다 — llama3.1:8b 로 재보니 8192 에서 5.9GB,
    131072 에서 **22GB** 였다. 파생본은 원본과 **같은 blob 을 공유**해 디스크가 늘지 않는다.
    `OLLAMA_NUM_CTX` 상수 하나가 Modelfile 과 config 양쪽을 채워 값이 갈라질 수 없다.
  - **PyYAML 비의존** — 호스트 python3 에 PyYAML 이 없다. `model:` 최상위 블록만 행 단위로
    치환해 `agent:`·Hermes 가 스스로 써 넣은 `onboarding:`·root config 의 `platform_toolsets:` 를
    무손상으로 남긴다. 상태 파일 없이 **config 파일 자체**가 단일 진실원이다.
- **`docs/14_local_model_backend.md`** — 배치 근거, config 키가 하나씩 빠졌을 때 무엇이 깨지는지,
  전환·복귀 절차, 호스트 Ollama 설정.

### Changed
- **`scripts/usage_report.py` 가 백엔드를 인식한다.** 로컬 백엔드에서는 codex 한도가 착수
  판정의 근거가 아니다 — 로그의 429 `resets_at` 만 보면 **리셋 시각까지 계속 `exit 1`** 이라
  로컬로 옮긴 의미가 사라진다. `ollama` 백엔드에서는 **Ollama 서버 도달 + 배치 모델 설치
  여부**로 판정하고(`/api/tags` — 여전히 **LLM 미호출**), 한도 기록은 복귀 판단용 참고로만
  표시한다. `--backend codex|ollama` 강제 지정 추가.
- `profiles-src/*/config.yaml` 의 `model:` 블록은 이제 **생성물**이다 — 직접 고치지 마라.

### Verified (2026-08-05 · 연결 검증)
- 프로필 11종 전부 로컬 모델로 전환 · 세 티어 모두 실호출 성공 · **`ollama ps` CONTEXT = 65536**
  (설정이 실제로 반영됐는지를 바깥에서 관측 — 이게 없었으면 262144 인 걸 몰랐다).
- **tool call 실증**: `scout`·`developer` 가 지시한 파일을 실제로 썼다.
- `usage_report.py` 가 로컬 백엔드에서 **exit 0**(codex 한도는 아직 리셋 전인데도).
- 토글 왕복(ollama→codex→ollama) 양방향 정상.
- 회귀: 린터 **20/20** · E2E **14/14 510케이스** · 단위 **322종** 전건 통과.

### Notes
- ⚠️ **로컬 30B 급은 도구 프로토콜을 덜 지킨다 — 연결 검증에서 이미 보였다.** `developer` 가
  목표 파일은 정확히 썼지만 **경로를 백틱으로 감싼 채** 엉뚱한 곳에 두 번 더 쓰려 했다
  (`HERMES_WRITE_SAFE_ROOT` 와 `.json` 문법 검증이 막았다 — 가드레일이 일했다). 실미션에서는
  `kanban_complete` 미호출·`VERDICT:` 포맷 이탈이 같은 계열의 위험이다. 객관 게이트 62종은
  산출물을 보므로 그대로 작동하지만 **LLM 검증자의 판정 포맷**은 모델 품질에 직접 의존한다.
- **설정 키가 있다는 것은 그 키가 먹힌다는 뜻이 아니다.** `docs/13 §5` 의 "동작하는 척하는
  게이트" 와 같은 계열 — 넣은 설정이 반영됐는지를 **바깥에서 관측**하라(`ollama ps` 의 CONTEXT).

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
