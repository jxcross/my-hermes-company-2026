# M-2026-002 Independent Re-Review

- 재검토일: 2026-08-03
- 검토자: Reviewer (Writer와 독립)
- 대상: 수정된 `report.md`, `SCOPE.md`, 이전 `review/review.md`, `verify/verification.md`, `synthesis/synthesis.md`, `raw/sources.md`, 관련 Reader 산출물
- 판정: **수정요청(changes-requested)**

## 판정 요약

수정된 `report.md`는 이전 리뷰의 세 가지 보고서 서술 오류를 모두 바로잡았다. 그러나 보고서가 인용하는 상위 파이프라인 산출물은 갱신되지 않았다. Fact-Checker 검증표는 여전히 재인용 보도를 독립 확인으로 오분류하고 Reader 노트를 빈 파일로 오판하며 총괄 `보완요청` 상태다. 출처 목록도 이미 확인 가능한 정확한 발행일을 반영하지 않았다. 따라서 보고서 문구의 정정은 확인하지만, SCOPE의 독립 교차검증·출처 메타데이터 완료조건은 아직 충족되지 않아 승인할 수 없다.

## 이전 지적 해소 확인

1. **(a) 재인용 보도의 독립 교차확인 오분류 — 보고서 서술은 해소됨.**  
   `report.md:15,39,49`는 Socket·Help Net Security를 Anthropic 발표의 재서술로 명시하고, 사건 범위와 계수를 `Anthropic 자기보고·미검증`으로 제한했다. 재표본 확인에서도 Socket은 “Anthropic disclosed / The company said”, Help Net Security는 “Anthropic has disclosed / Anthropic said”라고 귀속하므로 수정된 보고서의 처리가 정확하다. 다만 `verify/verification.md:12,39,68`은 S11 사건 자체를 여전히 `확인`으로 둬 검증표 기준(`verification.md:5-6`)과 모순된다.

2. **(b) S14 Reader 산출물 ‘빈 파일’ 오단정 — 보고서 서술은 해소됨.**  
   `report.md:70`은 해당 파일이 비어 있지 않고 RSS 제목·발행일·고수준 설명 및 추출 한계를 담았다고 정확히 정정했다. 실제 `analysis/openai-hf-evaluation-security-incident.md`는 1,457바이트이며 이 내용을 포함한다. 다만 `verify/verification.md:12,47,60,68`과 `synthesis/synthesis.md`의 S14 항목은 여전히 `0바이트/빈 파일`로 서술한다.

3. **(c) 발행일·수집일 기록 과대서술 — 보고서 서술은 해소됨.**  
   `report.md:78`은 수집일은 전부 기록됐지만 WildClawBench·IETF는 월 단위이고 IBM·Anthropic 2건은 발행일이 `미확인`이라고 명시한다. “모든 발행일 기록 완료”로 읽히던 이전 표현은 제거됐다. 다만 `raw/sources.md:15-18` 자체는 갱신되지 않아 완료조건은 여전히 부분 충족이다.

## SCOPE 완료조건 재대조

| 완료조건 | 판정 | 재검토 결과 |
|---|---|---|
| 주요 공개 자료 8편 이상, 각 출처·발행일·수집일 기록 | **부분 충족/수정 필요** | 자료 수와 수집일은 충족한다. 그러나 `raw/sources.md:15-18`에 일 단위 미확인 2건과 발행일 미확인 2건이 남아 있다. 최소한 검증표가 이미 확인한 WildClawBench `2026-05-11`과 IETF `2026-07-05`도 반영되지 않았다. |
| 먼저 llm-wiki query 후 재사용, 재사용률 기록 | **충족** | `raw/search-strategy.md:9-25`에 선조회가 있고, 이전 검토에서 공식 재사용률 7/17(41.2%) 및 선별 집합 7/15(46.7%) 기록을 확인했다. |
| 핵심 주장 Fact-Checker 독립 교차검증 | **미충족** | `verify/verification.md` 총괄은 여전히 `보완요청`이다. S11 독립성 판정과 S14 파일 상태 판정이 수정되지 않았고, 확인/상충/미검증 집계도 재계산되지 않았다. Writer의 보수적 재서술은 Fact-Checker의 독립 재판정을 대체하지 못한다. |
| 보고서 모든 주장에 출처, 불확실성·반대근거 명시 | **부분 충족** | 수정 보고서 자체는 주요 주장에 링크를 붙이고 자기보고·preprint·상충·반례를 명시했다. AISI 예산 민감성/HealthBench 반례와 S11 재인용 성격을 재표본 검증해 서술 일치를 확인했다. 그러나 보고서가 근거로 인용하는 `verify/verification.md`와 `synthesis/synthesis.md`가 S11·S14에서 현재 사실과 모순돼 provenance chain이 일관되지 않다. |
| Reviewer(≠Writer) 독립 검토 통과 | **미충족** | 본 재검토 판정이 수정요청이다. |
| Curator raw→wiki→reflection 및 index/log·재사용률 갱신 | **후속 단계 미확인** | 현재 Reviewer 단계 산출물에서 완료 증거가 없다. 독립검토 통과 후 확인할 항목이다. |
| Deliver 게이트에서 Sam 확인 | **후속 단계 미확인** | 현재 확인 증거가 없다. |

## 남은 필수 수정 지시

1. **Fact-Checker가 Cross-Verify를 재실행할 것.** `verify/verification.md:S11-1`을 피해 조직·평가 파트너의 독립 로그나 직접 공개가 없는 한 `Anthropic 자기보고/미검증`으로 재판정하고, 총괄 문장·집계·결론을 함께 갱신하라. Writer가 판정을 임의로 변경해서는 안 된다.

2. **S14 상태를 검증·종합 산출물 전체에서 일치시킬 것.** Fact-Checker는 현재 1,457바이트 Reader 노트를 기준으로 `verify/verification.md:12,47,60,68`의 `빈 파일/0바이트` 판정을 제거하고, RSS 수준 분석의 한계와 Hugging Face·JFrog 독립 자료에 따른 사건 검증을 구분하라. 이후 Synthesizer가 `synthesis/synthesis.md`의 S14 결함 서술과 관련 총계를 갱신해야 한다.

3. **출처 날짜 원장을 갱신할 것.** `raw/sources.md:15-16`에 이미 검증된 WildClawBench `2026-05-11`, IETF Datatracker `2026-07-05`를 반영하라. `raw/sources.md:17-18`의 두 자료를 주요 검토 자료로 유지한다면 공식 페이지나 보존 원문으로 발행일을 확인하고, 확인 불가 시 해당 자료를 완료조건의 날짜 기록 완료 집합에서 제외했음을 명시하라.

4. **상위 산출물 갱신 뒤 보고서의 상태 문구를 재동기화할 것.** 갱신된 Fact-Checker 총괄 판정·집계·필수 보완사항만 `report.md:5,66,78`에 반영하고, 현재처럼 보고서와 검증표가 서로 다른 사실 상태를 가리키지 않게 하라.

5. **위 변경 후 재독립검토를 받을 것.** 핵심 차단 사유는 수정 보고서의 문장 품질이 아니라 검증표·종합·출처 원장의 미갱신이다. 이 provenance chain이 일치하기 전 Wiki Update·Deliver를 최종 완료 처리하지 말라.

## 승인 가능 조건

S11과 S14가 Fact-Checker에 의해 재판정되고, 정확한 출처 날짜가 원장에 반영되며, 갱신된 검증표·종합·보고서가 같은 상태를 나타내면 승인 가능하다.
