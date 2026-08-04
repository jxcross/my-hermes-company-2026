# M-2026-004 독립 검토

- 검토 단계: 9 Independent Review
- 검토 대상: `report.md`
- 완료조건 기준: `SCOPE.md`
- 판정: **수정요청(changes-requested)**

## 1. 완료조건 대조

| SCOPE 완료조건 | 판정 | 근거 |
|---|---|---|
| llm-wiki 선조회, 재사용 항목·부족분·재사용률 기록 | 충족 | `raw/search-strategy.md:55-59`, `raw/curated.md:7-12`에 선조회와 재사용률 0/15가 기록돼 있다. |
| 공개 자료 10편 이상 및 URL·발행일/연도·수집일·유형·선별 상태 기록 | **불충족** | `raw/sources.yaml`에는 필드가 있으나 canonical 선별 상태가 후속 산출물과 모순된다. YAML의 `selected`는 18건인데 `raw/curated.md:18-22`와 `analysis/_index.md:5`는 12건이라고 한다. Curator가 제외했다고 명시한 Apple landing page와 MLPerf Client release도 YAML에서는 여전히 `selected`다(`raw/sources.yaml:36-42,86-92`; `raw/curated.md:41-47`). NIST·뉴스 3건도 YAML에서 `selected`지만 12건 분석·보고서에는 포함되지 않는다(`raw/sources.yaml:107-134`). 따라서 어떤 12건이 최종 선별 집합인지 canonical inventory가 확정돼 있지 않다. |
| academic 2+, vendor 2+, research_org 1+ 및 벤더 편향 방지 | 조건부 충족 | 보고서가 실제 사용한 12건 기준 academic 5, vendor 4, research_org 3으로 최소 분배를 충족한다(`raw/curated.md:21-22`). 다만 위 YAML 상태 불일치부터 정정해야 자동 집계 가능한 정책 준수가 성립한다. |
| 양자화/압축, 메모리·KV, 런타임·하드웨어, 품질·성능·전력 평가 및 각 영역의 성숙도·trade-off | **부분 충족** | `report.md:12-25,27-50`은 기술 분류·성숙도·성능/품질 측정 전제를 다룬다. 그러나 전력은 주로 “측정해야 한다”는 체크리스트에 머문다. 원자료에는 sparse 방식이 순간 전력은 낮지만 긴 생성시간 때문에 총에너지는 더 높았다는 직접 반대근거가 보존돼 있는데(`raw/llm-in-a-flash-efficient-inference-limited-memory.md:94`), 보고서는 이를 누락했다. 전력 trade-off를 다뤘다고 보기에는 핵심 관찰이 빠졌다. |
| 대표 배포 경로 3개 이상 비교 및 비교 가능/불가능 조건 구분 | **부분 충족** | `report.md:64`는 iPhone 13/ExecuTorch, Xiaomi 14/MNN, A100/KIVI, Apple Silicon·RTX, S24 Ultra 경로가 이질적이라 직접 순위화할 수 없음을 정확히 밝힌다. 하지만 최소 3개 경로를 공통 축(장치/OS, 모델, 정밀도, runtime, prefill/decode, 측정 지표, 현재 지원 상태)으로 실제 비교한 결과표나 대응 서술은 없다. “모두 직접 비교 불가”라는 금지선만으로 SCOPE의 ‘3개 대표 배포 경로 비교’가 완료되지는 않는다. |
| 핵심 주장별 1차 출처 및 Fact-Checker 확인/상충/미검증 판정 | **불충족** | 보고서의 핵심 주장에는 링크가 연결돼 있으나 Fact-Checker 검증표는 Google AI Edge 분석 1건의 21개 주장만 대상으로 한다(`verify/verification.md:1-6`). MobileLLM, KIVI, ElastiLM, MNN-LLM, LLM in a Flash, MLPerf, AICore, Gemma 3n, Qualcomm에 관한 보고서 핵심 결론에는 확인/상충/미검증 ID가 없다. `report.md:10`의 “21개 핵심 주장 집계”는 전체 보고서 검증처럼 읽힐 여지가 있으나 실제 범위는 단일 Reader 문서다. 독립 확인 가능한 전체 핵심 주장에 Fact-Checker 상태를 부여하라는 완료조건을 충족하지 못한다. |
| 출처 없는 사실 주장 금지 및 수치 전제·불확실성·벤치마크 한계 명시 | 대체로 충족 | 표본 감사에서 KIVI의 Falcon-7B 2-bit 품질 저하/4-bit 필요 및 A100 합성 workload(`analysis/kivi-...md:51-54`), MNN의 Xiaomi 14 및 비대칭/대칭 양자화 불일치(`analysis/mnn-...md:51-54`), Gemma 2,585 tk/s 조건(`report.md:31-33`, `verify/verification.md:22-23`)이 출처 범위와 일치했다. Google 원문도 2.5–4×, 2,585 prefill, 1,000페이지/사진, 당시 SDK 가용성을 공급자 주장으로 실제 제시하며, 보고서는 이를 미검증으로 공개했다. 다만 전수 Fact-Checker 상태 부재 때문에 전체 주장 정확성을 승인할 수는 없다. |
| 독립 Reviewer PASS | **불충족** | 본 검토는 FAIL이다. |
| Curator wiki 반영·reflection·재사용률 갱신 | 후속 단계 | 현재 9단계 뒤의 10단계 조건이므로 본 보고서 승인 근거로 선취하지 않는다. |
| Deliver에서 Sam에게 요약·권고·검증 결과 제시 | 후속 단계 | 현재 9단계 뒤의 11단계 조건이다. |

