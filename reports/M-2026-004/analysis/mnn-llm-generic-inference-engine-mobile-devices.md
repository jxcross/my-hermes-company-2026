# 원자료 심층 분석 노트: MNN-LLM

## 1. 자료 식별 및 원문 접근범위

- **자료 식별자:** `mnn-llm-generic-inference-engine-mobile-devices` (`raw/sources.yaml` 51–60행)
- **제목:** *MNN-LLM: A Generic Inference Engine for Fast Large Language Model Deployment on Mobile Devices* (`raw/mnn-llm-generic-inference-engine-mobile-devices.md` 1행; `raw/sources.yaml` 52행)
- **URL:** https://arxiv.org/abs/2506.10443v1 (`raw/sources.yaml` 53행). 원문에는 기본 URL, 실제 버전 URL, PDF URL이 각각 제시되어 있다(원문 3–5행).
- **발행일:** 2025-06-12 (`raw/sources.yaml` 54행; 원문 6–7행).
- **자료 유형:** academic (`raw/sources.yaml` 56행; 원문 9행).
- **원문 접근범위:** versioned arXiv PDF(v1)에서 추출한 텍스트이며, 초록만이 아니라 초록, 1–7절, 그림·표 캡션, 참고문헌을 포함한다(원문 10–12행, 14–115행). 다만 현재 검토 가능한 것은 PDF에서 추출된 텍스트이므로, 도표의 시각적 세부값·축·오류막대와 수식의 조판 정확성은 텍스트 추출 품질의 제약을 받는다.
- **선정 맥락(메타데이터):** 모바일 runtime에서 DRAM–Flash, KV cache, data reorder, CPU/GPU 평가를 함께 제공한다는 사유로 selected, relevance score 98로 기록되어 있다(`raw/sources.yaml` 57–60행). 이는 원문의 실증 결과가 아니라 수집 인벤토리의 큐레이션 판단이다.

## 2. 핵심 주장

1. **MNN-LLM은 모바일에서 LLM뿐 아니라 여러 딥러닝 모델을 배포할 수 있도록 설계된 범용 추론 프레임워크이다.** 저자들은 MNN 기반이라는 점과 LLM 전용 엔진보다 폭넓은 모델 지원을 차별점으로 제시한다(원문 24행, 32–35행, 79행).
2. **메모리 제약은 DRAM–Flash 하이브리드 저장과 결합 양자화로 완화할 수 있다는 주장이다.** 임베딩·KV cache의 접근 특성에 따라 Flash를 활용하고, 연산 경로·하드웨어별로 정밀도/비트폭을 달리한다(원문 37–53행).
3. **모바일 성능은 하드웨어 맞춤 데이터 재배열, 이기종 CPU 코어 부하균형, 혼합 부동소수점, 기하학적 연산으로 개선할 수 있다는 주장이다.** Linear와 Attention의 행렬곱 및 장꼬리 데이터 재배열 연산을 대상화한다(원문 54–69행).
4. **온라인 다중-LoRA에서는 행렬곱 결합 순서 변경이 메모리 접근량을 크게 줄인다는 주장이다.** `(LoRA_A·LoRA_B)·A`를 `LoRA_A·(LoRA_B·A)`로 바꾸어 작은 rank를 활용한다고 설명한다(원문 70–74행).
5. **Xiaomi 14에서의 저자 실험에서 CPU 기준 MNN-LLM은 llama.cpp 및 fastllm보다 높은 prefill/decode 속도를 보였고, GPU에서는 MLC-LLM과의 비교가 양자화 방식 차이에 영향을 받는다고 주장한다.** CPU 최대 prefill 향상은 llama.cpp 대비 8.6배, fastllm 대비 20.5배로 보고된다. GPU에서는 MLC-LLM 대비 일부 경우 열세를 인정하면서도, llama.cpp·MLC-LLM 대비 최대 향상치도 함께 제시한다(원문 75–78행).

## 3. 주장과 분리한 원문 근거

### 3.1 메모리 병목 및 DRAM–Flash 근거

