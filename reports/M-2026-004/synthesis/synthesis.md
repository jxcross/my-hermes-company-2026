# M-2026-004 — Synthesis: 온디바이스 LLM 추론 최적화 동향

> 단계 7 Synthesis · 입력: Reader 분석 12건, `verify/verification.md` (G6R `VERDICT: PASS`)

## 1. 판정 범위와 읽는 법

- Cross-Verify의 단일 기준 상태는 **확인 12, 상충 0, 미검증 9**이다. 이는 `analysis/google-ai-edge-on-device-slms.md`의 21개 핵심 주장에 대한 판정이다. `PASS`는 미검증 항목의 귀속·제한을 공개한 게이트 판정이며, 미검증 주장이 확인된 사실이 되었다는 뜻은 아니다. [검증: `verify/verification.md`]
- 성숙도는 **연구**=논문/제안 수준이거나 독립 재현·운영 조건이 부족함, **초기**=구현물·제품 경로는 있으나 지원/비교/운영 안정성 범위가 제한됨, **실무**=현재 적용 가능한 도구·절차가 있고 조건을 명시해 내부 검증으로 운영할 수 있음으로 사용한다. 실무는 보편적 성능 우위를 뜻하지 않는다.
- 본 노트는 앞 단계의 주장을 새로 수집·검증하지 않고, 기술 분류·성숙도·적용 전제로 재구성한다. 성능 수치와 제품 상태는 각 Reader/검증표가 적은 장치·정밀도·런타임·길이 조건을 벗어나 일반화하지 않는다.

## 2. 기술 분류와 성숙도

