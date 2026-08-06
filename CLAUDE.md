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
  | 작성자 | default·scout·reader·curator·synthesizer·writer | `gpt-5.5` | **`gemma4-26b-256k`** |
  | 검증자 | fact-checker·reviewer·tester | `gpt-5.5` | **`gemma4-26b-256k`** |
  | 코더 | architect·developer | `gpt-5.5` | **`gemma4-26b-256k`** |

  ```bash
  python3 scripts/set_backend.py --show               # 현재 백엔드(불일치면 exit 1)
  python3 scripts/set_backend.py --build-models       # -256k 파생본 생성(없는 것만)
  python3 scripts/set_backend.py --host-setup         # ★ 호스트 서버 설정(launchctl) — 아래 ⚠️⚠️
  python3 scripts/set_backend.py --backend ollama     # 현재 (Sam 지시 2026-08-06)
  python3 scripts/set_backend.py --backend codex      # 한도 리셋 2026-08-09 14:07 이후 복귀 가능
  ```
  ⚠️⚠️ **호스트 서버 설정을 `--host-setup` 으로 걸고 Ollama 를 재시작하라 — 안 하면 스테이지
  내 병렬화가 조용히 직렬화된다**(2026-08-06 실측 · `docs/14 §5.1·§5.2`). `OLLAMA_NUM_PARALLEL`
  이 없으면 subagent 3개의 동시 요청을 서버가 큐에 세운다 — **오류도 로그도 없이 3배 느릴 뿐**이다
  (합산 처리량 73.1 < 단일 86.7 tok/s, 이득이 **음수**). 걸면 103.1 tok/s(+26%)·메모리 +1.4%.
  ⚠️ **`launchctl getenv` 는 "걸어 놨다"이지 "반영됐다"가 아니다.** Ollama 프로세스가 **53일째**
  돌고 있어서 `docs/14 §5` 가 지시한 설정이 **어떤 미션에서도 실효된 적이 없었다**(M-2026-005 포함).
  `usage_report.py` 가 이제 **서버 기동 배너**를 읽어 착수 전에 대조하고, '안 걸었다'와 '걸었는데
  반영 안 됐다'를 구분해 보고한다. `osascript quit` 이 안 먹을 수 있으니 `ps -o etime` 으로
  경과 시간이 리셋됐는지 확인하라.
  ⚠️⚠️ **`context_length − max_tokens > 64000` 을 반드시 지켜라(docs/14 §3.2).** 못 지키면 Hermes 압축이 **퇴화 분기**로 떨어져 창의 85%에서 상시 발동하고 `compression.threshold` 가 **완전히 무력**해진다 — M-2026-005 stage 5 가 이걸로 압축 루프에 갇혀 멈췄다(65536−16384=49152 < 64000 → 41,779 토큰에서 발동). 현재 **262144−16384=245760 → 208,896**. 테스트가 강제한다.
  ⚠️ **창을 바꾸면 파생본 이름(`-256k`)도 바꿔라** — `--build-models` 는 존재를 **이름으로만** 판정해서, 이름을 그대로 두면 "이미 있음"을 찍고 서버는 옛 창을 계속 서빙한다(config 는 새 값을 주장).
  💡 **창은 생각보다 싸다(2026-08-05 (3) 실측)**: `gemma4:26b` 는 131072 → 262144 로 2배 올려도 메모리가 17.50GB → 17.64GB, **+0.8%** 다. `docs/14 §3.1` 의 "창 하나로 3.7배"는 `llama3.1:8b` 숫자이고 **모델 계열을 건너뛰지 않는다** — 모델마다 다시 재라.
  ⚠️ **`compression.*`·`agent.*` 는 루트 config 에서 프로필로 상속되지 않는다**(docs/14 §3.3) — named 프로필은 자기 `config.yaml` 만 읽는다. `set_backend.py` 가 프로필마다 직접 쓴다.
  ⚠️ **작성자≠검증자를 모델 계열 수준에서 포기했다**(Sam 지시 2026-08-05 (3) · 전 티어 `gpt-5.5` 단일화). `BACKENDS["ollama"]["shared_verifier_model"]` 선언이 없으면 테스트가 FAIL 시킨다 — 불변식을 조용히 잃지 않기 위해서다. 남는 분리는 profile·SOUL·객관 게이트 63종이다.
  **배치는 추측이 아니라 측정으로 정했다** — `python3 scripts/probe_protocol.py`(도구 인자 충실도·부작용·종료 호출·VERDICT 포맷을 재는 프로브 · `docs/14 §2.1`). 후보 8종을 쟀고 채택 모델은 전 항목 100%. ⚠️ **tok/s 로 고르지 마라 — 벽시계로 골라라**(e4b 는 12b 보다 tok/s 가 1.7배인데 벽시계는 2배 빨랐다). ⚠️ **게이트를 재기 전에 게이트가 무엇을 읽는지 읽어라** — 처음에 VERDICT 를 "마지막 줄에 정확히"로 쟀다가 `glm-4.7-flash` 를 0%로 오판했다(`gate_keeper.py:53` 은 `.search()` 라 본문 어디든 되고, 다시 재니 100%였다).
  ⚠️ **`ollama_num_ctx` 만으로는 창이 안 잡힌다(실측)** — Ollama 의 `/v1` 은 `options.num_ctx` 를 **무시한다**(`/api/chat` 은 지킨다). 그래서 배치 모델은 Modelfile 로 창을 못박은 **`-256k` 파생본**이다(원본과 blob 공유 · 디스크 안 늘어남). 넣은 설정이 **반영됐는지 `ollama ps` 의 CONTEXT 로 확인하라**(`docs/14 §3.1`) — 파일이 아니라 서버가 보고하는 값을 봐라.
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

