# my-hermes-company-2026 — AI-Native Company (Solomon)

> **버전: v0.1.0** · 상태: **Stage 0 완료** (Solomon 격리 컨테이너 구동)

Hermes Agent 기반으로, 1인 창업자(**Sam**)가 AI 총괄 대표(**Solomon, AI CEO**)와 Slack에서
브레인스토밍하며 **기획→제안→설계→구현→배포**까지 수행하는 AI-Native Company 프로젝트.

핵심 원리: **사람은 목표·경계조건을 정하고, AI는 계획·조사·구현·검증·정리를 수행한다.**
회사는 시간이 지날수록 결과물·속도·품질이 좋아지는 **복리(compounding) 조직**을 지향한다.

---

## 아키텍처 (요약)

```
Sam ──Slack──> Solomon(대표: 기획·오케스트레이션·검증총괄·보고, 구현 안 함)
                     │
                     ▼
             Hermes 네이티브 Kanban = 워크플로우 관리자
             (미션=부모 task, 단계=자식 task, 게이트·감사·대시보드)
                     │  디스패치
        ┌────────────┼────────────┐
     전문 profile (Scout·Reader·Fact-Checker·Synthesizer·Writer·Reviewer·Curator)
        └────────────┼────────────┘  ※ 단계 내 병렬은 subagent
                     ▼
             LLM Wiki (별도 repo, raw→wiki→reflection)
```

- **오케스트레이션**: Option B — Hermes 네이티브 **Kanban + 전문 profile**
- **작성자 ≠ 검증자** (코드 구현 profile ≠ 코드 검증 profile)
- **전문화 4계층**: SOUL(좁은 역할)·Skill·누적 Memory·공유 Knowledge(Wiki)
- 미션 아키타입: **A** 연구·기술 동향 보고서 · **B** 학술 논문 · **D** 웹개발(시뮬레이션 포함)

자세한 설계는 [`docs/`](docs/) 참조:
| 문서 | 내용 |
|------|------|
| [02_company_design](docs/02_company_design.md) | 회사 설계·아키텍처·로드맵 |
| [03_mission_pipeline_and_workflow](docs/03_mission_pipeline_and_workflow.md) | 파이프라인↔Kanban·Skill Library |
| [04_mvp_research_trend_report_spec](docs/04_mvp_research_trend_report_spec.md) | 1호 미션 SPEC(11단계) |
| [05_stage0_setup_guide](docs/05_stage0_setup_guide.md) | Stage 0 구축 가이드 |
| [06_design_decision_log](docs/06_design_decision_log.md) | 의사결정 기록(ADR) |
| [07_diagrams](docs/07_diagrams.md) | 다이어그램(Mermaid) |
| [08_agent_specialization_and_governance](docs/08_agent_specialization_and_governance.md) | 전문화·거버넌스 |
| [09_mission_board_and_visibility](docs/09_mission_board_and_visibility.md) | 게시판·워크플로우 가시성 |

---

## 실행 (로컬 Docker)

전제: Docker, 그리고 별도의 [llm-wiki repo](https://github.com/jxcross/my-hermes-company-llm-wiki-2026)를
형제 디렉터리에 클론.

```bash
cp .env.example .env                 # 값 채우기(아래 참고)
docker compose run --rm hermes-solomon hermes setup   # OAuth 로그인(ChatGPT), 모델 gpt-5.5
cp solomon-profile/SOUL.md hermes-home/SOUL.md         # Solomon 정체성 배포
mkdir -p hermes-home/memories && cp solomon-profile/USER.md hermes-home/memories/USER.md
docker compose up -d                 # 게이트웨이 기동
```

- 인증: **OAuth(ChatGPT 구독) GPT-5.5** (provider `openai-codex`) — API 키 불필요
- **웹 대시보드(게시판)**: `http://localhost:9129` (basic auth)
- 격리: 호스트 `~/.hermes`(다른 프로젝트)와 분리 — 데이터는 이 repo의 `hermes-home/`(gitignore)

`.env`에 필요한 값: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_ALLOWED_USERS`, `SLACK_HOME_CHANNEL`,
`HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`. (Slack 앱은 `hermes-home/slack-manifest.json`으로 생성)

---

## 로드맵

- **Stage 0 — 기반** ✅ (완료): 격리 컨테이너·OAuth gpt-5.5·Slack·Kanban·대시보드
- **Stage 1 — 1호 미션 MVP**: 연구·기술 동향 보고서 11단계 파이프라인 완주
- **Stage 2 — 복리 루프**: Skill 추출·Reflection·Wiki 재사용(성장 지표)
- **Stage 3 — 24시간 학습**: 수요 기반 cron 축적
- **Stage 4 — 부서 확장 + Control Plane**: profile fleet·고급 실행상태 뷰
- **Stage 5+ — 미션 B/D**: 논문·웹개발

---

## 새 세션 / 다른 PC에서 이어가기

- 어느 PC의 새 Claude Code 세션이든 **[`CLAUDE.md`](CLAUDE.md)가 자동 로드**되어 맥락·규칙·상태를 복원한다.
- **주의**: `.env`(시크릿)·`hermes-home/`(auth·kanban·sessions)·프로젝트 메모리는 **git에 없다(로컬 전용)**.
  다른 PC에서는 [`docs/05_stage0_setup_guide.md`](docs/05_stage0_setup_guide.md)로 **부트스트랩**(repo 2개 clone → `docker compose pull` → `.env` 작성 → `hermes setup` OAuth 재로그인 → 정체성 배포 → `up -d`)한다.
- 첫 메시지 예: *"my-hermes-company-2026 이어서 진행하자. v0.1.0/Stage 0 완료 상태 확인 후 Stage 1 계획을 제시하라."*

## 저장소 구조
```
docs/               설계 문서(02~09) + 조사 자료
docker-compose.yml  Solomon 격리 Hermes 서비스
.env.example        환경변수 템플릿(.env는 gitignore)
solomon-profile/    Solomon 정체성 소스(SOUL·USER)
hermes-home/        (gitignore) 컨테이너 데이터: profiles·kanban·sessions·auth 등
history.html        작업 이력
CHANGELOG.md        릴리스 변경 이력
```

라이선스/공개 범위는 미정(내부 프로젝트).
