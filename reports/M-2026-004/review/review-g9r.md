# M-2026-004 G9R 독립 재검토

- 검토 단계: G9R Re-Verify
- 검토 대상: `report.md` 수정본
- 완료조건 기준: `SCOPE.md`
- 판정: **승인(approve)**

## 1. 직전 차단 사유 재검증

| 직전 차단 사유 | 재검증 결과 | 근거 |
|---|---|---|
| canonical 선별 inventory 불일치 | **해소** | `raw/sources.yaml`은 19건 중 `selected` 12건, `excluded` 7건이다. `raw/curated.md:14-25`의 전체·선별·제외·최근성·유형 집계와 일치하며, Apple landing page·MLPerf Client release·Google 무발행일 landing page·NIST·뉴스 3건은 모두 제외 사유가 기록돼 있다. |
| Fact-Checker가 Google 단일 분석만 검증 | **해소** | `verify/verification.md:1-6,43-85`가 Google 하위 V01–V21과 나머지 핵심 범위 X01–X17을 구분한다. 전체 38건은 확인 25·상충 0·미검증 13이며, `report.md:10`도 전체·Google 하위·비-Google 범위를 분리해 표기한다. |
| 대표 배포 경로 3개 실질 비교 미완료 | **해소** | `report.md:41-49`가 iPhone 13/ExecuTorch, Xiaomi 14/MNN-LLM, Snapdragon AI PC/QAI AppBuilder를 장치·OS, 모델·정밀도, runtime·가속기, prefill/decode·지표, 지원·재현 상태, 비교 경계의 공통 축으로 대조한다. 조건이 다른 수치를 순위화하지 않는다. |
| 전력과 총에너지의 반대근거 누락 | **해소** | `report.md:74`가 LLM in a Flash의 낮은 순간 power와 더 높은 total energy를 함께 제시하고, 정량 평가는 future work라는 한계 및 타 장치 일반화 금지를 명시한다. 원문 `raw/llm-in-a-flash-efficient-inference-limited-memory.md:94-105` 및 검증 X07과 일치한다. |

## 2. SCOPE 완료조건 대조

| SCOPE 완료조건 | 판정 | 재검토 근거 |
|---|---|---|
| llm-wiki 선조회, 재사용 항목·부족분·재사용률 기록 | 충족 | `raw/curated.md:7-12`에 선조회 범위, 직접 재사용 자료 부재, 부족분 판단, 재사용률 0/19가 기록돼 있다. |
| 공개 자료 10편 이상 및 URL·발행일/연도·수집일·유형·선별 상태 기록 | 충족 | `raw/sources.yaml` 19개 레코드 전부에 필수 메타데이터가 있고, 최종 선별은 12건이다. 자동 점검 결과 metadata 누락 0건이다. |
| academic 2+, vendor 2+, research_org 1+ 및 벤더 편향 방지 | 충족 | 선별 12건은 academic 5, vendor 4, research_org 3이다. 공급자 효능은 미검증으로 분리하고 논문·MLCommons 근거와 혼합해 보편적 결론으로 승격하지 않는다(`report.md:18-25,62-76`). |
| 양자화/압축, 메모리·KV, 런타임·하드웨어, 품질·성능·전력 평가와 성숙도·trade-off | 충족 | `report.md:12-25`가 8개 기술 분류와 연구/초기 성숙도를 제시한다. `report.md:27-39,53-60,62-76`은 품질 gate, TTFT/TPOT, memory, 전력·열, power/energy 경계를 함께 다룬다. |
| 대표 배포 경로 3개 이상 및 비교 가능/불가능 조건 구분 | 충족 | `report.md:41-49`의 3개 경로 공통 축 비교표가 비교 가능한 후속 조건과 직접 비교 불가 조건을 행별로 구분한다. |
| 핵심 주장별 1차 출처 및 Fact-Checker 판정 | 충족 | 보고서의 기술·수치·제품 경로 주장에 원문 또는 검증표 링크가 연결돼 있다. `verify/verification.md`는 전체 38개 핵심 주장에 확인/상충/미검증을 부여하고 독립 재현 한계를 별도 열에서 공개한다. |
| 출처 없는 사실 주장 금지, 수치 전제·불확실성·벤치마크 한계 | 충족 | 표본 감사 및 본문 추적성 점검에서 차단할 무출처 사실 주장을 찾지 못했다. 수치는 모델·정밀도·장치·runtime·길이·작업 단계 범위에 귀속되고, 이질 조건의 순위화가 금지돼 있다(`report.md:31-49,62-76`). |
| 독립 Reviewer PASS | 충족 | 본 재검토 판정은 PASS다. |
| Curator wiki 반영·reflection·재사용률 갱신 | 후속 단계 | 9단계 승인 뒤 수행할 10단계 조건으로 선취하지 않는다. |
| Deliver에서 Sam에게 요약·권고·검증 결과 제시 | 후속 단계 | 11단계 조건이다. |