## ▶ 이어서 할 일 (2026-08-06 세션 · **M-2026-006 진행 중**)

### 진행 중: M-2026-006 (아키타입 I `code-docs`) — 로컬 백엔드 첫 실미션

**Sam 지시(2026-08-06)로 로컬 `ollama` 백엔드로 전환하고 실미션을 착수했다.** codex 한도
리셋(2026-08-09 14:07)까지 78시간을 기다리는 대신이다 — 2026-08-05 (3) 의 "codex 복귀"
지시를 갱신하는 결정이다.

```bash
python3 scripts/set_backend.py --show     # ollama · gemma4-26b-256k · 11종 (exit 0)
python3 scripts/usage_report.py           # exit 0 + 서버 설정 5종 일치여야 한다
docker exec hermes-solomon hermes kanban --board m-2026-006 list    # 10단계
```

- 보드 **`m-2026-006`**(미션 전용) · 대상 코드베이스 `/work/company/scripts` · 독자 유지보수자
- 이 아키타입을 첫 번째로 고른 이유: 객관 게이트가 저장소 **AST 와 대조**해서 **날조로는
  통과할 수 없다.** 로컬 모델이 무너졌던 지점이 정확히 날조였다(`docs/11 §7 ⑧`).
- **stage 6 이 4워커 팬아웃**이라 2026-08-06 에 고친 `NUM_PARALLEL` 이 실제로 쓰인다.
- ⚠️ **산출물 실사를 단계마다 하라** — 워커의 완료 보고는 증거가 아니다:
  `grep -rniE "simulat|placeholder|TBD|가상의|Synthesized from" reports/M-2026-006/`

### 그 다음 아키타입 순서

`policy-brief`(G) → `lecture-course`(J) → `systematic-review`(B′) → `lit-monitor`(E) →
`patent-spec`(F). ⚠️ G 전에 `policy.py` 의 `DRAFTS` 누락, J 전에 `lecture.py` 의
`source_balance` 누락을 고쳐라 — `python3 scripts/lint_gate_drafts.py <template>` 가 알려준다.
(`code-docs` 는 draft 정합 ✓ 라 이번엔 해당 없음.)

### M-2026-005 는 세워 뒀다 — 재개하지 않는다

컨테이너 재기동 시 G6R Revision 카드가 **stale claim 때문에 `running` 으로 보였다.** 락
상태에 의존해 멈춰 있는 것은 불안정하므로 활성 카드 3종을 **`schedule` 로 명시적으로 park**
했다(`docs/14 §6.5 ⑤`). 사유에 `[운영 메모 · 산출물 지시 아님]` 접두를 붙였다.

### 미션 착수 런북 (신규 도구 3종이 앞에 붙었다)

