# 원자료 심층 분석 노트 — KIVI

## 1. 자료 식별 및 접근 범위

| 항목 | 내용 |
|---|---|
| 자료 식별자 | `kivi-tuning-free-asymmetric-2bit-kv-cache-quantization` |
| 제목 | *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache* |
| URL | https://arxiv.org/abs/2402.02750v2 |
| 원자료 유형 | 학술 논문(ICML 2024 표기) |
| 원문 버전·수집 메타데이터 | arXiv v2, 관측된 게시일 2024-02-05, 최종 갱신 2024-07-25, 수집일 2026-08-03 (원문 raw 3–10행; sources record 29–38행) |
| 원문 접근범위 | `raw/kivi-tuning-free-asymmetric-2bit-kv-cache-quantization.md`에 보존된 versioned arXiv PDF 텍스트 추출본만 읽었다. 초록만 읽은 것이 아니라 본문 §1–§5, 표 1–7, 부록 A–D 일부가 포함된다. 다만 raw 자체가 원 PDF 추출에서 중간을 생략했다고 표시한다(raw 102행, 151–154행). 따라서 생략된 중간 본문·참고문헌·부록 전체에는 접근하지 않았고, 아래 해석은 보존된 구간에 한정한다. |

## 2. 핵심 주장

1. **KV cache는 긴 문맥·큰 배치에서 LLM 추론의 메모리 및 속도 병목이 되며, 이를 줄이려면 KV cache의 바이트 수를 줄이는 양자화가 필요하다.**
   - 위치: 초록(raw 14–15행), §1 Introduction(raw 21–25행), §2 Memory and Speed Analysis(raw 38–39행).
   - 논문은 KV cache가 재계산을 피하려 attention key/value를 저장하며, 생성 토큰마다 GPU 메인 메모리에서 SRAM으로 전체 KV cache를 적재하는 동안 연산 코어가 유휴 상태가 된다고 서술한다.

2. **2비트 KV cache 양자화에서 key cache와 value cache에는 서로 다른 축이 적합하다: key는 채널별(per-channel), value는 토큰별(per-token)이다.**
   - 위치: 초록(raw 15행), §1의 분석 요약(raw 26–29행), §3.1 관찰 OB1–OB3(raw 45–48행), §3.2(raw 50–58행).
   - 이 비대칭 선택이 논문의 중심 설계 주장이다. 특히 value를 채널별로 양자화하면 key의 축 선택과 무관하게 정확도가 크게 악화된다고 보고한다.

3. **KIVI는 미세조정 없이(tuning-free) 작동하는 plug-and-play 2비트 비대칭 KV cache 양자화 알고리즘이며, 스트리밍 decoding에서 최근 residual KV를 full precision으로 남기는 구조로 채널별 key 양자화의 구현 문제를 해결한다.**
   - 위치: §1(raw 29–32행), §3.3 Algorithm(raw 59–66행), Algorithm 1(raw 132–134행).
   - 논문은 key를 일정 토큰 그룹 단위로 양자화하고, 완전한 그룹을 이루지 못한 residual은 full precision으로 유지한다. value도 grouped/residual로 나누되, 그룹 부분은 토큰별 양자화를 사용한다.

4. **저자들의 평가 범위에서는 KIVI가 품질 저하를 작게 유지하면서 peak memory를 줄이고, 더 큰 배치와 더 높은 처리량을 가능하게 한다.**
   - 위치: 초록(raw 15행), §4.2.2(raw 75–83행), §4.2.4(raw 87–90행), 표 3(raw 87–88행), 표 4(raw 96행).
   - 이는 논문 저자들의 실험 결과에 관한 주장이다. 모든 모델·작업·하드웨어에 일반화된 보장은 원문에서 제시되지 않는다.

## 3. 주장과 분리한 근거

### 3.1 병목 주장에 대한 원문 근거

- **규모 예시:** 540B PaLM에서 batch 512, context 2048일 때 KV cache만 3TB이고 모델 파라미터 크기의 3배라는 인용된 사례가 제시된다(§1, raw 21행).
- **별도 산식 예시:** KV cache 형상을 `b × (l_prompt + l_gen) × d`로 두며, OPT-175B·batch 512·prompt 512·output 32의 KV cache가 1.2TB, 모델 weight의 3.8배라고 제시한다(§2, raw 38–39행).
- **속도 메커니즘:** 생성 매 토큰에 KV cache를 GPU 메인 메모리에서 SRAM으로 한 번 적재하고, 그 동안 연산 코어가 사실상 idle이라고 설명한다(§2, raw 39행).

### 3.2 비대칭 축 선택에 대한 원문 근거

