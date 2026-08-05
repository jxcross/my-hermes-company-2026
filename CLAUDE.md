# CLAUDE.md — my-hermes-company-2026

> 이 파일은 어느 PC의 새 세션에서도 자동 로드된다(git에 포함). 프로젝트의 맥락·규칙·재개 방법을 담는다.
> (참고: Claude Code의 프로젝트 **메모리**와 `.env`·`hermes-home/`은 **로컬 전용**이라 PC 간 이동하지 않는다.)

## 프로젝트
Hermes Agent 기반 **AI-Native Company**. 창업자 **Sam**(CS 박사, 한국어) ↔ AI CEO **Solomon**, Slack 소통.
**Stage 1 full 11단계 파이프라인 실동작 중 + 템플릿 기반 미션 시스템 Pilot 완료**(미션 3건 완주: M-2026-001 슬라이스, M-2026-002 full, **M-2026-003 템플릿+이중게이트**). 사람은 목표·경계조건을 정하고 AI가 계획·조사·검증·정리를 수행(복리 성장 지향).

## 작업 규칙 (반드시 준수)
1. 구현 전 단계별 계획을 `docs/NN_*.md`(번호 접두)로 작성.
2. 사용자 요청·주요 작업·결과를 `history.html`에 기록.
3. 주요 단계 완료 시 **커밋 + `origin` 푸시**(메시지 명확히).
4. git **태그·릴리스는 Sam이 명시 요청할 때만**.

## 아키텍처 (요약 — 상세는 docs/)
- **Option B**: Hermes 네이티브 **Kanban + 전문 profile**. **Solomon = 기획·오케스트레이션·검증총괄·보고(구현 안 함)**, 실무는 전문 profile 위임.
- **작성자 ≠ 검증자**(코드 구현 profile ≠ 코드 검증 profile). 단계 내 병렬은 subagent.
- **전문화 4계층**: SOUL(좁은 역할)·Skill·누적 Memory·공유 Knowledge(LLM Wiki). 오염 방지.
- 미션 아키타입: **A** 동향 보고서 · **B** 논문 · **D** 웹개발(시뮬레이션 포함).
- 문서: `docs/02`~`docs/09` (설계·파이프라인·1호미션 SPEC·Stage0 가이드·ADR·다이어그램·전문화·게시판).

## 실행 상태 (Stage 1 — full 11단계 운영)
- 격리 컨테이너 **`hermes-solomon`** (`docker-compose.yml`, 공식 이미지 nousresearch/hermes-agent). 인증: OAuth(ChatGPT), provider `openai-codex`.
- **프로필 11종**: default(Solomon)·scout·reader·curator·synthesizer·writer(작성자) · **fact-checker·reviewer·tester**(검증자) · **architect·developer**(코더). 소스=`profiles-src/`. architect·developer·tester는 2026-08-04 아키타입 D 도입으로 신설(`docs/13 §7`).
- **⚠️ 추론 백엔드는 갈아끼운다 — 모델을 손으로 고치지 마라**(2026-08-05 신설 · `docs/14`). `model:` 블록은 **`scripts/set_backend.py` 가 생성**한다. 배치표는 그 스크립트 상단 `TIERS`·`BACKENDS` 한 곳에만 있다.
  | 티어 | 프로필 | `codex` | **`ollama`(현재)** |
  |---|---|---|---|
  | 작성자 | default·scout·reader·curator·synthesizer·writer | `gpt-5.6-terra` | `gemma4-26b-128k` |
  | 검증자 | fact-checker·reviewer·tester | `gpt-5.6-sol` | `gemma4-26b-128k` |
  | 코더 | architect·developer | `gpt-5.6-terra` | `gemma4-26b-128k` |

  ```bash
  python3 scripts/set_backend.py --show               # 현재 백엔드(불일치면 exit 1)
  python3 scripts/set_backend.py --build-models       # -128k 파생본 생성(없는 것만)
  python3 scripts/set_backend.py --backend ollama     # 로컬 · 한도 없음
  python3 scripts/set_backend.py --backend codex      # 8/09 14:07 이후 복귀
  ```
  ⚠️⚠️ **`context_length − max_tokens > 64000` 을 반드시 지켜라(docs/14 §3.2).** 못 지키면 Hermes 압축이 **퇴화 분기**로 떨어져 창의 85%에서 상시 발동하고 `compression.threshold` 가 **완전히 무력**해진다 — M-2026-005 stage 5 가 이걸로 압축 루프에 갇혀 멈췄다(65536−16384=49152 < 64000 → 41,779 토큰에서 발동). 현재 131072−16384=114688 → 97,484. 테스트가 강제한다.
  ⚠️ **`compression.*`·`agent.*` 는 루트 config 에서 프로필로 상속되지 않는다**(docs/14 §3.3) — named 프로필은 자기 `config.yaml` 만 읽는다. `set_backend.py` 가 프로필마다 직접 쓴다.
  ⚠️ **작성자≠검증자를 모델 계열 수준에서 포기했다**(Sam 승인 2026-08-05 · 속도 우선 통일). `BACKENDS["ollama"]["shared_verifier_model"]` 선언이 없으면 테스트가 FAIL 시킨다 — 불변식을 조용히 잃지 않기 위해서다. 남는 분리는 profile·SOUL·객관 게이트 62종이다.
  **배치는 추측이 아니라 측정으로 정했다** — `python3 scripts/probe_protocol.py`(도구 인자 충실도·부작용·종료 호출·VERDICT 포맷을 재는 프로브 · `docs/14 §2.1`). 후보 8종을 쟀고 채택 모델은 전 항목 100%. ⚠️ **tok/s 로 고르지 마라 — 벽시계로 골라라**(e4b 는 12b 보다 tok/s 가 1.7배인데 벽시계는 2배 빨랐다). ⚠️ **게이트를 재기 전에 게이트가 무엇을 읽는지 읽어라** — 처음에 VERDICT 를 "마지막 줄에 정확히"로 쟀다가 `glm-4.7-flash` 를 0%로 오판했다(`gate_keeper.py:53` 은 `.search()` 라 본문 어디든 되고, 다시 재니 100%였다).
  ⚠️ **`ollama_num_ctx` 만으로는 창이 안 잡힌다(실측)** — Ollama 의 `/v1` 은 `options.num_ctx` 를 **무시한다**(`/api/chat` 은 지킨다). 그래서 배치 모델은 Modelfile 로 창을 못박은 **`-128k` 파생본**이다(원본과 blob 공유 · 디스크 안 늘어남). 창 하나 차이로 메모리가 3.7배 난다 — 넣은 설정이 **반영됐는지 `ollama ps` 의 CONTEXT 로 확인하라**(`docs/14 §3.1`).