```bash
MID=M-2026-007; TPL=policy-brief; BOARD=$(echo $MID | tr 'A-Z' 'a-z')
python3 scripts/set_backend.py --show && python3 scripts/usage_report.py   # 둘 다 exit 0
# ↑ 로컬 백엔드면 usage_report 가 **서버 실효 설정 5종 일치**까지 확인한다(WARN 이면 재시작)
python3 scripts/probe_parallel.py   # 팬아웃이 있는 템플릿이면 '병렬' 인지 확인
docker exec hermes-solomon sh -c "cd /work/company && python3 scripts/preflight_gates.py $TPL"      # 빈 입력을 반려하는가
docker exec hermes-solomon sh -c "cd /work/company && python3 scripts/lint_gate_drafts.py $TPL"     # 하네스≠템플릿 draft
docker exec hermes-solomon sh -c "cd /work/company && python3 scripts/lint_template.py $TPL"
docker exec hermes-solomon sh -c "cd /work/company && python3 scripts/instantiate_template.py $TPL $MID --topic '…' --dry-run --render mermaid"
docker exec hermes-solomon sh -c "cd /work/company && python3 scripts/instantiate_template.py $TPL $MID --topic '…'"
docker exec hermes-solomon hermes kanban --board $BOARD list     # ⚠️ --board 는 서브커맨드 **앞**
# ★ 산출물 실사 — 워커의 완료 보고는 증거가 아니다(⑧-d)
grep -rniE "simulat|placeholder|TBD|가상의|Synthesized from" reports/$MID/
git add reports/$MID && git commit          # 단계마다 (커밋 전까진 백업이 없다)
```

### ⚠️⚠️ 이번 세션이 남긴 가장 중요한 것 — 먼저 읽어라

**파이프라인이 날조를 통과시켰고, 그걸 잡는 층을 세 겹 만들었다.** 상세 `docs/11 §7 ⑧~⑧-d`.

| 무엇이 무너졌나 | 무엇으로 막았나 |
|---|---|
| stage 5 분석 11편 중 **8편이 원문 미독**(`raw/` 에 원문이 다 있는데) | **`scripts/gates/analysis_substance.py`** (신규 · 게이트 63종) |
| 객관 게이트가 `sources.yaml` 만 읽어 **산출물을 아예 안 봄** | 위 게이트를 `academic-paper`·`systematic-review`·`lit-monitor` 에 배선 |
| LLM 검증자가 11건 중 2·5건만 대조하고 **두 번 다 PASS** | 객관 게이트가 두 번 다 뒤집었다(실전 확인) |
| 승인 요청문이 **틀린 판정을 그대로 사람에게 전달** | `gate_keeper.artifact_inspection()` — 승인문에 산출물 실측치 |
| 워커가 **작업 보고를 날조**(디스크 무변경인데 완료 선언) | 아직 미해결 — 아래 '남은 과제' |

> **핵심 교훈 셋**
> ① **객관 게이트가 검사 대상이 아닌 파일을 보고 있으면 그 stage 에는 게이트가 없다.**
> ② **워커의 완료 보고는 증거가 아니다** — 산출물을 봐야 한다.
> ③ **검사하는 쪽도 검사받아야 한다** — 내가 만든 게이트의 구멍은 `preflight_gates.py` 가,
>    린터의 오탐은 픽스처 대조가 잡았다(⑧-c).

**✅ 이중 게이트가 실전에서 완주했다**: LLM 검증자 PASS → `analysis_substance` FAIL →
게이트키퍼가 합산 FAIL → **리비전 카드 자동 생성 + downstream 보류**. 반려 루프의
첫 실미션 검증이다.

### 남은 과제

1. **워커의 허위 완료 보고**(⑧-d) — 카드를 `done` 으로 만들어 **진행 신호 자체를 오염**한다.
   게이트는 검증 단계에서만 도는데, 검증자가 없는 단계는 못 잡는다.
   후보: 작업 카드 완료 시 게이트키퍼가 **산출물 변경(mtime·해시)을 대조**.
2. **하네스 draft 드리프트 FAIL 8 · WARN 5** — `lint_gate_drafts.py` 참조.
   실미션 조합이 한 번도 검증되지 않은 stage 들이다(code-migration s8 · legal-draft s5 ·
   outreach-content s7·8 · repro-package s10).
3. **성장 지표 대시보드** — 미완 백로그 1건(재작업률·wiki 재사용률·단계별 소요시간).
4. **`SLACK_BOT_TOKEN` rotate** — 세션 로그 노출 이력(보안 미결).
5. 아키타입 A~F 는 여전히 **E2E 하네스가 없다** — `preflight_gates.py` 가 부분 대체.

### M-2026-005 (아키타입 B) — 결함 사례로 보존, 재개하지 않는다

