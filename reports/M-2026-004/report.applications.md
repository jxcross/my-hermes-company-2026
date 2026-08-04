# 적용 후보와 도입 전제

> 이 섹션은 수집·검증된 자료를 바탕으로 한 **내부 pilot 후보의 우선순위**다. 아래의 측정·품질·운영 효과는 도입 효과의 확정값이 아니라, 해당 장치·모델·런타임 조합에서 확인해야 할 판정 항목이다. 서로 다른 장치·정밀도·workload의 수치를 순위나 일반 성능으로 합치지 않는다.

## 우선순위별 후보

### 1. 장치별 측정 harness를 먼저 고정

- **적용 범위:** 모든 후속 후보의 공통 전제다. 같은 workload에서 prefill/decode, TTFT/TPOT, peak memory, 정확도·과업 품질, 전력·열을 기록하는 내부 측정 harness를 먼저 만든다. MLPerf Inference는 서버 시나리오의 TTFT·TPOT 및 과업별 정확도 지표를 구분하며, MLPerf Client는 실행별 compute·memory readout과 결과 이력·CSV export 경로를 제시한다. [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5) · [MLPerf Client v1.0](https://mlcommons.org/2025/07/mlperf-client-v1-0)
- **도입 전제:** 모델 revision, 정밀도·양자화 방식, prompt·output 길이, batch/concurrency, warm-up·반복, 온도·전력 상태를 결과와 함께 보존한다. MobileLLM의 iPhone 13/ExecuTorch/FP16 프로파일 및 MNN-LLM의 특정 모바일 장치·엔진 조건은 장치·런타임 의존적 측정이 필요함을 보여 주는 자료로만 사용한다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1)
- **보류:** MLPerf 발표·도구만으로 온디바이스의 완결된 사양이나 기기 간 순위를 만들지 않는다. [MLPerf Client v1.0](https://mlcommons.org/2025/07/mlperf-client-v1-0) · [MLPerf Inference v5.0 결과](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results)

### 2. 기본 경로에서 저비트 weight PTQ pilot

- **적용 범위:** 동일 모델의 원본과 저비트 배포본을 짝지어, 품질 gate와 memory·TTFT·TPOT을 함께 측정하는 pilot으로 한정한다. MobileLLM은 125M/350M 모델에서 W8A8 PTQ 실험을 보고하며, Google AI Edge 발표는 모바일·웹용 변환 모델 및 온디바이스 SLM 경로를 소개한다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)
- **도입 전제:** 원본 모델과 rollback 절차를 보존하고, 모델·정밀도·runtime별 결과가 품질 gate를 통과할 때만 다음 배포 단계로 이동한다.
- **보류:** Google이 제시한 int4 관련 메모리 감소 배율은 일반 효과로 채택하지 않으며, weight-only 경로의 지연 개선 여부도 내부 측정 전에는 확정하지 않는다. [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)

### 3. KV cache를 컨텍스트 길이별 별도 실험 축으로 운용

