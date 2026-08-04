# 근거·수치·평가 설계

## 근거를 읽는 기준

이 섹션은 수집·분석·검증 단계에서 확인된 정의와 측정 조건만 정리한다. 공급자 발표의 수치, 학술 자료의 저자 보고치, 벤치마크 설계의 임계값은 서로 다른 종류의 근거이므로 같은 의미의 성능 결과로 합치지 않는다. 특히 모델·장치·런타임·정밀도·입출력 길이·동시성·열 상태가 다른 `tokens/s`, 지연, 메모리 수치를 직접 순위화하지 않는다.

### Gemma 3n의 `E` 표기

Gemma 3n의 `E2B`와 `E4B`에서 `E`는 총 파라미터 수가 아니라 **유효(effective) 파라미터** 표기다. Google의 [Gemma 3n 모델 개요](https://ai.google.dev/gemma/docs/gemma-3n#model_parameters_and_effective_parameters)는 E2B도 표준 실행에서 5B를 초과하는 파라미터를 로드한다고 설명한다. 따라서 E2B/E4B를 각각 총 2B/4B 파라미터 모델로 축약하지 않는다. 이 항목은 모델 용어의 공식 정의에 대한 대조이며, 장치별 속도·메모리·품질의 독립 재현 근거는 아니다.

## 인용 가능한 수치와 엄격한 조건

| 항목 | 확인된 내용과 조건 | 해석 경계 |
|---|---|---|
| Gemma 3 1B 모바일 GPU prefill | [Gemma3-1B-IT 모델 카드](https://huggingface.co/litert-community/Gemma3-1B-IT)는 **Samsung S24 Ultra / MediaPipe GPU / dynamic int4 QAT / context 2048**에서 최대 **2,585 tokens/s** prefill을 제시한다. | prefill 처리량만을 뜻한다. decode 생성 속도, TTFT, TPOT 또는 end-to-end 응답 성능으로 바꾸어 해석하지 않는다. |
| 별도 런타임 경로 | 같은 [모델 카드](https://huggingface.co/litert-community/Gemma3-1B-IT)의 LiteRT-LM 경로는 **2,531 tk/s**로 별도 표기된다. | 2,585 tk/s와 경로가 다르므로 합산·평균·대체 수치로 쓰지 않는다. |
| ‘한 페이지 1초 미만’ 환산 | Google AI Edge 발표 원문은 모바일 GPU prefill과 ‘한 페이지’ 표현을 함께 제시했지만, [검증 대상 원문](https://developers.googleblog.com/en/google-ai-edge-small-language-models-multimodality-rag-function-calling/)에는 2,585 tk/s의 재현 조건이 없다. | 페이지의 토큰 수, 전처리, prefill chunk가 정의되지 않아 ‘한 페이지 1초 미만’은 검증된 성능 지표로 사용하지 않는다. |

2,585 tk/s는 위의 네 조건을 한 세트로 붙일 때만 인용한다. 해당 수치는 특정 모델 카드의 특정 prefill 경로에 대한 수치이며, 다른 기기·양자화·컨텍스트 길이·런타임이나 일반 생성 성능으로 일반화하지 않는다.

## 지연·정확도·처리량의 분리

온디바이스 LLM 평가는 하나의 평균 처리량으로 대체하지 않는다.

- **TTFT (time to first token):** prompt 처리 이후 첫 출력 토큰이 도착하기까지의 지연이다. [Elastic On-Device LLM Service](https://arxiv.org/abs/2409.09071v2)는 prefill을 prompt-processing 단계, TTFT를 그 단계의 지연 지표로 구분한다.
- **TPOT (time per output token):** 출력 토큰 생성 단계의 토큰당 지연이다. 같은 자료는 decode를 token-generation 단계, TPOT를 그 단계의 지연 지표로 구분한다.
- **정확도·품질:** 지연과 별도 축이다. [MLPerf Inference v5.0](https://mlcommons.org/2025/04/llm-inference-v5)은 요약에 ROUGE-L, 검색·문서 QA에 exact match를 사용하고, closed division에는 FP16 reference의 99% 정확도 기준을 둔다고 설명한다. 이는 특정 장치의 결과나 순위가 아니라 평가 통과 조건의 예다.
- **처리량:** MLPerf의 offline 시나리오는 token throughput을, server 시나리오는 TTFT와 TPOT를 사용한다. 따라서 prefill `tokens/s` 하나만으로 대화형 지연 또는 과업 품질을 판정하지 않는다.

MLPerf의 405B/70B 관련 수치와 임계값은 장문맥·서버 벤치마크 설계를 설명하는 자료다. 온디바이스 장치의 실증이나 시스템 간 우열의 근거로 전용하지 않는다. 또한 [MLPerf v5.0 방법론 발표](https://mlcommons.org/2025/04/llm-inference-v5)와 [v5.0 결과 발표](https://mlcommons.org/2025/04/mlperf-inference-v5-0-results)는 발표 범위와 제공 정보가 다르므로, 둘을 결합해 개별 시스템의 측정값이나 순위를 만들지 않는다.

## 장치별 measurement harness

배포 후보는 동일 workload를 사용하는 **device-specific measurement harness**에서 측정한다. 이 harness의 목적은 서로 다른 환경의 수치를 비교표로 단순화하는 것이 아니라, 각 배포 후보가 해당 장치와 운영 조건에서 허용 가능한지 판정하는 것이다.

### 고정·보존할 측정 조건

| 범주 | 보존 항목 |
|---|---|
| 실행 대상 | 모델명과 revision, tokenizer, 정밀도·양자화, runtime 및 실행 경로, 장치·SoC·OS·드라이버 |
| workload | 과업/데이터셋, prompt 길이와 내용, 목표 output 길이·종료 조건, context 길이, batch와 concurrency |
| 실행 절차 | warm-up 여부, 반복 횟수, 측정 구간, 실패·fallback 처리 |
| 기기 상태 | 메모리 사용량, 전력·열 상태 및 측정 시점의 장치 상태 |
| 결과 축 | prefill/decode 구분, TTFT, TPOT, peak memory, 정확도·품질, 전력·열 |

### 판정 방식

1. **동일 조건 안에서만 비교한다.** 모델 revision, 정밀도, runtime, prompt/output 길이, batch·concurrency, warm-up 및 기기 상태가 같은 실행끼리 지연·메모리·품질을 비교한다.
2. **지연과 품질을 함께 기록한다.** TTFT/TPOT 개선은 정확도·품질 gate를 통과한 실행에서만 해석한다. 지연 목표 충족과 품질 유지 중 하나만으로 채택하지 않는다.
3. **prefill과 decode를 별도 보고한다.** [Elastic On-Device LLM Service](https://arxiv.org/abs/2409.09071v2)가 제시한 Redmi K60 Champion/Snapdragon 8 Gen 2/4 big-core thread 측정은 TTFT가 prompt 길이와 모델 크기의 영향을 함께 받고, TPOT는 주로 모델 크기의 영향을 받는다고 서술한다. 이는 특정 장치 조건의 관찰이므로 다른 장치에 그대로 적용하지 않고, harness에서 다시 분리 측정할 이유로만 사용한다.
4. **장치 간 직접 순위화를 금지한다.** MobileLLM, MNN-LLM, KIVI, LLM in a Flash, Gemma/AI Edge 및 MLPerf 자료는 모델·기기·정밀도·작업 단계가 다르다. 서로 다른 출처의 토큰/초, 배율, 메모리 수치를 합산하거나 단일 리더보드로 정렬하지 않는다.

이 설계에서 수치는 ‘모델 일반의 우열’이 아니라, 명시된 모델·런타임·장치·workload 조건 아래의 관측값으로만 남긴다. 채택 판단은 평균 `tokens/s`가 아니라 TTFT, TPOT, peak memory, 정확도·품질, 전력·열, 지원 행렬을 함께 기록한 장치별 결과에 근거한다.