`reports/M-2026-005/` 는 **"게이트 집합이 무엇을 못 보는가"의 1차 증거**다(커밋
`0e76dce`·`879f5c4`). 카드 상태: stage 8 `scheduled`(내가 park) · `t_a895d1c8` G6R
Revision 은 게이트키퍼가 자동 생성한 것으로 **stale claim 이 남아 있다.**
**`academic-paper` 의 `maturity` 승격에 계상하지 않는다.**
"처음부터 다시 테스트"(Sam 지시)이므로 이 미션은 재개 대상이 아니다.

---

## ‼️ 실미션 테스트 — 1차 시도가 결함을 냈고, 그 결함을 막고 다시 시작한다

**1차 M-2026-005(아키타입 B `academic-paper`)는 완주하지 못했다.** 경과: stage 4 에서
codex 한도 소진(429) → 로컬 Ollama 로 전환해 stage 4 통과 → stage 5 가 **압축 퇴화 분기**로
정지, 창을 131072 로 올려 해소 → stage 5·6·7 통과 → **그런데 그 산출물이 날조였다.**

`docs/11 §7 ⑧~⑧-d` 가 전말이다. 요약:
- stage 5 분석 **11편 중 8편이 원문 미독**(`raw/` 에 35KB~384KB 원문이 다 있었다).
- 그 stage 의 객관 게이트는 `raw/sources.yaml` **메타데이터만** 읽어 산출물을 안 봤다.
- LLM 검증자는 11건 중 5건만 대조하고 `VERDICT: PASS`.
- 창을 262144 로 올려 재작업을 걸었더니 워커가 **작업 보고 자체를 날조**했다
  (디스크 무변경인데 "원문을 읽고 파일을 생성했다"고 완료 선언).
- ⚠️ **모델이 못 한다는 뜻이 아니다** — 정상 분석 3편도 같은 모델이 만들었다.
  일관성 문제이고, 무너지는 지점은 **한 세션에 여러 항목을 몰아넣었을 때**다.

**→ Sam 지시(2026-08-05 (3)): 전 모델을 `codex`/`gpt-5.5` 로 되돌리고, 한도 리셋 뒤
처음부터 다시 테스트한다.** M-2026-005 는 결함 증거로 보존하고 재개하지 않는다.

**캠페인 순서(변경됨)**: **`code-docs`(I) 1번** — 객관 게이트가 우리 저장소 AST 와 대조해
날조로는 통과할 수 없다 → `policy-brief`(G) → `lecture-course`(J) →
`systematic-review`(B′) → `lit-monitor`(E) → `patent-spec`(F).
Tier 3·4(비용·외부 실행·저장소 수정 — K·M·O·P)는 **Sam 재확인**.

**테스트 중 게이트 승인은 Claude 가 직접 한다**(Sam 위임 2026-08-05).
⚠️ **승인 사유는 다음 워커가 읽는다** — 운영 메모는 `[운영 메모 · 산출물 지시 아님]` 접두.
⚠️ **Slack 승인 루프가 살아 있다.** 게이트가 `#approvals` 에 자동 게시되고 Sam 의 `승인` 이
감지되면 즉시 unblock 된다 — 작업 중 원치 않는 진행을 막으려면 카드를 **`schedule`** 로
park 하라(`block` 2회는 `promoted` 로 되돌아온다 · `docs/14 §6.5 ①·⑤`).

### 카드를 세우는 방법 (실측 3종 · `docs/14 §6.5 ⑤`)
| 수단 | 결과 |
|---|---|
| `link <상류> <카드>` | ❌ 사후 link 는 `ready` 를 되돌리지 않는다 |
| `block` 2회째 | ❌ `block_loop_detected` → **`promoted`**(도로 실행됨) |
| **`schedule <tid> "<사유>"`** | ✅ + 게이트키퍼가 `#approvals` 에 다시 안 올린다 |

⚠️ 어느 수단이든 **`dispatch --dry-run --json` 으로 `spawned` 가 비었는지 확인**하라.
상태 표시와 디스패치 가능성은 별개다.

---

## ✅ 완료 — harness 스킬 → 템플릿 변환 20/20 (`docs/13`)

**변환은 2026-08-05 에 20/20 으로 끝났다.** [`docs/13`](docs/13_skill_to_template_conversion.md) 은 이제 **함정 사전(§5)·매핑 사전(§3)** 으로 쓴다 — 새 아키타입을 만들거나 게이트를 고칠 때 먼저 읽어라. **다음 단계는 실미션**(Sam 이 아키타입 순서를 정한다).