- **적용 범위:** KIVI의 key per-channel/value per-token 비대칭 양자화와 full-precision residual window를 장문 생성의 메모리 후보 설계로만 평가한다. [KIVI](https://arxiv.org/abs/2402.02750v2)
- **도입 전제:** model-attention 구조별로 2/4/16-bit 기준선을 두고, context 길이·과업 품질·peak memory·throughput을 함께 비교한다.
- **보류:** KIVI의 2-bit 품질은 모든 모델에서 균일하지 않으며, 논문의 A100·합성 workload 결과를 모바일 배포 목표나 일반 효과로 전환하지 않는다. [KIVI](https://arxiv.org/abs/2402.02750v2)

### 4. DRAM–Flash 계층 배치를 제한적 실험으로 검토

- **적용 범위:** 상주 weight, embedding, KV overflow, prefetch/window을 분리하는 설계를 제한된 메모리 조건의 실험 후보로 둔다. [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1)
- **도입 전제:** storage throughput, cache eviction, first-token 비용, thermal/power, 동시 요청을 포함한 장치 실험을 수행한다.
- **보류:** LLM in a Flash의 스마트폰 4-bit 적용은 구현 성과가 아니라 저자 제안의 함의로 취급하고, MNN-LLM 결과도 해당 모델·Xiaomi 14·가정의 범위를 벗어나 일반화하지 않는다. [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1)

### 5. Android의 RAG/function calling은 내부 기능 pilot로 제한

- **제공 사실:** Google AI Edge 발표는 온디바이스 SLM의 RAG와 function calling 라이브러리를 소개한다. 기능 호출의 실제 실행은 앱의 책임으로 분리해 설계한다. [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)
- **도입 전제:** 함수 allowlist, 인자 검증, 권한·실패 처리, 오프라인 데이터 갱신, retrieval 품질·지연 시험을 갖춘 내부 pilot으로만 평가한다.
- **보류:** 페이지·사진 처리량이나 tool simulation 관련 공급자 예시는 제품 효과·정확도 보장으로 사용하지 않는다. 발표 시점의 SDK 가용성 역시 현재의 지원 범위로 단정하지 않는다. [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)

### 6. Android AICore 및 Snapdragon NPU는 지원 행렬 기반의 배포 후보로 분리

- **제공 사실:** Gemini Nano/AICore 문서는 ML Kit GenAI API와 AICore를 통한 Android 온디바이스 생성 AI의 고수준 인터페이스를 안내한다. QAI AppBuilder 문서는 Genie/GenieAPIService와 QNN 변환·로컬 OpenAI-compatible endpoint 경로를 제시한다. [Gemini Nano/AICore 문서](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) · [QAI AppBuilder 문서](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)
- **도입 전제:** OS/SoC/API·모델·정밀도별 지원 행렬, 라이선스·배포 산출물, local endpoint의 오류·호환 범위를 사전에 확인한다.
- **보류:** 저지연·비용·프라이버시·간편 배포는 공급자 서술과 API 제공 사실을 분리한다. 특히 QAI의 ‘약 2시간’ 및 ‘10줄’ 표현은 일반 온보딩 SLA나 운영 효과로 사용하지 않는다. [QAI AppBuilder 문서](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)

### 7. SLO-aware submodel/prompt 선택은 연구 pilot으로만 수행

- **적용 범위:** ElastiLM이 제시한 요청별 prompt/model 조합 선택과 TTFT·TPOT 분리 관점을 연구 pilot에서 검토한다. [ElastiLM](https://arxiv.org/abs/2409.09071v2)
- **도입 전제:** 실제 서비스의 절대 latency, 품질, fallback 발생률, offline preparation cost를 고정 기준선과 비교한다.
- **보류:** 보존된 평가 자료의 상세 기준과 random fallback의 품질 영향이 운영 정책을 뒷받침할 만큼 충분하지 않으므로, 기본 운영 정책으로 채택하지 않는다. [ElastiLM](https://arxiv.org/abs/2409.09071v2)

### 8. Gemma 3n은 기능 검증용 preview track으로 격리

- **제공 사실:** Google은 Gemma 3n을 preview로 소개하고, PLE에 따라 raw parameter count와 모바일에서의 메모리 표기를 구분한다. 따라서 E2B/E4B는 총 파라미터 수로 바꾸어 쓰지 않는다. [Gemma 3n 발표](https://developers.googleblog.com/introducing-gemma-3n)
- **도입 전제:** preview checkpoint의 text/vision 범위와 장치별 resource 사용량을 내부에서 확인한 뒤, 멀티모달·RAG 기능 후보로만 평가한다.
- **보류:** ‘첫’ 멀티모달 SLM, 지원 모델 수, 메모리 감소 배율, 페이지 처리 시간 및 token/s 수치는 공급자 발표의 조건부 표현으로만 남기며, 일반 성능·용량·제품화 효과로 승격하지 않는다. [Gemma 3n 발표](https://developers.googleblog.com/introducing-gemma-3n) · [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)

## 도입 판정 원칙

1. **API 제공 사실과 효과를 분리한다.** Android/AICore 및 Snapdragon 경로는 문서상 API·변환·endpoint가 제공되는 배포 후보라는 사실까지만 확정하고, latency·비용·프라이버시·호환성·운영 편의 효과는 지원 행렬과 내부 pilot 측정으로 판정한다. [Gemini Nano/AICore 문서](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) · [QAI AppBuilder 문서](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)
2. **성능 수치는 조건에 귀속한다.** TTFT·TPOT, memory, 품질, 전력·열은 모델·정밀도·runtime·입출력 길이·장치 조건을 함께 보존한 내부 결과로만 비교한다. [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5) · [MobileLLM](https://arxiv.org/abs/2402.14905v2)
3. **제품화 전에는 rollback과 제한을 유지한다.** 저비트·KV·계층 메모리·SLO 선택은 기능 및 성능의 보편적 개선을 전제하지 않고, 기준선·품질 gate·fallback/rollback을 갖춘 pilot 결과가 있을 때에만 확대한다. [KIVI](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [ElastiLM](https://arxiv.org/abs/2409.09071v2)
