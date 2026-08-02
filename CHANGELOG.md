# Changelog

이 프로젝트의 주요 변경 이력. 형식은 [Keep a Changelog](https://keepachangelog.com/) 및
[Semantic Versioning](https://semver.org/)을 따른다.

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

[v0.1.0]: https://github.com/jxcross/my-hermes-company-2026/releases/tag/v0.1.0