- **인프라 정비 완료**: `HERMES_WRITE_SAFE_ROOT=/opt/data:/work/company:/work/llm-wiki`(워커 직접쓰기, 복사 불필요) · **Tavily 웹검색**(키는 repo `.env`의 `TAVILY_API_KEY`, 전 프로필 os.environ 노출 필수) · **`WIKI_PATH=/work/llm-wiki`**(Curator의 karpathy-llm-wiki 스킬).
- **미션 산출물**: 보고서→`reports/M-2026-NNN/`, 지식→llm-wiki repo(raw/entities/concepts/reflections, 재사용률 추적). Kanban 게이트: 미션=부모·단계=자식, `link`=순차, `block --kind needs_input`=Sam 게이트, `--workspace dir:/work/company/reports/<mission>`.
- **반려 게이트 자동화(게이트키퍼)**: 사이드카 컨테이너 **`hermes-gatekeeper`**(`docker-compose.yml`, `scripts/gate_keeper.py`). 검증 task(6·9) 판정이 `VERDICT: FAIL`이면 산출물 재작업 루프(리비전→재검증) 자동 생성 + downstream(7·10) PASS 전까지 보류. **활성 게이트만** 처리(완료 미션 스킵, 재시작 안전). **Sam 승인 게이트도 자동화**(`approval_poll`, Web API): 활성 Sam-게이트를 `#approvals`에 자동 게시 + Sam의 `승인`/`승인 <task_id>` 감지→`kanban unblock`(SLACK_ALLOWED_USERS만). 상세 `docs/10 §4.4`·`docs/11 §7`.
- 웹 대시보드 `http://localhost:9129`, Slack `#ceo-office`/`#approvals`/`#mission-log`. 기동 `docker compose up -d`(게이트키퍼 포함) · `.env`/compose 변경 시 `--force-recreate`.
- **미해결 이슈**: ⚠️ **Slack 도달 불가 — 2026-08-05 재발(미해소)**. 실측: 호스트·컨테이너 모두 `slack.com` HTTP **000**(타임아웃) · `google.com`·`github.com` 은 200 → **네트워크성**(08-03·08-04 와 같은 증상, 그때는 와이파이 변경으로 복구). Kanban 전부 done·활성 게이트 0 이라 **당장의 실무 영향은 없다**. ~~Slack 도달 불가(2026-08-04 오전 재발)~~ → **[해소 2026-08-04 오후]** 네트워크 복구·게이트키퍼 폴링 정상. ~~Slack 아웃바운드 실패~~ → **[해소 2026-08-03]** 근본원인은 **네트워크가 slack.com 도달 불가**(force-recreate 오진). 와이파이 변경 후 복구·전송 검증 완료. Slack 이상 시 **1순위 진단=`curl https://slack.com/api/auth.test` 도달성**(status의 `configured`는 토큰존재만 의미). 진단 runbook·홈채널ID(`C0BM8FK3RTM`)는 `docs/10 §4.3`. · 반려 게이트 미강제(9→10 무조건 링크). Scoping은 Solomon이 자율분해하므로 수동 카드와 충돌 주의.

## ‼️ 로컬 전용 (git에 없음 — PC마다 재구성 필요)
- **`.env`**: Slack 토큰 등 시크릿. Sam이 안전하게 보관 후 새 PC에서 재작성(`cp .env.example .env`).
- **`hermes-home/`**: `auth.json`·`kanban.db`·`sessions` 등. 새 PC에선 `hermes setup`으로 **OAuth 재로그인**.
- **llm-wiki repo**: 형제 폴더에 clone — `github.com/jxcross/my-hermes-company-llm-wiki-2026`.
- **Claude Code 프로젝트 메모리**: 로컬. 이 CLAUDE.md가 대체 컨텍스트 역할.

## 새 PC 부트스트랩 (순서)
`docs/05_stage0_setup_guide.md` 참조. 요약: repo 2개 clone → `docker compose pull` → `cp .env.example .env`(SLACK·`TAVILY_API_KEY` 값 채움) → `hermes setup`(OAuth) → `solomon-profile/`의 SOUL·USER를 `hermes-home/`에 복사 → **전문 프로필 7종 재생성**(`profiles-src/<name>/`의 SOUL·config를 `hermes profile create` 후 `hermes-home/profiles/<name>/`에 복사: scout·reader·writer·synthesizer·curator·fact-checker·reviewer) → **`python3 scripts/set_backend.py --backend codex|ollama`**(배치 동기화 — `hermes profile create` 가 만든 config 를 배치표대로 덮는다) → `docker compose up -d`(hermes-solomon + **hermes-gatekeeper 사이드카** 동시 기동) → 대시보드/Slack/`set_backend.py --show`·`hermes profile list`·`docker compose ps`(게이트키퍼 Up) 확인.
**로컬 Ollama 백엔드로 부트스트랩하면 OAuth(`hermes setup`) 자체가 필요 없다** — 호스트에 Ollama 와 배치 모델 3종만 있으면 된다(`docs/14`).