## 3. 출처 정확성 표본 감사

1. **KIVI — 적합:** 외부 원문은 key per-channel/value per-token 2-bit 양자화와 full-precision residual cache, 제한된 저자 실험을 제시한다. `report.md:19,55`는 이를 모델별 품질 차이와 A100·합성 workload에 한정하며 보편적 모바일 기본값으로 승격하지 않는다.
2. **MobileLLM — 적합:** 외부 논문은 deep-and-thin, embedding sharing, GQA, immediate block-wise sharing을 제시한다. `report.md:18,47`은 iPhone 13·iOS 17.2.1·ExecuTorch/MPS·FP16·125M 계열·50회 평균이라는 측정 범위를 보존한다.
3. **Gemma 3n 정의 — 적합:** 공식 모델 개요는 E2B/E4B의 `E`가 effective parameters이며 E2B 표준 실행에서 5B 초과 파라미터가 로드된다고 명시한다. `report.md:24,31`의 정정과 일치한다.
4. **Gemma3-1B-IT 2,585 tk/s — 적합:** 모델 카드는 Samsung S24 Ultra, GPU, dynamic int4 QAT, context 2048의 prefill 2,585 tk/s를 제시한다. `report.md:32-33`은 decode·TTFT·TPOT·end-to-end로의 오해와 ‘한 페이지’ 일반화를 금지한다.
5. **MLPerf Inference v5.0 — 적합:** 공식 글은 offline token throughput, server TTFT/TPOT, ROUGE-L/EM, closed division의 FP16 reference 99% 기준을 구분한다. `report.md:25,37`은 이를 온디바이스 시스템 순위가 아닌 평가 언어로 제한한다.
6. **QAI AppBuilder — 적합하나 공급자 범위:** 공식 PDF는 Snapdragon AI PC NPU, `GenieContext`, `GenieAPIService`, localhost endpoint를 제시한다. `report.md:22-23,49,58`은 경로 존재만 채택하고 저지연·호환성·간편 배포 효능은 미검증으로 남긴다.
7. **LLM in a Flash 반대근거 — 적합:** 원문은 sparse 방식이 낮은 power에도 긴 생성시간으로 total energy가 더 높았다고 명시한다. `report.md:74,86`은 두 지표를 분리하고 해당 저자 비교 범위 밖 일반화를 금지한다.

## 4. 자동·구조 점검

- `raw/sources.yaml`: 19건 = selected 12 + excluded 7.
- selected 유형: academic 5, vendor 4, research_org 3.
- recent: 2024년 이후 11/12로 91.7%, 정책 60% 이상 충족.
- 19개 레코드의 URL·발행연도·수집일·유형·상태 누락: 0건.
- `report.md` 상대 링크 4종(`analysis/_index.md`, `raw/sources.yaml`, `synthesis/synthesis.md`, `verify/verification.md`)의 누락: 0건.
- 보고서 외부 링크: 71회, 고유 URL 17개. 표본 외부 원문 접근 및 주장 대조에서 차단 오류 없음.

## 최종 판정

**승인(approve).** 직전 FAIL의 네 차단 사유가 모두 구체적으로 해소됐다. 전체 핵심 주장 검증 범위와 하위 집계가 분리됐고, 3개 배포 경로의 공통 축 비교, power–total energy 반대근거, canonical inventory 정합성이 확인됐다. 미검증 13건은 공급자·저자 자기보고 또는 독립 snapshot/재현 부재로 정직하게 공개돼 있으며 확인 사실로 승격되지 않았으므로 그 자체를 실패 사유로 삼지 않는다.