| | 상태 |
|---|---|
| 변환 | **20/20 ✅ 완료** — A `trend-report`(**proven**) · B `academic-paper` · B' `systematic-review`(PRISMA) · D `webapp-build` · E `lit-monitor`(주기 실행 — 미션 간 지속 상태 `monitors/`) · F `patent-spec`(고지 강제) · G `policy-brief`(4포맷 동시 산출 + 3게이트) · H `legal-draft`(계약서·의견서·자문서·약관 + **개인정보 차단**) · I `code-docs`(코드베이스 문서화 — **AST 대조 검증**) · J `lecture-course`(강의 자료 — LO·Bloom 사슬) · K `code-migration`(마이그레이션 — **실제 코드 변경·git 대조**) · L `security-audit`(보안 감사 — **공개 범위 분리**) · M `agent-eval`(RAG/Agentic 시스템 구축·평가 — **평가셋·통계·재현성 3중 검증**, 산출물이 아키타입 B 의 입력) · N `dataset-release`(데이터셋 큐레이션·배포 — **개인정보·라이선스·공개범위 3중 강제**) · O `repro-package`(재현 패키지 — **실행 증거 요구·미검증 경로 공시 강제**) · P `sim-experiment`(DOE 파라미터 스윕 — **해시 재계산·입력 드리프트·민감도 불변식**) · Q `research-proposal`(연구비 제안서 — **추적성 사슬·예산 회계·자격 요건**, 기본 비공개) · R `reviewer-response`(리뷰어 응답서 — **원문 대조·원고 실변경 대조**, 기본 비공개) · S `outreach-content`(성과 발신 — **수치↔claim 값 대조·공개 근거 강제**) · T `conference-slides`(학회 발표 슬라이드 — **발표 분량 양방향·번들 미치환 검출·재사용 4종**). **A 외 전부 `draft`** |
| **다음 단계** | 변환 끝. **실미션을 하나씩**(Sam 이 순서를 정한다) · 그 전에 Slack 도달성 확인 |
| profile | **11종** — 기존 8 + `architect`·`developer`·`tester`(아키타입 D 도입 시 신설) |
| 객관 게이트 | **63종** `scripts/gates/` — **analysis_substance**(신규 · 산출물 실체성)·recency·source_balance·doc_consistency·test_run·prisma_counts·prisma_checklist·seen_dedup·digest_shape·claim_consistency·patent_format·evidence_grade·stakeholder_coverage·format_consistency·clause_completeness·law_citation·legal_safety·symbol_truth·api_coverage·doc_links·objective_coverage·bloom_distribution·course_consistency·content_accessibility·atomic_commit·test_pass_rate·behavior_diff·owasp_coverage·cve_remediation·finding_completeness·secret_redaction·eval_set_quality·stat_significance·repro_determinism·run_completeness·pii_presence·license_compat·schema_conformance·datasheet_completeness·result_tolerance·env_consistency·install_evidence·reproduce_doc·bit_exact·solver_pin·doe_completeness·analysis_integrity·proposal_format·budget_integrity·call_alignment·proposal_traceability·comment_fidelity·comment_coverage·change_consistency·response_quality·claim_provenance·channel_format·outreach_tone·release_readiness·**slide_budget·deck_format·diagram_integrity** |
| 산출 도구 | 4종 `scripts/tools/` — bib_export·monitor_state·relevance_score·budget_build |
| 운영 도구 | **`scripts/preflight_gates.py`**(빈 입력 반려 확인) · **`scripts/lint_gate_drafts.py`**(하네스↔템플릿 draft 정합) · `scripts/match_template.py`(미션→템플릿 3-way 매처 · `--rebuild` 로 manifest 생성) · `scripts/usage_report.py`(착수 전 점검 · **LLM 미호출** · 백엔드별 판정 + **서버 실효 설정·창 대조**) · **`scripts/set_backend.py`**(백엔드 전환 + **`--host-setup`** 호스트 서버 설정 · `docs/14`) · **`scripts/probe_protocol.py`**(도구 프로토콜 준수도 — 모델 선정 근거) · **`scripts/probe_parallel.py`**(동시 요청이 실제로 병렬인지 — 2026-08-06 신규) |
| 검증 | `python3 scripts/lint_template.py --all`(20/20) · 테스트 **355종**(35 템플릿·보드 + 34 게이트키퍼 + 214 게이트 + 8 매처 + 12 사용량 + 30 백엔드 + 22 기타) · **E2E 하네스 `scripts/tests/fixtures/run_all.py`(14종 510케이스)** |

