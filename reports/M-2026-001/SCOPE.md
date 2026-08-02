# M-2026-001 — 미션 스펙 (1단계 Scoping 산출물)

> 유형: `research-trend-report` (축소 슬라이스) · 요청자: Sam · 승인: 2026-08-02 (주제·자동실행 승인)
> 파이프라인: Scoping → Search+Collection(scout) → Deep Analysis(reader) → Report Draft(writer) → Deliver(Solomon+Sam)

## 주제
**최근 3개월(2026-05 ~ 2026-08) Agentic AI / LLM 에이전트 동향.**
멀티에이전트 오케스트레이션, 에이전트 프레임워크, 툴 유즈/컴퓨터 유즈, 신뢰성·평가 등 실무 적용 관점의 핵심 흐름.

## 목표
공개 자료를 조사·분석·종합해 **출처 포함 Markdown 동향 보고서**를 생산하고, 축소 파이프라인이 실제로 도는 것을 증명한다.

## 완료 조건 (Completion Criteria)
- [ ] 주요 공개 자료 **8편 이상** 검토(공식 블로그·arXiv·릴리스 노트·1차 문서 우선)
- [ ] 각 자료에 **출처(URL)·발행일·수집일** 메타데이터 기록
- [ ] 자료별 **주장/근거 분리** 분석
- [ ] 보고서의 **모든 주장에 출처 링크**
- [ ] **불확실성·반대근거** 명시
- [ ] Deliver 게이트에서 Sam 확인

## 제약
- 공개 자료만. 유료 자료 무단 접근 금지, robots/allowlist 준수.
- 출처·날짜 불명확 자료는 그 사실을 명시(추측 금지).
- 비용 드는 자원 필요 시 중단하고 보고.

## 산출물 위치 (컨테이너 경로 = /work/company/reports/M-2026-001)
- `raw/` — scout: 수집 원문 요약 + `raw/sources.md`(출처·발행일·수집일 표)
- `analysis/` — reader: 자료별 분석 노트(`analysis/<slug>.md`)
- `report.md` — writer: 최종 보고서(출처 포함)

## N (검토 목표 편수)
최소 8편, 권장 10~12편.
