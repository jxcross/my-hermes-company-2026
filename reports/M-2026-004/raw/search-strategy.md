# M-2026-004 — 검색 전략

- 작성일: 2026-08-03
- 단계: Search Strategy (원문 수집·분석·선정 판정은 이 단계 범위 밖)
- 주제: 온디바이스 LLM 추론 최적화 동향
- 기준일: 2026-08-03
- 우선순위: 공개 1차 자료(논문·공식 런타임/하드웨어 문서·독립 벤치마크) → 표준 → 뉴스(발견 보조만)

## 적용 범위·수집 정책

- 범위: 스마트폰·PC·엣지 장치에서의 저비트 양자화/압축, KV cache·메모리, 런타임·컴파일러·하드웨어 가속, 지연시간·메모리·전력·품질 평가.
- 제외: 클라우드 전용 서빙, 학습/파인튜닝 전용 기법, 장치·정밀도·모델·측정 조건을 확인할 수 없는 성능 주장.
- 최근성: 2024년 이후 자료가 최종 `selected`의 60% 이상. 2021년 이전은 `seminal: true`인 원전 외에는 후보에서 제외.
- 최종 목표: 12–15건(최소 10건); academic 2+ / vendor 2+ / research_org 1+를 충족하도록 수집한다.
- 검색 결과·미러·재게시물은 원문 URL을 찾기 위한 보조 수단이며 별도 원자료로 보존하지 않는다.
- 수집 단계는 각 URL의 원문 날짜·접근성·열람 버전을 재검증한다. 확인 실패 시 `raw/sources.yaml`에는 `status: excluded`와 사유를 남긴다.

## 검색식

| ID | 검색식 | 우선 대상 | 목적 |
|---|---|---|---|
| Q1 | `site:arxiv.org/abs ("on-device LLM" OR "mobile LLM") (inference OR deployment) after:2023-12-31` | academic | 모바일/엣지 실제 배포·런타임 |
| Q2 | `site:arxiv.org/abs ("KV cache" OR "KV-cache") quantization LLM after:2023-12-31` | academic | KV cache 메모리·대역폭 최적화 |
| Q3 | `site:arxiv.org/abs LLM (quantization OR compression) (mobile OR edge OR "on-device") after:2023-12-31` | academic | 저비트 양자화·압축의 장치 연결성 |
| Q4 | `site:arxiv.org/abs "limited memory" "large language model inference"` | academic | DRAM/Flash·weight-memory 경로 |
| Q5 | `site:machinelearning.apple.com LLM inference (memory OR flash OR quantization)` | vendor | Apple 장치 메모리·가속 연구 |
| Q6 | `site:ai.google.dev/edge ("LLM Inference" OR "on-device")` | vendor | Google AI Edge/MediaPipe/LiteRT 런타임 |
| Q7 | `site:ai.google.dev "Gemini Nano" "on-device"` | vendor | Android AICore·NPU 배포 경로 |
| Q8 | `site:docs.qualcomm.com (LLM OR GenieContext) (NPU OR Snapdragon)` | vendor | Qualcomm NPU/AI PC 런타임·배포 |
| Q9 | `site:mlcommons.org ("MLPerf Client" OR "MLPerf Mobile") LLM` | research_org | 독립적 클라이언트 성능 측정 조건·결과 |
| Q10 | `site:nist.gov OR site:nvlpubs.nist.gov (quantization OR "edge devices") LLM inference` | standards | 저정밀·에너지·배포 위험 관련 기준 보강 |
| Q11 | `("on-device LLM" OR "mobile LLM") (latency OR memory OR power) benchmark 2024..2026` | academic/research_org | 전력·지연·메모리 측정 후보 확장 |
| Q12 | `("LLM runtime" OR "LLM inference engine") (Android OR iOS OR "AI PC" OR edge) 2024..2026` | vendor/academic | 세 배포 경로별 런타임 후보 확장 |

## 1차 수집 후보

아래는 검색 결과에서 URL·제목·연도를 확인한 공개 원문 후보이다. `발행 연도`는 검색 결과 또는 원문이 보인 연도이며, Collection 단계에서 원문 화면의 정확한 날짜와 접근 가능 여부를 재검증한다. 아직 원문을 내려받거나 `sources.yaml`을 작성하지 않았다.