| 분류 | 기술/메커니즘 | 성숙도 | 근거와 경계 | 추적 경로 |
|---|---|---|---|---|
| A. 모델 구조·가중치 압축 | sub-billion deep-and-thin, SwiGLU, embedding sharing, GQA, immediate block-wise sharing, W8A8 PTQ | 연구 | MobileLLM은 125M/350M 범위에서 구조 조합과 즉시 블록 공유의 평가를 제시하고 iPhone 13/ExecuTorch/FP16 프로파일도 보고한다. 그러나 모바일 실측은 125M 계열·한 기기 조건이며, 에너지·다른 SoC·장문맥 일반화 근거는 없다. | 분석 `mobilellm-optimizing-sub-billion-parameter-language-models` §§2–5 |
| B. KV cache 양자화·관리 | KIVI의 key per-channel/value per-token 2-bit 양자화, full-precision residual window | 연구 | KIVI는 긴 생성에서 KV cache 병목을 겨냥한 명시적 알고리즘·실험을 제공한다. Falcon-7B는 2-bit 품질 하락 가능성과 4-bit 필요성을 함께 보이므로, 2-bit를 보편적 기본값으로 승격할 수 없다. 효율 평가는 A100/합성 workload 조건이다. | 분석 `kivi-tuning-free-asymmetric-2bit-kv-cache-quantization` §§2–5 |
| C. DRAM–Flash 계층형 메모리 | flash weight loading, activation-sparsity predictor, windowing, row-column bundling; embedding/overflow KV Flash 배치 | 연구 | LLM in a Flash와 MNN-LLM은 제한 DRAM에서 I/O·가중치·KV 배치를 다룬다. 전자는 half-memory·single-sequence·특정 SSD/backend 조건, 후자는 Qwen2/Xiaomi 14의 대역폭·Flash 가정에 묶인다. MNN의 Flash KV 추정과 성능은 장기 열·전력·OS I/O 경합을 측정하지 않았다. | 분석 `llm-in-a-flash-efficient-inference-limited-memory` §§2–5; `mnn-llm-generic-inference-engine-mobile-devices` §§2–5 |
| D. 요청 적응형 SLO 조정 | submodel 전환, prompt compression, TTFT/TPOT SLO 기반 선택(ElastiLM) | 연구 | ElastiLM은 모델 크기와 프롬프트 길이를 함께 조절하는 설계 및 Redmi K60의 관계 측정을 제시한다. 그러나 핵심 평가표·baseline 정의가 보존 raw의 중간 생략 범위에 있어, 보고된 정확도/전환/메모리 우위는 저자 보고로만 사용한다. SLO도 full-model latency 대비 비율이지 절대 UX 예산은 아니다. | 분석 `elastic-on-device-llm-service` §§2–5 |
| E. 런타임·하드웨어 가속 | CPU/GPU data reorder·heterogeneous core balancing·mixed precision·LoRA, LiteRT 양자화, Qualcomm NPU API | 초기 | MNN-LLM은 Xiaomi 14에서 엔진별 prefill/decode 결과를 제시하지만 MLC-LLM 비교는 양자화가 대칭/비대칭으로 달라 동일조건 비교가 아니다. AI Edge/Qualcomm은 구현·배포 경로를 제공하나 제품 문서의 지연·호환·생산성 표현은 독립 성능 검증이 아니다. | 분석 `mnn-llm-generic-inference-engine-mobile-devices` §§3–5; `google-ai-edge-on-device-slms` §§2–5; `qualcomm-qai-appbuilder-wos` §§2–5; 검증 V09, V15, V17, V19 |
| F. 온디바이스 기능 조합 | RAG, function calling, 멀티모달 SLM, AICore/ML Kit API, OpenAI-compatible local endpoint | 초기 | Android AI Edge의 현재 RAG/function-calling 문서·코드는 확인되며, 실제 함수 실행은 앱 코드가 담당한다. Gemini Nano/AICore와 QAI AppBuilder는 시스템/API 경계를 제시하지만, 지원 기기·모달리티·안전·API 호환성·품질은 문서 범위를 넘어 확정할 수 없다. 발표 시점의 SDK 가용성은 미검증 상태다. | 분석 `google-ai-edge-on-device-slms` §§2–5; `google-gemini-nano-aicore` §§2–5; `qualcomm-qai-appbuilder-wos` §§2–5; 검증 V07, V15–V18 |
| G. 모델/메모리 가변화 | Gemma 3n PLE, KVC sharing, activation quantization, MatFormer 및 E2B/E4B 유효 파라미터 표기 | 초기 | Gemma 3n의 `E`는 총 파라미터가 아닌 effective parameter 정의로 확인됐다. PLE/속도/메모리/품질은 공급자 발표이며 재현 조건이 부족하다. 오디오 기능은 발표 당시 public implementation이 후속 예정이었고, 멀티모달 소개와 실제 preview checkpoint 범위를 구분해야 한다. | 분석 `google-gemma-3n` §§2–5; `google-ai-edge-on-device-slms` §§2–5; 검증 V04, V06, V07 |
| H. 성능 평가·비교 운영 | MLPerf Client v1.0의 PC/client LLM 도구 경로, MLPerf Inference v5.0의 TTFT/TPOT·정확도 기준·결과 생태계 | 초기 | MLPerf 문서는 공통 workload와 지표 언어를 제공한다. 그러나 Client 발표에는 상세 사양/결과가 없고, Inference 방법론 발표와 결과 발표는 시스템 순위 근거로 합치면 안 된다. MLPerf 405B/70B 자료는 온디바이스 실증이 아니라 비교 설계의 참조로 제한한다. | 분석 `mlcommons-mlperf-client-v1-0` §§2–7; `mlcommons-mlperf-inference-v5-0` §§2–5; `mlcommons-mlperf-inference-v5-0-results` §§2–6 |

## 3. 적용 후보·전제 조건

