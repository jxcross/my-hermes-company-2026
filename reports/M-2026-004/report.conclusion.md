## 결론과 의사결정 기준

### 제한적 결론

온디바이스 LLM 추론 최적화는 단일한 성능 향상 기법이 아니라, **모델 가중치·KV cache·DRAM–Flash 배치·런타임/가속기 경로를 함께 조정하는 조건부 trade-off**다. 메모리 절감, 첫 응답과 생성 지연, 과업 품질, 전력·열, 지원 가능 장치가 서로 영향을 주므로, 한 축의 개선만으로 배포 우위를 결론 내릴 수 없다. KIVI의 KV cache 양자화, LLM in a Flash의 계층형 메모리, MNN-LLM의 모바일 런타임, MobileLLM의 소형 모델 구조는 각각의 조건에서 검토할 후보를 제공하지만, 서로 다른 모델·정밀도·작업 단계·장치에서 얻은 수치로 공통 순위나 보편적 최적값을 만들 수 없다. [KIVI 원문](https://arxiv.org/abs/2402.02750v2) · [LLM in a Flash 원문](https://arxiv.org/abs/2312.11514v3) · [MNN-LLM 원문](https://arxiv.org/abs/2506.10443v1) · [MobileLLM 원문](https://arxiv.org/abs/2402.14905v2)

따라서 의사결정의 기준은 평균 token/s가 아니라, 같은 workload와 기록 조건에서의 **TTFT, TPOT, peak memory, 과업 품질, 전력·열, 그리고 OS/SoC/API·모델·정밀도별 지원 행렬**을 함께 측정한 결과여야 한다. MLPerf 자료는 TTFT·TPOT와 정확도 기준을 분리해 다루는 비교 언어를 제공하지만, 이를 곧바로 온디바이스 시스템의 순위나 특정 제품의 우위로 해석하지 않는다. [MLPerf Client v1.0 원문](https://mlcommons.org/2025/07/mlperf-client-v1-0) · [MLPerf Inference v5.0 원문](https://mlcommons.org/2025/04/llm-inference-v5)

API 제품화는 별도 판단이 필요하다. Android AICore/ML Kit 및 Qualcomm QAI AppBuilder와 같은 경로는 시스템·SDK·변환/배포 경계를 제시하지만, API의 존재가 장치 간 호환성, 지연, 품질, 운영 안정성을 보장하지는 않는다. 제품화 여부는 대상 장치별 pilot에서 기능 범위, 오류·fallback, 권한과 데이터 처리, 성능·열 조건을 확인한 뒤에 결정한다. [Gemini Nano with AICore 문서](https://ai.google.dev/gemini-api/docs/get-started/android_aicore) · [Qualcomm QAI AppBuilder 문서](https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf)

### 의사결정 기준

| 결정 질문 | 채택 기준 | 보류 또는 중단 기준 |
|---|---|---|
| 저비트 weight 경로를 기본 경로로 둘 것인가 | 원본 대비 품질 gate를 통과하면서 TTFT·TPOT·peak memory를 함께 개선하거나, 명시한 목표 범위 안에 유지하는지 확인 | 메모리 절감만 있고 지연 또는 품질의 손실을 수용 기준 안에서 설명할 수 없음 |
| KV cache 최적화를 적용할 것인가 | 목표 context 길이와 과업에서 정밀도별 기준선 대비 품질·peak memory·생성 성능을 함께 확인 | 특정 2-bit 결과를 모든 모델/attention 구조의 기본값으로 일반화해야만 효과가 성립 |
| DRAM–Flash 계층 배치를 사용할 것인가 | storage throughput, cache eviction, first-token 비용, 전력·열, 동시 요청을 포함한 실제 장치 조건에서 목표를 충족 | 제한 메모리 실험의 속도 향상을 장기 열·전력·OS I/O 경합 검증 없이 제품 기준으로 사용 |
| 런타임·가속기 또는 API를 제품 경로로 채택할 것인가 | 지원 행렬과 모델·정밀도·배포 산출물을 고정하고, 장치별 pilot에서 기능·호환성·오류 처리와 공동 측정 지표를 검증 | 공급자 문서의 성능·간편 배포 표현 또는 한 기기의 결과만으로 일반 배포를 결정 |

### 실행 원칙

1. 장치별 harness를 먼저 고정한다. 모델 revision, 정밀도/양자화, prompt·output 길이, batch/concurrency, warm-up·반복, 온도·전력 상태를 측정 결과와 함께 보존한다.
2. 저비트 weight, KV cache, DRAM–Flash, 런타임/API 경로를 한 번에 승격하지 않는다. 각 축을 기준선과 비교하고 rollback 가능한 원본을 유지한다.
3. KIVI, LLM in a Flash, MNN-LLM, MobileLLM의 수치와 우위 주장은 해당 저자·장치·런타임·워크로드 조건에 귀속한다. 이들 수치를 합산·직접 비교하거나 보편적 성능 보장으로 표현하지 않는다.
4. API 기반 기능은 장치별 pilot을 통과한 범위에서만 제품화한다. 지원 여부와 API 표면, 실제 기능 품질과 운영 효과를 별개의 검증 대상으로 유지한다.