## 다음 할 일
**완료(2026-08-03):** ✅ Slack 재연결(`docs/10 §4.3`) · ✅ 반려 게이트 자동화=`hermes-gatekeeper` 사이드카(`docs/10 §4.4`) · ✅ **템플릿 기반 미션 시스템 Pilot(P0–P4)**: 선언적 템플릿→Kanban 번역기 + 이중 게이트(객관 Python + LLM 검증자) + 실미션 **M-2026-003 완주**(11/11, 커밋 b7ec055). 상세 `docs/11 §7`. 신규 미션 실행: `python3 scripts/instantiate_template.py trend-report <MID> --topic "..."`(협상 미리보기 `--dry-run --render mermaid`).

**← 현 최우선: Phase 2** (`docs/11 §7`의 미해결·개선점):
1. ~~**병렬화**~~ **[완료·라이브검증 2026-08-04]** subagent 스테이지 내 팬아웃 구현(형제 task 아님 — Hermes는 동일 profile task 순차 실행). 번역기가 템플릿 `parallel` 블록을 읽어 stage 3·5·8 task **본문에 delegation 배치 위임 프로토콜 주입**(스테이지 1 task 유지→gate_keeper 무손상). **라이브 파일럿 M-2026-004 완주**(11/11, 보고서 커밋 b585526): stage3 병렬 subagent 디스패치→worker shard 5·병합, stage5 분석 12·stage8 집필 7 shard. 파일럿이 **gate_keeper fail-open 결함 발견·수정**(자식 transient 조회실패 None을 종단 오인→downstream 고아화; `classify_children`+defer, 테스트 4종, 커밋 3d25a54). 상세 `docs/11 §5·§3.B·§7`. 신규 미션: `python3 scripts/instantiate_template.py trend-report <MID> --topic "..."`.
2. ~~**컨테이너 GITHUB_TOKEN**~~ **[해소 2026-08-04]** `.env`의 `GITHUB_TOKEN`(Fine-grained PAT, Contents:write) + docker-compose가 `GIT_CONFIG_*`로 github.com credential helper 주입(토큰 파일 미저장, 신원 보존). 컨테이너 `git push` 인증 검증됨. ~~**Deliver Slack 실패**~~ **[해소]** Deliver 게시를 `hermes send`(Web API)로 고정(템플릿 stage11). **[신규 잔여] Slack Socket Mode 인바운드 flapping**(2026-08-02~, 아웃바운드는 정상) 조사 필요.
3. ~~**Slack 승인→Kanban unblock 배선**~~ · ~~**pre-blocked Sam 게이트 알림**~~ **[해소 2026-08-04]** gate_keeper `approval_poll`(Web API 폴링, Socket Mode 비의존): #4 활성 Sam-게이트를 `#approvals`에 **판단 내용 포함**(주제·계획·정책 또는 보고서요약·검증·공개대상) 자동 게시 + #3 `SLACK_ALLOWED_USERS`(Sam)의 `승인`(단일)/`승인 <task_id>`(명시) 감지→`kanban unblock`. 단위테스트 10 + 라이브 E2E 검증. **[잔여] Socket Mode 인바운드 flapping**(네트워크성; recreate 후 안정, 승인흐름은 비의존) 모니터.
4. ~~**Slack 네트워크 도달 불가**~~ **[해소 2026-08-04 오후]** 세션 초 `slack.com` HTTPS 타임아웃(google·github은 정상 = 네트워크성)이 있었으나 복구됨. 검증: 호스트 `auth.test` 200 · 컨테이너 Web API `ok=true` · **게이트키퍼 WARN 3시간 38분째 없음**(마지막 10:16, 확인 13:54). 진단 순서는 `docs/10 §4.3`.
5. ~~**매처(C)**~~ **[완료 2026-08-05]** `scripts/match_template.py` + `templates/manifest.json`(템플릿에서 생성). 3-way 판정 + 근거 낱말 + `draft` 경고. 템플릿 20종에 `keywords:` 선언 추가. ~~전용 린터(E)~~ [완료 — `scripts/lint_template.py`].
6. **성장 지표 대시보드** ← **남은 백로그 1건**(로컬 백엔드 도입 후에도 유효) — 재작업률·wiki 재사용률·소요시간 누적. + **미션 진행상황 Slack 실시간 보고**(현재 통지는 게이트 이벤트·Deliver 시점만 — Sam이 "진행상황을 전혀 모르겠다"고 지적한 건).

---

## ▶ 이어서 할 일 (2026-08-05 (3) 세션)

**⚠️⚠️ 최우선 사실: 파이프라인이 날조를 통과시켰다. 이게 다른 모든 것에 우선한다.**
M-2026-005 는 stage 5·6·7 을 **통과해** stage 8 승인 대기에 있는데, **stage 5 분석 11편 중
7편이 날조다**(본문에 `[Simulated deep analysis based on relevance impacts.]` 라고 스스로 적혀
있다). `raw/` 에 원문이 다 있는데 읽지 않고 `curated.md` 메모를 재서술했다. 창 크기 탓이
아니다 — 35KB 원문도 똑같이 날조됐다. **게이트 3종이 전부 통과시켰다**: 객관 게이트는
`sources.yaml` 메타데이터만 읽고, LLM 검증자는 11편 중 5편만 대조하고 `VERDICT: PASS` 를
냈다. 상세·교훈은 **`docs/11 §7 ⑧`**·**`docs/14 §7 1.5`**. 증거는 커밋 `0e76dce`.

