# M-2026-004 · 4단계 Dedup·Relevance 판정

- 판정일: 2026-08-03
- 주제: 온디바이스 LLM 추론 최적화 동향
- canonical inventory: [sources.yaml](sources.yaml)

## 사전 위키 query와 재사용

`/work/llm-wiki/index.md` 및 온디바이스/모바일/추론/양자화/KV cache/MLPerf/Gemma/Apple 키워드 검색을 먼저 수행했다. 기존 위키는 agentic AI의 평가·안전성·memory/context 주제를 보유하지만, 이번 미션의 직접 근거로 재사용할 온디바이스 LLM 추론 원자료는 확인되지 않았다. `agent-evaluation`의 일반적인 측정 provenance 원칙은 해석 보조 맥락일 뿐 미션 출처 재사용으로 계상하지 않는다.

- 재사용률(전체 수집 inventory 기준): **0/19 (0.0%)**
- 선별 기준: 범위 적합성, 1차/공식성, 발행일 확인, 방법·측정 조건의 보존 여부, 기존/동일 자료와의 중복 여부.

## 선별 결과

`raw/sources.yaml`의 19개 레코드가 전체 inventory이며, 각 레코드의 `status`가 유일한 선별 상태다. 아래 모든 집계는 이 파일에서 `status: selected`인 동일한 12개 ID만 대상으로 산출했다. `excluded` 레코드는 원자료와 URL·수집일·제외 사유·대체 canonical 관계를 보존하되 후속 분석 집계에는 넣지 않는다.

| 구분 | 수 | 판정 |
|---|---:|---|
| 전체 수집 | 19 | 원자료 보존 |
| 선별 | 12 | 후속 Deep Analysis 대상 |
| 제외 | 7 | 중복·발행일 미확인·범위/근거 적합성 미달 |
| 재사용률 | 0/19 (0.0%) | 기존 위키 원자료 재사용 0건; 분모는 전체 수집 inventory |
| 최근성 | 11/12 (91.7%) | `selected` 중 2024년 이후 11건; 2024년 이후 ≥60% 정책 통과 |
| 출처 균형 | academic 5 · vendor 4 · research_org 3 | `selected` 12건의 유형 분배; 최소치 통과 |

### 선별 12건

| ID | 유형 | 점수 | 선별 근거/후속 사용 경계 |
|---|---|---:|---|
| `mobilellm-optimizing-sub-billion-parameter-language-models` | academic | 96 | sub-billion 모바일 모델 구조와 평가. 특정 모델군 결과로 한정. |
| `kivi-tuning-free-asymmetric-2bit-kv-cache-quantization` | academic | 97 | KV cache 2-bit 비대칭 양자화의 방법·조건·품질/throughput trade-off. |
| `elastic-on-device-llm-service` | academic | 94 | 스마트폰 SLO별 model/prompt elasticization. 기기·baseline 조건 외 일반화 금지. |
| `mnn-llm-generic-inference-engine-mobile-devices` | academic | 98 | mobile runtime의 DRAM-Flash·양자화·hardware-aware layout과 비교 평가. |
| `llm-in-a-flash-efficient-inference-limited-memory` | academic | 92 | 2023 예외: flash loading 계보의 직접 원전. 2024+ 자료와 비교 기준으로만 사용. |
| `mlcommons-mlperf-client-v1-0` | research_org | 91 | AI PC/client LLM benchmark의 측정 범위·지원 경로. 성능 우열의 단독 근거로 사용하지 않음. |
| `mlcommons-mlperf-inference-v5-0` | research_org | 83 | TTFT/TPOT·long-context benchmark 설계와 조건 해석. 주로 datacenter 문맥임을 표시. |
| `mlcommons-mlperf-inference-v5-0-results` | research_org | 80 | v5.0 결과·제출 생태계 보조 자료; methodology와 합쳐 단일 성능 주장으로 만들지 않음. |
| `google-ai-edge-on-device-slms` | vendor | 89 | 날짜가 명시된 Google AI Edge SLM/RAG/function calling 제품 자료. vendor 주장으로 표시. |
| `google-gemini-nano-aicore` | vendor | 88 | Android AICore/ML Kit GenAI API의 현재 배포 인터페이스. `last updated` 날짜 기반임을 표시. |
| `google-gemma-3n` | vendor | 90 | mobile-first multimodal open model 제품 발표. vendor 성능 주장은 독립 검증 필요. |
| `qualcomm-qai-appbuilder-wos` | vendor | 90 | Snapdragon AI PC NPU와 local OpenAI-compatible service의 구현 경로. 문서의 사용 약관/지원 플랫폼을 함께 확인. |

### 제외 7건

| ID | 사유 | canonical/replacement |
|---|---|---|
| `apple-llm-in-a-flash` | 동일 논문의 vendor landing page. versioned academic PDF보다 추가 방법·수치 근거가 없어 이중 계상하지 않음. | `llm-in-a-flash-efficient-inference-limited-memory` |
| `mlcommons-mlperf-client-v1-0-release` | 동일 MLPerf Client v1.0의 GitHub release metadata. benchmark 범위·지원 경로가 더 완전한 announcement를 canonical로 선정. | `mlcommons-mlperf-client-v1-0` |
| `google-ai-edge` | 페이지 발행일을 확인할 수 없어 핵심 근거에서 제외. | `google-ai-edge-on-device-slms` |
| `nist-ai-100-2e2023` | 적대적 ML taxonomy로서 이번 미션의 온디바이스 LLM 추론 최적화 직접 근거가 아니므로 범위에서 제외. | — |
| `tomshardware-amd-ryzen-8040-llm-benchmarks` | vendor 비교 주장의 2차 보도이며, grounded 비교에 필요한 1차 benchmark 방법론이 부족해 제외. | — |
| `tomshardware-ryzen-ai-300-local-llm-studio` | 기기 특화 2차 보도이나 비교 가능한 추론 분석에 필요한 1차 방법론이 부족해 제외. | — |
| `venturebeat-ibm-granite-4-nano-local-browser` | 1차 academic·vendor·MLCommons 자료가 미션 차원을 이미 포괄하므로 2차 뉴스 보도는 canonical set에서 제외. | — |

## 후속 단계 입력 계약

- Deep Analysis는 `raw/sources.yaml`의 `status: selected` 12건만 대상으로 한다.
- 모든 성능 수치는 원자료의 모델·정밀도·장치·prompt/sequence·batch와 baseline을 함께 보존한다.
- MLPerf v5.0은 on-device 단독 benchmark가 아니므로, client/edge 자료와 측정 조건이 다르면 직접 순위화하지 않는다.
- vendor 문서는 배포 인터페이스·지원 경로의 1차 근거로 사용하되, 성능/품질 주장은 논문 또는 독립 benchmark와 분리해 다룬다.
- 원자료 파일은 수정하지 않는다. 제외 항목도 provenance와 중복 판정의 추적성을 위해 보존한다.
