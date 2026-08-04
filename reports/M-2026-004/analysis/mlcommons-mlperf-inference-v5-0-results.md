# 단일 원자료 심층 분석 노트: MLPerf Inference v5.0 결과 발표

## 1. 자료 식별 및 원문 접근범위

| 항목 | 내용 |
|---|---|
| 자료 식별자 | `mlcommons-mlperf-inference-v5-0-results` (`raw/sources.yaml` 108–118행) |
| 제목 | *MLCommons Releases New MLPerf Inference v5.0 Benchmark Results* (`raw/sources.yaml` 109행; 원문 1행) |
| URL | https://mlcommons.org/2025/04/mlperf-inference-v5-0-results (`raw/sources.yaml` 110행) |
| 발행일 | 2025-04-02 (`raw/sources.yaml` 111행) |
| 수집일 | 2026-08-03 (`raw/sources.yaml` 112행) |
| 출처 유형 | research_org (`raw/sources.yaml` 113행) |
| 원문 파일 | `raw/mlcommons-mlperf-inference-v5-0-results.md` (`raw/sources.yaml` 114행) |
| 인벤토리상 성격 | 동일 릴리스의 결과·제출 생태계 문서이며, 방법론 문서와 역할이 다르므로 상호 성능 순위 근거로 합치지 않는다고 명시되어 있다 (`raw/sources.yaml` 117–118행). |

**접근범위.** 이 노트는 위 인벤토리 record와 지정된 원문 Markdown(1–73행)만 분석했다. 원문은 MLCommons의 v5.0 결과 **발표문**으로, 벤치마크의 고수준 목적·새 workload·집계 수치·선별된 상대 성능 진술을 포함한다. 반면 시스템별 결과표, 제출별 설정, 개별 점수, 정확도 검증 세부, TTFT/TPOT 임계값, 점수 산출식은 원문에 없다. 원문은 별도 결과 페이지와 보충 블로그를 링크하지만(39, 47, 53, 67행), 이 노트에서는 해당 링크를 열거나 그 내용을 사용하지 않았다. 따라서 abstract-only는 아니지만, **결과 상세가 아닌 발표문 범위의 원문**이다.

## 2. 핵심 주장 (저자/발표문 주장)

1. **MLPerf Inference v5.0은 아키텍처 중립적·대표적·재현 가능한 ML 시스템 성능 벤치마킹을 제공하며, 최근 GenAI 최적화 하드웨어·소프트웨어 발전이 지난 1년간 큰 성능 향상으로 이어졌다고 발표한다** (원문 3행). 이는 발표문의 총괄적 해석이며, 본문은 이 결론을 검증할 원시 점수나 비교 표를 제시하지 않는다.
2. **Llama 2 70B benchmark의 GenAI 비중과 제출 관심이 커졌고, v5.0에서 이 시험이 ResNet50을 제치고 가장 높은 제출률의 시험이 되었다고 주장한다** (9행). 또한 전년 대비 중앙 제출 점수는 두 배, 최고 점수는 Inference v4.0 대비 3.3배 빨라졌다고 주장한다 (11행).
3. **v5.0은 Llama 3.1 405B를 새 benchmark로 도입해 성능 benchmark 내 GenAI 모델 규모의 새 기준점을 만들었다고 설명한다** (31행). 이 모델은 4,050억 파라미터 및 최대 128,000-token 입·출력 길이를 지원하며, 일반 질의응답·수학·코드 생성의 세 과제를 시험한다고 서술한다 (31행).
4. **Llama 2 70B Interactive는 TTFT와 TPOT에 더 엄격한 응답성 요구사항을 부과하여 저지연 대화형 사용 사례를 겨냥한 추가 시험이라고 주장한다** (35–37행). 발표문은 이를 실제 환경의 LLM 성능에 관한 새 통찰을 제공하는 시험으로 평가한다 (37행).
5. **v5.0에는 관계 그래프 모델링용 datacenter RGAT benchmark와 자동차용 edge Automotive PointPainting benchmark가 포함되었다고 설명한다** (43–53행). 후자는 자동차 카메라 피드의 3D 객체 탐지를 위한 중요한 edge 시나리오의 proxy로 규정된다 (51행).
6. **이번 릴리스가 23개 제출 기관의 17,457개 성능 결과를 포함하고, 제출자 공동체 및 에너지 효율 측정의 중요성이 확대되고 있다고 주장한다** (59–63행).