- 원문은 edge 기기에서 prefill은 계산 제약(computation-bound), decode는 메모리 제약(memory-bound)이라는 문제 설정을 둔다(원문 25–29행).
- LPDDR5X 약 58 GB/s와 UFS 4.0 약 450 MB/s–3 GB/s를 대비하여 DRAM이 Flash보다 19–130배 빠르다고 적는다. 따라서 Flash 활용은 메모리를 줄이지만 추론 성능을 해칠 가능성이 있다는 전제를 명시한다(원문 37–39행).
- Qwen2 7B의 표 1 구성에서 Embedding 1.09B, Layers 4.89B, Lm head 1.09B, 총 7.07B 파라미터를 제시하며, Embedding이 총량의 약 15%이고 통상 레이어 파라미터처럼 연산에 참여하지 않는다고 설명한다(원문 40행).
- decode에서 토큰 하나에 필요한 bfloat16 Embedding 읽기량을 7 KB로, UFS 4.0의 추가 읽기 시간을 LPDDR5X보다 약 15 μs 느린 것으로, non-Embedding 로딩을 약 103 ms로 제시한다. 이를 바탕으로 Embedding을 Flash에 놓을 때 추론시간 증가는 약 1.4‱이고 DRAM 사용량은 15% 감소하며, Qwen-7B의 bfloat16 저장에서는 약 2.18 GB DRAM 감소라는 계산을 제시한다(원문 41행).
- KV cache는 임계값을 초과한 부분을 Flash로 옮기고, MLP 및 다음 레이어 qkv projection 중 prefetch한다고 설명한다. Qwen2 7B의 단일 레이어 qkv+MLP 파라미터 178.83 MB, LPDDR5X 로드 약 3 ms, Flash 1 GB/s 가정 아래 Flash KV 길이가 3072 K 이하이면 로드 오버헤드가 가려지고, 초과 뒤에는 추가 1 K마다 약 1 ms 지연된다고 제시한다(원문 43–45행).

### 3.2 결합 양자화 근거

- Embedding은 Flash에 저장하여 DRAM을 차지하지 않으므로 bfloat16을 쓰고, 매 decode마다 모두 읽어야 하는 Layer 및 LM head는 CPU에서 int4/int8 weight와 int8 activation(W4A8/W8A8), GPU에서 W4A16/W8A16을 사용한다고 설명한다. 정확도 유지를 위해 비대칭 양자화를 사용하고 LM head는 int8을 우선한다고 한다(원문 46–51행).
- KV의 key는 축소 차원이 고정된 `headdim`이므로 int4/int8 양자화가 가능하나, value는 축소 차원이 `seqlen`이라 새 값 추가 시 기존 값의 분포·양자화값 갱신 문제가 생길 수 있어 fp8을 쓴다는 설계 근거를 든다(원문 52–53행).

### 3.3 연산 최적화 근거

- 저자들은 Linear와 Attention을 주요 시간 소모 연산으로 규정하고, Loop Tiling 및 CPU instruction set별 타일 크기 선택을 설명한다(원문 54–56행). 표 2의 타일 크기는 ARM i8sdot `(e_p=12, h_p=8, l_p=4)`, ARM i8mm `(10,8,8)`, x86 AVX2 `(4,8,4)`, x86 AVX512 `(4,64,4)`이다(원문 54행).
- ARM i8mm의 `smmla` throughput이 `sdot`의 2배라고 서술하고, i8mm 지원 시 로딩 단계에서 `l_p=8`로 weight를 재배열한다고 한다(원문 56행). GPU에서는 연속 접근·128-bit load/store·Image 객체를 이용하도록 `[l/l_p, h, l_p]`, `l_p=32` 형식으로 재배열한다고 설명한다(원문 57–59행).
- big.LITTLE CPU의 코어별 성능 차이를 반영해 시작 시 부하율을 정하고 `seqlen`, `h/h_p` 방향으로 병렬화한다고 설명한다. Snapdragon 8 Gen 3의 prime core 1개와 performance core 3개를 예시로 들어 균등 분배보다 부하균형이 speedup을 높인다고 주장한다(원문 60–63행).
- float16은 float32의 절반 메모리와 2배 NEON throughput을 제공하지만 값이 65,504를 넘으면 오차가 커질 수 있으므로, Softmax는 float32를 유지하고 QK 행렬곱에서는 `√d_k` 나눗셈을 query에 선적용한다고 설명한다(원문 64행).
- Transpose/Gather/Concat을 주소의 선형 매핑(Region)으로 표현하고 Region Fusion을 적용해 데이터 재배열의 읽기·쓰기를 줄이며, 장꼬리 연산 오버헤드를 약 3% 줄인다고 보고한다(원문 65–69행).