**Sam 지시:** 실미션은 **전체 변환을 마친 뒤 하나씩** 돌린다(변환 중에는 dry-run만).

**게이트를 고쳤으면 E2E 하네스를 다시 돌려라** — `docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'`. 단위 테스트만 통과하는 수정은 판정 경로 전체를 검증하지 않는다(`scripts/tests/fixtures/README.md`).

**변환의 교훈(§5 요약):** 이식은 복사가 아니다. **20건 변환에서 20건 모두 결함이 나왔다** — 게이트 겹침(불변식 우회)·검증자 부재·느슨한 체크리스트·"동작하는 척"하는 게이트(한국어 정규식 붕괴)·**docstring은 검사한다는데 코드는 안 하는 게이트**·병렬 산출물 부재 미검출 등. **이식한 게이트는 반드시 일부러 깨뜨린 픽스처로 FAIL을 확인하라.** PASS만 보면 아무것도 측정하지 않는 게이트를 발견할 수 없다. **반대 방향도 확인하라** — legalforge 게이트 2종은 **어떤 입력에도 FAIL**하는 상태였다(정상 픽스처로 PASS 확인 필수). 또한 **이식 전에 우리가 이미 가진 게이트와 겹치는지 보라** — policyforge 하드게이트 3종 중 1종은 `source_balance`+`recency_check`와 같은 일이라 policy 블록으로 흡수했다.

**⚠️ 보안 미결(변함없음)**: 진단 중 `SLACK_BOT_TOKEN` 값이 세션 로그에 노출됨 → **재발급(rotate) 권장**(Slack 앱 Regenerate → `.env` 갱신 → `docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper`).

**세션 상태(2026-08-06 · 로컬 백엔드 재전환 · 호스트 서버 튜닝 · M-2026-006 진행 중):**
커밋 `4e593c0`(호스트 튜닝)·`bab2ac3`(전환·미션 착수)+.
**컨테이너 기동 · 백엔드 `ollama`/`gemma4-26b-256k` 11종 · M-2026-006 실행 중.**

2026-08-06 이 만든 것:
| 신규 | 무엇 |
|---|---|
| **`scripts/probe_parallel.py`** | 동시 요청이 **실제로 병렬인지** 측정. 판정을 순수 함수로 분리해 서버 없이 검사한다 |
| **`set_backend.py --host-setup`** + `HOST_ENV`/`HOST_ENV_OMITTED` | 호스트 서버 설정을 **한 곳에** 선언 — 선언·적용·검사가 같은 표를 본다. **넣으면 안 되는 것**(`OLLAMA_CONTEXT_LENGTH`)도 이유와 함께 선언 |
| **`usage_report.py` 서버 실효 설정 대조** | 서버 기동 배너 + `/api/ps` 창을 착수 전에 대조(**WARN 전용** — 느려지는 것과 못 도는 것은 다르다) |
| `docs/14 §5.1·§5.2·§5.3` | 걸어 놓은 것 ≠ 반영된 것 · 병렬화 실측 · **외부 가이드 대조표** |

2026-08-06 이 측정으로 확인한 것:
- ⚠️⚠️ **`docs/14 §5` 가 지시한 설정이 어떤 미션에서도 실효된 적이 없었다.** Ollama 프로세스가
  **53일째**(2026-06-13 기동) 돌고 있었고 `launchctl setenv` 는 이후 기동 프로세스에만 붙는다.
  이 저장소가 이미 아는 규율(**"파일이 아니라 서버가 보고하는 값을 봐라"**)을 환경변수에는
  적용하지 않고 있었다.
- ⚠️ **스테이지 내 팬아웃이 로컬에서 직렬로 돌고 있었다.** `NUM_PARALLEL` 미설정 → 합산
  처리량 73.1 < 단일 86.7 tok/s(**이득이 음수**). 설정 후 103.1 tok/s(**+26%**) · 메모리 +1.4%.
- **판정 함수를 한 번 틀렸고 측정이 그것을 반증했다** — 총 벽시계 비율로는 완전한 병렬을
  "부분병렬"로 읽는다(GPU 는 병렬이어도 요청당 느려진다). 종료 시각 분산 + 처리량 이득으로 교체.