**→ stage 8(`t_3748d855`)을 승인하지 마라.** stage 11 Deliver 가 PUBLIC 저장소에 push 한다.

**계획서: `~/.claude/plans/profile-optimized-moore.md` (Sam 승인). 6 Phase.**

**① Phase 2 — 프로필 11종 256k 전환**(Sam 지시). `gemma4:26b` 의 천장이 정확히 262144 다.
⚠️ **파생본 이름을 반드시 `gemma4-26b-256k` 로 바꿔라** — `--build-models` 는 존재를 **이름으로만**
판정해서(`set_backend.py:382`), 상수만 올리면 "이미 있음"을 찍고 서버는 131072 를 계속 서빙한다.
```bash
python3 scripts/tests/test_set_backend.py     # 먼저
python3 scripts/set_backend.py --build-models # 모델 먼저(config 가 없는 모델을 가리키지 않게)
python3 scripts/set_backend.py --backend ollama
docker compose up -d --force-recreate
ollama ps                                     # ★ CONTEXT=262144 실측 · SIZE 기록(docs/14 §5 갱신)
```

**② Phase 3 — `analysis_substance` 게이트 신설**(캠페인 전제). 자가선언 시뮬레이션 문구 탐지 ·
샤드 개수 == `sources.yaml` 의 `selected` 개수 항등 · 분량 상하한 쌍. **빈 입력에서 FAIL 해야
한다**(공집합 버그 11회 반복). + `lint_gate_drafts.py`(하네스 draft 정합) + `preflight_gates.py`
(A~F 하네스 부재의 대체). ⚠️ 이 게이트를 넣으면 stage 의 **공유 `--draft`** 가 바뀐다 —
`docs/13 §5` 의 `exit 2` 조합을 먼저 확인하라.

**③ Phase 4 — M-2026-005 복구.** 날조 7편만 재분석하는 리비전 카드를 stage 8 앞에 링크.
⚠️ `t_3748d855` 에 **`block` 을 쓰지 마라**(이미 blocked · 2회면 `triage`, 비-LLM 탈출구 없음) —
`comment` 로 사유를 남겨라. 이 단계가 **256k 효과와 새 게이트를 동시에 측정한다**(같은 자료·
같은 프롬프트·창만 2배). 여전히 날조면 **모델 문제로 확정**이고 ⑥ 전에 티어를 다시 논의한다.

**④ Phase 5 — 미션별 Kanban 보드**(Sam 지시). Hermes 는 **이미 다중 보드다**(게이트웨이
디스패처가 매 틱 보드를 열거 · 새 보드를 재시작 없이 집는다). 작업은 우리 사이드카 2개뿐:
`instantiate_template.py`(`--board`) 와 **`gate_keeper.py`**(`:403` 단일 보드 가정 — 다른 보드의
미션은 **검증 게이트가 영영 안 돌고 로그 한 줄도 안 남는다**). ⚠️ `--board` 는 **전역 플래그 —
서브커맨드 앞**이다. 기존 `default` 보드는 아카이브로 유지, 신규 미션만 새 보드.

**⑤ Phase 6 — 실미션 캠페인, 1건씩 순차.** 순서: **`code-docs`(I) 먼저** — 객관 게이트가 우리
저장소 **AST 와 대조**해서 날조로는 통과할 수 없는 유일한 저비용 후보다 → `policy-brief`(G) →
`lecture-course`(J) → `systematic-review`(B′) → `lit-monitor`(E) → `patent-spec`(F).
⚠️ G 전에 `policy.py` 의 `DRAFTS` 누락, J 전에 `lecture.py` 의 `source_balance` 누락을 고쳐라.

**⑥ 미완 백로그 1건: 성장 지표 대시보드**(재작업률·wiki 재사용률·단계별 소요시간).

**⑦ 2026-08-09 14:07 이후**: `python3 scripts/usage_report.py --backend codex` 로 리셋 확인.
③의 재분석 결과가 나쁘면 **작성자·검증자 티어를 codex 로 되돌리는 판단의 근거**가 된다.

---

## ‼️ 현재 진행 중 — 실미션 테스트 (`draft` 19종 → `tested`)

**1차 M-2026-005(아키타입 B `academic-paper`)는 stage 8 승인 대기다 — 그리고 그 산출물은
믿을 수 없다.** 경과: stage 4 에서 [API 한도 소진](docs/11_template_driven_missions.md)으로
정지(429 · 리셋 2026-08-09 14:07) → **로컬 Ollama 백엔드**(`docs/14`)로 전환해 stage 4 통과
(원인이 파이프라인이 아니라 429 였다는 진단이 확인됨) → stage 5 가 **압축 퇴화 분기**로 멈춰
창을 131072 로 올려 고침 → stage 5·6·7 통과.

**⚠️⚠️ 그런데 stage 5 분석 11편 중 7편이 날조다.** 본문이 스스로 그렇게 적고 있다:
`**Evidence:** [Simulated deep analysis based on relevance impacts.]`. `raw/` 에 원문이
다 있는데(35KB~384KB) 읽지 않고 `curated.md` 의 관련성 메모를 재서술했다.
**창 크기 탓이 아니다** — 384KB 원문도, 35KB 원문도 똑같이 날조됐다.

**게이트 3종이 전부 통과시켰다.** 객관 게이트(`recency_check`·`source_balance`)는
`raw/sources.yaml` **메타데이터만** 읽어 산출물을 아예 열지 않는다. LLM 검증자는 11편 중
**5편만 표에 올리고** 그중 2건을 스스로 `unverified` 로 적으면서 `VERDICT: PASS` 를 냈다
(근거: "모순의 징후가 없다" — 읽지 않은 것에 모순이 없는 건 당연하다). stage 7 Synthesis 가
그 위에 논지를 쌓았다.