- **분포 관찰:** Llama-2-13B와 Falcon-7B의 여러 layer/head 시각화에서 key cache에는 magnitude가 매우 큰 소수의 고정 채널이 있고, value cache에는 뚜렷한 outlier pattern이 없다고 관찰한다(그림 2 및 캡션, raw 49행; §3.2, raw 51–53행).
- **가짜 양자화 비교:** Llama-2-13B, group size 32에서 CoQA/TruthfulQA는 16bit `66.37/29.53`, 2bit key-channel/value-token은 `63.53/28.60`, 2bit key-token/value-token은 `52.93/24.98`이었다. value-channel을 포함한 두 구성은 더 낮은 수치(`2.88/0.74`, `2.80/0.26`)를 보였다(표 1, raw 41–48행).
- **key 오차 통계:** 모든 layer/head 평균에서 key의 상대 재구성 오차는 per-token 13.67, per-channel 4.55이고, 상대 attention-score 오차는 각각 47.00, 9.60이다(표 2, raw 54–55행). 논문은 이를 per-token key 양자화가 attention-score 오차를 약 5배 크게 만든다는 근거로 든다.
- **value 오차 통계와 기전:** value 재구성 오차는 per-token 4.57, per-channel 3.73으로 큰 차이가 아니지만, attention output 상대 오차 `Δ`는 각각 3.55와 49.89이다(표 2, raw 55행). 논문은 attention score sparsity 84.3% 및 attention output이 토큰별 value의 attention-weighted 합이라는 식을 근거로, 토큰별 양자화가 중요한 토큰의 오류를 다른 토큰으로 전파하지 않는다고 설명한다(§3.2, raw 56–58행).

### 3.3 KIVI 구조와 성능 주장에 대한 원문 근거

- **스트리밍 구조:** 새 token의 value는 토큰 축으로 바로 append할 수 있지만, key의 채널별 양자화는 여러 token을 가로지르므로 직접 적용하기 어렵다. KIVI는 key를 group `X_Kg`와 residual `X_Kr`로 분할하고 group만 양자화한다(§3.3, raw 60–63행).
- **residual의 역할:** residual key/value에는 최대 `R`개 토큰만 남고, 논문은 실사용에서 `R ≤ 128`이며 긴 시퀀스에서는 memory overhead가 작다고 분석한다. 이는 key에는 기대 크기 `R/2`, value에는 `R`의 full-precision local sliding window를 유지하며, GSM8K 같은 어려운 작업의 성능에 중요하다고 주장한다(§3.3, raw 65–66행).
- **일반 generation 평가:** Llama/Mistral에서 2bit KIVI의 정확도 하락이 최대 2%라고 서술한다. Falcon-7B는 multi-query attention으로 이미 KV head가 하나여서, 정확도 유지를 위해 4bit KIVI가 필요하고 2bit에서는 큰 하락이 있을 수 있다고 한정한다(§4.2.2, raw 76–78행).
- **구체적 표 3 예시:** Llama-2-13B GSM8K는 16bit 22.67, KIVI-2 20.77이고, Falcon-7B GSM8K는 16bit 4.55, KIVI-2 3.41, KIVI-4 4.47이다(표 3, raw 87–88행). 따라서 ‘2bit 품질 유지’는 모델별로 균일하지 않다는 표 내부 근거도 존재한다.
- **긴 문맥 평가:** LongBench 평균은 Llama2-7B에서 16bit 44.52/KIVI-2 44.27, Llama2-13B에서 44.85/44.69, Falcon-7B에서 8.71/7.95, Mistral-7B에서 46.58/45.85로 제시된다(표 4, raw 96행). Needle-in-a-Haystack에서는 2bit KV cache에서도 retrieval ability를 유지한다고 본문이 주장한다(§4.2.2, raw 80–83행).
- **효율 평가:** ShareGPT 기반 synthetic workload(평균 prompt 161, output 338), 단일 NVIDIA A100 80GB에서 Llama-2-7B와 FP16 baseline을 비교했고, KIVI는 최대 4배 큰 batch 및 2.35–3.47배 throughput을 보였다고 보고한다(§4.2.4, raw 87–90행).

## 4. 수치·정의·방법론

### 4.1 용어와 정량화 정의

- `X ∈ R^(l_prompt × d)`에서 `l_prompt`는 토큰 수, `d`는 채널 수다. **per-token**과 **per-channel**은 각각 token 또는 channel 차원으로 요소를 그룹화해 함께 양자화하는 방식이다(그림 1 설명, raw 24행).
- B-bit 정수 quantize/dequantize는 `Q(X)=round((X-z_X)/s_X)`, `X'=Q(X)·s_X+z_X`이며, `z_X=min X`, `s_X=(max X-min X)/(2^B-1)`로 정의한다(§3.1, raw 41–42행).
- decoding에서 `t_Q=tW_Q`, attention score `A=Softmax(t_QX_K^T)`, output `t_O=AX_V`로 쓴다(식 1, raw 37행). value 오류 분석에는 `Δ=||AX_V-AX'_V||_F / ||AX_V||_F`를 사용한다(§3.2, raw 55–57행).
- `G`는 group size, `R`은 residual length다. key residual 길이는 `l mod R`로 두며 `R`은 `G`로 나누어떨어져야 한다(§3.3, raw 60–62행; Algorithm 1, raw 133–134행).

