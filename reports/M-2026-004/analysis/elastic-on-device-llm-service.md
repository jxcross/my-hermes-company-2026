# 원자료 심층 분석 노트 — Elastic On-Device LLM Service

## 1. 자료 식별 및 원문 접근범위

| 항목 | 내용 |
|---|---|
| 자료 식별자 | `elastic-on-device-llm-service` (`raw/sources.yaml` 40–49행) |
| 제목 | *Elastic On-Device LLM Service* (`raw/elastic-on-device-llm-service.md` 1행; 이하 **원문**) |
| 저자·소속 | Wangsong Yin, Rongjie Yi, Daliang Xu, Gang Huang, Mengwei Xu, Xuanzhe Liu; Peking University·Beijing University of Posts and Telecommunications·Beiyou Shenzhen Institute (원문 14행) |
| 원문 URL | 버전 고정 arXiv URL: https://arxiv.org/abs/2409.09071v2 (원문 4행; inventory URL도 동일: `raw/sources.yaml` 42행) |
| PDF 콘텐츠 URL | https://arxiv.org/pdf/2409.09071v2 (원문 5행) |
| 출처 유형·선정 상태 | academic, `selected`, 관련성 점수 94 (`raw/sources.yaml` 45–49행) |
| 관측된 날짜 | 최초 게시 2024-09-08T06:32:08Z, 최종 갱신 2025-10-03T18:03:47Z, 수집 2026-08-03 (원문 6–8행) |
| 출판 표기 | ACM MobiCom ’25, 2025-11-04~08, Hong Kong, 16쪽 (원문 17–19행) |
| 접근 범위 | 원문 파일은 versioned arXiv PDF에서 추출한 텍스트라고 명시한다(원문 10행). 다만 현재 raw artifact에는 본문 중간이 `[...] middle omitted`로 생략되어 있고(원문 130행), 표시상 총 clean text 80,794자 중 앞 37,219자와 뒤 12,459자만 포함된다(원문 188–191행). 따라서 이 노트는 **초록, 서론~§3.3의 접근 가능한 부분 및 참고문헌 일부**에 한정한다. **abstract-only 자료는 아니지만, 원문 전체를 읽은 분석도 아니다.** |

## 2. 핵심 주장

1. **문제 정의 — 단일 정적 온디바이스 LLM은 요청별로 서로 다른 지연 SLO를 충족하기 어렵다.**
   - 저자들은 하나의 온디바이스 LLM 서비스가 여러 앱·작업에 공유된다고 전제하고, 정적 모델이 이질적 SLO를 만족하지 못한다고 주장한다(원문 22–25행). 특히 prefill과 decode는 각각 TTFT와 TPOT로 측정되며, 앱 유형에 따라 두 지표의 요구가 달라진다고 설명한다(원문 24행; 표 1은 41–42행).

2. **ElastiLM의 중심 해법은 모델 크기와 프롬프트 길이를 함께 탄력화하는 것이다.**
   - ElastiLM은 모델과 프롬프트 두 차원을 탄력화한다고 제시한다(원문 14행, 29–35행). 온라인 요청은 프롬프트와 SLO를 입력으로 받아, 압축 프롬프트와 알맞은 서브모델을 선택한 뒤 추론한다(원문 71–73행).

3. **모델 탄력화의 핵심은 permutation-consistent unit의 오프라인 one-shot 재배치이며, 온라인 전환의 데이터 이동을 피하려는 설계다.**
   - Transformer에서 attention head와 MLP neuron을 permutation-consistent unit으로 규정한다(원문 94–96행). 단위 중요도 순으로 블록 내부를 오프라인 재배치해 연속 메모리 구간을 서브모델로 만들고(원문 97–101행), 온라인에서는 메모리 포인터 이동과 adapter 교체로 모델을 전환한다고 주장한다(원문 102–103행).

4. **프롬프트·모델 압축 비율의 조합은 내용 의존적이므로, dual-head TLM이 이를 결정해야 한다.**
   - 동일 SLO를 만족하는 프롬프트/모델 압축 조합도 생성 정확도가 다를 수 있다고 주장하며(원문 28행, 60행, 70행), MobileBERT 변형 TLM의 score-head가 토큰 보존 중요도를, decision-head가 프롬프트·모델 탄력화 수준을 선택하도록 설계한다(원문 117–122행).

5. **평가상 저자들은 ElastiLM이 SLO 충족 조건에서 정확도·전환 오버헤드·메모리 측면의 이점을 보였다고 주장한다.**
   - 초록은 7개 강한 baseline 대비 end-to-end trace에서 절대 정확도 최대 14.83%p·평균 10.45%p 향상, TTFT 전환 오버헤드 1% 미만, 유사 메모리 사용량, 오프라인 GPU 100시간 미만을 주장한다(원문 14행). 본문 서론은 standalone dataset에서 최대 40%라는 별도 수치도 제시한다(원문 36행). 이들은 저자 보고치이며, 접근 가능한 텍스트에는 전체 평가표·분산·통계검정이 없다.

## 3. 주장과 분리한 근거·관찰

