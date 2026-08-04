# 불확실성·반대근거·비교 제한

## 검증 상태와 해석 경계

이 섹션의 단일 검증 기준은 21개 핵심 주장에 대한 **확인 12건, 상충 0건, 미검증 9건**이다. 최종 `PASS`는 미검증 항목의 귀속과 제한을 공개했다는 게이트 판정일 뿐, 미검증 주장을 확인된 사실로 전환하지 않는다. [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증표의 집계 및 판정](verify/verification.md#판정-집계)

## 미검증 9건: 허용 표현과 금지 승격

아래 항목은 독립 확인이 완료되지 않았으므로, 원문이 제공하는 **공급자 발표·수치·예시**라는 귀속을 유지한다. 각 항목을 독립적으로 확인된 과거 배포 사실, 일반 성능치, 용량 보장 또는 품질 향상 사실로 승격하지 않는다. [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증표의 미검증 판정](verify/verification.md#판정-상세)

| 검증 ID | 허용 표현 | 금지 승격 | 원문 및 검증 문서 |
|---|---|---|---|
| V01 | Google의 2024년 발표상 Android·iOS·Web 지원 및 4개 모델이라는 인벤토리 | 독립적으로 확인된 2024년 당시의 정확한 모델 목록·배포 상태 | [2024 Google I/O 세션](https://www.youtube.com/watch?v=uWCX1h9YamI) · [검증 V01](verify/verification.md#v01) |
| V02 | Google의 2025-05-20 발표상 Gemma 3n 지원 수가 12개 초과라는 표현 | 독립적으로 확인된 당시 지원 모델 수 또는 릴리스 인벤토리 | [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증 V02](verify/verification.md#v02) |
| V05 | Google이 Gemma 3n을 ‘첫’ 멀티모달 SLM으로 소개했다는 표현 | 독립적으로 확립된 모델 계보·최초성 사실 | [Gemma 3n 발표](https://developers.googleblog.com/introducing-gemma-3n) · [검증 V05](verify/verification.md#v05) |
| V08 | Google이 int4 PTQ의 bf16 대비 `2.5–4×` 축소를 제시했다는 수치 | 일반적인 메모리 감소율 또는 모든 경로의 성능·용량 보장 | [Google AI Edge SLM 발표](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/) · [검증 V08](verify/verification.md#v08) |
| V12 | `2,585 tokens/s`는 제시된 prefill 측정 수치라는 표현 | 일반 생성 성능, end-to-end 성능 또는 다른 런타임과의 직접 우위 | [Gemma3-1B-IT 측정 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) · [검증 V12](verify/verification.md#v12) |
| V14 | Google의 Android RAG 예시가 1,000페이지와 1,000장 사진을 언급한다는 표현 | 일반적인 검색 가능 용량·처리량 보장 | [AI Edge RAG Android 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/rag/android) · [검증 V14](verify/verification.md#v14) |
| V16 | 현재 RAG 가이드가 존재한다는 표현 | RAG SDK가 2025-05-20에 Android에서 이용 가능했다는 과거 릴리스 사실 | [AI Edge RAG 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/rag) · [검증 V16](verify/verification.md#v16) |
| V18 | 현재 function calling 가이드가 존재한다는 표현 | function calling SDK가 2025-05-20에 Android에서 이용 가능했다는 과거 릴리스 사실 | [AI Edge Function Calling 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling) · [검증 V18](verify/verification.md#v18) |
| V20 | Google의 tool simulation 관련 효능 주장이라는 표현 | function calling 정확도 향상이 독립적으로 확인된 일반 효과라는 결론 | [AI Edge Function Calling 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling) · [검증 V20](verify/verification.md#v20) |

## 해소된 정의 상충

- **Gemma 3n의 E2B/E4B:** `E`는 총 파라미터 수가 아니라 **effective parameters(유효 파라미터)** 표기다. 따라서 E2B/E4B를 총 파라미터 `2B`/`4B` 모델로 바꾸어 쓰지 않는다. E2B도 표준 실행에서 5B 초과 총 파라미터를 로드한다는 정의가 확인되어, 이 표기 혼동은 해소되었다. [Gemma 3n 모델 개요 — Model parameters and effective parameters](https://ai.google.dev/gemma/docs/gemma-3n#model_parameters_and_effective_parameters) · [검증 V06](verify/verification.md#v06)
- **`2,585 tokens/s`의 의미:** 이 수치는 Samsung S24 Ultra, MediaPipe GPU, dynamic int4 QAT, context 2048의 **prefill** 조건에 한정한다. LiteRT-LM의 `2,531 tk/s`와 런타임 경로가 다르므로 두 수치를 병합하지 않으며, 이를 decode·TTFT·TPOT·end-to-end 또는 일반 생성 성능으로 표현하지 않는다. [Gemma3-1B-IT 측정 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) · [검증 V11](verify/verification.md#v11) · [검증 V12](verify/verification.md#v12)

## 반대근거와 직접 비교 금지

- MobileLLM(iPhone 13/ExecuTorch/FP16), MNN-LLM(Xiaomi 14/CPU·OpenCL), KIVI(A100), LLM in a Flash(M1/M2/RTX 4090), Gemma/AI Edge(S24 Ultra 등)의 수치는 모델, 장치, 정밀도, 런타임, 작업 단계가 이질적이므로 token/s·배율·메모리 수치를 단일 순위나 직접 우열로 만들지 않는다. [MobileLLM](https://arxiv.org/abs/2402.14905v2) · [MNN-LLM](https://arxiv.org/abs/2506.10443v1) · [KIVI](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash](https://arxiv.org/abs/2312.11514v3) · [Gemma3-1B-IT 측정 카드](https://huggingface.co/litert-community/Gemma3-1B-IT) · [검증 V11](verify/verification.md#v11) · [검증 V12](verify/verification.md#v12)
- MLPerf Inference v5.0의 방법론 발표와 결과 발표는 각각 설계·임계값 및 발표 수준의 결과 자료이므로, 이를 결합해 개별 시스템의 순위나 온디바이스 우열 근거로 쓰지 않는다. [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5) · [MLPerf Inference v5.0 결과](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results) · [검증 V21](verify/verification.md#v21)
- 제품 문서에서 확인되는 API 존재·현재 안내와 특정 시점의 가용성, 성능, 품질, 보안 효과는 서로 별개의 주장이다. 그러므로 현재 RAG/function calling 문서를 과거 SDK 출시 증명이나 일반 효능 근거로 사용하지 않는다. [AI Edge RAG 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/rag) · [AI Edge Function Calling 가이드](https://developers.google.com/edge/mediapipe/solutions/genai/function_calling) · [검증 V16](verify/verification.md#v16) · [검증 V18](verify/verification.md#v18) · [검증 V20](verify/verification.md#v20)