### 3.4 LoRA 근거

- base model과 여러 LoRA를 온라인 로딩할 수 있으며 LoRA는 base weight를 공유해 메모리 오버헤드가 작지만 추가 연산비용이 있다고 설명한다(원문 70–73행).
- `h=3584`, `r=8`인 Qwen2 7B 예에서 결합 순서 변경 후 메모리 접근량이 원래의 0.5%라고 제시한다(원문 73–74행). 표 3은 두 계산 순서의 연산량·메모리 식을 제공한다(원문 68–69행).

### 3.5 평가 근거

- **평가 구성:** Qwen2 1.5B, Qwen2 7B, Llama3 8B의 양자화 모델을 Xiaomi 14에서 측정했다. CPU는 4 threads, GPU는 OpenCL이며, 비교 엔진은 llama.cpp, MLC-LLM, fastllm이다. MLC-LLM은 CPU 미지원, fastllm은 GPU 미지원이어서 해당 조합은 제외했다. prompt 길이는 64/256/1024 tokens, decode 상한은 16 tokens다(원문 75행).
- **비교 조건의 비대칭성:** MLC-LLM이 비대칭 양자화 모델에서 성능이 낮아 MLC-LLM 결과는 대칭 양자화 모델로, 경쟁 엔진은 비대칭 모델로 실행했다고 저자들이 명시한다(원문 76행). 따라서 이 논문 내 MLC-LLM 비교는 동일 양자화 조건의 순수 runtime 비교가 아니다.
- **보고된 CPU 결과:** MNN-LLM의 최대 prefill 속도는 llama.cpp 대비 8.6배, fastllm 대비 20.5배이고, decode는 각각 2.3배 및 8.9배라고 서술한다(원문 78행). 그림 5에는 모델·prompt 길이별 token/s 막대값이 실려 있다(원문 77행).
- **보고된 GPU 결과:** MLC-LLM보다 특히 짧은 prompt의 Qwen2-7B에서 약간 낮은 성능이 나타난다고 적으며 이를 MLC-LLM의 대칭 양자화 이점으로 설명한다. 동시에 llama.cpp 대비 최대 prefill 25.3배/decode 7.1배, MLC-LLM 대비 2.8배/1.7배 향상이라는 수치를 제시한다(원문 78행).

## 4. 수치·정의·방법론 정리

