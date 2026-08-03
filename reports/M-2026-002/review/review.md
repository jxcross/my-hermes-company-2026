# M-2026-002 Independent Review

- 검토일: 2026-08-02
- 검토자: Reviewer (Writer와 독립)
- 대상: `report.md`, `SCOPE.md`, `verify/verification.md`, `synthesis/synthesis.md`, `raw/sources.md`, 관련 Reader 산출물
- 판정: **수정요청(changes-requested)**

## 판정 요약

승인하지 않는다. 보고서는 상충 수치와 제공자 자기보고의 한계를 대체로 보수적으로 반영했지만, (1) 재인용 기사에 근거한 사건을 “독립 교차확인”으로 잘못 분류했고, (2) 실제로 내용이 있는 S14 Reader 파일을 “빈 파일”이라고 단정했으며, (3) 출처별 발행일 기록 완료를 사실과 다르게 서술한다. Cross-Verify 자체가 `보완요청` 상태인 데다 검증표의 독립성 기준 적용 오류가 보고서의 `확인` 판정으로 전파됐으므로 완료조건의 출처정확성·독립 교차검증 게이트를 통과하지 못했다.

## SCOPE 완료조건 대조

| 완료조건 | 판정 | 검토 결과 |
|---|---|---|
| 주요 공개 자료 8편 이상, 각 출처·발행일·수집일 기록 | **부분 충족/수정 필요** | `raw/curated.md`는 15편을 선별했고 수집일은 기록했다. 그러나 `raw/sources.md:15-18`에는 WildClawBench와 IETF가 월 단위이고 IBM·Anthropic 2건은 `미확인`이다. 특히 검증표 `S07-3`은 WildClawBench 발행일을 2026-05-11로 보강하라고 했으나 반영되지 않았다. `report.md:78`의 “전체 17건의 발행일·수집일”은 현재 파일 내용과 불일치한다. |
| llm-wiki 선조회·재사용, 재사용률 기록 | **충족** | `raw/search-strategy.md:9-25`에 선조회가 있고, `raw/curated.md`에 공식 재사용률 7/17(41.2%) 및 선별 집합 7/15(46.7%)가 구분되어 있다. |
| 핵심 주장 Fact-Checker 독립 교차검증(확인/상충/미검증) | **미충족** | 검증표 총괄이 `보완요청`이다. 또한 `verify/verification.md:6`은 발표 재인용 기사를 독립 증거로 세지 않는다고 했지만 `S11-1`은 Anthropic 발표를 재서술한 Socket·Help Net Security 기사만으로 `확인` 처리했다. 표본 확인한 Socket 본문은 “Anthropic disclosed”, “company said”라고 명시하며 피해 조직의 독립 로그나 직접 확인을 제시하지 않는다. 독립성 기준의 자기모순이다. |
| 보고서 모든 주장에 출처, 불확실성·반대근거 명시 | **미충족** | 대부분의 단락에 출처가 있고 S10 상충, simulation/incident 구분, HealthBench 반례를 보존한 점은 양호하다. 그러나 `report.md:39,49`의 “사고 자체는 독립 보안 매체 보도로 교차확인/확인”은 위 재인용 자료가 뒷받침하지 않는다. `report.md:70`의 S14 빈 파일 주장도 현재 파일과 불일치한다. 출처 링크의 존재만으로 정확성이 충족되지 않는다. |
| Reviewer(≠Writer) 독립 검토 통과 | **미충족** | 본 리뷰 판정이 수정요청이다. |
| Curator raw→wiki→reflection 및 index/log·재사용률 갱신 | **후속 단계 미완료** | 현재 Reviewer 단계에서는 완료 증거가 없다. 본 수정요청 해소 및 재검토 통과 전 최종 완료로 간주할 수 없다. |
| Deliver 게이트에서 Sam 확인 | **후속 단계 미완료** | 현재 확인 증거가 없다. |

## 출처 표본검증 결과

1. **AISI 예산 민감성 — 정확**  
   `report.md:21,45`의 10M→100M tokens, 최대 59% 상승은 AISI 연구 초록 원문과 일치한다. `report.md:9,74`의 HealthBench plateau 반례도 AISI 원문 각주와 일치한다.

2. **ReviewBench — 정확하나 자기보고 경계 필요(보고서 반영됨)**  
   `report.md:29,46`의 59 tasks, 64 baseline issues, strongest run 약 30%는 LangChain 원문과 일치한다. 단일 mono-repo, hidden LLM judge, 제공자 자체평가라는 제한도 보고서에 반영됐다.

3. **WildClawBench — 수치 전사 정확, 독립 재현 아님(보고서 반영됨)**  
   `report.md:27,47`의 60개 bilingual·multimodal task, native CLI harness, hybrid grading은 arXiv 원문과 일치한다. OpenTrain은 “No benchmark numbers could be verified”라고 명시하므로 보고서의 `미검증` 처리는 적절하다. 다만 OpenTrain은 발행일 2026-05-11을 제시하며, 수집 목록의 월 단위 기록은 보강이 필요하다.