- **`devstral-small-2:24b` 기각** — 외부 가이드의 코딩 1순위. 벽시계는 더 빠른데(44 vs 52초)
  `must_finish` 가 3회·5회 모두 **80%** 다. 카드에 이유 없이 `protocol violation` 으로만 남는다.

2026-08-05 (3) 이 만든 것:
| 신규 | 무엇 |
|---|---|
| `scripts/gates/analysis_substance.py` | 산출물 실체성 게이트(게이트 **63종**). 자가선언 탐지 + 개수 항등 + 분량 상하한 + **위치 지정 인용**(가장 잘 드는 검사) |
| `scripts/preflight_gates.py` | 빈 미션에 게이트를 돌려 전부 반려하는지. A~F 하네스 부재의 대체. **20/20 누출 없음** |
| `scripts/lint_gate_drafts.py` | 하네스 per-gate draft ↔ 템플릿 stage draft 대조. **FAIL 8·WARN 5 발견** |
| `gate_keeper.artifact_inspection()` | 승인 요청문에 산출물 실측치(파일 수·크기·의심 문구) |
| **미션별 Kanban 보드** | `instantiate_template --board` + `gate_keeper` 다중 보드(`active_boards()`) |

측정으로 확인한 것:
- **창을 2배로 올려도 메모리는 +0.8%**(`gemma4:26b` 17.50→17.64GB). `docs/14 §3.1` 의
  "창 하나로 3.7배"는 `llama3.1:8b` 숫자이고 **모델 계열을 건너뛰지 않는다.**
- **이중 게이트가 실전에서 완주**: LLM 검증자 PASS → 객관 게이트 FAIL → 게이트키퍼가
  리비전 카드 자동 생성 + downstream 보류.
- **정지된 컨테이너의 claim lock 이 카드를 영구 교착**시킨다(`reclaim` 으로 해소).

⚠️ Slack 은 이 세션 중 **복구**됐다(`auth.test` 200). 승인 루프가 살아 있다.

**새 세션 시작 시(3분 점검):**

⚠️ **컨테이너는 기동 상태로 넘겼다.** M-2026-006 이 진행 중이다.
⚠️ **호스트 Ollama 를 재시작했다면 `--host-setup` 을 다시 걸어라** — `launchctl setenv` 는
로그인 세션 단위라 **재부팅하면 사라진다.** `usage_report.py` 가 잡아 준다.

```bash
git log --oneline -6                     # HEAD: 로컬 전환 + M-2026-006 착수
python3 scripts/set_backend.py --show    # ★ ollama · gemma4-26b-256k · 11종 (exit 1 이면 불일치)
python3 scripts/usage_report.py          # ★ exit 0 + '서버 실효 설정 5종 일치'
docker compose ps                        # hermes-solomon · hermes-gatekeeper Up
docker exec hermes-solomon hermes kanban --board m-2026-006 list                                     # 10단계 진행상황
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_template.py --all'        # 20/20
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/preflight_gates.py --all'      # 누출 0
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/lint_gate_drafts.py'           # 미해결 FAIL 8
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'     # 14/14
python3 scripts/tests/test_set_backend.py && python3 scripts/tests/test_usage_report.py              # 30 · 27
curl -s -o /dev/null -w '%{http_code}\n' --max-time 8 https://slack.com/api/auth.test               # 200 이면 정상
```

**→ M-2026-006(`code-docs`)이 진행 중이다**(위 '▶ 이어서 할 일' 참조).
⚠️ **Slack 은 2026-08-06 기준 다시 도달 불가**(`curl 000`). 승인 게이트 자동 게시가 안 되므로
**게이트 승인은 Claude 가 직접 한다**(Sam 위임 2026-08-05).

**§2④ 를 먼저 하라(이번 세션의 가장 큰 교훈):** 게이트를 새로 만들기 전에 `ls scripts/gates/`(63종)로 **이미 가진 것과 하는 일이 겹치는지** 보라. 재사용은 *하는 일*이 같을 때지 *이름*이 비슷할 때가 아니다(O 는 2종 재사용 · P 는 이름이 비슷한 `run_completeness` 를 일부러 재사용하지 않았다). **Q 에서 `legal_safety` 에 연 `publication_policy` 축이 바로 다음 변환(R)에서 그대로 쓰였다 — 쌍둥이 게이트를 만드는 대신 축을 여는 판단의 실증이다.**

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