| 우선 | 예상 원문 파일명 | URL | 확인 연도 | 정규화 출처유형 | 검색식 | 커버 영역 | 상태/수집 시 확인 |
|---:|---|---|---:|---|---|---|---|
| 1 | `mobilellm-optimizing-sub-billion-parameter-language-models` | https://arxiv.org/abs/2402.14905 | 2024 | academic | Q1 | 소형 모델 설계·온디바이스 사용 | 수집 대기; ICML 2024·열람 버전 보존 |
| 2 | `kivi-tuning-free-asymmetric-2bit-kv-cache-quantization` | https://arxiv.org/abs/2402.02750 | 2024 | academic | Q2 | 2-bit KV cache 양자화 | 수집 대기; 장치별 측정 조건 유무 표시 |
| 3 | `elastic-on-device-llm-service` | https://arxiv.org/abs/2409.09071 | 2024 | academic | Q1 | 온디바이스 서비스·자원 적응 | 수집 대기; MobiCom 2025 표기와 최초 게시일 분리 기록 |
| 4 | `mnn-llm-generic-inference-engine-mobile-devices` | https://arxiv.org/abs/2506.10443 | 2025 | academic | Q1 | 모바일 추론 엔진 | 수집 대기; 원문이 표기한 MMAsia 2024/2025 arXiv 날짜 모두 보존 |
| 5 | `llm-in-a-flash-efficient-inference-limited-memory` | https://arxiv.org/abs/2312.11514 | 2024 | academic | Q4 | Flash-DRAM weight-memory 최적화 | 수집 대기; ACL 2024 출판일과 arXiv 최초 제출일을 구분 |
| 6 | `apple-llm-in-a-flash` | https://machinelearning.apple.com/research/efficient-large-language | 2024 | vendor | Q5 | 공식 연구 원문·제한 DRAM/Flash | 수집 대기; Apple 페이지의 2024-08 표기 보존 |
| 7 | `google-ai-edge-on-device-llms` | https://ai.google.dev/edge | 2025 | vendor | Q6 | Android/iOS/Web/embedded 배포 스택 | 수집 대기; 페이지 내 2025-05-20 항목과 페이지 갱신일 구분 |
| 8 | `google-gemini-nano-aicore` | https://ai.google.dev/gemini-api/docs/get-started/android_aicore | 미확인 | vendor | Q7 | Android AICore·온디바이스 추론 | 수집 대기; 원문 발행일 없으면 `excluded` 또는 보조 문서 처리 |
| 9 | `google-gemma-3n-mobile-first` | https://developers.googleblog.com/introducing-gemma-3n | 2025 | vendor | Q7 | 모바일 우선 모델·하드웨어 협업 | 수집 대기; 게시일·성능 수치의 장치 조건 기록 |
| 10 | `qualcomm-qai-appbuilder-wos` | https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf | 2025 | vendor | Q8 | Snapdragon AI PC NPU·GenieContext | 수집 대기; 문서 revision date 2025-10과 공개 접근성 확인 |
| 11 | `mlcommons-mlperf-client-v1-0` | https://mlcommons.org/2025/07/mlperf-client-v1-0 | 2025 | research_org | Q9 | AI PC/클라이언트 LLM 벤치마크 | 수집 대기; 2025-07-30 게시일·측정 정의 보존 |
| 12 | `mlcommons-mlperf-inference-v5-0` | https://mlcommons.org/2025/04/llm-inference-v5 | 2025 | research_org | Q9 | LLM 추론 측정 범위·저지연 시나리오 | 수집 대기; edge/client 직접 적용 가능 범위 표시 |
| 13 | `nist-ai-100-2-adversarial-machine-learning-taxonomy` | https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2023.pdf | 2024 | standards | Q10 | 양자화·엣지 배포의 정의/위험 보강 | 수집 대기; 2024 판본·LLM 최적화 직접성 제한 표시 |

## 위키 선조회 결과·재사용 지시

- `/work/llm-wiki/SCHEMA.md`, `index.md`, `log.md`를 읽고 `on-device`, `edge LLM`, `mobile LLM`, `inference optimization`, `quantization`, `KV cache`를 전수 검색했다.
- 기존 위키는 agentic AI 업무 적용·안전성 범위이며, 이번 주제의 직접 원자료·개념 페이지는 확인되지 않았다. 검색된 `KV cache` 언급은 에이전트 리소스 고갈의 passing mention이므로 재사용하지 않는다.
- 따라서 이번 전략의 직접 재사용 후보는 0건이며, Collection은 위 후보의 새 원문을 별도 사본으로 보존한다.

## 수집 실행 순서

1. academic 후보 1–5의 arXiv abstract와 공개 PDF/HTML을 수집한다. 최초 게시일, 실제 열람한 버전 URL, 논문에 명시된 모델·정밀도·장치·시퀀스 길이·측정값을 원문 그대로 보존한다.
2. vendor 후보 6–10을 수집한다. 날짜 없는 지속 갱신 문서는 날짜 미확인으로 표시하고 핵심 근거에는 넣지 않는다.
3. research_org 후보 11–12에서 측정 workload·모델·지연/전력·하드웨어 조건을 포함하는 원문을 보존한다. 특정 벤더 제출 결과만 인용하지 않도록 결과 방법론과 구분한다.
4. standards 후보 13은 보강 자료로만 수집한다. 온디바이스 LLM 최적화와의 직접 관련성이 낮으면 `excluded` 표시 후 Curator에 넘긴다.
5. 각 확보 원문을 `raw/<id>.md`로 보존하고 URL·발행일·수집일·출처유형·접근/날짜 상태를 기록한다. 그 후 동일 ID를 `raw/sources.yaml`에 `selected`/`failed`/`excluded`로 기록한다.
6. 중복 제거·관련성 최종 판정·성능 결과 해석은 Curator/Reader 단계의 업무이다. 이 단계에서는 미러·날짜 미확인·동일 논문의 벤더/학술 버전 가능성만 표시한다.

## 수집 후 선별 전 목표 분배

| source_type | 목표 후보 수 | 후보 |
|---|---:|---|
| academic | 5 | 1–5 |
| vendor | 5 | 6–10 |
| research_org | 2 | 11–12 |
| standards | 1 | 13 |
| news | 0 | 필요 시 발견 보조만 |

총 13건이다. 후보 8의 날짜가 원문에서 확인되지 않거나 후보 10이 공개적으로 접근 불가하면, Q6–Q8로 날짜가 명시된 대체 vendor 원문을 추가해 vendor 최소치를 유지한다.