4. **IETF 문서 상태 — 정확**  
   `report.md:37,48`의 individual Internet-Draft, 비표준 상태는 IETF Datatracker의 `Active Internet-Draft (individual)`, `No stream defined`, `I-D Exists`와 일치한다.

5. **ARC-AGI-3 설정 효과 — 정확한 귀속**  
   `report.md:50`의 public set 13.3%→38.3%, output token 6x 감소는 OpenAI 원문과 일치하며, 보고서는 이를 OpenAI 자체 harness 비교·`미검증` 사례로 제한했다.

6. **Anthropic 평가환경 사건 — 독립 교차확인 주장은 부정확**  
   Anthropic 원문은 세 조직 무단 접근을 자기보고한다. 표본 확인한 Socket 기사는 사건 계수와 범위를 Anthropic 발표에 명시적으로 귀속해 재서술한다. 따라서 `report.md:39,49` 및 `verify/verification.md:S11-1`의 독립 교차확인 판정은 검증표 자체 기준(`verification.md:6`)을 충족하지 않는다.

7. **S14 Reader 파일 — 보고서의 파일 상태 주장이 틀림**  
   `analysis/openai-hf-evaluation-security-incident.md`는 현재 1,457바이트이며 제목, 원자료, RSS 기반 주장, 근거 한계, 전달 경계를 포함한다. 파일 수정시각(13:32)이 검증표(13:40), synthesis(13:43), report(13:46)보다 앞선다. 따라서 `verify/verification.md:12,47,60,68`, `synthesis/synthesis.md`의 S14 결함 서술, `report.md:70`의 “빈 파일”은 현재 산출물과 모순된다. 내용이 충분한지는 별도 문제지만 “0바이트/빈 파일” 판정은 사실 오류다.

## 필수 수정 지시

1. **S11 독립성 판정을 바로잡을 것.** `verify/verification.md:S11-1`과 이를 인용한 `report.md:39,49`에서 Socket·Help Net Security가 Anthropic 발표를 재인용하는 2차 보도임을 반영하라. 피해 조직·평가 파트너의 직접 로그/독립 공개 등 1차 독립 증거를 확보하지 못하면 사건 범위를 `Anthropic 자기보고/미검증`으로 하향하고 “독립 교차확인” 표현을 삭제하라.

2. **S14 파일 상태를 재검증하고 파이프라인 산출물을 일치시킬 것.** 현재 파일을 0바이트로 판정한 원인을 확인한 뒤 `verify/verification.md`, `synthesis/synthesis.md`, `report.md:70`을 실제 상태에 맞게 갱신하라. 단순히 “빈 파일” 문구만 지우지 말고, 현재 Reader 노트가 RSS 수준이라 Fact-Checker 필수 보완사항의 3자(OpenAI·Hugging Face·JFrog) 기술 서술을 충족하는지 다시 판정하라.

3. **출처 날짜 메타데이터를 정정할 것.** `raw/sources.md`의 최종 선별 15건에 대해 가능한 정확한 발행일을 기록하라. 최소한 Fact-Checker가 이미 확인한 WildClawBench 2026-05-11과 IETF Datatracker의 2026-07-05를 반영하고, 제외 자료의 `미확인`을 유지한다면 `report.md:78`을 “17건 모두 발행일 기록 완료”로 읽히지 않게 정확히 서술하라.

4. **Cross-Verify를 재실행해 총괄 판정을 갱신할 것.** 위 수정 후 확인/상충/미검증 집계와 필수 보완사항을 다시 계산하고, `보완요청`이 해소됐는지 Fact-Checker가 독립적으로 판정하게 하라. Writer가 검증 상태를 임의로 승격해서는 안 된다.

5. **보안 통제 주장과 직접 출처의 대응을 명확히 할 것.** `report.md:11,56`의 access·memory·tool·execution·infrastructure·supply chain 및 egress/audit/resource-cap 묶음은 현재 NIST 두 문서만 직접 나열해 각 세부 통제가 어느 출처에 근거하는지 불명확하다. 검증표가 사용한 IETF/NIST 발표/Hugging Face technical timeline 등 실제 근거를 각 세부 주장에 연결하거나, 직접 근거가 확인된 범위로 주장을 축소하라.

6. **수정본은 재독립검토를 받을 것.** 위 항목을 반영한 뒤 Reviewer가 동일한 SCOPE 체크리스트와 출처 표본검증으로 재판정하기 전 Wiki Update·Deliver를 최종 완료 처리하지 말라.

## 승인 가능 조건

필수 수정 지시 1~5가 산출물 전반에 일관되게 반영되고, 갱신된 Cross-Verify가 핵심 주장에 대해 기준과 증거가 일치하는 판정을 내리며, 수정 보고서가 재독립검토를 통과해야 한다.
