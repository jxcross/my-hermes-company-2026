# M-2026-004 Cross-Verify — 보고서 핵심 주장 전체 범위

- 검증 대상: `report.md` 및 Reader 분석 12건. V01–V21은 Google AI Edge 하위 범위이고, X01–X17은 Reviewer가 지적한 나머지 핵심 범위다.
- 검증일: 2026-08-03
- 근거 범위: 이 보완은 Kanban 지시대로 새 외부 조사를 하지 않고 현재 `raw/` 원문과 `analysis/` 원장만 대조했다. 원문 일치 여부는 확인할 수 있으나, 단일 논문의 저자 실험이나 공급자 문서의 효능을 제3자가 재현했는지는 별도 문제다.
- 판정 기준: 설계 정의·문서상 지원 경로·실험 조건을 Reader가 원문과 일치하게 옮겼으면 `확인`, 원문과 어긋나면 `상충`, 공급자/저자 효과 수치에 독립 재현이 없거나 현재 접근범위로 판단할 수 없으면 `미검증`으로 판정했다.

## A. Google AI Edge 하위 검증표

| ID | Reader 핵심 주장 | 판정 | 교차검증 근거 | 판단 및 제한 |
|---|---|---|---|---|
| V01 | 2024년 초기 지원은 Android·iOS·Web의 4개 모델이었다. | 미검증 (unverified) | [2024 Google I/O 세션](https://www.youtube.com/watch?v=uWCX1h9YamI) | 세 플랫폼은 나오나 정확히 4개라는 당시 독립 인벤토리를 현재 근거에서 확인하지 못했다. |
| V02 | 2025-05-20에 지원 모델이 12개 초과로 확대됐다. | 미검증 (unverified) | [LiteRT Community](https://huggingface.co/litert-community), [Gemma Family](https://huggingface.co/collections/litert-community/gemma-family) | 현재 규모는 확인되나 발표일 스냅샷이 아니다. |
| V03 | 지원 모델은 LiteRT Hugging Face Community에 호스팅된다. | 확인 (corroborated) | [LiteRT Community](https://huggingface.co/litert-community) | 독립 플랫폼에서 실제 저장소를 확인했다. |
| V04 | Gemma 3n은 Google AI Edge early preview로 제공됐다. | 확인 (corroborated) | [`gemma-3n-E4B-it-litert-preview`](https://huggingface.co/google/gemma-3n-E4B-it-litert-preview) | preview 저장소와 모델 카드가 존재한다. 게시자는 Google이다. |
| V05 | Gemma 3n은 Gemma의 첫 멀티모달 온디바이스 SLM이다. | 미검증 (unverified) | [Gemma 3n overview](https://ai.google.dev/gemma/docs/gemma-3n), [모델 페이지](https://deepmind.google/models/gemma/gemma-3n) | 멀티모달·온디바이스 지향은 확인되나 ‘첫’이라는 계보 표현은 독립 확립되지 않았다. |
| V06 | E2B·E4B의 E는 effective parameters이며 총 파라미터 수가 아니다. | 확인 (corroborated) | [Gemma 3n parameter definition](https://ai.google.dev/gemma/docs/gemma-3n#model_parameters_and_effective_parameters) | 공식 정의와 수정 Reader가 일치한다. 같은 조직의 권위 정의이며 제3자 재현은 아니다. |
| V07 | 설계는 텍스트·이미지·비디오·오디오를 다루나 preview checkpoint는 텍스트·이미지만 지원했다. | 확인 (corroborated) | [preview 모델 카드](https://huggingface.co/google/gemma-3n-E4B-it-litert-preview) | 카드가 설계 능력과 당시 checkpoint 범위를 구분한다. |
| V08 | int4 PTQ는 bf16 대비 정확히 2.5–4× 크기를 줄인다. | 미검증 (unverified) | [AI Edge Quantizer](https://github.com/google-ai-edge/ai-edge-quantizer), [LiteRT PTQ](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization) | 4-bit 지원은 확인되나 해당 배율의 독립 비교표가 없다. |
| V09 | 양자화는 크기·메모리를 낮추고 정수 경로에서는 지연을 개선할 수 있다. | 확인 (corroborated) | [AI Edge Quantizer](https://github.com/google-ai-edge/ai-edge-quantizer), [LiteRT PTQ](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_quantization) | 가능성 표현은 맞다. weight-only 경로까지 보편화하면 안 된다. |
| V10 | Gemma 3 1B dynamic int4 QAT artifact는 529MB다. | 확인 (corroborated) | [Gemma3-1B-IT 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) | 카드가 529MB를 명시한다. 공급자 관리 카드다. |
| V11 | 모바일 GPU prefill은 최대 2,585 tokens/s다. | 확인 (corroborated) | [Gemma3-1B-IT 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) | S24 Ultra·GPU·dynamic int4 QAT·context 2048 조건에서 확인했다. LiteRT-LM 2,531 tk/s와 구분해야 한다. |
| V12 | 2,585 tokens/s이므로 한 페이지를 1초 미만에 처리한다. | 미검증 (unverified) | [Gemma3-1B-IT 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) | 페이지 토큰 수·전처리·prefill chunk가 정의되지 않았다. |
| V13 | RAG는 가중치를 바꾸지 않고 외부 데이터를 문맥으로 연결하는 수단이 될 수 있다. | 확인 (corroborated) | [Fine-Tuning or Retrieval?](https://arxiv.org/html/2312.05934v3), [AI Edge RAG](https://developers.google.com/edge/mediapipe/solutions/genai/rag) | ‘수단이 될 수 있다’는 범위에서 확인했다. |
| V14 | 1,000페이지 또는 1,000장 사진에서 관련 조각을 찾을 수 있다. | 미검증 (unverified) | [Android RAG guide](https://developers.google.com/edge/mediapipe/solutions/genai/rag/android) | 샘플에 1,000페이지/사진 규모의 품질·지연 실험이 없다. |
| V15 | RAG SDK는 Android 온디바이스에서 저장·청킹·검색 구성을 바꿀 수 있다. | 확인 (corroborated) | [RAG guide](https://developers.google.com/edge/mediapipe/solutions/genai/rag), [샘플](https://github.com/google-ai-edge/ai-edge-apis/tree/main/examples/rag) | 문서·코드가 의존성, embedder, 저장소, chunking, retrieval 구성을 보인다. |
| V16 | RAG SDK는 정확히 2025-05-20 Android에서 이용 가능했다. | 미검증 (unverified) | [현재 RAG guide](https://developers.google.com/edge/mediapipe/solutions/genai/rag) | 현재 가용성은 확인되나 당시 독립 release snapshot이 없다. |
| V17 | Function Calling SDK는 선언·등록·파싱·앱 함수 실행 흐름을 지원한다. | 확인 (corroborated) | [Function Calling guide](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling), [Android guide](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling/android) | 모델은 호출을 제안하고 실제 실행은 앱 코드가 담당한다. |
| V18 | Function Calling SDK는 정확히 2025-05-20 Android에서 이용 가능했다. | 미검증 (unverified) | [현재 Function Calling guide](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling) | 현재 가용성은 확인되나 당시 독립 release snapshot이 없다. |
| V19 | Python tool simulation 구성요소가 합성 데이터 생성·평가용으로 존재한다. | 확인 (corroborated) | [AI Edge APIs](https://github.com/google-ai-edge/ai-edge-apis) | 공개 저장소 경로가 구성요소 존재를 뒷받침한다. |
| V20 | tool simulation이 온디바이스 function calling 정확도를 높인다. | 미검증 (unverified) | [Function Calling guide](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling), [AI Edge APIs](https://github.com/google-ai-edge/ai-edge-apis) | 기준선·데이터셋·지표·향상 폭·독립 실험이 없다. |
| V21 | 원 발표에는 정량 표·실험 설계·원시값 및 2,585 tk/s의 재현 조건이 빠져 있다. | 확인 (corroborated) | [원 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/), [조건이 있는 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) | 원문 부재와 별도 카드의 S24 Ultra·dynamic int4 QAT·context 2048 조건을 대조했다. |

### Google 하위 집계

- 확인(corroborated): **12건**
- 상충(conflicting): **0건**
- 미검증(unverified): **9건**
- 소계: **21건**

미검증 9건은 당시 inventory/release snapshot 부재, 공급자만 제시한 수치·효능, ‘첫’·‘한 페이지’ 같은 분류·마케팅 표현이다. 공급자 발표로 귀속해야 한다.

## B. 보고서 나머지 핵심 범위 검증표

아래 근거 위치는 허용된 현재 자료의 행 번호다. 원문 일치 확인과 효과의 독립 재현을 구분했다.

| ID | 보고서 핵심 주장 | 판정 | 근거 위치 | 독립성·접근범위 판단 |
|---|---|---|---|---|
| X01 | MobileLLM은 deep-and-thin, SwiGLU, embedding sharing, GQA 및 immediate block-wise sharing을 결합한다. | 확인 (corroborated) | [`analysis/mobilellm-...md:15-29`](../analysis/mobilellm-optimizing-sub-billion-parameter-language-models.md), [`raw/mobilellm-...md:287-295,441-519`](../raw/mobilellm-optimizing-sub-billion-parameter-language-models.md) | 논문의 구조 정의와 Reader가 일치한다. 독립 구현 검증은 없어 보편적 우월성까지 확인한 것은 아니다. |
| X02 | MobileLLM 모바일 측정은 iPhone 13·iOS 17.2.1·ExecuTorch·MPS·FP16, 125M 계열, 50회 평균 조건이다. | 확인 (corroborated) | [`analysis/mobilellm-...md:50,69-71`](../analysis/mobilellm-optimizing-sub-billion-parameter-language-models.md), [`raw/mobilellm-...md:721-747`](../raw/mobilellm-optimizing-sub-billion-parameter-language-models.md) | 장치·runtime·정밀도·반복 조건이 원문에 있다. 외부 재현은 없으므로 다른 SoC·에너지·장문맥에 일반화할 수 없다. |
| X03 | KIVI는 key per-channel/value per-token 양자화와 full-precision residual window를 쓰는 tuning-free KV-cache 방식이다. | 확인 (corroborated) | [`analysis/kivi-...md:20-30,47-50`](../analysis/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md), [`raw/kivi-...md:45-68`](../raw/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md) | 알고리즘 정의와 Reader가 일치한다. 보존 raw 중간 일부는 생략됐으나 해당 정의 구간은 포함한다. |
| X04 | KIVI 2-bit 품질은 모델별로 균일하지 않고 Falcon-7B는 큰 하락 가능성 때문에 4-bit가 필요할 수 있다. | 확인 (corroborated) | [`analysis/kivi-...md:51-53,81-84`](../analysis/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md), [`raw/kivi-...md:76-88,96`](../raw/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md) | Falcon-7B GSM8K 16bit/2bit/4bit `4.55/3.41/4.47` 등 반대근거가 있어 보고서의 조건부 표현이 정확하다. |
| X05 | KIVI의 batch·throughput 개선은 단일 A100 80GB, Llama-2-7B, ShareGPT 합성 workload의 저자 결과다. | 확인 (corroborated) | [`analysis/kivi-...md:54,71-76,82`](../analysis/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md), [`raw/kivi-...md:87-90`](../raw/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md) | 최대 4× batch 및 2.35–3.47× throughput의 조건을 확인했다. 효과 자체의 제3자 재현은 현재 범위에 없다. |
| X06 | LLM in a Flash의 지연 개선은 약 half-memory, single-sequence, 특정 M1/M2/RTX 4090 backend와 naive/hybrid 기준선에 묶인다. | 확인 (corroborated) | [`analysis/llm-in-a-flash-...md:34-36,55-66,91-101`](../analysis/llm-in-a-flash-efficient-inference-limited-memory.md), [`raw/llm-in-a-flash-...md:73-90,103-107`](../raw/llm-in-a-flash-efficient-inference-limited-memory.md) | OPT-6.7B CPU `3182→669ms`, GPU `2218→84ms`와 기준선 단서가 일치한다. 독립 재현은 없고 raw 중간 일부가 생략됐다. |
| X07 | LLM in a Flash sparse 방식은 순간 전력은 낮았지만 생성 시간이 길어 총에너지는 더 높았다. | 확인 (corroborated) | [`analysis/llm-in-a-flash-...md:89-95`](../analysis/llm-in-a-flash-efficient-inference-limited-memory.md), [`raw/llm-in-a-flash-...md:94-105`](../raw/llm-in-a-flash-efficient-inference-limited-memory.md) | 원문이 power와 total energy의 반대 방향을 명시한다. 정량 전력 평가는 저자도 future work로 남겼다. |
| X08 | MNN-LLM 비교는 Xiaomi 14, Qwen2 1.5B/7B·Llama3 8B, CPU 4 threads/GPU OpenCL, prompt 64/256/1024·decode 최대 16 조건이다. | 확인 (corroborated) | [`analysis/mnn-...md:49-54,72-80`](../analysis/mnn-llm-generic-inference-engine-mobile-devices.md), [`raw/mnn-...md:75-78`](../raw/mnn-llm-generic-inference-engine-mobile-devices.md) | 단일 기기·짧은 decode 범위를 확인했다. 저자 token/s를 다른 장치로 일반화할 독립 자료는 없다. |
| X09 | MNN-LLM 대 MLC-LLM 수치는 대칭/비대칭 양자화 조건이 달라 순수 runtime 우열로 직접 비교할 수 없다. | 확인 (corroborated) | [`analysis/mnn-...md:51-54,77-79`](../analysis/mnn-llm-generic-inference-engine-mobile-devices.md), [`raw/mnn-...md:76-78`](../raw/mnn-llm-generic-inference-engine-mobile-devices.md) | 논문 자체가 MLC-LLM에는 대칭, 경쟁 엔진에는 비대칭 모델을 썼다고 밝힌다. 보고서의 직접 순위화 금지가 정확하다. |
| X10 | ElastiLM은 SLO를 full-LLM latency 대비 `<ζTTFT, ζTPOT>`로 정의하고 prompt·submodel을 함께 선택한다. | 확인 (corroborated) | [`analysis/elastic-...md:19-29,49-69`](../analysis/elastic-on-device-llm-service.md), [`raw/elastic-...md:22-35,71-73`](../raw/elastic-on-device-llm-service.md) | 설계 정의·흐름이 일치한다. 절대 ms SLO나 운영 보장을 뜻하지 않는다. |
| X11 | ElastiLM은 SLO 충족 조건에서 절대 정확도 최대 14.83%p·평균 10.45%p 향상, 1% 미만 전환 overhead 등을 달성한다. | 미검증 (unverified) | [`analysis/elastic-...md:31-32,71-85`](../analysis/elastic-on-device-llm-service.md), [`raw/elastic-...md:36-37`](../raw/elastic-on-device-llm-service.md) | 접근 raw에서 평가표·7 baseline 정의·분산·전체 기기 조건이 생략됐고 독립 재현도 없다. 보고서는 저자 보고로 제한했다. |
| X12 | MLPerf Inference v5.0은 offline token throughput, server TTFT·TPOT, ROUGE-L/EM, FP16 reference 99% 기준을 구분한다. | 확인 (corroborated) | [`analysis/mlcommons-mlperf-inference-v5-0.md:21-28,35-60`](../analysis/mlcommons-mlperf-inference-v5-0.md), [`raw/mlcommons-mlperf-inference-v5-0.md:35-43,53-55`](../raw/mlcommons-mlperf-inference-v5-0.md) | 지표·임계값이 설계문에 명시돼 있다. 같은 기관의 권위 정의 확인이며 조직적으로 독립된 검증은 아니다. |
| X13 | MLPerf v5.0 결과의 Llama 2 70B 중앙 2×·최고 3.3× 개선은 일반 시스템 성능 향상으로 재현됐다. | 미검증 (unverified) | [`analysis/mlcommons-mlperf-inference-v5-0-results.md:20-34,40-44,64-71`](../analysis/mlcommons-mlperf-inference-v5-0-results.md), [`raw/mlcommons-mlperf-inference-v5-0-results.md:9-11`](../raw/mlcommons-mlperf-inference-v5-0-results.md) | 발표문에 절대 점수·표본·동일성 조건·시스템 설정이 없다. 보고서는 이 수치를 순위 근거로 쓰지 않았다. |
| X14 | AICore는 Android 시스템 서비스이고 ML Kit GenAI API가 그 위에서 Gemini Nano 기능을 노출한다. | 확인 (corroborated) | [`analysis/google-gemini-nano-aicore.md:17-23,41-52`](../analysis/google-gemini-nano-aicore.md), [`raw/google-gemini-nano-aicore.md:8609-8626,8647-8663`](../raw/google-gemini-nano-aicore.md) | 제품 경로·아키텍처 역할은 공식 문서와 일치한다. 공급자 문서이므로 운영 효과의 독립 검증은 아니다. |
| X15 | AICore 경로가 일반적으로 낮은 지연·비용 절감·프라이버시 개선을 보장한다. | 미검증 (unverified) | [`analysis/google-gemini-nano-aicore.md:34-38,49-60`](../analysis/google-gemini-nano-aicore.md), [`raw/google-gemini-nano-aicore.md:8614-8617,8666-8715`](../raw/google-gemini-nano-aicore.md) | 기기·모델·지표·비교 기준·정량 결과가 없다. 보고서는 API 존재와 효과를 분리한다. |
| X16 | QAI AppBuilder는 `GenieContext`와 localhost `GenieAPIService`로 Snapdragon AI PC 로컬 NPU LLM 경로를 제시한다. | 확인 (corroborated) | [`analysis/qualcomm-qai-appbuilder-wos.md:23-25,39-46`](../analysis/qualcomm-qai-appbuilder-wos.md), [`raw/qualcomm-qai-appbuilder-wos.md:9-19`](../raw/qualcomm-qai-appbuilder-wos.md) | API 코드와 `http://localhost:8910/v1` 예로 경로 존재를 확인했다. 저장소 실행·지원 행렬은 현재 범위 밖이다. |
| X17 | QAI AppBuilder가 ultra-low latency, 보장된 privacy, 무수정 호환성 및 통상 2시간 내 배포를 제공한다. | 미검증 (unverified) | [`analysis/qualcomm-qai-appbuilder-wos.md:15-37,69-82`](../analysis/qualcomm-qai-appbuilder-wos.md), [`raw/qualcomm-qai-appbuilder-wos.md:5-11,39-43`](../raw/qualcomm-qai-appbuilder-wos.md) | 성능 표·장비·모델·반복·호환 endpoint 범위가 없고 문서는 `AS IS`라고 고지한다. 보고서는 효과를 채택 근거로 사용하지 않았다. |

### 비-Google 추가 범위 집계

- 확인(corroborated): **13건**
- 상충(conflicting): **0건**
- 미검증(unverified): **4건**
- 소계: **17건**

미검증 X11·X13·X15·X17은 각각 논문 보존본에서 평가 상세가 빠진 저자 수치, 결과 발표문의 분모 없는 상대 수치, Google/Qualcomm 공급자 효능 주장이다. 현재 허용 corpus에는 독립 재현·제3자 측정이 없어 본질적으로 독립 확인할 수 없으며, 보고서는 이를 저자/공급자 주장으로 제한하거나 채택 근거에서 제외했다.

## C. 전체 집계 및 판정

- 확인(corroborated): **25건**
- 상충(conflicting): **0건**
- 미검증(unverified): **13건**
- 총계: **38건**
- Google 하위 집계: **확인 12 / 상충 0 / 미검증 9 / 총 21**
- 비-Google 추가 집계: **확인 13 / 상충 0 / 미검증 4 / 총 17**

독립 검증 가능한 정의·지원 경로·원문 조건은 모두 현재 raw와 대조했다. 잔여 미검증 13건은 당시 snapshot 부재, 독립 재현 없는 저자/공급자 성능·효능, 평가 상세가 빠진 발표 수치, 계보·마케팅 표현이다. 미검증을 확인 사실로 승격하지 않고 보고서의 사용 제한을 명시했으므로 미해소 상충은 없다.

## Reader 유지·보완 조건

1. 보고서의 Cross-Verify 집계는 Google 단일 분석의 21건과 전체 38건을 구분해 표기해야 한다.
2. MobileLLM·KIVI·LLM in a Flash·MNN의 수치는 각각 iPhone 13/A100/M1·M2·RTX 4090/Xiaomi 14 조건의 저자 결과이며 독립 재현치가 아님을 유지한다.
3. LLM in a Flash의 순간 power 감소와 total energy 증가를 함께 적고 power와 energy를 혼용하지 않는다.
4. ElastiLM 14.83%p/10.45%p, MLPerf 2×/3.3×, AICore/QAI 효능은 미검증 상태로 유지하고 일반 성능 보장으로 쓰지 않는다.
5. MNN 대 MLC-LLM은 양자화 조건이 달라 runtime 순위로 사용하지 않는다.
6. AICore/QAI는 문서상 지원 경로 존재만 확인됐으며 장치·OS·모델·정밀도별 실제 지원과 성능은 별도 pilot 전제다.

## 최종 판정

**PASS.** 전체 38건 중 확인 25건, 상충 0건, 미검증 13건이다. 현재 corpus에서 독립 확인 가능한 정의·경로·조건은 모두 대조했고, 잔여 미검증은 독립 snapshot/재현/평가 상세가 없는 저자·공급자 주장이라는 본질적 한계를 공개했다. 이 PASS는 미검증 효과의 사실성을 승인하는 것이 아니라 불확실성과 사용 제한을 정직하게 보존했다는 게이트 판정이다.