| 우선 | 후보 | 근거·전제 조건 | 보류/불확실성 |
|---:|---|---|---|
| 1 | **장치별 측정 harness를 먼저 고정**: prefill/decode, TTFT/TPOT, 메모리, 정확도/품질, 전력·열을 같은 workload로 기록 | MLPerf는 TTFT/TPOT·정확도 기준 분리를, MobileLLM/MNN은 기기·runtime 의존성을 보여 준다. 모델 revision, 정밀도/양자화, prompt·output 길이, batch/concurrency, warm-up·반복, 온도·전력 상태를 함께 보존한다. | MLPerf 발표문만으로 완결된 온디바이스 사양/순위를 만들 수 없다. 서로 다른 모델·기기·런타임 수치를 직접 순위화하지 않는다. |
| 2 | **기본 경로에서 저비트 weight PTQ pilot** | W8A8 MobileLLM과 AI Edge int4 경로는 저비트 배포의 후보를 제시한다. 동일 모델에서 품질 gate와 memory/TTFT/TPOT을 동시 측정하고 rollback 가능한 원본을 보존한다. | int4의 `2.5–4×` 감소는 미검증(V08)이며, weight-only 경로는 지연이 개선되지 않거나 악화될 수 있다(V09 제한). |
| 3 | **KV cache를 컨텍스트 길이별 별도 실험 축으로 운용** | KIVI의 비대칭 축/잔여 window는 장문 생성의 메모리 후보 설계를 제공한다. model-attention 구조별 2/4/16-bit 기준선, context 길이, task quality, peak memory, throughput을 함께 비교한다. | KIVI 2-bit 품질은 Falcon-7B에서 균일하지 않으며, A100·합성 workload 수치를 모바일 배포 목표로 쓰지 않는다. |
| 4 | **DRAM–Flash 계층 배치를 제한적 실험으로 검토** | LLM in a Flash와 MNN-LLM은 상주 weight, embedding, KV overflow, prefetch/window의 선택지를 제시한다. storage throughput·cache eviction·first-token 비용·thermal/power·동시 요청을 포함한 장치 실험을 한다. | LLM in a Flash의 스마트폰 4-bit 적용은 구현 결과가 아닌 함의이며 특수 kernel이 필요하다. MNN 수치는 Qwen2/Xiaomi 14 및 가정에 한정된다. |
| 5 | **Android의 RAG/function-calling은 내부 기능 pilot로 제한** | Android RAG의 on-device 저장소/chunk/retrieval 설정과 function declaration/parser/앱 실행 분리는 확인됐다(V15, V17). 함수 allowlist, 인자 검증, 권한·실패처리, 오프라인 데이터 갱신, retrieval 품질/지연 테스트를 전제한다. | 발표일(2025-05-20) 가용성은 미검증(V16, V18). 1,000페이지/사진 처리(V14)와 tool simulation 정확도 향상(V20)은 채택 효과 근거가 아니다. |
| 6 | **Android AICore 및 Snapdragon NPU는 지원 행렬 기반의 배포 후보로 분리** | AICore/ML Kit는 시스템 서비스·고수준 API 경계, QAI AppBuilder는 Genie/GenieAPIService·QNN 변환 경로를 제공한다. OS/SoC/API·모델·정밀도별 지원 행렬, 라이선스·배포 산출물, local endpoint의 오류/호환 범위를 사전 확인한다. | 두 문서의 저지연·비용/프라이버시·간편 배포 주장은 공급자 서술이고 재현 benchmark가 아니다. QAI의 2시간/10줄은 일반 온보딩 SLA로 사용하지 않는다. |
| 7 | **SLO-aware submodel/prompt 선택은 연구 pilot으로만 수행** | ElastiLM은 TTFT와 TPOT의 분리, 요청별 prompt/model 조합 선택의 필요성을 제시한다. 실제 서비스의 절대 latency·품질·fallback 발생률·offline preparation cost를 기준선과 비교한다. | 평가 상세가 보존 범위 밖이고, random fallback의 품질 영향이 불명이다. 현 운영 기본정책으로 채택하지 않는다. |
| 8 | **Gemma 3n은 기능 검증용 preview track으로 격리** | E2B/E4B가 유효 파라미터 표기임은 확인됐다(V06). preview checkpoint의 text/vision 범위와 장치별 사용량을 검증해 멀티모달/RAG 후보로 평가한다. | ‘첫’ 멀티모달 SLM(V05), 12개 초과 지원(V02), 2.5–4×(V08), 한 페이지 1초(V12)는 미검증이다. 2,585 tk/s는 S24 Ultra/MediaPipe GPU/dynamic int4 QAT/context 2048의 prefill 조건으로만 인용한다(V11). |

