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

1. Hermes 설치 방식 확인(공식 문서 기준). 로컬 설치형은 보통:
   ```bash
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   ```
   그러나 우리는 **컨테이너 격리**를 원하므로, 다음 중 공식이 권장하는 방식을 택한다:
   - (권장 확인 대상) 공식 Docker 이미지/Compose가 있으면 그것을 사용
   - 없으면, `python:3.11-slim` 기반 컨테이너 안에서 설치 스크립트 실행하는 커스텀 `Dockerfile` 작성

2. **볼륨 매핑 원칙** (컨테이너 재생성해도 유지되어야 하는 것):
   | 유지(볼륨) | 격리(컨테이너 내부) |
   |-----------|---------------------|
   | `~/.hermes/` (profiles·memory·sessions·skills·cron·**kanban.db**) | 코드 실행 샌드박스 |
   | llm-wiki repo 체크아웃 | 브라우저 프로세스 |
   | Slack/API 토큰(`.env`) | 임시 캐시 |

3. 예시 뼈대(`docker-compose.yml` 초안 — 실제 이미지/명령은 공식 문서로 확정):
   ```yaml
   services:
     hermes:
       build: .              # 또는 image: <공식 이미지>
       env_file: .env        # SLACK_*, ANTHROPIC_API_KEY 등
       volumes:
         - ./hermes-home:/root/.hermes      # 영속: profiles·memory·kanban.db
         - /Users/admin/DEVELOP/Y2026/GITHUB/01-JXCROSS/my-hermes-company-llm-wiki-2026:/work/llm-wiki   # 지식 repo(실제 경로)
       restart: unless-stopped
   ```

**검증**: 컨테이너 안에서 `hermes --version` (또는 상응 명령)이 동작. 컨테이너 재시작 후에도 `~/.hermes` 유지.

---

## 단계 0-C. Solomon profile 생성
1. 프로필 생성(예):
   ```bash
   hermes profile create solomon
   ```
2. **`SOUL.md`** 작성(정체성·운영 원칙). 핵심 포함 사항:
   - "너는 AI-Native Company의 대표 AI **Solomon**이다. 사용자는 **Sam**이다."
   - **브레인스토밍 우선**: 미션 실행 전 Sam과 협의해 미션 스펙(목표·완료조건·제약)을 합의한다.
   - **직접 구현하지 않는다**: 조사·집필·코딩은 전문 profile에 위임하고, 너는 기획·오케스트레이션·게이트 검증·보고를 한다.
   - **작성자 ≠ 검증자** 원칙 준수.
   - **승인 게이트**: 개인정보·보안·비용·외부공개·파괴적작업은 Sam 승인. 승인 요청은 행동·이유·영향·위험·복구를 함께 제시.
   - 모든 중요한 주장에 출처. 재사용 지식은 LLM Wiki·Skill로 축적.
3. **`USER.md`** 작성: "Sam, 컴퓨터공학 박사, 한국어 소통 선호, 관심=AI/LLM 동향·논문·웹 시뮬레이션·웹개발."
4. **`config.yaml`**: 사용할 상용 모델·비용 관련 옵션 설정(모델은 후속 확정).

**검증**: `hermes -p solomon chat` (또는 상응)으로 로컬에서 Solomon과 대화 가능.

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