> **교훈: 객관 게이트가 검사 대상이 아닌 파일을 보고 있으면 그 stage 에는 사실상 게이트가 없다.**
> 상세 `docs/11 §7 ⑧` · 모델 선정과의 관계는 `docs/14 §7 1.5`. 증거 커밋 `0e76dce`.

**→ `t_3748d855`(stage 8) 승인 금지.** 복구 = 날조 7편 재분석 리비전 → `analysis_substance`
포함 재검증 통과 후 승인. 이게 **256k 와 새 게이트의 첫 실전 측정**이다.

⚠️ **일시중지는 컨테이너를 세워라**(`docs/14 §6.5`). `kanban block` 을 두 번 하면 카드가
**`triage`** 로 가는데 거기엔 **비-LLM 탈출구가 없다**(`unblock`·`promote` 모두 거부 ·
`specify` 는 LLM 이 본문을 다시 쓴다). 그리고 **DB 를 손으로 고치면 디스패처가 즉시 다시
집는다** — 실제로 워커 2개가 동시에 떠 완료 산출물 1건을 덮어썼다(14.1KB→4.1KB, git 에 없어
복구 불가).

**계획서**: `~/.claude/plans/profile-optimized-moore.md`(2026-08-05 (3) Sam 승인 · 6 Phase).
캠페인 순서를 **`code-docs`(I) 먼저**로 바꿨다 — 객관 게이트가 우리 저장소 **AST 와 대조**해서
**날조로는 통과할 수 없는 유일한 저비용 후보**이기 때문이다. 그 다음 `policy-brief`(G) →
`lecture-course`(J) → `systematic-review`(B′) → `lit-monitor`(E) → `patent-spec`(F).
Tier 3·4(비용·외부 실행·저장소 수정 — K·M·O·P)는 **Sam 재확인**. 4-티어 원안은
`history.html #47`·`#48`.

### 재개 절차
```bash
# 백엔드에 따라 점검 대상이 다르다 — ollama=서버·모델 존재 · codex=한도 소진
python3 scripts/set_backend.py --show           # 현재 백엔드 확인
python3 scripts/usage_report.py                 # exit 0 이어야 재개 가능
docker compose up -d && docker compose ps       # 2개 Up
docker exec hermes-solomon hermes kanban list | grep M-2026-005
# ⚠️ 컨테이너를 세웠다 켰으면 stale claim lock 을 먼저 풀어라(docs/14 §6.5 ④).
#    카드가 ready 인데 디스패처가 영영 안 집고, 로그도 안 남는다.
docker exec hermes-solomon hermes kanban reclaim <tid>
docker exec hermes-solomon hermes kanban dispatch --dry-run --json   # spawned 에 뜨는지
```
남은 경로: **stage 5 리비전(날조 7편 재분석)** → 재검증 → **8 집필 개시 승인** → 9 → 10 →
**11 Deliver 승인**. 승인은 내가 직접 한다(Sam 위임).
⚠️ stage 4 는 `peer_reviewed` 를 **하한 6에 정확히 맞춘** 상태에서 선별했다 — 한 건이라도
`rejected` 로 버리면 stage 6 이 반려한다(그게 정상 동작이다).

**⚠️ 라이브가 결함 8건을 냈다 — 그중 7건은 E2E 픽스처 510케이스가 원리적으로 볼 수 없는 층이다**
(`docs/11 §7`). ①인스턴스화가 디스패처와 경합해 **상류 없이 워커 6개 실행** ②`block` 실패를
WARN 으로 넘겨 **게이트 빠진 파이프라인** ③**`archive` 가 워커를 안 죽여** 폐기된 그래프가
새 미션에 20파일을 씀 ④`VERIFIERS` 하드코딩 ⑤**승인 `--reason` 이 산출물 주제를 오염**
⑥`status: rejected` 가 정책 카운트에 잡힘 ⑦**실패 표면 증상과 근본 원인이 두 층 떨어짐**(429 가
카드에 안 남는다) ⑧**작성자가 "시뮬레이션했다"고 자백한 산출물을 게이트 3종이 전부 통과**
(가장 심각 — 객관 게이트가 검사 대상이 아닌 파일을 보고 있었다).
①②④⑥은 수정·커밋, ③⑤는 절차 규약, ⑦은 후속 과제, **⑧은 진행 중**(`analysis_substance`).

**테스트 중 게이트 승인은 Claude 가 직접 한다**(Sam 위임 2026-08-05). ⚠️ **승인 사유는 다음
워커가 읽는다** — 파이프라인에 대한 지시로 쓰고, 운영 메모는 `[운영 메모 · 산출물 지시 아님]`
접두를 붙여라(⑤가 그래서 났다).

**미완 백로그 1건**: **성장 지표 대시보드**(재작업률·wiki 재사용률·단계별 소요시간).
데이터 출처는 kanban 이벤트·`reports/*/pipeline.json`·게이트키퍼 로그. Sam 이 지적한
"미션 진행상황을 전혀 모르겠다"에 대한 답이기도 하다. 나머지 3건(발견 문서화·사용량
가시화·매처 C)은 완료.

**⚠️ 미션을 시작하기 전에 `python3 scripts/usage_report.py` 를 돌려라.** 착수 불가면 `exit 1` 이고,
그 상태로 미션을 걸면 워커가 60초마다 크래시하다 카드가 blocked 로 떨어진다(카드에는
'protocol violation' 만 남아 원인을 알 수 없다). 이 스크립트는 **LLM 을 호출하지 않는다.**
**점검 대상은 백엔드에 따라 다르다**(`docs/14 §6`): `codex`=워커 로그의 429 `resets_at` ·
`ollama`=**Ollama 서버 도달 + 배치 모델 설치 여부**(로컬은 한도가 없으므로 지나간 429 기록으로
막지 않는다). `--backend codex` 로 강제 지정하면 복귀 시점을 확인할 수 있다.