## 2. 출처 정확성 표본 감사

1. **Google AI Edge 공급자 주장 — 정확한 제한 공개:** 외부 원문은 2025-05-20 발표, 12개 초과 모델, int4 2.5–4× 축소, 2,585 tokens/s prefill, 1,000페이지/사진, Android RAG/function calling 가용성 및 tool simulation 효능을 실제로 주장한다. `report.md:32-33,44,47,50,54-60`은 이를 일반 사실로 승격하지 않고 공급자 발표·미검증으로 제한했다. 적합하다.
2. **KIVI — 적합:** `report.md:19,45`의 Falcon-7B 2-bit 품질 저하 가능성, 4-bit 필요, A100·합성 workload 제한은 분석 원장의 표·실험 조건(`analysis/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md:51-54`)과 일치한다.
3. **MNN-LLM — 적합:** `report.md:22,46`의 Xiaomi 14 한정 및 MLC-LLM과 양자화 조건 불일치는 분석 원장(`analysis/mnn-llm-generic-inference-engine-mobile-devices.md:51-54`)과 일치한다.
4. **QAI AppBuilder — 적합하나 공급자 범위:** `report.md:23,48`의 local endpoint/API 경로는 원문 분석의 `GenieAPIService` localhost 예시(`analysis/qualcomm-qai-appbuilder-wos.md:23-25`)가 뒷받침한다. 보고서는 성능·호환성을 확정하지 않아 과장이 없다.
5. **LLM in a Flash 전력 반대근거 — 누락:** 원자료가 순간 전력과 총에너지의 방향이 반대일 수 있음을 명시하지만 보고서는 이 결과를 반영하지 않는다. SCOPE가 전력 평가와 trade-off를 명시한 만큼 단순 부가정보가 아니라 완료조건 관련 반증이다.

## 3. 수정 지시

1. `raw/sources.yaml`을 Curator의 최종 판정과 일치시키라. 최소한 Apple landing page, MLPerf Client release metadata, NIST, 뉴스 3건의 `selected/excluded` 상태를 실제 채택 여부에 맞게 정정하고, `raw/curated.md`의 전체 수집 수·선별 수·제외 수·재사용률 분모·출처 분배·최근성 집계를 같은 canonical 집합에서 다시 계산하라.
2. Fact-Checker가 Google AI Edge 1건 외의 보고서 핵심 주장도 표본이 아닌 체계적 단위로 판정하게 하라. 최소한 MobileLLM 구조/모바일 측정, KIVI 품질·효율, LLM in a Flash 지연·에너지, MNN runtime 비교, ElastiLM SLO, MLPerf 지표, AICore/QAI 지원 경로에 `확인/상충/미검증` 상태와 독립성 한계를 부여하고, 보고서의 검증 집계를 전체 범위와 Google 하위 범위로 구분하라.
3. 대표 배포 경로 최소 3개를 공통 비교 축으로 명시하라. 서로 다른 조건의 수치를 순위화하지 말고, 각 경로의 장치/OS·모델·정밀도·runtime/가속기·prefill/decode·측정 지표·지원/재현 상태를 나란히 제시해 비교 가능한 항목과 불가능한 항목을 행별로 구분하라.
4. 전력·에너지 평가에 실제 근거와 반증을 반영하라. 특히 LLM in a Flash의 “낮은 순간 전력이나 더 높은 총에너지” 결과를 정확한 실험 범위에 귀속하고, power와 energy를 혼용하지 말라는 평가 경계를 추가하라.
5. 위 수정 뒤 출처 집계, 검증표 범위, 보고서 요약의 숫자와 범위 표현을 재대조하라. 특히 `report.md:10`의 21개 핵심 주장이 전체 보고서가 아니라 Google AI Edge 단일 분석의 주장이라는 범위를 문장 자체에서 분명히 하라.

## 최종 판정

**수정요청(changes-requested).** 본질적으로 검증 불가한 공급자 자기보고를 정직하게 공개한 점은 차단 사유가 아니다. 차단 사유는 (1) canonical 선별 inventory의 상태·집계 모순, (2) Fact-Checker 검증 범위가 보고서 핵심 주장 전체를 포괄하지 못한 점, (3) 최소 3개 배포 경로의 실질 비교 미완료, (4) 전력/총에너지 반대근거 누락이다.
