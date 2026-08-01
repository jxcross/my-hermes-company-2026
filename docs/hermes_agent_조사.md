# Hermes Agent 조사 정리

> **조사 기준일:** 2026-08-01
> **대상:** Hermes Agent (NousResearch)
> **출처:** 공식 사이트 및 GitHub 저장소 문서 (하단 [출처](#출처) 참조)
> **관련 문서:** [`ai_native_company_개념.md`](./ai_native_company_개념.md) — 본 문서는 그 구상의 기반 기술 정리다.

> ⚠️ **주의:** 이 문서는 2026-08-01 시점에 공개 문서를 조사·정리한 것이다.
> 버전 번호, 메모리 문자 수 제한, 의존성 버전 등 **세부 수치는 빠르게 변한다.**
> 실제 설치·설정 전에는 반드시 [공식 문서](https://hermes-agent.nousresearch.com/)를 재확인할 것.

---

## 1. 개요

**한 줄 정의**
Hermes Agent는 NousResearch가 만든 **자체 개선형(self-improving) 오픈소스 AI 에이전트 플랫폼**이다.
경험에서 스스로 skill을 생성·개선하고, 지속적 메모리를 유지하며, 여러 메시징 플랫폼에서 동작한다.

**핵심 특징**
- 다중 메시징 플랫폼 연결 (Slack, Telegram, Discord, WhatsApp, Signal, Email, CLI 등)
- 경험 기반 자동 skill 생성·개선(폐쇄형 학습 루프)
- 세션 간 지속 메모리 및 사용자 모델링
- 자연어/cron 예약 작업
- subagent 위임을 통한 병렬 처리
- 다양한 실행 백엔드(local/Docker/SSH/원격 샌드박스)

| 항목 | 내용 |
|------|------|
| 개발 | NousResearch |
| 라이선스 | MIT (오픈소스) |
| 공식 사이트 | https://hermes-agent.nousresearch.com/ |
| 저장소 | https://github.com/nousresearch/hermes-agent |
| 설치 | 셸/PowerShell 원라인 설치 스크립트 |
| 런타임 | Python 3.11–3.13 (uv 기반 자동 설치) |

> 세부 버전/구독 플랜 등은 변동성이 크므로 본문에서는 사실 골격만 정리하고, 정확한 수치는 공식 문서 확인을 권장한다.

---

## 2. 핵심 아키텍처

```
진입점 (CLI / Gateway / 메시징 플랫폼)
        │
        ▼
   AIAgent 대화 루프
   (프롬프트 조립 · 모델 제공자 해석 · 도구 호출 반복)
        │
        ▼
   Session 저장소 (SQLite + FTS5 전문검색)
        │
        ├── Memory (지속 사실: 항상 컨텍스트에 주입)
        ├── Skills (절차 지식: 필요할 때만 로드)
        ├── Subagents (격리 위임 작업자)
        └── Tools 백엔드 (Terminal / Browser / Web / MCP)
        │
        ▼
   Gateway → 메시징 플랫폼 (Slack 등)
   Cron/Scheduler → 예약 작업 실행
```

### 주요 컴포넌트

| 컴포넌트 | 역할 |
|----------|------|
| **Agent Core** | 메인 대화 루프. 시스템 프롬프트 조립, 모델 제공자 해석, 도구 호출 반복 처리 |
| **Gateway** | 메시징 플랫폼과의 연결·라우팅. 플랫폼별 adapter, 사용자 권한(allowlist) 관리 |
| **Session** | 대화 이력 영구 저장. SQLite + FTS5 전문 검색(LLM 요약 포함) |
| **Memory** | 세션 간 유지되는 작은 지속 사실. 시작 시 시스템 프롬프트에 주입 |
| **Skills** | 필요 시 로드되는 긴 절차 지식(progressive disclosure) |
| **Subagents** | 격리된 위임 작업자. 독립 대화·도구 호출, 병렬 작업 |
| **Tools** | Terminal(local/Docker/SSH/원격 샌드박스), Browser 자동화, Web 검색, MCP 연결, 파일/코드 조작 |
| **Cron/Scheduler** | 자연어 또는 cron 표현식 기반 예약 작업 실행 |

---

## 3. Profile 기능 (다중 에이전트 운영의 핵심)

Profile은 단순 역할 프롬프트가 아니라 **독립된 홈 디렉터리를 가진 별도 에이전트 정체성**이다.
각 profile은 자체 설정·비밀정보·메모리·세션·skill·cron·gateway 상태를 가지므로,
독립된 "AI 직원" 또는 "부서"처럼 운영할 수 있다.

### 3.1 Profile 디렉터리 구조

각 profile은 대략 다음 요소를 가진다(경로는 `~/.hermes/profiles/<name>/` 형태):

```
<profile>/
├── config.yaml        # 모델·제공자·도구세트 등 모든 설정
├── .env               # API 키, 봇 토큰 (비밀정보)
├── SOUL.md            # 성격·행동 원칙(정체성)
├── memories/          # MEMORY.md(에이전트 노트), USER.md(사용자 프로필)
├── sessions/          # 대화 이력
├── skills/            # 사용자 skill
├── cron/              # 예약 작업 정의
└── state.db / gateway 상태 파일 등
```

### 3.2 다중 Profile 운영

- 하나의 시스템에서 여러 profile을 동시에 운영 가능(각각 별도 세션·메모리·비밀정보)
- 각 profile은 별도 gateway 프로세스로 실행 가능(서로 다른 봇 토큰 사용)
- profile마다 명령 별칭이 생성되어 `<name> chat`, `<name> gateway start` 형태로 호출

### 3.3 Profile Distribution (Git 패키징)

profile을 **Git 저장소로 패키징해 배포·공유**할 수 있다.

- 매니페스트(`distribution.yaml`)에 이름·버전·환경 요구사항 정의
- 번들 가능: `SOUL.md`, `config.yaml`, `skills/`, `cron/`, MCP 연결 설정 등
- **배포-소유(distribution-owned)** vs **사용자-소유(user-owned)** 파일을 구분:
  - 배포-소유(SOUL, config 기본값, skills, cron)는 업데이트 시 교체
  - 사용자-소유(`.env`, `memories/`, `sessions/`, 로그)는 설치·업데이트에서 **항상 제외/보존**
- 설치/업데이트 명령으로 버전 관리된 에이전트 공유 가능

> **개념 문서와의 연결:** 개념 문서 2장의 profile 구상(`chief-ai` → `research-lab`/`software-lab`/... 분리)과
> profile distribution을 통한 "부서 패키징"은 이 기능에 그대로 대응된다.

---

## 4. Slack 연동

개념 문서의 운영 구조(Slack 채널을 통한 사람↔대표 AI 대화)는 Hermes Gateway의 Slack 연동으로 구현된다.

### 4.1 연결 방식 — Socket Mode

- **Socket Mode(WebSocket)** 사용 → 외부 공개 webhook URL 불필요, 방화벽 뒤에서도 동작
- 인증: **Bot Token(`xoxb-`)** + **App-Level Token(`xapp-`)**
- (참고) 구형 Classic Slack App(RTM API)은 폐기되어 Socket Mode가 표준

### 4.2 필요한 권한/이벤트 (요지)

| 구분 | 예시 |
|------|------|
| 주요 scope | `chat:write`, `app_mentions:read`, `channels:history`, `groups:history`, `im:history`/`im:write`, `files:read`/`files:write` |
| 이벤트 구독 | `message.im`, `message.channels`, `message.groups`, `app_mention` 등 |

### 4.3 응답 동작

| 컨텍스트 | 동작 |
|----------|------|
| DM | 모든 메시지에 응답(@mention 불필요) |
| 채널 | 기본적으로 **@mention 시에만** 응답 |
| 스레드 | 최초 @mention 이후 스레드 내에서는 mention 없이 이어감 |

- 채널별 시스템 프롬프트·skill 바인딩 설정 가능(예: 특정 리서치 채널에서 리서치 skill 자동 로드)
- **다중 workspace** 지원(여러 봇 토큰을 콤마로 연결)
- **cron 전달 대상**을 홈 채널/특정 채널/사용자 DM으로 지정 가능

> **개념 문서와의 연결:** 개념 문서 3장의 초기 채널 구성(`#ai-ceo`, `#approvals`, `#mission-log`)과
> "채널에서는 @mention, 승인은 별도 채널" 운영은 위 응답 규칙·채널 바인딩으로 실현 가능하다.

---

## 5. Memory vs Skills

Hermes는 **memory**(작고 항상 참조되는 지속 사실)와 **skill**(필요할 때만 불러오는 긴 절차)을 구분한다.

| 종류 | 저장 내용 | 로딩 |
|------|-----------|------|
| **Memory** | 사용자 선호, 조직 원칙, 중요한 환경 사실 | 세션 시작 시 항상 주입 |
| **Skill** | 반복 가능한 업무 수행 절차 | 필요 시 조건부 로드(progressive disclosure) |

- `/learn` 명령으로 로컬 디렉터리·온라인 문서·직전 대화 기록으로부터 **새 skill을 자동 생성**할 수 있다.
- Skill 형식(`SKILL.md`)은 개방형 Agent Skills 표준(agentskills.io)과 호환된다.

> **개념 문서와의 연결:** 개념 문서 9장의 "Memory / LLM Wiki / Skill / Mission / Profile / Workspace" 역할 구분은
> 이 memory–skill 구분을 확장한 것이다.

---

## 6. Cron / Scheduler (자율 학습의 기반)

- **자연어 또는 cron 표현식**으로 예약 작업 등록 (예: "매 2시간", `0 9 * * *`)
- 일회성/반복 작업 모두 지원
- 작업에 0개 이상의 skill을 연결 가능
- 결과 전달 대상 지정(원본 대화, 로컬 파일, 플랫폼 채널 등)
- **no-agent 모드**: LLM 없이 스크립트만 실행하는 경량 작업 가능
- 모델 해석 순서: 작업별 고정 모델 → cron 기본 모델 → 글로벌 기본값(변경 시 보호 장치)

> **개념 문서와의 연결:** 개념 문서 7장의 "할 일이 없을 때의 자율 학습"(매일 06:00 신규 논문 검색 등)은
> 이 cron 기능 위에 Idle Mission Queue 정책을 얹어 구현한다.

---

## 7. 설치 및 실행 요구사항

| 항목 | 내용 |
|------|------|
| OS | Linux, macOS, Windows(native/WSL2), Android(Termux) |
| 전제 도구 | Git 필수 (설치 스크립트가 uv·Python 3.11·Node.js·ripgrep·ffmpeg 등 자동 설치) |
| Python | 3.11 ~ 3.13 (uv로 격리 설치, sudo 불필요) |
| 설치 | Linux/macOS: `curl -fsSL https://hermes-agent.nousresearch.com/install.sh \| bash` / Windows: PowerShell 스크립트 |
| LLM 제공자 | OpenAI, Anthropic, OpenRouter, Google, Azure, AWS Bedrock, Ollama 등 다수 지원. 코드 수정 없이 모델 전환 |
| 선택적 API 키 | 웹 검색(Firecrawl 등), 이미지 생성, TTS, 클라우드 브라우저 등 기능별 |

> 정확한 설치 명령·의존성 버전·제공자 목록은 [공식 설치 문서](https://hermes-agent.nousresearch.com/)에서 확인.

---

## 8. 개념 문서 각주 검증

개념 문서(`ai_native_company_개념.md`)가 인용한 Hermes 관련 각주가 현재도 유효한지 점검한 결과다.

| 개념 문서 각주 | 인용 경로(요지) | 2026-08-01 상태 |
|----------------|-----------------|-----------------|
| [1] README | `README.md` | 유효 |
| [2] Profiles | `website/docs/user-guide/profiles.md` | 유효 |
| [3] Profile distributions | `website/docs/user-guide/profile-distributions.md` | 유효 |
| [4] Slack | `website/docs/user-guide/messaging/slack.md` | 유효 (Socket Mode 표준) |
| [6] Scheduler | `cron/scheduler.py` (예약 작업) | 유효 (cron 기능 문서화됨) |
| [7] Skills | `website/docs/user-guide/features/skills.md` | 유효 (`/learn` 포함) |

> 위 표는 조사 에이전트가 문서 fetch를 통해 확인한 결과이며, 경로 리팩터링 가능성이 있으므로
> 링크가 깨질 경우 저장소 루트에서 `website/docs/` 하위를 다시 탐색할 것.

---

## 9. AI-Native Company 관점 요약

개념 문서의 구상은 Hermes의 다음 기능 조합으로 **별도 오케스트레이션 플랫폼 없이** 출발할 수 있다.

```
Profile + SOUL.md + Skills + Subagents + Cron + Slack Gateway + Git + LLM Wiki
```

- **대표 AI(`chief-ai`)** = profile 1개 + SOUL.md + 승인/미션 관리 skill
- **전문 조직** = 추가 profile(`research-lab` 등) + profile distribution으로 패키징
- **자율 학습** = cron + Idle Mission Queue
- **사람 개입** = Slack `#approvals` 채널 + 승인 요청 형식(행동·이유·영향·위험·복구)

---

## 출처

**공식 사이트 / 문서**
- https://hermes-agent.nousresearch.com/
- https://hermes-agent.nousresearch.com/docs/

**GitHub 저장소 및 문서**
- https://github.com/nousresearch/hermes-agent
- https://github.com/nousresearch/hermes-agent/blob/main/README.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/profiles.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/profile-distributions.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/messaging/slack.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/developer-guide/architecture.md

**관련**
- Agent Skills 표준: https://agentskills.io
- NousResearch: https://nousresearch.com

---
*이 문서는 2026-08-01 조사 결과다. 세부 수치·경로는 공식 문서 재확인을 권장한다.*