**⚠️ 미션을 폐기·재시작할 때는 카드 archive 만으로 부족하다**:
`docker exec hermes-solomon ps -eo pid,args | grep 'kanban task'` 로 **프로세스를 확인하고 죽여라**.

---

## ✅ 완료 — harness 스킬 → 템플릿 변환 20/20 (`docs/13`)

**변환은 2026-08-05 에 20/20 으로 끝났다.** [`docs/13`](docs/13_skill_to_template_conversion.md) 은 이제 **함정 사전(§5)·매핑 사전(§3)** 으로 쓴다 — 새 아키타입을 만들거나 게이트를 고칠 때 먼저 읽어라. **다음 단계는 실미션**(Sam 이 아키타입 순서를 정한다).

| | 상태 |
|---|---|
| 변환 | **20/20 ✅ 완료** — A `trend-report`(**proven**) · B `academic-paper` · B' `systematic-review`(PRISMA) · D `webapp-build` · E `lit-monitor`(주기 실행 — 미션 간 지속 상태 `monitors/`) · F `patent-spec`(고지 강제) · G `policy-brief`(4포맷 동시 산출 + 3게이트) · H `legal-draft`(계약서·의견서·자문서·약관 + **개인정보 차단**) · I `code-docs`(코드베이스 문서화 — **AST 대조 검증**) · J `lecture-course`(강의 자료 — LO·Bloom 사슬) · K `code-migration`(마이그레이션 — **실제 코드 변경·git 대조**) · L `security-audit`(보안 감사 — **공개 범위 분리**) · M `agent-eval`(RAG/Agentic 시스템 구축·평가 — **평가셋·통계·재현성 3중 검증**, 산출물이 아키타입 B 의 입력) · N `dataset-release`(데이터셋 큐레이션·배포 — **개인정보·라이선스·공개범위 3중 강제**) · O `repro-package`(재현 패키지 — **실행 증거 요구·미검증 경로 공시 강제**) · P `sim-experiment`(DOE 파라미터 스윕 — **해시 재계산·입력 드리프트·민감도 불변식**) · Q `research-proposal`(연구비 제안서 — **추적성 사슬·예산 회계·자격 요건**, 기본 비공개) · R `reviewer-response`(리뷰어 응답서 — **원문 대조·원고 실변경 대조**, 기본 비공개) · S `outreach-content`(성과 발신 — **수치↔claim 값 대조·공개 근거 강제**) · T `conference-slides`(학회 발표 슬라이드 — **발표 분량 양방향·번들 미치환 검출·재사용 4종**). **A 외 전부 `draft`** |
| **다음 단계** | 변환 끝. **실미션을 하나씩**(Sam 이 순서를 정한다) · 그 전에 Slack 도달성 확인 |
| profile | **11종** — 기존 8 + `architect`·`developer`·`tester`(아키타입 D 도입 시 신설) |
| 객관 게이트 | **62종** `scripts/gates/` — recency·source_balance·doc_consistency·test_run·prisma_counts·prisma_checklist·seen_dedup·digest_shape·claim_consistency·patent_format·evidence_grade·stakeholder_coverage·format_consistency·clause_completeness·law_citation·legal_safety·symbol_truth·api_coverage·doc_links·objective_coverage·bloom_distribution·course_consistency·content_accessibility·atomic_commit·test_pass_rate·behavior_diff·owasp_coverage·cve_remediation·finding_completeness·secret_redaction·eval_set_quality·stat_significance·repro_determinism·run_completeness·pii_presence·license_compat·schema_conformance·datasheet_completeness·result_tolerance·env_consistency·install_evidence·reproduce_doc·bit_exact·solver_pin·doe_completeness·analysis_integrity·proposal_format·budget_integrity·call_alignment·proposal_traceability·comment_fidelity·comment_coverage·change_consistency·response_quality·claim_provenance·channel_format·outreach_tone·release_readiness·**slide_budget·deck_format·diagram_integrity** |
| 산출 도구 | 4종 `scripts/tools/` — bib_export·monitor_state·relevance_score·budget_build |
| 운영 도구 | `scripts/match_template.py`(미션→템플릿 3-way 매처 · `--rebuild` 로 manifest 생성) · `scripts/usage_report.py`(착수 전 점검 · **LLM 미호출** · 백엔드별 판정) · **`scripts/set_backend.py`**(추론 백엔드 codex↔ollama 전환 · `docs/14`) · **`scripts/probe_protocol.py`**(로컬 모델 도구 프로토콜 준수도 측정 — 모델 선정 근거) |
| 검증 | `python3 scripts/lint_template.py --all`(20/20) · 테스트 **326종**(32 템플릿 + 23 게이트키퍼 + 204 게이트 + 8 매처 + 12 사용량 + 27 백엔드 + 20 기타) · **E2E 하네스 `scripts/tests/fixtures/run_all.py`(14종 510케이스)** |

**Sam 지시:** 실미션은 **전체 변환을 마친 뒤 하나씩** 돌린다(변환 중에는 dry-run만).

**게이트를 고쳤으면 E2E 하네스를 다시 돌려라** — `docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'`. 단위 테스트만 통과하는 수정은 판정 경로 전체를 검증하지 않는다(`scripts/tests/fixtures/README.md`).

