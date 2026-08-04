# M-2026-004 — 온디바이스 LLM 추론 최적화 동향

> 범위: Reader 분석 12건 및 Cross-Verify 결과를 재구성한 보고서다. 본문은 새 사실을 추가하지 않으며, 수치와 제품 상태는 명시된 모델·장치·정밀도·런타임·작업 단계 조건에서만 읽는다. [분석 인덱스](analysis/_index.md) · [검증표](verify/verification.md)

## 1. 요약

- 온디바이스 LLM 최적화는 가중치 압축, KV cache, DRAM–Flash 계층 배치, 런타임·가속기 경로를 함께 조정하는 **조건부 trade-off**다. 배포 판단은 평균 `tokens/s` 하나가 아니라 동일 장치·workload에서 측정한 TTFT, TPOT, peak memory, 과업 품질, 전력·열, 지원 행렬을 함께 보아야 한다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [KIVI](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5)
- 구조·가중치 압축, KV cache, DRAM–Flash, 요청 적응형 SLO 조정은 논문 또는 제한 실험 조건의 **연구** 단계로 분류했다. 런타임·하드웨어 가속, RAG·function calling, 모델·메모리 가변화, 평가 도구 경로는 구현·제품 경로가 있으나 지원·비교·운영 조건이 제한된 **초기** 단계로 분류했다. 이 분류는 보편적 성능 우위를 뜻하지 않는다. [기술 분류 근거](#2-기술-분류와-성숙도)
- 우선순위는 장치별 측정 harness 고정, 동일 모델의 저비트 weight PTQ pilot, 컨텍스트 길이별 KV cache 실험, 제한적 DRAM–Flash 실험 순이다. Android RAG/function calling은 내부 기능 pilot, AICore·Snapdragon NPU는 지원 행렬 기반 배포 후보, SLO-aware 선택과 Gemma 3n은 연구 또는 preview track으로 제한한다. [적용 후보](#4-적용-후보와-도입-전제)
- Cross-Verify의 **보고서 전체 핵심 주장 38건** 집계는 **확인 25건, 상충 0건, 미검증 13건**이며 최종 판정은 `PASS`다. 이 중 Google AI Edge 분석 하위 21건은 **확인 12·상충 0·미검증 9**이고, 나머지 범위 17건은 **확인 13·상충 0·미검증 4**이다. `PASS`는 미검증 항목의 귀속과 한계를 공개했다는 게이트 판정이지, 미검증 주장이 확인된 사실이 되었다는 뜻이 아니다. [전체·하위 범위 검증표](verify/verification.md)

## 2. 기술 분류와 성숙도

성숙도에서 **연구**는 논문·제안 수준이거나 독립 재현·운영 조건이 부족한 경우, **초기**는 구현물·제품 경로는 있으나 지원 범위·비교 조건·운영 안정성의 범위가 제한된 경우를 뜻한다. 성능·메모리·지연 수치는 각 장치, 정밀도, 런타임, 작업 단계 및 길이 조건 밖으로 일반화하지 않는다. [Synthesis의 성숙도 정의](synthesis/synthesis.md#1-판정-범위와-읽는-법)

| 분류 | 기술/메커니즘 | 성숙도 | 근거와 경계 |
|---|---|---|---|
| A. 모델 구조·가중치 압축 | sub-billion deep-and-thin, SwiGLU, embedding sharing, GQA, immediate block-wise sharing, W8A8 PTQ | 연구 | [MobileLLM](https://arxiv.org/abs/2402.14905v2)은 125M/350M 구조 조합과 iPhone 13·ExecuTorch·FP16 프로파일을 보고한다. 모바일 실측은 125M 계열 한 기기 조건이며, 다른 SoC·에너지·장문맥으로 일반화할 근거는 없다. |
| B. KV cache 양자화·관리 | key per-channel/value per-token 2-bit, full-precision residual window | 연구 | [KIVI](https://arxiv.org/abs/2402.02750v2)는 긴 생성의 KV cache 병목을 겨냥하지만 Falcon-7B에서 2-bit 품질 하락 가능성 및 4-bit 필요성을 함께 보인다. 효율 평가는 A100·합성 workload 조건이다. |
| C. DRAM–Flash 계층형 메모리 | flash weight loading, predictor/windowing, embedding·overflow KV Flash 배치 | 연구 | [LLM in a Flash](https://arxiv.org/abs/2312.11514v3)와 [MNN-LLM](https://arxiv.org/abs/2506.10443v1)은 제한 DRAM의 I/O·가중치·KV 배치를 다룬다. 전자는 half-memory·single-sequence·특정 SSD/backend, 후자는 Qwen2/Xiaomi 14의 대역폭·Flash 가정에 묶인다. |
| D. 요청 적응형 SLO 조정 | submodel 전환, prompt compression, TTFT/TPOT SLO 기반 선택 | 연구 | [ElastiLM](https://arxiv.org/abs/2409.09071v2)은 모델 크기와 prompt 길이 조절 설계 및 Redmi K60 관계 측정을 제시한다. 보존된 자료에서 핵심 평가표·baseline 정의가 누락되어 정확도·전환·메모리 우위는 저자 보고로만 사용한다. |
| E. 런타임·하드웨어 가속 | CPU/GPU reorder, heterogeneous balancing, mixed precision, LoRA, LiteRT, Qualcomm NPU API | 초기 | [MNN-LLM](https://arxiv.org/abs/2506.10443v1)의 Xiaomi 14 엔진 비교는 양자화 조건이 같지 않다. [Google AI Edge](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)와 [QAI AppBuilder](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)는 배포 경로를 제시하지만 독립 성능 검증은 아니다. |
| F. 온디바이스 기능 조합 | RAG, function calling, 멀티모달 SLM, AICore/ML Kit, local endpoint | 초기 | [AI Edge](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling)의 현재 문서·코드는 기능 경로를 보이고 실제 함수 실행은 앱 코드가 담당한다. [AICore](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) 및 [QAI](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)의 지원 기기·품질·호환성은 문서 범위를 넘어 확정하지 않는다. |
| G. 모델·메모리 가변화 | PLE, KVC sharing, activation quantization, MatFormer, E2B/E4B | 초기 | [Gemma 3n](https://developers.googleblog.com/introducing-gemma-3n)의 `E`는 총 파라미터가 아닌 effective parameter 정의다. PLE·속도·메모리·품질은 공급자 발표이며 재현 조건이 부족하다. |
| H. 성능 평가·비교 운영 | MLPerf Client 및 MLPerf Inference의 TTFT/TPOT·정확도 기준 | 초기 | [MLPerf Client](https://mlcommons.org/2025/07/mlperf-client-v1-0)와 [MLPerf Inference](https://mlcommons.org/2025/04/llm-inference-v5)는 공통 지표 언어를 제공한다. 방법론 발표와 [결과 발표](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results)는 시스템 순위 근거로 합치지 않는다. |

## 3. 근거·수치·평가 설계

### 정의와 조건이 확인된 항목

- Gemma 3n의 `E2B`/`E4B`에서 `E`는 총 파라미터 수가 아닌 **유효 파라미터** 표기다. E2B도 표준 실행에서 5B 초과 파라미터를 로드하므로 E2B/E4B를 총 2B/4B 모델로 축약하지 않는다. 이는 공식 용어 정의의 대조이며 장치별 성능·품질 재현 근거는 아니다. [Gemma 3n 모델 개요](https://ai.google.dev/gemma/docs/gemma-3n#model_parameters_and_effective_parameters) · [검증 V06](verify/verification.md)
- `2,585 tokens/s`는 [Gemma3-1B-IT 모델 카드](https://huggingface.co/litert-community/Gemma3-1B-IT)가 제시한 **Samsung S24 Ultra / MediaPipe GPU / dynamic int4 QAT / context 2048의 prefill** 수치다. 같은 카드의 LiteRT-LM 경로 `2,531 tk/s`와 합산·평균·대체하지 않으며, decode·TTFT·TPOT·end-to-end 응답 성능으로 바꾸어 해석하지 않는다. [검증 V11·V12](verify/verification.md)
- Google의 ‘한 페이지 1초 미만’ 표현은 페이지 토큰 수·전처리·prefill chunk가 정의되지 않아 검증된 성능 지표로 사용하지 않는다. [Google AI Edge 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증 V12](verify/verification.md)

### 측정 기준

TTFT는 prompt 처리 후 첫 출력 토큰까지의 지연, TPOT는 출력 토큰당 지연으로 구분한다. [ElastiLM](https://arxiv.org/abs/2409.09071v2)은 prefill/TTFT와 decode/TPOT를 분리하며, [MLPerf Inference](https://mlcommons.org/2025/04/llm-inference-v5)는 요약 ROUGE-L, 검색·문서 QA exact match 및 closed division의 FP16 reference 대비 99% 정확도 기준을 설명한다. MLPerf의 offline throughput 및 server TTFT·TPOT는 평가 언어이지 온디바이스 시스템 우열의 근거가 아니다. [MLPerf 결과 발표](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results)

장치별 measurement harness에는 모델 revision·tokenizer·정밀도·runtime·장치/OS, prompt/output/context 길이·batch/concurrency, warm-up·반복·실패/fallback, 메모리·전력·열, prefill/decode·TTFT·TPOT·peak memory·품질을 함께 보존한다. 동일 조건 안에서만 비교하며, 지연 개선은 품질 gate를 통과한 결과에서만 해석한다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1) · [Synthesis 적용 전제](synthesis/synthesis.md#3-적용-후보전제-조건)

### 대표 배포 경로: 공통 축 비교

아래 표는 서로 다른 경로를 **순위화하지 않고**, 장치/OS·모델·정밀도·런타임/가속기·작업 단계·측정 지표·지원/재현 상태라는 동일 축으로 대조한다. 이 세 경로는 모델, 장치, 양자화, workload와 측정 목적이 달라 경로 간 `tokens/s`·지연·전력 수치를 직접 비교할 수 없다. 같은 행에서 명시된 조건이 모두 일치하는 후속 내부 측정만 비교 후보가 된다.

| 대표 경로 | 장치/OS | 모델·정밀도 | 런타임/가속기 | prefill/decode·측정 지표 | 지원·재현 상태 | 비교 가능/불가능 경계 |
|---|---|---|---|---|---|---|
| 모바일 구조·런타임 측정 | iPhone 13 / iOS 17.2.1 | MobileLLM 125M 계열 / FP16 | ExecuTorch / MPS | 논문은 모바일 프로파일을 50회 평균 조건으로 보고한다. | 저자 실험 조건의 원문 일치만 확인됐으며 독립 재현은 현재 corpus에 없다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [X02](verify/verification.md) | 같은 모델 revision·길이·반복·기기 상태를 재현한 내부 측정과만 비교한다. Xiaomi, PC/NPU 또는 다른 정밀도 결과와 직접 비교하지 않는다. |
| 모바일 엔진 비교 | Xiaomi 14 | Qwen2 1.5B/7B, Llama3 8B / 엔진별 양자화 조건 상이 | CPU 4 threads 또는 GPU OpenCL / MNN-LLM | prompt 64/256/1024, decode 최대 16 조건의 prefill/decode 비교다. | 단일 기기·짧은 decode의 저자 결과다. MLC-LLM과는 대칭/비대칭 양자화가 달라 순수 runtime 재현·순위가 아니다. [MNN-LLM](https://arxiv.org/abs/2506.10443v1) · [X08–X09](verify/verification.md) | 동일 모델·양자화·prompt/decode 길이·가속기에서만 엔진 비교 후보가 된다. iPhone 또는 QAI 경로와 token/s 순위화는 불가하다. |
| PC 로컬 NPU 서비스 경로 | Snapdragon AI PC / Windows on Snapdragon 문서 경로 | 문서상 QNN 변환·Genie 맥락; 특정 비교 모델·정밀도·workload 실측은 제시되지 않음 | QAI AppBuilder / `GenieContext`, localhost `GenieAPIService` | 문서가 API·local endpoint 경로를 제시하지만 통일된 prefill/decode·지연·전력 측정값은 없다. | 경로 존재는 확인됐으나 실행·지원 행렬·성능의 독립 재현은 현재 corpus 밖이다. [QAI AppBuilder](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf) · [X16–X17](verify/verification.md) | API/endpoint 존재만 모바일 두 논문의 측정 결과와 대조할 수 있다. 성능·호환성·배포 소요 시간은 동일 harness의 별도 pilot 없이는 비교 불가다. |

## 4. 적용 후보와 도입 전제

1. **장치별 harness를 먼저 고정한다.** 동일 workload에서 prefill/decode, TTFT/TPOT, peak memory, 정확도·과업 품질, 전력·열을 기록하고 모델 revision·정밀도·길이·동시성·기기 상태를 결과와 보존한다. MLPerf 자료는 지표의 분리를, MobileLLM/MNN은 장치·runtime 의존성을 보여 주는 자료로만 사용한다. [MLPerf Client](https://mlcommons.org/2025/07/mlperf-client-v1-0) · [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1)
2. **저비트 weight PTQ는 rollback 가능한 pilot으로 제한한다.** 동일 모델의 원본과 저비트 배포본을 품질 gate·memory·TTFT·TPOT으로 함께 측정한다. Google의 int4 `2.5–4×` 축소는 공급자 수치로만 남기며, weight-only 경로의 지연 개선은 확정하지 않는다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [AI Edge 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증 V08·V09](verify/verification.md)
3. **KV cache는 컨텍스트 길이별 별도 실험 축으로 운용한다.** attention 구조별 2/4/16-bit 기준선에서 context 길이·품질·peak memory·throughput을 같이 비교한다. KIVI의 2-bit 결과는 A100·합성 workload 및 모델별 품질 차이라는 조건을 벗어나 모바일 기본값으로 삼지 않는다. [KIVI](https://arxiv.org/abs/2402.02750v2)
4. **DRAM–Flash 계층 배치는 제한적 실험으로 검토한다.** 상주 weight·embedding·KV overflow·prefetch/window을 분리하고 storage throughput, cache eviction, first-token 비용, thermal/power, 동시 요청을 장치에서 확인한다. 스마트폰 4-bit 적용은 LLM in a Flash의 구현 결과가 아니라 함의이며, MNN 결과는 Qwen2/Xiaomi 14 가정에 한정한다. [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1)
5. **Android RAG/function calling은 내부 기능 pilot으로 제한한다.** RAG의 저장·청킹·검색 구성, function declaration/parser 및 앱 코드의 실제 실행 분리는 확인됐지만, allowlist·인자 검증·권한/실패 처리·오프라인 갱신·품질/지연 시험이 전제다. 발표 시점 SDK 가용성, 1,000페이지/사진, tool simulation 효능은 채택 효과로 쓰지 않는다. [RAG 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/rag) · [Function Calling 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling) · [검증 V14–V20](verify/verification.md)
6. **AICore와 Snapdragon NPU는 지원 행렬 기반 배포 후보로 분리한다.** OS/SoC/API·모델·정밀도별 지원, 라이선스·배포 산출물, local endpoint 오류·호환성을 먼저 확인한다. 문서상 API/변환/endpoint 경로가 존재한다는 사실과 저지연·비용·프라이버시·간편 배포 효과는 구분한다. [Gemini Nano/AICore](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) · [QAI AppBuilder](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)
7. **SLO-aware submodel/prompt 선택은 연구 pilot으로만 다룬다.** 실제 서비스의 절대 latency·품질·fallback 발생률·offline preparation cost를 고정 기준선과 비교하고, 보존된 평가 상세와 random fallback의 품질 영향이 불명확한 상태에서 운영 기본정책으로 채택하지 않는다. [ElastiLM](https://arxiv.org/abs/2409.09071v2)
8. **Gemma 3n은 기능 검증용 preview track으로 격리한다.** preview checkpoint의 text/vision 범위와 장치별 사용량을 확인해 기능 후보로 평가한다. ‘첫’ 멀티모달 SLM, 지원 모델 수, 메모리 감소 배율, 페이지 처리 시간은 공급자 발표·미검증 상태를 유지한다. [Gemma 3n](https://developers.googleblog.com/introducing-gemma-3n) · [검증 V02·V05·V08·V12](verify/verification.md)

## 5. 불확실성·반대근거·비교 제한

전체 미검증 13건은 당시 snapshot 부재, 독립 재현 없는 저자·공급자 성능/효능, 평가 상세가 빠진 발표 수치, 계보·마케팅 표현에 해당한다. 이 중 Google AI Edge 하위 미검증 9건(V01, V02, V05, V08, V12, V14, V16, V18, V20)은 발표일 인벤토리·릴리스 상태, 공급자 수치·효능, 또는 계보/분류 표현이다. 따라서 ‘Google 발표상’이라는 귀속을 유지하고, 독립적으로 확인된 과거 배포 사실·일반 성능치·용량 보장·품질 향상 사실로 승격하지 않는다. 비-Google 미검증(X11, X13, X15, X17)도 저자/공급자 보고 또는 발표 수치로만 남긴다. [전체·하위 범위 검증표](verify/verification.md)

| ID | 허용 표현 | 금지하는 승격 |
|---|---|---|
| V01/V02/V16/V18 | 발표상 모델 수·지원 또는 당시 가용성 | 독립 확인된 과거 릴리스 인벤토리·배포 상태 |
| V05 | Google이 ‘첫’으로 소개 | 확립된 모델 계보·최초성 사실 |
| V08/V12/V14/V20 | 공급자가 제시한 수치·예시·효능 | 일반 성능·용량 보장·정확도 향상 사실 |

Gemma E 표기 및 `2,585 tokens/s`는 해소된 정의 혼동이지만 여전히 조건을 유지한다. E2B/E4B는 유효 파라미터 표기이며, 2,585 tk/s는 S24 Ultra/MediaPipe GPU/dynamic int4 QAT/context 2048의 prefill 조건에서만 인용한다. [Gemma 정의](https://ai.google.dev/gemma/docs/gemma-3n#model_parameters_and_effective_parameters) · [Gemma3-1B-IT 모델 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) · [검증 V06·V11](verify/verification.md)

**전력과 총에너지의 반대근거:** [LLM in a Flash](https://arxiv.org/abs/2312.11514v3)의 sparse model 비교에서 저자들은 dense 유사 규모 모델보다 단위시간 **power**는 낮았으나, token 생성 시간이 길어져 **total energy**는 더 높았다고 서술했다. 정확한 power pattern의 체계적·정량 평가는 future work로 남겼다. 따라서 낮은 순간 전력을 낮은 요청당/작업당 에너지로 바꾸어 해석하지 않으며, 장치 pilot에서는 power(시간당 소비)와 total energy(시간 적분)를 별도로 기록해야 한다. 이 관찰은 해당 저자 비교 범위의 반대근거이며, 다른 모델·장치·runtime의 에너지 결과로 일반화하지 않는다. [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [검증 X07](verify/verification.md)

MobileLLM(iPhone 13/ExecuTorch/FP16), MNN-LLM(Xiaomi 14/CPU·OpenCL), KIVI(A100), LLM in a Flash(M1/M2/RTX 4090), Gemma/AI Edge(S24 Ultra 등)는 모델·정밀도·runtime·작업 단계가 이질적이다. token/s·배율·메모리를 단일 순위나 직접 우열로 만들지 않으며, MLPerf의 방법론 발표와 결과 발표도 시스템 순위 근거로 합치지 않는다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1) · [KIVI](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MLPerf Inference](https://mlcommons.org/2025/04/llm-inference-v5) · [MLPerf 결과](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results)

## 6. 결론과 의사결정 기준

온디바이스 최적화는 단일 성능 향상 기법이 아니라 조건부 trade-off다. 저비트 weight, KV cache, DRAM–Flash, 런타임/API 경로는 기준선·품질 gate·fallback/rollback을 갖춘 장치별 pilot을 통과할 때에만 확대한다. API 제공 사실과 장치 간 호환성·지연·품질·운영 효과도 분리해 판단한다. [KIVI](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1) · [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [AICore](https://ai.google.dev/gemini-api/docs/get-started/android_aicore)

| 결정 질문 | 채택 기준 | 보류·중단 기준 |
|---|---|---|
| 저비트 weight 경로 | 품질 gate 통과와 TTFT·TPOT·peak memory의 공동 측정 | 메모리 절감만 있고 지연·품질 손실을 수용 기준 안에서 설명하지 못함 |
| KV cache | 목표 context에서 정밀도별 기준선 대비 품질·memory·생성 성능 확인 | 특정 2-bit 결과를 모든 모델의 기본값으로 일반화해야만 효과가 성립 |
| DRAM–Flash | storage·eviction·first-token·power·total energy·열·동시 요청을 포함한 장치 목표 충족 | 제한 메모리 실험의 속도 또는 낮은 순간 power를 total energy·열·OS I/O 검증 없이 제품 기준으로 사용 |
| 런타임·가속기/API | 지원 행렬 및 장치별 기능·호환성·오류 처리 검증 | 공급자 문서 또는 한 기기 결과만으로 일반 배포 결정 |

위 기준은 평균 token/s가 아닌 공동 측정과 명시된 비교 경계를 적용하기 위한 운영 기준이다. [적용 후보](#4-적용-후보와-도입-전제) · [불확실성](#5-불확실성반대근거비교-제한)

## 7. 출처 목록과 추적성

### 원문 12건

1. [MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases](https://arxiv.org/abs/2402.14905v2) — arXiv
2. [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://arxiv.org/abs/2402.02750v2) — arXiv
3. [Elastic On-Device LLM Service](https://arxiv.org/abs/2409.09071v2) — arXiv
4. [MNN-LLM: A Generic Inference Engine for Fast Large Language Model Deployment on Mobile Devices](https://arxiv.org/abs/2506.10443v1) — arXiv
5. [LLM in a Flash: Efficient Large Language Model Inference with Limited Memory](https://arxiv.org/abs/2312.11514v3) — arXiv
6. [MLPerf Client v1.0](https://mlcommons.org/2025/07/mlperf-client-v1-0) — MLCommons
7. [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5) — MLCommons
8. [MLPerf Inference v5.0 Results](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results) — MLCommons
9. [On-device small language models with multimodality, RAG, and Function Calling](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling) — Google Developers Blog
10. [Gemini Nano](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) — Google AI for Developers
11. [Announcing Gemma 3n preview](https://developers.googleblog.com/introducing-gemma-3n) — Google Developers Blog
12. [QAI AppBuilder - WoS](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf) — Qualcomm

### 내부 산출물

- [수집 인벤토리](raw/sources.yaml)
- [Reader 분석 인덱스](analysis/_index.md)
- [Cross-Verify 검증표](verify/verification.md)
- [Synthesis](synthesis/synthesis.md)