### 4.2 알고리즘·구현

- prefill에는 정확한 key/value tensor를 다음 layer로 전달하되, 메모리에는 양자화된 KV cache만 보존한다고 명시한다(§3.3, raw 63–64행).
- decoding에서는 새 key/value를 full-precision residual에 붙이고, residual이 임계 길이에 이르면 key는 channel 방식, value는 token 방식으로 양자화해 기존 grouped cache에 연결한다(Algorithm 1, raw 133–134행).
- 양자화 해제와 matrix multiplication을 tile 수준에서 융합한 CUDA `Q_MatMul`, 그리고 Triton group-wise quantization kernel을 구현했다고 하며, weight-only quantization과 완전 호환된다고 한다(§3.3 System Support, raw 67–68행).

### 4.3 실험 설계와 주요 수치

- 모델군: Llama/Llama-2, Falcon, Mistral. Llama/Mistral은 multi-head attention, Falcon은 multi-query attention으로 설명한다(§4.1, raw 69–71행).
- 기본 설정: 모든 실험에서 `G=32`, key/value `R=128`(§4.1, raw 71행). LongBench 최대 길이는 Mistral 8192, 기타 4096으로 설정했다(raw 72–74행).
- 과제·측정: LM-Eval의 CoQA(exact match), TruthfulQA(BLEU), GSM8K(exact match); LongBench의 Qasper(F1), QMSum/MultiNews/SAMSum(ROUGE), TREC(classification), TriviaQA(F1), LCC/RepoBench-P(similarity)를 사용했다(raw 72–74행).
- ablation: `R=128`에서 `G=32/64/128`의 Llama2-13B GSM8K는 `20.77/21.00/17.29`; `G=32`에서 `R=32/64/96/128`은 `20.62/19.86/20.55/20.77`이다(표 5, raw 84–86행, 96–97행). 저자들은 group 128에서 성능 하락, residual 길이에서는 일관된 정확도 패턴이 없으나 충분히 큰 residual이 hard task에서 중요하다고 해석한다(raw 85–86행).
- residual 32의 추가 표에서 Llama-2-13B KIVI-2는 CoQA/TruthfulQA/GSM8K가 R128 `66.23/29.84/20.77`, R32 `66.57/29.35/20.62`로 제시된다(표 6, raw 141–143행). 이는 저자들이 효율 평가에 R32도 사용한 맥락을 제공한다.

## 5. 원문 한계 및 확인 필요 항목

1. **보존본의 접근 한계:** raw 텍스트가 중간 생략을 명시하므로, 이 노트는 생략 구간의 표·그림·세부 실험 조건을 검증하지 못했다(raw 102행, 151–154행). 특히 Figure 5의 개별 memory/throughput 좌표값은 보존 텍스트에 없어서 인용하지 않았다.
2. **평가 환경의 범위:** 효율 수치는 단일 NVIDIA A100 80GB, Llama-2-7B, ShareGPT 기반 synthetic workload에서의 결과다(raw 87–89행). 다른 GPU, 모바일/온디바이스 장치, runtime, context·output 길이에서 동일한 배율이 나오는지는 이 원문 보존 범위만으로 확인할 수 없다.
3. **정확도 보존의 조건성:** 논문도 Falcon-7B에서는 2bit KIVI가 큰 accuracy drop을 낼 수 있고 4bit가 필요하다고 명시한다(raw 78행). 따라서 ‘2bit’ 성능 주장을 모델 구조와 과제에 무관한 일반 명제로 읽으면 안 된다.
4. **공정 비교의 차이:** fake 2bit 양자화는 모든 token을 양자화하지만 KIVI는 residual을 full precision으로 남긴다(표 3 설명, raw 87행). 두 결과의 차이는 축 선택뿐 아니라 residual sliding window의 존재도 포함한다.
5. **메모리 주장 해석:** 초록의 ‘2.6× less peak memory’는 모델 weight를 포함한다고 명시한다(raw 15행). 반면 방법론은 residual full precision overhead가 긴 시퀀스에서 작다고 논증한다(raw 65–66행). KV cache만의 압축비, 모델 전체 peak memory, 특정 workload의 OOM batch 확대는 같은 지표가 아니므로 구분해 확인해야 한다.
6. **벤치마크 제외:** 저자들은 MMLU 같은 closed-end task는 decoding이 한 단계이고 compressed KV cache 영향을 연구하기에 적합하지 않아 사용하지 않았다고 밝힌다(raw 72–73행). 결과 범위는 generation 및 long-context retrieval 중심이다.
