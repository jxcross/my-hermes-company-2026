# M-2026-002 — 미션 스펙 (1단계 Scoping 산출물)

> 유형: `research-trend-report` (full 11단계) · 요청자: Sam · 승인: 2026-08-02 (계획 승인 시 주제·자동실행 승인)
> 파이프라인: Scoping → Search Strategy(scout) → Collection(scout) → Dedup·Relevance(curator) → Deep Analysis(reader) → **Cross-Verify(fact-checker, ≠reader)** → Synthesis(synthesizer) → Report Draft(writer) → **Independent Review(reviewer, ≠writer)** → Wiki Update(curator) → Deliver(Solomon+Sam)

## 주제
**AI 에이전트 평가·신뢰성·안전성(evaluation · reliability · safety) 동향** (최근 3개월, 2026-05~08).
에이전트 벤치마크·평가 방법론, 검증 가능한 verifier 설계, 신뢰성·재현성, 오정렬(misalignment)·보안·거버넌스.

## 목표
공개 자료를 조사·**교차검증**·종합해 **출처 포함 + 독립검토 통과** 보고서를 생산하고,
**기존 llm-wiki(M-2026-001 지식) 재사용(복리)**과 **작성자≠검증자** 게이트를 실증한다.

## 완료 조건 (Completion Criteria)
- [ ] 주요 공개 자료 **8편 이상** 검토(1차 출처 우선), 각 출처·발행일·수집일 기록
- [ ] **먼저 llm-wiki를 query해 재사용**, 부족분만 신규 수집 (재사용률 기록)
- [ ] 핵심 주장은 **Fact-Checker가 독립 출처로 교차검증**(확인/상충/미검증 판정)
- [ ] 보고서의 **모든 주장에 출처**, 불확실성·반대근거 명시
- [ ] **Reviewer(≠Writer) 독립 검토 통과**(완료조건·출처정확성)
- [ ] Curator가 raw→wiki→reflection을 llm-wiki에 반영 + index/log·재사용률 갱신
- [ ] Deliver 게이트에서 Sam 확인

## 제약
- 공개 자료만, 유료 무단접근 금지, robots/allowlist 준수. 출처 없는 주장 제외. 비용 상한 초과 시 Sam 승인.

## 산출물 위치 (컨테이너 경로 = /work/company/reports/M-2026-002)
- `raw/`(scout) · `analysis/`(reader) · `verify/`(fact-checker 검증표) · `synthesis/`(synthesizer) · `review/`(reviewer) · `report.md`(writer)
- 지식 축적: `/work/llm-wiki`(curator, karpathy-llm-wiki 스킬)

## N
최소 8편(신규+재사용 합산), 권장 10~12편.
