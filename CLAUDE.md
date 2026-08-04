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
- **프로필 8종**: default(Solomon)·scout·reader·writer·synthesizer·curator=`gpt-5.6-terra`, **fact-checker·reviewer=`gpt-5.6-sol`**(검증자). 소스=`profiles-src/`.
- **인프라 정비 완료**: `HERMES_WRITE_SAFE_ROOT=/opt/data:/work/company:/work/llm-wiki`(워커 직접쓰기, 복사 불필요) · **Tavily 웹검색**(키는 repo `.env`의 `TAVILY_API_KEY`, 전 프로필 os.environ 노출 필수) · **`WIKI_PATH=/work/llm-wiki`**(Curator의 karpathy-llm-wiki 스킬).
- **미션 산출물**: 보고서→`reports/M-2026-NNN/`, 지식→llm-wiki repo(raw/entities/concepts/reflections, 재사용률 추적). Kanban 게이트: 미션=부모·단계=자식, `link`=순차, `block --kind needs_input`=Sam 게이트, `--workspace dir:/work/company/reports/<mission>`.
- **반려 게이트 자동화(게이트키퍼)**: 사이드카 컨테이너 **`hermes-gatekeeper`**(`docker-compose.yml`, `scripts/gate_keeper.py`). 검증 task(6·9) 판정이 `VERDICT: FAIL`이면 산출물 재작업 루프(리비전→재검증) 자동 생성 + downstream(7·10) PASS 전까지 보류. **활성 게이트만** 처리(완료 미션 스킵, 재시작 안전). **Sam 승인 게이트도 자동화**(`approval_poll`, Web API): 활성 Sam-게이트를 `#approvals`에 자동 게시 + Sam의 `승인`/`승인 <task_id>` 감지→`kanban unblock`(SLACK_ALLOWED_USERS만). 상세 `docs/10 §4.4`·`docs/11 §7`.
- 웹 대시보드 `http://localhost:9129`, Slack `#ceo-office`/`#approvals`/`#mission-log`. 기동 `docker compose up -d`(게이트키퍼 포함) · `.env`/compose 변경 시 `--force-recreate`.
- **미해결 이슈**: ~~Slack 아웃바운드 실패~~ → **[해소 2026-08-03]** 근본원인은 **네트워크가 slack.com 도달 불가**(force-recreate 오진). 와이파이 변경 후 복구·전송 검증 완료. Slack 이상 시 **1순위 진단=`curl https://slack.com/api/auth.test` 도달성**(status의 `configured`는 토큰존재만 의미). 진단 runbook·홈채널ID(`C0BM8FK3RTM`)는 `docs/10 §4.3`. · 반려 게이트 미강제(9→10 무조건 링크). Scoping은 Solomon이 자율분해하므로 수동 카드와 충돌 주의.

## ‼️ 로컬 전용 (git에 없음 — PC마다 재구성 필요)
- **`.env`**: Slack 토큰 등 시크릿. Sam이 안전하게 보관 후 새 PC에서 재작성(`cp .env.example .env`).
- **`hermes-home/`**: `auth.json`·`kanban.db`·`sessions` 등. 새 PC에선 `hermes setup`으로 **OAuth 재로그인**.
- **llm-wiki repo**: 형제 폴더에 clone — `github.com/jxcross/my-hermes-company-llm-wiki-2026`.
- **Claude Code 프로젝트 메모리**: 로컬. 이 CLAUDE.md가 대체 컨텍스트 역할.

## 새 PC 부트스트랩 (순서)
`docs/05_stage0_setup_guide.md` 참조. 요약: repo 2개 clone → `docker compose pull` → `cp .env.example .env`(SLACK·`TAVILY_API_KEY` 값 채움) → `hermes setup`(OAuth) → `solomon-profile/`의 SOUL·USER를 `hermes-home/`에 복사 → **전문 프로필 7종 재생성**(`profiles-src/<name>/`의 SOUL·config를 `hermes profile create` 후 `hermes-home/profiles/<name>/`에 복사: scout·reader·writer·synthesizer·curator·fact-checker·reviewer) → `docker compose up -d`(hermes-solomon + **hermes-gatekeeper 사이드카** 동시 기동) → 대시보드/Slack/`hermes profile list`(모델 terra/sol)·`docker compose ps`(게이트키퍼 Up) 확인.

## 다음 할 일
**완료(2026-08-03):** ✅ Slack 재연결(`docs/10 §4.3`) · ✅ 반려 게이트 자동화=`hermes-gatekeeper` 사이드카(`docs/10 §4.4`) · ✅ **템플릿 기반 미션 시스템 Pilot(P0–P4)**: 선언적 템플릿→Kanban 번역기 + 이중 게이트(객관 Python + LLM 검증자) + 실미션 **M-2026-003 완주**(11/11, 커밋 b7ec055). 상세 `docs/11 §7`. 신규 미션 실행: `python3 scripts/instantiate_template.py trend-report <MID> --topic "..."`(협상 미리보기 `--dry-run --render mermaid`).

