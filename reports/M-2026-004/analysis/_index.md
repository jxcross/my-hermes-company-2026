# M-2026-004 자료별 심층 분석 인덱스

## 범위와 병합 규칙

- 분석 대상은 상위 큐레이션 handoff에서 `selected`로 확정된 12개 자료다. 각 분석 노트는 해당 자료의 보존된 `raw/*.md`와 당시의 `raw/sources.yaml` 레코드만 사용해 작성되었다.
- 각 shard에 **자료 식별·접근 범위·핵심 주장·근거/관찰·수치·정의·방법론·한계/확인 필요** 항목과 원문 위치가 있는지 확인했다. 12개 모두 수용했다.
- 이 파일은 주장들의 옳고 그름·자료 간 우열을 판정하지 않는다. 자료별 노트의 근거 범위와 후속 Cross-Verify가 확인할 항목만 연결한다.
- 병합 중 동일 자료의 중복 note는 없었다. Apple landing page, MLPerf Client GitHub release metadata, 무날짜 Google AI Edge landing page는 상위 큐레이션에서 제외되어 여기에는 포함하지 않는다.

## 수용된 자료별 분석 노트

| ID | 자료·유형 | 분석 노트 | 원문 접근 범위/주의 | 후속 확인 표지 |
|---|---|---|---|---|
| `mobilellm-optimizing-sub-billion-parameter-language-models` | MobileLLM / academic | [노트](mobilellm-optimizing-sub-billion-parameter-language-models.md) | versioned arXiv PDF 텍스트 추출본의 본문·부록·표/그림 캡션을 확인. PDF 표 레이아웃/텍스트 순서 제약이 있음. | 아키텍처·학습·평가 수치는 원문 표/절 위치에서 재확인 필요. |
| `kivi-tuning-free-asymmetric-2bit-kv-cache-quantization` | KIVI / academic | [노트](kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md) | 보존된 arXiv PDF 텍스트는 본문·표·부록 일부를 포함하나 원문 중간 생략 표시가 있음. | 2-bit KV cache 수치와 비교 조건은 표/절 단위로 재확인 필요. |
| `elastic-on-device-llm-service` | Elastic On-Device LLM Service / academic | [노트](elastic-on-device-llm-service.md) | arXiv PDF 텍스트의 앞·뒤 일부만 보존되어 중간 본문이 생략됨. | SLO(TTFT/TPOT)·기기 측정 조건과 결과는 보존 구간 한정으로 검증 필요. |
| `mnn-llm-generic-inference-engine-mobile-devices` | MNN-LLM / academic | [노트](mnn-llm-generic-inference-engine-mobile-devices.md) | versioned arXiv PDF 텍스트의 초록·본문·표/그림 캡션·참고문헌을 확인. | DRAM–Flash, KV cache, CPU/GPU 성능 수치의 하드웨어·설정 조건을 분리 검증 필요. |
| `llm-in-a-flash-efficient-inference-limited-memory` | LLM in a Flash / academic | [노트](llm-in-a-flash-efficient-inference-limited-memory.md) | arXiv PDF의 서론~한계 및 일부 부록을 보존하나 중간이 생략됨. | flash weight loading/windowing/bundling의 수치·비교 조건은 보존 범위 제약을 고려해 검증 필요. |
| `mlcommons-mlperf-client-v1-0` | MLPerf Client v1.0 발표 / research_org | [노트](mlcommons-mlperf-client-v1-0.md) | 출시 발표문 본문만 확인; 사양서·코드·개별 제출/측정 로그는 범위 밖. | 지원 범위·워크로드 서술을 성능 결과나 사양 완결성으로 확장하지 말 것. |
| `mlcommons-mlperf-inference-v5-0` | MLPerf Inference v5.0 방법론 발표 / research_org | [노트](mlcommons-mlperf-inference-v5-0.md) | 63행 게시글 추출문 전체. 그림 캡션만 있고 원시 결과·도표는 없음. | TTFT/TPOT, long-context workload의 정확한 측정·통과 조건은 사양/원시 결과로 확인 필요. |
| `mlcommons-mlperf-inference-v5-0-results` | MLPerf Inference v5.0 결과 발표 / research_org | [노트](mlcommons-mlperf-inference-v5-0-results.md) | 결과 발표문이며 시스템별 결과표·제출 설정·점수 산출식은 없음. | 방법론 발표와 역할이 다름; 둘을 단일 성능 순위 근거로 합치지 말 것. |
| `google-ai-edge-on-device-slms` | Google AI Edge SLM/RAG/function calling 발표 / vendor | [노트](google-ai-edge-on-device-slms.md) | 날짜·본문을 포함한 HTML 원문. 일부 문단은 단일 긴 행으로 보존됨. | 제품 지원·최적화·정확도 언급은 vendor 발표 주장으로 취급, 독립 실험으로 전환 금지. |
| `google-gemini-nano-aicore` | Gemini Nano/AICore 문서 / vendor | [노트](google-gemini-nano-aicore.md) | 9,935행 HTML 추출본. 렌더링·동적 요소·이미지 자체는 범위 밖. | AICore/ML Kit API 가용 범위·요건은 문서의 최종 갱신일과 플랫폼 조건을 함께 검증 필요. |
| `google-gemma-3n` | Gemma 3n 발표 / vendor | [노트](google-gemma-3n.md) | HTML 발표문 전체 텍스트. 벤치마크 차트의 축/개별 수치/조건은 텍스트에 없음. | 메모리·속도·품질 주장은 vendor 발표이며, 시각적 차트 수치나 독립 비교로 확장하지 말 것. |
| `qualcomm-qai-appbuilder-wos` | QAI AppBuilder - WoS / vendor | [노트](qualcomm-qai-appbuilder-wos.md) | 51쪽 슬라이드형 PDF의 텍스트 추출본. 화면·도표/스크린샷 및 실행 로그는 확인 불가. | 배포 API·지원 경로와 실제 성능을 구분하고, 성능 그래프/벤치마크는 별도 근거 필요. |

## 자료 간 후속 검증 이관 항목 (판정 아님)

1. **메모리 최적화 계열:** MobileLLM, KIVI, MNN-LLM, LLM in a Flash, Gemma 3n은 모두 메모리·양자화·구조 관련 서술을 담지만, 대상 모델·하드웨어·측정 단위·원문 접근 범위가 다르다. 동일 조건의 성능 비교 또는 일반화는 Cross-Verify 단계에서만 검토한다.
2. **지연/성능 측정 계열:** Elastic On-Device LLM Service와 MLPerf 문서는 TTFT/TPOT 또는 client/LLM workload를 다루지만, 전자는 보존된 논문 구간의 실험 서술이고 MLPerf는 발표문/방법론 안내다. 수치의 직접 비교는 하지 않는다.
3. **벤더 제품 문서:** Google AI Edge, Gemini Nano/AICore, Gemma 3n, Qualcomm 문서는 제품/배포 안내 또는 발표다. 제공 범위·호환성·성능 표현은 각 문서의 주장으로 보존하며 독립 재현·일반적 성능 결론으로 해석하지 않는다.
4. **MLPerf v5.0 두 문서:** 방법론 게시글과 결과 발표문은 같은 릴리스이나 기능이 다르다. 전자는 설계/워크로드, 후자는 집계/제출 생태계의 근거로 각각 유지한다.

## 병합 검증 기록

- 기대 shard 수: 12 (상위 큐레이션 selected 목록 기준)
- 수용 shard 수: 12
- 누락/중복/형식 부적합 shard: 0
- 파일 인코딩과 필수 섹션 존재 여부는 shard 작성 시 및 병합 시 확인했다.