| 항목 | 원문 정의·방법 또는 수치 | 원문 위치 |
|---|---|---|
| 추론 단계 | prefill은 입력 시퀀스를 처리해 첫 token을 생성, decode는 종료 token까지 매 연산마다 token 하나를 생성 | 26–28행 |
| 주요 병목 | edge 기기에서 prefill은 computation-bound, decode는 memory-bound | 28행 |
| KV cache | 이전 계산의 key/value를 저장해 decode에서의 중복 계산을 피하는 저장소 | 29행 |
| 저장장치 대역폭 | LPDDR5X 약 58 GB/s; UFS 4.0 약 450 MB/s–3 GB/s; DRAM은 19–130배 빠름 | 38행 |
| Qwen2 7B 파라미터 | vocabulary 151,646; hidden 3,584; intermediate 18,944; 28 layers; Embedding 1.09B, Layers 4.89B, Lm head 1.09B, 총 7.07B | 40행 |
| Embedding Flash 배치 추정 | token당 7 KB(bfloat16); Flash 추가 약 15 μs; non-Embedding 약 103 ms; 약 1.4‱ 시간 증가, DRAM 15%/약 2.18 GB 감소(Qwen-7B) | 41행 |
| KV Flash prefetch 추정 | qkv+MLP 178.83 MB; LPDDR5X 약 3 ms; Flash 1 GB/s 가정; 3072 K 이하 마스킹, 이후 1 K당 약 1 ms 지연 | 45행 |
| weight/activation 양자화 | CPU W4A8 또는 W8A8, GPU W4A16 또는 W8A16; Layer/LM head는 int4 또는 int8, activation은 CPU에서 int8 | 49–50행 |
| KV 양자화 | key int4/int8, value fp8 | 53행 |
| CPU 타일 크기 | ARM i8sdot 12/8/4, ARM i8mm 10/8/8, AVX2 4/8/4, AVX512 4/64/4 (`e_p/h_p/l_p`) | 54행 |
| float16 경계 | 65,504 초과 시 큰 오차 가능성을 언급; Softmax float32 유지 | 64행 |
| LoRA 예시 | Qwen2 7B, `h=3584`, `r=8`: 최적화된 memory access가 원래의 0.5% | 74행 |
| 실험 조건 | Xiaomi 14; Qwen2 1.5B/7B, Llama3 8B; CPU 4 threads, GPU OpenCL; prompt 64/256/1024, decode 최대 16 tokens | 75행 |
| 대표 성능 요약 | CPU: prefill 최대 8.6×(vs llama.cpp), 20.5×(vs fastllm); decode 2.3×, 8.9×. GPU: 최대 25.3×/7.1×(vs llama.cpp), 2.8×/1.7×(vs MLC-LLM) | 78행 |

## 5. 원문 한계 및 확인 필요 항목

- **단일 기기·제한된 모델 범위:** 평가는 Xiaomi 14 한 기기, 세 모델, 세 prompt 길이, decode 최대 16 tokens 조건에 한정된다(원문 75행). 다른 모바일 SoC, 메모리/저장장치 조합, 더 긴 생성 길이로 일반화할 수 있는지는 이 원문만으로 확인되지 않는다.
- **비교 양자화 조건이 일치하지 않는다:** MLC-LLM은 대칭 양자화, 경쟁 엔진은 비대칭 양자화로 수행되었다고 명시되어 있다(원문 76행). MLC-LLM 대비 수치에는 양자화 방식 차이의 영향이 포함될 수 있으므로, 동등한 모델·비트폭·양자화 방식 아래 재측정이 필요하다.
- **정확도 결과의 부재:** 양자화가 정확도에 영향을 주며 이를 균형화해야 한다고 서술하지만(원문 46–51행), 제시된 평가절은 속도 중심이다(원문 75–78행). 모델별 정확도/품질 지표, 양자화 전후 손실, KV fp8·key int4/int8 선택별 품질 결과는 이 텍스트에서 확인되지 않는다.
- **에너지·발열·지속성 미측정:** 모바일 배포의 성능 평가는 token/s로 제시되나, 전력소비, 배터리 영향, 온도 상승, 장시간 실행에서의 thermal throttling은 원문 평가 조건·결과에 보고되어 있지 않다(원문 75–78행).
- **DRAM–Flash 수치의 전제 의존성:** 1.4‱, 2.18 GB, 3072 K/1 ms 등의 값은 Qwen2 7B와 명시된 bfloat16·대역폭·Flash 1 GB/s·memory-bound 가정에 기반한다(원문 41행, 45행). 실제 기기별 UFS 상태, OS I/O 경합, context/모델 구성에 따른 재현성은 추가 확인이 필요하다.
- **그림의 정밀 수치 검증 필요:** 그림 4·5의 그래프는 추출 텍스트에 포함되어 있으나, 일부 막대의 정확한 대응·오차표현·반복 횟수는 본 텍스트만으로 충분히 확인되지 않는다(원문 63행, 77행). PDF 원도표 및 실험 코드/설정이 필요하다.
- **저자 보고 성능이라는 범위:** 본 노트의 성능 수치와 설계 효과는 모두 논문 저자들이 보고한 값·해석이다. 독립 재현 또는 외부 비교는 이 단일 원자료의 접근범위에 포함되지 않는다.
