# 01. Hermes Agent · LLM Wiki 조사 문서화 계획

> 작업 일자: 2026-08-01
> 요청자: CEO(사용자)
> 목적: `docs/ai_native_company_개념.md` 구상의 두 기반 기술을 최신 자료로 조사하여 별도 참고 문서로 정리

---

## 1. 배경 (Context)

`docs/ai_native_company_개념.md`는 Hermes Agent 기반 "AI-Native Company"의 상세 구상을 담고 있으며,
그 근거로 **Hermes Agent(NousResearch)**와 **Karpathy의 LLM Wiki**를 각주로 인용한다.

개념을 실제로 구현하기 전에, 이 두 핵심 기반 기술의 **정확한 사실 자료**를
독립된 참고 문서로 확정해 두어야 이후 로드맵/설계 단계에서 근거로 활용할 수 있다.

## 2. 목표 (Deliverables)

| # | 산출물 | 설명 |
|---|--------|------|
| 1 | `docs/hermes_agent_조사.md` | Hermes Agent 기술 정리 (아키텍처·profile·Slack·설치·각주 검증) |
| 2 | `docs/llm_wiki_조사.md` | LLM Wiki 개념·구현 정리 (워크플로·계층·디렉터리·통합) |
| 3 | `history.html` | 작업 이력 기록 |

## 3. 조사 출처

**Hermes Agent**
- 공식: https://hermes-agent.nousresearch.com/
- 저장소: https://github.com/nousresearch/hermes-agent
- 문서: README, user-guide/{profiles, profile-distributions, messaging/slack}, features/{memory, skills, cron}, developer-guide/architecture

**LLM Wiki**
- 원문: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- 참고 구현: https://github.com/Astro-Han/karpathy-llm-wiki

## 4. 작업 단계

1. [x] 개념 문서(`ai_native_company_개념.md`) 검토
2. [x] Hermes Agent 웹 자료 조사 (공식 사이트·GitHub 문서 fetch)
3. [x] LLM Wiki 웹 자료 조사 (Karpathy gist·Astro-Han 구현 fetch)
4. [ ] 이 계획 문서 작성 (본 파일)
5. [ ] `docs/hermes_agent_조사.md` 작성
6. [ ] `docs/llm_wiki_조사.md` 작성
7. [ ] `history.html` 갱신
8. [ ] Git 커밋 및 원격 푸시

## 5. 검증 방법

- 생성된 문서 3종 + `history.html` 파일 존재·내용 확인
- 각 조사 문서에 **출처 URL 섹션**과 **조사 기준일(2026-08-01)** 포함 여부 확인
- Hermes 문서에 **개념 문서 각주 검증표** 포함 여부 확인
- `git log` / `git status`로 커밋·푸시 결과 확인

## 6. 주의 사항

- 조사 결과의 세부 수치(버전 번호, 메모리 문자수 제한 등)는 빠르게 변할 수 있으므로,
  각 문서에 **"실제 사용 전 공식 문서 재확인 권고"** 주의 문구를 포함한다.
- Git 태그·릴리스는 사용자가 명시적으로 요청할 때만 수행한다(이번 작업 범위 아님).