**← 현 최우선: Phase 2** (`docs/11 §7`의 미해결·개선점):
1. ~~**병렬화**~~ **[완료·라이브검증 2026-08-04]** subagent 스테이지 내 팬아웃 구현(형제 task 아님 — Hermes는 동일 profile task 순차 실행). 번역기가 템플릿 `parallel` 블록을 읽어 stage 3·5·8 task **본문에 delegation 배치 위임 프로토콜 주입**(스테이지 1 task 유지→gate_keeper 무손상). **라이브 파일럿 M-2026-004 완주**(11/11, 보고서 커밋 b585526): stage3 병렬 subagent 디스패치→worker shard 5·병합, stage5 분석 12·stage8 집필 7 shard. 파일럿이 **gate_keeper fail-open 결함 발견·수정**(자식 transient 조회실패 None을 종단 오인→downstream 고아화; `classify_children`+defer, 테스트 4종, 커밋 3d25a54). 상세 `docs/11 §5·§3.B·§7`. 신규 미션: `python3 scripts/instantiate_template.py trend-report <MID> --topic "..."`.
2. ~~**컨테이너 GITHUB_TOKEN**~~ **[해소 2026-08-04]** `.env`의 `GITHUB_TOKEN`(Fine-grained PAT, Contents:write) + docker-compose가 `GIT_CONFIG_*`로 github.com credential helper 주입(토큰 파일 미저장, 신원 보존). 컨테이너 `git push` 인증 검증됨. ~~**Deliver Slack 실패**~~ **[해소]** Deliver 게시를 `hermes send`(Web API)로 고정(템플릿 stage11). **[신규 잔여] Slack Socket Mode 인바운드 flapping**(2026-08-02~, 아웃바운드는 정상) 조사 필요.
3. ~~**Slack 승인→Kanban unblock 배선**~~ · ~~**pre-blocked Sam 게이트 알림**~~ **[해소 2026-08-04]** gate_keeper `approval_poll`(Web API 폴링, Socket Mode 비의존): #4 활성 Sam-게이트를 `#approvals`에 **판단 내용 포함**(주제·계획·정책 또는 보고서요약·검증·공개대상) 자동 게시 + #3 `SLACK_ALLOWED_USERS`(Sam)의 `승인`(단일)/`승인 <task_id>`(명시) 감지→`kanban unblock`. 단위테스트 10 + 라이브 E2E 검증. **[잔여] Socket Mode 인바운드 flapping**(네트워크성; recreate 후 안정, 승인흐름은 비의존) 모니터.
4-b. **← 현재 진행 중: harness 스킬 → 템플릿 변환** (`docs/13`). 미션 파이프라인 협상 설계는 **`docs/12`**(현행 구조엔 협상 자리가 없음 → Phase 0으로 앞당김·논의 단위를 단계→의도로). 변환은 **`docs/13`이 절차서 겸 진행 대장** — **새 세션은 `docs/13 §6`에서 다음 대상을 고르고 §2 레시피대로** 진행. 현재 **3/20** — A `trend-report.yaml`(proven) · B `academic-paper.yaml`(draft, 실행가능) · **D `webapp-build.yaml`(draft, 실행 불가 — 신규 profile 3종 `architect`·`developer`·`tester` Sam 승인 대기, `docs/13 §7`)**. 다음 변환 대상 = **reviewforge**.
5. **매처(C)·전용 린터(E)** — 미션→템플릿 자동 선택, 불변식 린터 분리. ~~**B 아키타입**~~ [2026-08-04 변환 완료] · **D 아키타입**(웹개발)은 docs/13 대장 #3.
6. **성장 지표 대시보드** — 재작업률·wiki 재사용률·소요시간 누적.

**[2026-08-04 세션 완료]** Phase 2 대거 진전: 병렬화(1)·컨테이너 git 자격+Deliver Slack(2)·Slack 승인 자동화(3·4) **모두 해소**. 라이브 파일럿 M-2026-004 11/11 완주. gate_keeper fail-open 결함 발견·수정. 남은 우선순위 = **위 5(매처·린터·B/D 아키타입)·6(지표 대시보드)** + Socket Mode 인바운드 flapping 모니터.
**⚠️ 보안 미결**: 진단 중 `SLACK_BOT_TOKEN` 값이 세션 로그에 노출됨 → **재발급(rotate) 권장**(Slack 앱 Regenerate → `.env` 갱신 → `docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper`).

새 세션 시작 시: 최신 `git log`(현 HEAD 근처: 병렬화→fail-open수정→git자격→승인자동화→gate_summary)와 `docker compose ps`(hermes-solomon + **hermes-gatekeeper** 2개 Up)·`hermes profile list`로 상태 확인 → **`docs/11 §7`(Pilot 결과·미해결)** 읽고 → 위 Phase 2 우선순위 중 Sam이 지정한 것부터 계획 제시.