**변환의 교훈(§5 요약):** 이식은 복사가 아니다. **20건 변환에서 20건 모두 결함이 나왔다** — 게이트 겹침(불변식 우회)·검증자 부재·느슨한 체크리스트·"동작하는 척"하는 게이트(한국어 정규식 붕괴)·**docstring은 검사한다는데 코드는 안 하는 게이트**·병렬 산출물 부재 미검출 등. **이식한 게이트는 반드시 일부러 깨뜨린 픽스처로 FAIL을 확인하라.** PASS만 보면 아무것도 측정하지 않는 게이트를 발견할 수 없다. **반대 방향도 확인하라** — legalforge 게이트 2종은 **어떤 입력에도 FAIL**하는 상태였다(정상 픽스처로 PASS 확인 필수). 또한 **이식 전에 우리가 이미 가진 게이트와 겹치는지 보라** — policyforge 하드게이트 3종 중 1종은 `source_balance`+`recency_check`와 같은 일이라 policy 블록으로 흡수했다.

**⚠️ 보안 미결(변함없음)**: 진단 중 `SLACK_BOT_TOKEN` 값이 세션 로그에 노출됨 → **재발급(rotate) 권장**(Slack 앱 Regenerate → `.env` 갱신 → `docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper`).

**세션 종료 상태(2026-08-05 (2) · 로컬 백엔드 도입):** 신규 도구 2종(`set_backend.py` 추론 백엔드 전환 · `probe_protocol.py` 모델 프로토콜 측정) + `docs/14`. 커밋 3건(`dc65ed7`·`3e8824e`·`f070850`). **컨테이너 정지 · M-2026-005 stage 5 `blocked`(분석 3/11, 커밋으로 백업 확보) · 백엔드 `ollama`/`gemma4-26b-128k` 11종.** 이번 세션의 가장 큰 발견은 **압축 퇴화 분기**(위 ⚠️⚠️) — 파이프라인을 멈춘 것이 모델이 아니라 창 크기였다. ⚠️ Slack 여전히 도달 불가(네트워크성).

**새 세션 시작 시(3분 점검):**

⚠️ **컨테이너는 정지 상태로 넘겼다**(2026-08-05 Sam 요청 일시중지). `docker compose ps` 가
비어 있는 것이 **정상**이다 — 미션을 이어갈 때만 올려라.

```bash
git log --oneline -4            # HEAD: 압축 퇴화 분기 수정 + gemma4:26b 통일(f070850)
python3 scripts/set_backend.py --show   # ★ 백엔드(ollama · gemma4-26b-128k 11종 · exit 1 이면 불일치)
docker compose up -d            # ← 미션을 이어갈 때만. 2개 Up 확인
python3 scripts/usage_report.py         # ★ 착수 가능한가(로컬=서버·모델 존재 · exit 1 이면 시작 금지)
docker exec hermes-solomon hermes kanban list | grep M-2026-005   # stage 5 가 blocked
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_template.py --all'   # 20/20
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py' # 14/14 하네스
curl -s -o /dev/null -w '%{http_code}\n' --max-time 8 https://slack.com/api/auth.test           # ⚠️ 현재 000(도달 불가)
```

**→ 다음 할 일은 위 '▶ 이어서 할 일' 을 보라.** ⚠️ **가장 먼저 읽을 것: 파이프라인이 날조를
통과시켰다**(`docs/11 §7 ⑧`). codex 한도는 **2026-08-09 14:07** 리셋 — 그 뒤에는
`set_backend.py --backend codex` 로 되돌릴지 판단한다(재분석 품질이 판단 근거).

**§2④ 를 먼저 하라(이번 세션의 가장 큰 교훈):** 게이트를 새로 만들기 전에 `ls scripts/gates/`(62종)로 **이미 가진 것과 하는 일이 겹치는지** 보라. 재사용은 *하는 일*이 같을 때지 *이름*이 비슷할 때가 아니다(O 는 2종 재사용 · P 는 이름이 비슷한 `run_completeness` 를 일부러 재사용하지 않았다). **Q 에서 `legal_safety` 에 연 `publication_policy` 축이 바로 다음 변환(R)에서 그대로 쓰였다 — 쌍둥이 게이트를 만드는 대신 축을 여는 판단의 실증이다.**

**이식 시 1순위 확인 항목(공집합이 11회 반복됐다):** 입력이 **비었을 때** 그 게이트가 PASS 하는지부터 보라 — `len(s) <= 1` · `all(...)` · `not any(...)` · `glob` 결과 0건 · 항목 0개는 전부 공집합에서 참이다. **그리고 아키타입 Q 에서 새 모양이 나왔다 — 검사 대상이 있는데 측정값이 0 인 경우다**(빈 섹션 파일 5개 + 빈 간트가 '규격 통과'). **분량·개수를 재는 게이트에는 상한과 하한을 짝으로 둬라.**

**⚠️ 아키타입 K(`code-migration`)는 미션 밖의 실제 코드를 바꾸고 커밋한다.** 대상 저장소는 `HERMES_WRITE_SAFE_ROOT` 안이어야 하고, **`/work/company` 자신을 대상으로 삼으면 안 된다**(파이프라인이 자기 코드를 고치게 된다). 코드 변경 개시 직전에 Sam 승인 게이트가 있다.

**⚠️ 아키타입 M(`agent-eval`)은 코드를 만들어 실행하고 LLM API 를 수십~수백 회 호출한다** — 비용이 발생한다. stage 8(Run Plan)이 호출 수·비용을 산정하고 **stage 9 실행 직전에 Sam 승인 게이트**가 있다. 코퍼스 원문과 run 예측(`raw.jsonl`)은 `_private/`(gitignore), 코드·설정·지표·보고서는 커밋 대상이다. **커밋되는 것이 문서만이 아니므로** `secret_redaction` 이 `.py`·`.json`·`.yaml` 까지 훑는다(정책 `scan_extensions`).