| 근거/관찰 | 원문 위치 | 이 근거가 뒷받침하는 주장 |
|---|---|---|
| 모바일 앱별 SLO 표: chatbot은 readable TTFT/TPOT, always-on voice assistant는 very-low TTFT·medium TPOT, API-calling/UI-automation agent는 low TTFT·acceptable TPOT 등으로 구분 | 41–42행, 표 1 | 요청별 SLO의 이질성(핵심 주장 1) |
| LLaMA-7B를 Redmi K60 Champion(Snapdragon 8 Gen 2), big core 4 thread에서 측정한 결과로, TTFT는 prompt length와 model size의 영향을 모두 받고 TPOT는 주로 model size에 의해 결정된다고 서술 | 50행, 61–62행; 그림 2는 43–45행 | 두 차원 탄력화의 동기(핵심 주장 2) |
| 구조적 pruning으로 만든 LLaMA-7B 20% 서브모델을 Redmi K60 Champion에서 30%로 바꾸는 데 8.2초가 걸렸다는 사례 | 27행 | 기존 전환 방식의 요청 수준 오버헤드 문제 및 one-shot 재배치의 필요성(핵심 주장 3) |
| WQ 4096×4096 행렬의 데이터 이동이 최악 조건 139ms이고, 모델 전체 전환은 초 단위 오버헤드라고 설명 | 65–66행 | 연속 메모리와 데이터 이동 회피의 동기(핵심 주장 3) |
| ARC_E 예시에서 40% TTFT SLO 아래 50% prompt/80% sub-model은 `cytotoxic T lymphocytes`, 80% prompt/50% sub-model은 `phagocytes`를 낸다는 그림 | 57–60행 | 압축 비율 조합의 민감성(핵심 주장 4) |
| Octopus에서 무작위 전략이 full LLaMA-7B의 50% TTFT·80% TPOT SLO에서 oracle 전략보다 top-5 API selection 정확도 15.2% 낮았다고 보고 | 28행 | TLM 기반 orchestration 필요성(핵심 주장 4) |
| 전환 시 WQ를 4096×4096으로 키우는 데 제안 방식은 2ms, naive pruning은 140ms 데이터 이동이라고 제시 | 102–103행 | 온라인 전환 비용 감소 주장(핵심 주장 3) |
| TLM은 약 40M parameter이며, 압축된 LLM prompt를 기준으로도 원래 LLM TTFT의 5% 이내에서 기기 내 추론 가능하다고 서술 | 124행 | orchestration 자체의 런타임 비용이 제한적이라는 주장(핵심 주장 4) |

## 4. 수치·정의·방법론

### 4.1 정의와 측정 프레임

- **SLO 정의:** 본문은 LLM 서비스 SLO를 `<ζ_TTFT, ζ_TPOT>`로 정의하며, 각 ζ는 full LLM latency 대비 compression ratio다. 서비스 개발자가 제공할 SLO를 미리 정한다(원문 71–73행).
- **지연 단계:** prefill은 prompt processing 단계, decode는 token generation 단계이며 각각 TTFT, TPOT로 측정된다(원문 24행).
- **관계식(저자 서술):** `TTFT ∝ PromptLength × ModelSize`, `TPOT ∝ ModelSize` (원문 61–62행). 단, prompt가 매우 길어 10K token을 넘으면 attention이 지배적이어서 TPOT도 prompt length의 영향을 받는다는 단서가 있다(원문 67행의 각주 2).
- **측정 장치·조건:** 그림 2의 LLaMA-7B 지연 측정은 Redmi K60 Champion, Snapdragon 8 Gen 2에서 했고(원문 45행), 본문은 big core 4 thread 사용을 명시한다(원문 50, 61행).

### 4.2 모델 탄력화 방법

- **단위와 성질:** permutation-consistent unit은 블록의 입출력을 바꾸지 않고 서로 재배열할 수 있는 신경망 단위로 정의된다(원문 80–82행). Transformer attention에서는 WQ/WK/WV의 같은 인덱스 열과 WO의 해당 행으로 된 attention head, MLP에서는 Wup의 열과 Wdown의 해당 행이 각각 단위다(원문 94–96행).
- **중요도 추정:** calibration corpus `C` 위 next-token prediction loss `L`를 이용하고, unit `i`의 중요도를 `imp_i = |L − L_{W_i=0}|`로 정의한 뒤 `|∂L/∂W_i · W_i|`를 근사치로 쓴다(원문 104–106행). 기본 `C`는 BookCorpus의 부분집합이다(원문 110행).
- **서브모델 구성:** 단위를 중요도 내림차순으로 블록 내부에서 재배열하고, 연속 접두 구간을 개발자가 정한 크기의 서브모델로 묶는다(원문 99–101행). 기본은 전체 비율 20%~100%, 10%p 단위이며, 이 비율을 탄력화 대상 Transformer layer에 균등하게 나눈다(원문 101행).
- **anchor layer:** layer 제거 시 loss 증가로 layer 중요도를 재며, 저자들은 중요도가 power-law/80:20 분포를 보이고 약 20% layer가 anchor layer라고 서술한다. 이 layer는 탄력화에서 제외한다(원문 110–111행).
- **회복:** 각 서브모델의 고정 WQ/K/V/O 및 Wup/down에 LoRA를 붙여 next-token prediction으로 task-agnostic recovery를 수행한다(원문 112–115행). 기본 LoRA rank는 8, LoRA weight는 전체 LLM weight의 0.1%~0.5%, fine-grained 설정에서도 추가 메모리는 5% 미만으로 제시된다(원문 113–114행). 기본 recovery data는 Alpaca-cleaned 약 50M token이다(원문 115행).

