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
- **프로필 11종**: default(Solomon)·scout·reader·writer·synthesizer·curator·**architect·developer**=`gpt-5.6-terra`, **fact-checker·reviewer·tester=`gpt-5.6-sol`**(검증자). 소스=`profiles-src/`. architect·developer·tester는 2026-08-04 아키타입 D 도입으로 신설(`docs/13 §7`).
- **인프라 정비 완료**: `HERMES_WRITE_SAFE_ROOT=/opt/data:/work/company:/work/llm-wiki`(워커 직접쓰기, 복사 불필요) · **Tavily 웹검색**(키는 repo `.env`의 `TAVILY_API_KEY`, 전 프로필 os.environ 노출 필수) · **`WIKI_PATH=/work/llm-wiki`**(Curator의 karpathy-llm-wiki 스킬).
- **미션 산출물**: 보고서→`reports/M-2026-NNN/`, 지식→llm-wiki repo(raw/entities/concepts/reflections, 재사용률 추적). Kanban 게이트: 미션=부모·단계=자식, `link`=순차, `block --kind needs_input`=Sam 게이트, `--workspace dir:/work/company/reports/<mission>`.
- **반려 게이트 자동화(게이트키퍼)**: 사이드카 컨테이너 **`hermes-gatekeeper`**(`docker-compose.yml`, `scripts/gate_keeper.py`). 검증 task(6·9) 판정이 `VERDICT: FAIL`이면 산출물 재작업 루프(리비전→재검증) 자동 생성 + downstream(7·10) PASS 전까지 보류. **활성 게이트만** 처리(완료 미션 스킵, 재시작 안전). **Sam 승인 게이트도 자동화**(`approval_poll`, Web API): 활성 Sam-게이트를 `#approvals`에 자동 게시 + Sam의 `승인`/`승인 <task_id>` 감지→`kanban unblock`(SLACK_ALLOWED_USERS만). 상세 `docs/10 §4.4`·`docs/11 §7`.
- 웹 대시보드 `http://localhost:9129`, Slack `#ceo-office`/`#approvals`/`#mission-log`. 기동 `docker compose up -d`(게이트키퍼 포함) · `.env`/compose 변경 시 `--force-recreate`.
- **미해결 이슈**: ~~Slack 도달 불가(2026-08-04 오전 재발)~~ → **[해소 2026-08-04 오후]** 네트워크 복구·게이트키퍼 폴링 정상. ~~Slack 아웃바운드 실패~~ → **[해소 2026-08-03]** 근본원인은 **네트워크가 slack.com 도달 불가**(force-recreate 오진). 와이파이 변경 후 복구·전송 검증 완료. Slack 이상 시 **1순위 진단=`curl https://slack.com/api/auth.test` 도달성**(status의 `configured`는 토큰존재만 의미). 진단 runbook·홈채널ID(`C0BM8FK3RTM`)는 `docs/10 §4.3`. · 반려 게이트 미강제(9→10 무조건 링크). Scoping은 Solomon이 자율분해하므로 수동 카드와 충돌 주의.

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
4. ~~**Slack 네트워크 도달 불가**~~ **[해소 2026-08-04 오후]** 세션 초 `slack.com` HTTPS 타임아웃(google·github은 정상 = 네트워크성)이 있었으나 복구됨. 검증: 호스트 `auth.test` 200 · 컨테이너 Web API `ok=true` · **게이트키퍼 WARN 3시간 38분째 없음**(마지막 10:16, 확인 13:54). 진단 순서는 `docs/10 §4.3`.
5. **매처(C)** — 미션→템플릿 자동 선택(`match_template.py` + `manifest.json`). 템플릿이 6종이 돼 이제 의미가 생겼다. 설계는 `docs/12 §5`(3-way 판정: 높음/어중간=경고+신규구성 병행/낮음=골격에서 신규). ~~전용 린터(E)~~ [완료 — `scripts/lint_template.py`].
6. **성장 지표 대시보드** — 재작업률·wiki 재사용률·소요시간 누적. + **미션 진행상황 Slack 실시간 보고**(현재 통지는 게이트 이벤트·Deliver 시점만 — Sam이 "진행상황을 전혀 모르겠다"고 지적한 건).

---

## ‼️ 현재 진행 중 — harness 스킬 → 템플릿 변환 (`docs/13`)

**재개 지점은 [`docs/13 §6` 진행 대장](docs/13_skill_to_template_conversion.md)이다.** 새 세션은 거기서 다음 대상을 고르고 **§2 레시피 8단계**대로 변환한 뒤 **§6 대장 갱신 + 커밋**한다. 함정은 §5, agent→profile 매핑 사전은 §3.

