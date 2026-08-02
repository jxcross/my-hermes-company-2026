# 05. Stage 0 구축 가이드 (Sam 실행용)

> 작성일: 2026-08-02 · 대상 실행자: **Sam** · 목표: 로컬에서 Solomon(대표 AI)이 Slack으로 대화하고 Kanban을 쓸 수 있는 기반 구축
> 관련: [`02_company_design.md`](./02_company_design.md) · [`hermes_agent_조사.md`](./hermes_agent_조사.md)

> ⚠️ **중요**: Hermes의 세부 명령·옵션·Kanban 설정은 버전에 따라 다를 수 있다.
> 각 단계에서 **공식 문서( https://hermes-agent.nousresearch.com/ )를 함께 확인**하고, 실제 출력으로 검증하며 진행할 것.
> 막히는 지점은 Claude(나)에게 출력/에러를 보여주면 단계별로 함께 해결한다.

---

## 준비물 체크리스트 (시작 전)
- [ ] 로컬 머신(macOS/Linux; Docker 구동 가능)
- [ ] **Docker Desktop / Docker Engine** 설치
- [ ] **Git** 설치, GitHub 계정
- [ ] **Slack 워크스페이스**(관리자 권한 — 앱 생성용)
- [ ] **상용 LLM API 키**: Anthropic 또는 OpenAI (또는 OpenRouter 단일 키)
- [ ] 비용 상한 정책 결정(월 한도 개략치)

---

## 단계 0-A. Git 저장소 2개 준비 ✅ (완료됨)
1. 회사 저장소: `my-hermes-company-2026` (현재 repo).
2. **별도 llm-wiki 저장소** — **이미 생성·클론 완료**:
   - 원격: `https://github.com/jxcross/my-hermes-company-llm-wiki-2026.git`
   - 로컬: `/Users/admin/DEVELOP/Y2026/GITHUB/01-JXCROSS/my-hermes-company-llm-wiki-2026`
   - 구조: `raw/ · wiki/ · reflections/` + 초기 커밋 존재.
   → 이유: 지식 자산을 회사 코드와 **분리**해 독립적으로 버전관리·백업.

**검증**: 두 repo가 GitHub에 존재하고 clone 가능. (llm-wiki는 확인 완료)

---

## 단계 0-B. Docker에서 Hermes 구동 (로컬)
목표: Hermes를 컨테이너에서 실행하되, **영속 데이터는 볼륨으로 유지**한다.

> **방식 확정: 공식 Docker 이미지 `nousresearch/hermes-agent:latest`로 (a) 전체 컨테이너화.**
> 호스트 `~/.hermes`(다른 프로젝트 `ainc-hermes` 등)와 **완전 분리** — 데이터는 이 repo의 `./hermes-home`(컨테이너 `/opt/data`)에만 저장.
> 포트도 기존 스택(8642·9219 사용 중)과 충돌 없게 **8652/9129**로 격리.

이 repo에 **이미 구성 완료**된 파일:
- `docker-compose.yml` — `hermes-solomon` 서비스(이미지·포트·마운트·리소스 제한)
- `.env.example` — 키/토큰 템플릿 (→ `.env`로 복사해 채움, 커밋 금지)
- `hermes-home/` — 격리 데이터 홈(gitignore)

1. **환경변수 설정**:
   ```bash
   cp .env.example .env    # ANTHROPIC_API_KEY, SLACK_* 채우기(0-C·0-D 진행하며)
   ```
2. **이미지 받기**:
   ```bash
   docker compose pull      # 또는 docker pull nousresearch/hermes-agent:latest
   ```
3. **컨테이너 데이터 경로(마운트)**:
   | 컨테이너 경로 | 호스트(이 repo) | 용도 |
   |---------------|-----------------|------|
   | `/opt/data` | `./hermes-home` | Hermes 홈: profiles·memories·sessions·skills·cron·**kanban.db**·config·SOUL |
   | `/work/llm-wiki` | `../my-hermes-company-llm-wiki-2026` | LLM Wiki repo |
   | `/work/company` | `./` | 회사 repo(보고서 산출) |

**검증**: `docker compose run --rm hermes-solomon --help`(또는 `version`)이 동작. `~/.hermes`(다른 프로젝트)는 그대로.

---

## 단계 0-C. 초기 설정 + Solomon 정체성 배포
1. **초기 설정(대화형)** — 제공자·모델·키를 지정:
   ```bash
   docker compose run --rm hermes-solomon setup
   ```
   - 제공자/모델: **Anthropic Claude 권장**(예: `anthropic/claude-sonnet-4`). `ANTHROPIC_API_KEY`는 `.env`에서 읽힘.
2. **Solomon 정체성 배포** — repo의 버전관리 소스(`solomon-profile/`)를 데이터 홈에 복사:
   ```bash
   cp solomon-profile/SOUL.md hermes-home/SOUL.md
   mkdir -p hermes-home/memories && cp solomon-profile/USER.md hermes-home/memories/USER.md
   ```
   > 기본 프로필을 Solomon으로 쓰는 구성(단순). named 프로필 방식은 `solomon-profile/README.md` 참고.
3. **대화 확인(로컬)**:
   ```bash
   docker compose run --rm -it hermes-solomon
   ```

**검증**: 컨테이너 대화에서 Solomon이 "나는 Solomon(AI CEO), 사용자는 Sam" 정체성으로 응답.

---

## 단계 0-D. Slack 연결 (Socket Mode)
> Socket Mode라 공개 URL 불필요. Sam이 Slack 관리자 권한으로 수행.

1. **Slack 앱 생성**: https://api.slack.com/apps → *From an app manifest* (Hermes가 manifest 생성 명령을 제공하면 그것을 사용).
2. **권한(Bot Token Scopes)**: `chat:write`, `app_mentions:read`, `channels:history`, `groups:history`, `im:history`, `im:write`, `files:read`, `files:write`.
3. **이벤트 구독**: `message.im`, `message.channels`, `message.groups`, `app_mention`.
4. **Socket Mode 활성화** → **App-Level Token(`xapp-`)** 발급(스코프 `connections:write`).
5. 워크스페이스 설치 → **Bot Token(`xoxb-`)** 확보.
6. **채널 생성 및 봇 초대**: `#ceo-office`, `#approvals`, `#mission-log` → 각 채널에서 `/invite @Solomon`.
7. **토큰을 `.env`에 설정**:
   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   SLACK_ALLOWED_USERS=<Sam의 Slack member ID>
   SLACK_HOME_CHANNEL=<#mission-log 채널 ID>
   ANTHROPIC_API_KEY=...   # 또는 OPENAI_API_KEY / OPENROUTER_API_KEY
   ```
8. **응답 규칙 확인**: DM은 항상 응답, 채널은 `@Solomon` 멘션 시 응답.

**검증**: `#ceo-office`에서 `@Solomon 안녕`에 응답이 오면 성공.

---

## 단계 0-E. Kanban 활성화 + 웹 대시보드 (소규모 검증)
> Kanban은 비교적 신기능이므로 **소규모로 먼저 검증**. 게시판·실행상태 뷰의 근간이다([09](./09_mission_board_and_visibility.md)).

1. 공식 문서로 Kanban 활성화·디스패처 설정 확인(`kanban.dispatch_in_gateway` 등).
2. **웹 대시보드 접속**: Kanban 대시보드(상태 컬럼·profile 레인·카드 코멘트)를 브라우저에서 연다(포트/명령은 공식 문서 확인). → Sam의 "게시판".
3. 테스트: `hermes kanban create "테스트 미션"`(부모) → 자식 task 생성·profile 할당 → 상태 변경 시 대시보드/`#mission-log` 반영 확인.
4. 의존(task_links)·block/unblock 동작 확인(사람 승인 흐름 리허설).
5. `~/.hermes/kanban.db` 경로·읽기 접근 확인(후속 Control Plane 대비).

**검증**: 웹 대시보드에서 미션(부모)-단계(자식) 구조와 상태가 보이고, Slack 알림 + block→unblock 사람 개입이 작동.

---

## 단계 0-F. 최소 전문 profile 스캐폴딩 (Stage 1 준비)
Stage 1 착수 직전에, 미션 A용 profile 뼈대 생성: Scout·Reader·Fact-Checker·Synthesizer·Writer·Reviewer·Curator.
각 profile은 간단한 `SOUL.md`(역할 한정)와 필요한 도구 스코프만 부여. (상세는 Stage 1에서)

---

## 완료 기준 (Stage 0 Done)
- [ ] 두 Git repo(회사 / llm-wiki) 준비
- [ ] Docker 컨테이너에서 Hermes 구동 + 영속 볼륨 유지
- [ ] Solomon profile(SOUL/USER/config) 생성, 로컬 대화 확인
- [ ] Slack 3채널 연결, `@Solomon` 응답 확인
- [ ] Kanban 소규모 동작(알림·의존·block/unblock) 확인
- [ ] 상용 API 키·비용 상한 설정

> Stage 0가 끝나면 → **Stage 1(미션 A)**: Slack에서 Sam이 주제를 던지면 Solomon과 브레인스토밍 후
> [`04_mvp_research_trend_report_spec.md`](./04_mvp_research_trend_report_spec.md)의 11단계 파이프라인을 완주시킨다.

---

## 진행 방식
각 단계는 Sam이 수행하고, **출력/에러를 공유하면 Claude가 다음 단계·문제 해결을 함께** 진행한다.
확정 필요 값(모델 조합, 비용 상한 수치, MCP 툴 목록)은 진행 중 결정한다.