### 4.3 프롬프트 탄력화·결정 방법

- **TLM 구조:** MobileBERT 기반이며, MobileBERT는 BERT_base parameter의 20%이면서 GLUE 정확도 손실 0.7%라는 기존 특성을 인용한다(원문 117–118행). SLO를 자연어 특수 토큰으로 embedding에 넣고, 예로 `[05]`는 50% TTFT, `<08>`은 80% TPOT을 나타낸다(원문 118–119행).
- **두 head의 역할:** score-head는 각 토큰을 retain/discard 이진 분류한다. decision-head는 prompt 및 model 탄력화 수준을 각각 다중분류한다(원문 121행). 두 head는 기본적으로 24개 중 하위 12개 layer를 공유한다(원문 121행).
- **학습 라벨:** generic corpus의 prompt·ground truth에 대해 가능한 strategy를 모두 순회해 inference result를 얻고, 최적 strategy를 라벨로 기록하는 self-induced labelling을 사용한다고 설명한다(원문 32–35행; 그림 12는 120행).
- **온라인 안전장치:** decision-head 출력이 SLO를 충족하지 못하면 runtime check 뒤 SLO를 엄격히 만족하는 random decision으로 fallback한다(원문 122행).

### 4.4 저자가 제시한 성능·비용 수치

- 구현/평가 범위는 COTS smartphone 3대, base·instruction-tuned LLM 5종(3B~7B), ARC_E·OBQA·PIQA·SCIQ·LlamaTouch·Octopus 및 end-to-end synthesized trace다(원문 36행).
- full LLM 대비 절대 정확도 2%p 이내 손실 조건에서 TTFT 최대 5×, TPOT 최대 2× 가속이라고 주장한다(원문 36행).
- LLaMA-7B를 MI14 smartphone용으로 탄력화하는 데 68.3 GPU hours 및 GPU 임대비 100달러 이내라고 제시한다(원문 37행).
- 초록의 `<1% TTFT switching overhead`, on-par memory, `<100 offline GPU hours`와 본문의 68.3 GPU hours는 서로 병기되지만, 접근 가능한 범위에서는 이 측정의 반복·분포·정확한 구성은 확인되지 않는다(원문 14, 37행).

## 5. 원문 한계 및 확인 필요 항목

1. **접근 가능한 raw artifact의 중간 본문 결손:** §3.3 뒤의 본문, 특히 평가 방법·baseline 정의·실험표·ablation·한계 논의가 현재 artifact에서 생략되어 있다(원문 130, 188–191행). 따라서 정확도·메모리·오버헤드 주장은 저자 제시값으로만 기록했으며, 재현성·통계적 안정성·조건별 결과를 이 자료 접근범위만으로 검증할 수 없다.
2. **수치의 비교 조건 불완전:** “7 strong baselines”, “on-par memory”, “all request SLOs” 및 end-to-end trace 결과가 언급되지만(원문 14, 36행), 접근 범위에는 baseline 이름·동일 하드웨어/모델/정확도 지표·trace 생성 방식·신뢰구간이 없다. 이후 전체 본문을 확보할 경우 이 조건을 확인해야 한다.
3. **기기 일반화의 제한:** 저자는 3대 COTS smartphone과 3B~7B 모델 5종을 언급한다(원문 36행). 그러나 현재 접근 범위에는 각 기기·SoC·runtime별 완전한 결과가 없고, 지연 관계의 명시적 측정 사례는 Redmi K60 Champion/Snapdragon 8 Gen 2/4 big-core thread다(원문 45, 50, 61행). 다른 모바일 하드웨어로의 일반화는 이 원문 범위만으로 확정할 수 없다.
4. **SLO 충족의 실제성:** SLO는 full LLM latency 대비 비율로 사전 정의된다(원문 72행). 이는 절대 밀리초 예산, 사용자 체감 기준, 온도·전력·동시 실행 등 동적 운영 조건을 직접 정의한 것은 아니다. 이 구분은 정의의 범위에서 확인해야 한다.
5. **TLM fallback의 품질 영향 미상:** SLO 미충족 TLM 판단 시 random decision으로 fallback한다고 하나(원문 122행), 접근 가능한 범위에는 발생 빈도와 fallback 후 품질 결과가 없다.
6. **offline 비용의 범위:** 68.3 GPU hours/100달러 미만은 LLaMA-7B→MI14 사례로 제시된다(원문 37행). 모든 모델·기기·서브모델 수준에 일반화되는 비용인지, GPU 종류·임대 단가·재학습 횟수가 무엇인지는 접근 범위에 없다.
