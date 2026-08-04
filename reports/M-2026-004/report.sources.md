# 출처 목록 및 방법·범위

## 범위와 방법

- 본 보고서는 Synthesis에 입력된 **Reader 분석 12건**을 대상으로 한다. 각 Reader 노트는 해당 보존 원문과 당시의 [`raw/sources.yaml`](raw/sources.yaml) 레코드에 근거하며, 분석 인덱스상 12건 모두 수용되었다. [Reader 분석 인덱스](analysis/_index.md)
- Cross-Verify의 단일 기준은 `google-ai-edge-on-device-slms`의 21개 핵심 주장에 대한 **확인 12건, 상충 0건, 미검증 9건**이다. 최종 **PASS**는 미검증 항목의 귀속과 제한을 공개했다는 게이트 판정이며, 미검증 주장을 확인된 사실로 바꾸지 않는다. [검증표](verify/verification.md#판정-집계) · [Synthesis의 판정 범위](synthesis/synthesis.md#1-판정-범위와-읽는-법)
- 인용은 원문 URL을 우선하고, 논문은 저자 보고·실험 조건에, 제품 문서·발표는 공급자 서술에 귀속한다. 수치와 제품 상태는 모델·장치·정밀도·런타임·작업 단계·입출력 길이 등의 조건 밖으로 일반화하지 않는다.
- 서로 다른 모델·장치·정밀도·런타임·작업 단계의 token/s, 배율, 메모리 수치는 단일 순위나 직접 우열로 비교하지 않는다. MLPerf의 방법론 발표와 결과 발표도 역할이 달라 개별 시스템 순위 또는 온디바이스 우열의 단일 근거로 병합하지 않는다. [Synthesis의 비교 금지선](synthesis/synthesis.md#교차자료-비교의-금지선)

## Synthesis에 사용한 Reader 원문 12건

| 번호 | 제목 | 발행 주체 | 원문 URL |
|---:|---|---|---|
| 1 | *MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases* | arXiv | [원문](https://arxiv.org/abs/2402.14905v2) |
| 2 | *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache* | arXiv | [원문](https://arxiv.org/abs/2402.02750v2) |
| 3 | *Elastic On-Device LLM Service* | arXiv | [원문](https://arxiv.org/abs/2409.09071v2) |
| 4 | *MNN-LLM: A Generic Inference Engine for Fast Large Language Model Deployment on Mobile Devices* | arXiv | [원문](https://arxiv.org/abs/2506.10443v1) |
| 5 | *LLM in a flash: Efficient Large Language Model Inference with Limited Memory* | arXiv | [원문](https://arxiv.org/abs/2312.11514v3) |
| 6 | *MLCommons Releases MLPerf Client v1.0: A New Standard for AI PC and Client LLM Benchmarking* | MLCommons | [원문](https://mlcommons.org/2025/07/mlperf-client-v1-0) |
| 7 | *MLPerf Inference v5.0 Advances Language Model Capabilities for GenAI* | MLCommons | [원문](https://mlcommons.org/2025/04/llm-inference-v5) |
| 8 | *MLCommons Releases New MLPerf Inference v5.0 Benchmark Results* | MLCommons | [원문](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results) |
| 9 | *On-device small language models with multimodality, RAG, and Function Calling* | Google Developers Blog | [원문](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling) |
| 10 | *Gemini Nano* | Google AI for Developers | [원문](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) |
| 11 | *Announcing Gemma 3n preview: powerful, efficient, mobile-first AI* | Google Developers Blog | [원문](https://developers.googleblog.com/introducing-gemma-3n) |
| 12 | *QAI AppBuilder - WoS* | Qualcomm | [원문](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf) |

## 검증·내부 산출물 추적

- [수집 인벤토리 (`raw/sources.yaml`)](raw/sources.yaml) — Reader 원문 URL·제목·선별 상태의 기준 목록
- [Reader 분석 인덱스](analysis/_index.md) — 12개 분석 노트의 수용 범위와 자료별 주의사항
- [Cross-Verify 검증표](verify/verification.md) — 확인·상충·미검증 판정과 제한
- [Synthesis](synthesis/synthesis.md) — 본 보고서에 인계된 기술 분류·성숙도·비교 경계