## 3. 원문이 제시한 근거·관측치 (주장과 구분)

- **범위 및 표방된 설계:** 원문은 suite가 datacenter와 edge를 함께 포괄하며 여러 workload에서 AI/ML 모델을 얼마나 빠르게 실행하는지 측정하도록 설계됐다고 서술한다. 또한 open-source·peer-reviewed suite라고 기술한다 (5행). 이는 benchmark의 표방된 속성에 대한 서술이지, 이 원문 안에서 재현성 또는 공정성을 독립 검증한 증거는 아니다.
- **제출량·상대 성능에 대한 보고:** Llama 2 70B 시험의 제출 수가 지난 1년간 2.5배 증가했고(9행), 중앙 제출 점수 2배 및 최고 점수 3.3배라는 상대 변화가 보고된다(11행). 원문은 절대 점수, 중앙값 계산 대상, 제출 건수, 하드웨어/소프트웨어 조건을 제시하지 않는다.
- **새 processor 목록:** 이번 결과에 새로 이용 가능하거나 출시 예정인 processor 여섯 종의 결과가 포함됐다고 열거한다: AMD Instinct MI325X, Intel Xeon 6980P “Granite Rapids”, Google TPU Trillium (TPU v6e), NVIDIA B200, NVIDIA Jetson AGX Thor 128, NVIDIA GB200 (15–27행). 이는 포함 사실의 목록이며, 각 processor의 점수·제출 수·비교 조건은 제공되지 않는다.
- **Llama 3.1 405B workload의 명시 사양:** 405B 파라미터, 최대 128,000-token 입·출력 길이, 세 과제(일반 QA·수학·코드 생성)가 보고된다 (31행). 원문은 데이터셋, prompt 분포, 평가 지표, 정확도 목표를 명시하지 않는다.
- **RGAT workload의 명시 사양:** RGAT가 Illinois Graph Benchmark Heterogeneous(IGBH) dataset에 기반하고, dataset이 547,306,935 nodes와 5,812,005,639 edges를 포함한다고 서술한다 (45행). 이는 원문이 인용한 dataset 규모이며, 이 발표문 자체가 dataset을 재측정한 결과로 제시하지는 않는다.
- **제출 생태계 집계:** 17,457개 성능 결과와 23개 제출 기관의 명단(AMD부터 Sustainable Metal Cloud까지), 처음 제출한 다섯 기관(CoreWeave, FlexAI, GATEOverflow, Lambda, MangoBoost)이 보고된다 (59–61행). Fujitsu의 datacenter power 제출과 GateOverflow의 edge power 제출도 언급된다 (61행). 다만 power 결과의 수치·방법·비교 기준은 없다.

## 4. 수치·정의·방법론

### 4.1 수치와 적용 맥락

| 수치 | 원문상 대상·의미 | 원문 위치 | 원문이 제공하지 않는 맥락 |
|---:|---|---|---|
| 2.5× | 지난 1년간 Llama 2 70B benchmark test의 submissions 증가 | 9행 | 기준 시점별 제출 건수 및 집계 규칙 |
| 2× | 1년 전 대비 Llama 2 70B의 median submitted score | 11행 | 절대 점수, score 단위/정의, 중앙값 표본 |
| 3.3× faster | Inference v4.0 대비 Llama 2 70B의 best score | 11행 | 두 릴리스의 정확한 비교 조건, 절대 점수, 시스템 구성 |
| 405 billion parameters | Llama 3.1 405B model parameter 수 | 31행 | parameter 산정 방식·정밀도 |
| 128,000 tokens | Llama 3.1 405B가 지원하는 최대 input/output length | 31행 | benchmark에서 실제 사용한 길이 분포·토큰화 방식 |
| 4,096 tokens | Llama 2 70B의 비교 대상 input/output length | 31행 | 해당 길이의 정확한 적용 방식 |
| 3 tasks | Llama 3.1 405B 시험: 일반 QA, 수학, 코드 생성 | 31행 | 과제별 dataset·점수·합산 방식 |
| 547,306,935 nodes | IGBH dataset의 node 수 | 45행 | split·전처리·benchmark에서의 사용 범위 |
| 5,812,005,639 edges | IGBH dataset의 edge 수 | 45행 | edge 정의·방향성·유형별 구성 |
| 17,457 | v5.0의 performance results 수 | 59행 | result의 단위, 유효성 판정·중복 처리 |
| 23 | submitting organizations 수 | 59행 | 기관별 제출 건수 및 시스템별 분포 |
| 5 | first-time submitters 수 | 61행 | 각 기관의 제출 workload·결과 |
| 6 | 새로 이용 가능하거나 출시 예정인 processor의 결과 포함 수 | 15–27행 | processor별 시험 조건·성능 |