## 4. 상충·불확실성

### 해소된 정의 상충

1. **Gemma 3n E2B/E4B:** 기존의 총 파라미터 축약은 유효 파라미터 표기라는 공식 정의로 정정됐다. E2B도 표준 실행에서 5B 초과 총 파라미터를 로드하므로 총 파라미터 2B/4B 모델로 쓰지 않는다. [검증 V06]
2. **2,585 tokens/s:** 확인된 수치이나 prefill의 Samsung S24 Ultra/MediaPipe GPU/dynamic int4 QAT/context 2048 조건이다. LiteRT-LM 2,531 tk/s와 런타임 경로가 다르므로 병합하거나 일반 생성 성능으로 서술하지 않는다. [검증 V11]

### 미검증 9건의 상태 보존

| 성격 | ID | 허용 표현 | 금지하는 승격 |
|---|---|---|---|
| 발표일 인벤토리·릴리스 상태 | V01, V02, V16, V18 | Google 발표상/당시 발표문상 지원·가용성 | 독립 확인된 과거 배포 상태 |
| 공급자 수치·효능 | V08, V12, V14, V20 | 공급자 제시 수치·예시·효능 주장 | 일반 성능치·용량 보장·정확도 향상 사실 |
| 계보/분류 표현 | V05 | Google이 ‘첫’으로 소개 | 독립적으로 확립된 모델 계보 사실 |

### 교차자료 비교의 금지선

- MobileLLM(iPhone 13/ExecuTorch/FP16), MNN-LLM(Xiaomi 14/CPU·OpenCL), KIVI(A100), LLM in a Flash(M1/M2/RTX 4090), Gemma/AI Edge(S24 Ultra 등)는 모델·정밀도·작업 단계·장치가 달라 token/s·배율·메모리 수치를 단일 순위로 만들 수 없다.
- MLPerf 방법론/결과 자료는 동일 릴리스라도 하나는 설계·임계값, 하나는 발표 수준의 집계다. 개별 시스템 결과나 온디바이스 우열을 뒷받침하지 않는다.
- 제품 문서의 API 존재·현재 안내와, 특정 시점의 가용성·성능·품질·보안 효과는 별개의 주장이다.

## 5. Writer 인계용 경계

- 중심 결론은 (a) 온디바이스 최적화는 weight/KV/DRAM–Flash/런타임을 함께 다루는 조건부 trade-off이고, (b) 배포 선택은 평균 token/s가 아니라 TTFT·TPOT·peak memory·품질·전력/열·지원 행렬의 공동 측정으로 결정하며, (c) API 제품화는 존재하되 호환성과 운영 효과는 장치별 pilot이 필요하다는 수준으로 제한한다.
- KIVI의 2-bit, LLM in a Flash의 speedup, MNN-LLM의 엔진 배율, MobileLLM의 구조 우위는 각 저자·실험 조건에 귀속한다. 서로 다른 수치의 비교·합산·보편 최적화 결론을 피한다.
- Google 관련 미검증 항목(V01, V02, V05, V08, V12, V14, V16, V18, V20)은 반드시 ‘공급자 발표/미검증’ 상태로 남긴다. E2B/E4B를 총 파라미터로 바꾸지 않는다.

## 6. 추적성

- Reader: `analysis/_index.md` 및 자료별 분석 12건
- 검증 상태의 단일 기준: `verify/verification.md`
- 본 노트는 위 입력을 새로 검증하지 않고 분류·성숙도·적용 전제로 재구성했다.