**⚠️ 아키타입 N(`dataset-release`)의 산출물은 데이터 자체다 — 공개 위험이 가장 크다.** `publication_policy.mode` 가 **기본 `local_only`** 로, 데이터는 `_private/bundle/` 에만 두고 커밋되는 것은 데이터시트·스키마·스캔 요약·릴리스 노트뿐이다. `repo_commit`(데이터도 커밋)은 **Sam 이 Scoping·Deliver 에서 두 번 승인**해야 하며 `pii_presence` 가 선언한 mode 와 실제 산출 위치의 일치를 강제한다. **정본 포맷은 `.jsonl`/`.csv`** — 컨테이너에 pyarrow 가 없어 게이트가 parquet 을 못 읽으므로 읽을 수 없는 데이터 파일이 번들에 있으면 반려된다.

**⚠️ 아키타입 O(`repro-package`)는 외부에서 패키지를 내려받아 이식한 코드를 실행한다** — stage 7 직전에 Sam 승인 게이트가 있다. **컨테이너에 docker 데몬이 없어**(소켓을 붙이지 않는다 — 호스트 root 권한을 미션에 주는 일이다) 설치 테스트는 `venv` 로 하고 Dockerfile 은 정적 검토만 한다. `install_evidence` 게이트가 **실행 증거**(방식·종료코드·소요·로그)와 **`docker_verified: false` 공시**를 강제한다 — 검증하지 못한 경로를 조용히 넘어가면 받는 쪽이 검증됐다고 읽는다.

**⚠️ 아키타입 P(`sim-experiment`)는 실제 계산 자원을 쓴다**(HPC 시간·원격 솔버 과금) — stage 6 직전에 Sam 승인 게이트. **컨테이너에 matplotlib·numpy 가 없어 그림을 만들 수 없다** — `plot.py` 와 CSV 를 내고 `figures_generated: false` 를 공시하며 `analysis_integrity` 가 강제한다(O 의 `docker_verified` 와 같은 계열). `bit_exact` 는 **출력 해시를 다시 계산해 대조**한다(파일 읽기는 코드 실행이 아니라 게이트가 해도 안전하다).

**⚠️ 아키타입 Q(`research-proposal`)의 산출물은 심사 전에 공개되면 아이디어를 선점당한다.**
`publication_policy.mode` 가 **기본 `local_only`** 로, 제안서 본문·예산·PI 정보는 `_private/`
(gitignore)에만 두고 커밋되는 것은 `report/summary.md`(무엇을 만들었고 게이트가 어떻게
판정했는지)뿐이다. `repo_commit` 은 **Sam 이 Scoping·Deliver 에서 두 번 승인**해야 하며
`legal_safety` 가 선언한 mode 와 실제 산출 위치의 일치를 강제한다(아키타입 N 의 규율을
문서 산출물에 적용 — 새 게이트를 만들지 않고 `legal_safety` 에 `publication_policy` 축을
열었다). **PI 개인정보(주민등록번호·계좌)는 `_private/` 안에서도 평문 금지** — 초안은
플레이스홀더로 쓰고 실제 값은 사람이 NTIS 에 직접 입력한다.

**⚠️ 아키타입 R(`reviewer-response`)의 입력은 대외비다.** 리뷰어 코멘트는 저널의
비밀유지 관행상 공개할 수 없고 심사 중 원고는 미발표 저작물이다. `publication_policy.mode`
기본 `local_only` — 원고·리뷰·응답은 `_private/`, 커밋은 `report/summary.md` 뿐이다.
**원본 원고(`_private/original-ms.md`)를 반드시 보존하라** — `change_consistency` 가 수정
원고를 원본과 대조해 **태그만 붙이고 내용을 안 고친 경우**를 잡는다(원본 게이트의 가장 큰
구멍이었다).

**⚠️ 아키타입 S(`outreach-content`)는 유일하게 '공개' 가 목적이다** — 그래서 규율이
뒤집힌다. 감추는 것이 아니라 **공개해도 되는 것만 공개하는 것**이다. 원본에는 이 질문이
아예 없다. `release_readiness` 가 **공개 근거를 선언하게 하고**(fail-closed) 엠바고·특허
상태를 발신일과 대조한다 — **`patent_status: planned`(출원 예정)면 막는다**(공개하면
신규성을 잃는다 · 아키타입 F 와 충돌). 커밋 자체가 공개이므로 `repo_commit` 은 원자료가
이미 공개된 경우(arXiv·DOI·릴리스)에만 허용한다. **우리는 게시하지 않는다** — 사람이 올린다.

**⚠️ 아키타입 T(`conference-slides`)에서 배운 것 — 한 stage 의 객관 게이트는 `--draft` 를
**하나만 공유한다**.** 게이트마다 draft 해석이 다르면(미션 루트 / 콘텐츠 디렉터리) 그 조합은
실미션에서 `exit 2` 로 막힌다 — 아키타입 S 의 stage 7·8 이 실제로 그랬고 하네스는 53/53
이었다(하네스가 게이트마다 편한 draft 를 골라 줬기 때문이다). **새 게이트는 walk-up
`mission_root`**(`SCOPE.md` 를 만날 때까지 위로)로 쓰고, **하네스의 draft 는 템플릿이 선언한
값을 그대로** 옮겨라. 상세 `docs/13 §5`.

**⚠️ 이 저장소는 PUBLIC 이다.** Deliver 단계가 `reports/` 를 커밋·push 하므로 **미션 산출물에 민감 정보가 남으면 그대로 공개된다.** 아키타입 H(법률 문서)는 초안을 플레이스홀더로 쓰고 `legal_safety` 가 강제한다(실제 개인정보는 `_personal/`). 아키타입 L(보안 감사)은 **취약점 상세를 `_private/`(gitignore)에, 공유용 요약만 `report/`에** 두고 `secret_redaction` 이 커밋 대상을 검사한다.