### 4.2 원문에 정의·서술된 방법론 요소

- **측정 대상:** suite는 여러 workload에서 AI/ML 모델을 실행하는 시스템의 속도를 측정하도록 설계되었다 (5행). 원문은 score가 throughput, latency 또는 다른 단위인지 workload별로 정의하지 않는다.
- **시스템 범위:** datacenter와 edge systems를 포괄한다 (5행). RGAT는 datacenter benchmark로(43–45행), Automotive PointPainting은 자동차를 특정 대상으로 한 edge benchmark로 소개된다 (49–52행).
- **Llama 2 70B Interactive의 응답성 지표:** TTFT는 prompt에 대한 응답을 시작하는 속도, TPOT는 전체 응답을 내는 pace와 연관된 지표로 설명되며, 시험은 이 두 지표에 더 엄격한 system response metrics를 요구한다 (35–37행). 그러나 원문에는 TTFT/TPOT의 정확한 수학적 정의, percentile, 측정 구간, 허용 임계값이 없다.
- **Llama 3.1 405B 과제 구성:** 일반 질의응답·수학·코드 생성의 세 과제를 분리해 시험한다 (31행). 과제별 정확도/품질 기준과 prompt·response 길이는 제공되지 않는다.
- **제출 및 결과 접근:** 원문은 결과를 Datacenter 및 Edge benchmark results pages에서 볼 수 있다고 안내한다 (65–67행). 이 원문 자체에는 결과표가 내장되어 있지 않다.

## 5. 원문 한계 및 확인 필요 항목

1. **발표문 한계:** 73행의 보도·발표 형식 원문은 결과의 상세 테이블이나 제출별 configuration을 포함하지 않는다. 따라서 “가장 빠른 시스템”, 특정 accelerator의 우열, on-device 성능, 에너지 효율의 크기에 관한 결론은 이 자료만으로 도출할 수 없다.
2. **상대 개선 수치의 재현 불가:** 2.5×, 2×, 3.3× 수치(9–11행)는 기준 분모·절대값·표본 및 동일성 조건이 빠져 있어, 이 발표문만으로 독립 계산·재현할 수 없다.
3. **TTFT/TPOT의 운영 정의 부재:** Interactive 시험이 더 엄격한 TTFT/TPOT 요건을 둔다는 서술(35행)은 있으나, 수치 임계값·통계 기준·동시성·prompt/response 조건이 없다. 해당 요건의 엄격성 정도는 확인이 필요하다.
4. **정확도·품질 조건 부재:** workload별 정확도 기준, 모델 정밀도, runtime, batch/concurrency, 전력 측정 절차가 제시되지 않는다. 성능 결과를 실사용 품질 또는 효율과 등치할 수 없다.
5. **‘대표성’·‘실제 환경’ 표현의 범위:** 원문은 benchmark를 representative라고 부르고(3행), Interactive 시험이 real-world scenarios에 관한 통찰을 준다고 평가한다(37행). 하지만 실제 사용자 workload와의 대응을 입증하는 표본·검증 절차는 이 원문에 제시되지 않는다.
6. **링크된 보충 자료는 미검토:** Llama workload 선택(39행), RGAT 구성(47행), Automotive PointPainting(53행), 상세 결과 페이지(67행)는 별도 URL로 안내될 뿐, 현재 허용 원문 범위에는 포함되지 않는다. 이 노트에서 이들 문서의 내용을 전제하지 않았다.

## 6. 분석상 해석 (원문 범위 내, 저자 주장과 구분)

발표문이 직접 뒷받침하는 범위는 v5.0이 GenAI·대형 모델·대화형 지연·그래프·자동차 edge workload를 추가 또는 강조했고, 결과·제출의 집계 규모를 보고했다는 점까지다 (5, 29–59행). 반면 Llama 2 70B 성능 향상(11행)을 특정 hardware, FP4, 혹은 개별 software technique의 **인과적 효과**로 분해할 수는 없다. 원문은 hardware와 software 발전 및 FP4 aligned support를 성능 기록의 배경으로 언급하지만(13행), 통제된 비교 결과를 제공하지 않기 때문이다.