| | 상태 |
|---|---|
| 변환 | **11/20** — A `trend-report`(**proven**) · B `academic-paper` · B' `systematic-review`(PRISMA) · D `webapp-build` · E `lit-monitor`(주기 실행 — 미션 간 지속 상태 `monitors/`) · F `patent-spec`(고지 강제) · G `policy-brief`(4포맷 동시 산출 + 3게이트) · H `legal-draft`(계약서·의견서·자문서·약관 + **개인정보 차단**) · I `code-docs`(코드베이스 문서화 — **AST 대조 검증**) · J `lecture-course`(강의 자료 — LO·Bloom 사슬) · K `code-migration`(마이그레이션 — **실제 코드 변경·git 대조**). **A 외 전부 `draft`** |
| **다음 변환 대상** | **secforge**(8-stage · agents 13 · 신규 profile 예상 있음 — 스캐너) |
| profile | **11종** — 기존 8 + `architect`·`developer`·`tester`(아키타입 D 도입 시 신설) |
| 객관 게이트 | **26종** `scripts/gates/` — recency·source_balance·doc_consistency·test_run·prisma_counts·prisma_checklist·seen_dedup·digest_shape·claim_consistency·patent_format·evidence_grade·stakeholder_coverage·format_consistency·clause_completeness·law_citation·legal_safety·symbol_truth·api_coverage·doc_links·objective_coverage·bloom_distribution·course_consistency·content_accessibility·atomic_commit·test_pass_rate·behavior_diff |
| 산출 도구 | 3종 `scripts/tools/` — bib_export·monitor_state·relevance_score |
| 검증 | `python3 scripts/lint_template.py --all` · 테스트 **146종**(29 템플릿 + 21 게이트키퍼 + 96 게이트) |

**Sam 지시:** 실미션은 **전체 변환을 마친 뒤 하나씩** 돌린다(변환 중에는 dry-run만).

**변환의 교훈(§5 요약):** 이식은 복사가 아니다. **11건 변환에서 11건 모두 결함이 나왔다** — 게이트 겹침(불변식 우회)·검증자 부재·느슨한 체크리스트·"동작하는 척"하는 게이트(한국어 정규식 붕괴)·**docstring은 검사한다는데 코드는 안 하는 게이트**·병렬 산출물 부재 미검출 등. **이식한 게이트는 반드시 일부러 깨뜨린 픽스처로 FAIL을 확인하라.** PASS만 보면 아무것도 측정하지 않는 게이트를 발견할 수 없다. **반대 방향도 확인하라** — legalforge 게이트 2종은 **어떤 입력에도 FAIL**하는 상태였다(정상 픽스처로 PASS 확인 필수). 또한 **이식 전에 우리가 이미 가진 게이트와 겹치는지 보라** — policyforge 하드게이트 3종 중 1종은 `source_balance`+`recency_check`와 같은 일이라 policy 블록으로 흡수했다.

**⚠️ 보안 미결(변함없음)**: 진단 중 `SLACK_BOT_TOKEN` 값이 세션 로그에 노출됨 → **재발급(rotate) 권장**(Slack 앱 Regenerate → `.env` 갱신 → `docker compose up -d --force-recreate hermes-solomon hermes-gatekeeper`).

**새 세션 시작 시:** `git log --oneline -6`(HEAD 근처: patentforge→policyforge→legalforge→docforge→lectureforge→migrateforge)과 `docker compose ps`(2개 Up)·`python3 scripts/lint_template.py --all` 로 상태 확인 → **`docs/13 §6` 대장**을 읽고 → 다음 대상(secforge)부터 §2 레시피대로 진행.

**⚠️ 아키타입 K(`code-migration`)는 미션 밖의 실제 코드를 바꾸고 커밋한다.** 대상 저장소는 `HERMES_WRITE_SAFE_ROOT` 안이어야 하고, **`/work/company` 자신을 대상으로 삼으면 안 된다**(파이프라인이 자기 코드를 고치게 된다). 코드 변경 개시 직전에 Sam 승인 게이트가 있다.

**⚠️ 이 저장소는 PUBLIC 이다.** Deliver 단계가 `reports/` 를 커밋·push 하므로 **미션 산출물에 개인정보 평문이 남으면 그대로 공개된다.** 아키타입 H(법률 문서)는 초안을 플레이스홀더로 쓰고 `legal_safety` 게이트가 이를 강제한다. 실제 개인정보는 `_personal/`(gitignore)에만 둔다.
