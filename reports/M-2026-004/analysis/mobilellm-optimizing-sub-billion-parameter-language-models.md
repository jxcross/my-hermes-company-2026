# 원자료 심층 분석 노트 — MobileLLM

## 1. 자료 식별 및 접근 범위

- **자료 식별자:** `mobilellm-optimizing-sub-billion-parameter-language-models`
- **제목:** *MobileLLM: Optimizing Sub-billion Parameter Language Models for On-Device Use Cases*
- **URL:** https://arxiv.org/abs/2402.14905v2
  - 원문 PDF URL: https://arxiv.org/pdf/2402.14905v2
- **유형:** 학술 논문(ICML 2024 표기; 원문 54–56행)
- **원문 버전·시점:** arXiv v2. 원문에 관측된 최초 게시 시각은 2024-02-22, 최종 갱신 시각은 2024-06-27이며, 수집일은 2026-08-03이다(원문 3–10행). `sources.yaml`의 해당 record도 같은 v2 URL, academic 유형, selected 상태를 명시한다(`raw/sources.yaml` 18–27행).
- **원문 접근범위:** 제공된 버전 고정 arXiv PDF의 pypdf 텍스트 추출본 전체(초록, 본문 1–5절, 부록 A–J, 표·그림 캡션·참고문헌)를 읽었다(원문 10–12행, 19–1599행). 따라서 **abstract-only 자료가 아니다**. 다만 PDF 추출 순서·표 레이아웃이 일부 흐트러져 있어(예: 본문 중 Table 9/10 일부가 앞쪽에 혼입) 아래 위치 표기는 제공된 원문 텍스트의 행 번호와 표/절명을 병기한다.

## 2. 핵심 주장

### 주장 1 — sub-billion LLM에서는 파라미터 수·데이터·학습 반복만이 아니라 아키텍처, 특히 깊고 얇은 구조가 성능에 중요하다
- **원문 위치:** 초록 24–36행; §1 기여 251–257행; §2.2.2 337–369행; 결론 821–827행.
- 저자들은 125M 및 350M급에서 폭보다 깊이를 늘린 구조가 동일하거나 유사한 모델 크기에서 더 좋은 성능을 낸다고 주장한다. 19개 모델(약 125M 9개, 약 350M 10개)을 깊이·폭만 달리하여 학습했고, 여러 zero-shot 상식추론 및 QA/독해 과제에서 더 깊고 얇은 모델이 대체로 우세했다고 서술한다(346–363행).
- 125M 부근에서는 30층 또는 42층 모델이 12층 모델보다 유의하게 좋았다고 하며(364–369행), 부록은 sub-billion 모델의 최적 깊이가 약 30층이라는 결론을 제시한다(1203–1208행).

### 주장 2 — SwiGLU, 입력-출력 임베딩 공유, GQA를 결합한 MobileLLM이 125M/350M급의 강한 기본망을 이룬다
- **원문 위치:** §2 도입 279–312행; §2.2.1 327–336행; §2.2.3 370–428행; §2.2.4 429–469행; 부록 B 1182–1194행.
- 설계 조합은 SwiGLU FFN, deep-and-thin 구조, input-output embedding sharing, grouped-query attention(GQA)이다(287–295행, 464–469행).
- 저자들의 해석은 sub-billion 모델에서는 임베딩이 전체 파라미터에서 차지하는 비중이 크므로, 공유로 확보한 저장 예산을 깊이에 재배치하는 것이 유리할 수 있다는 것이다(371–381행, 411–428행).
- GQA는 query head 대비 KV head를 줄여 중복을 낮추고, 저장된 모델 크기를 유지하도록 embedding dimension을 키웠을 때 125M에서 추가 성능 향상을 보였다고 주장한다(441–463행).

### 주장 3 — 인접 블록 즉시 반복(immediate block-wise weight sharing)은 모델 저장 크기를 늘리지 않고 정확도를 높이며, 모바일 메모리 계층에서 지연 오버헤드를 작게 유지할 수 있다
- **원문 위치:** 초록 37–42행; §1 기여 262–266행; §2.3 470–519행; §3.6 721–747행; 결론 824–828행.
- 제안 방식은 인접한 두 transformer block이 같은 가중치를 공유하고 이를 즉시 두 번 계산하는 방식이다. 저자들은 모바일 SoC의 SRAM이 대개 단일 transformer block 정도만 담을 수 있다는 전제에서, 인접 반복은 가중치를 SRAM에 유지해 SRAM–DRAM 이동을 피한다고 설명한다(487–517행).
- repeat-all-over 공유가 정확도는 약간 높을 수 있으나, 캐시 활용 관점에서 즉시 블록 단위 공유를 채택했다고 명시한다(507–519행). 즉, 본 논문의 선택은 정확도 최대화만이 아니라 데이터 지역성에 관한 하드웨어 가정에 의존한다.

### 주장 4 — MobileLLM 계열은 저자 평가에서 기존 동급/일부 더 큰 sub-billion 모델보다 높은 일반 벤치마크·채팅 성능을 보이고, 350M 모델은 특정 API 호출 정확도에서 LLaMA-v2 7B와 근접한다
- **원문 위치:** 초록 34–48행; §3.2 530–608행, 표 3·4(552–573행); §3.3 632–692행, 표 5·6(612–626행, 660–668행).
- zero-shot 상식추론 평균에서 MobileLLM-125M/350M은 각각 46.3/51.3, layer-sharing 버전은 47.0/52.1로 표에 제시된다(표 3, 555–556행). 저자들은 이전 SOTA 대비 125M에서 2.7점, 350M에서 4점 이상 개선이라고 요약한다(578–590행).
- 채팅 평가에서 MobileLLM-LS-350M은 MT-Bench 3.16, AlpacaEval 승률 48.20%로 제시되며, 비교 기준 text-davinci-001의 self-win rate 50%를 근거로 유사한 채팅 성능이라고 해석한다(625–651행).
- API 호출에서 MobileLLM-350M의 intent/structure exact match는 65.3/48.8, LLaMA-v2 7B는 62.8/50.9이다(표 6, 660–668행). 저자들은 이 두 exact-match 지표가 근접하다고 하되, ROUGE-1/-L은 46.8/44.6 대 56.5/54.3으로 350M이 낮음을 함께 인정한다(682–690행).

### 주장 5 — 제안 구조는 W8A8 사후 양자화와 양립하며, 지식증류는 이 실험 설정에서 비용 대비 이득이 없었다
- **원문 위치:** §3.4–3.5 693–731행; 부록 F–G 1235–1240행, 1267–1282행; 표 15·16(1291–1308행).
- 0.25T token으로 학습한 125M/350M MobileLLM 및 LS 모델에서 per-token min-max W8A8 PTQ의 평균 정확도 차이는 0.0–0.4점으로 표에 제시되며, 저자들은 0.5점 이내라고 요약한다(693–700행; 1291–1301행).
- LLaMA-v2 7B teacher를 쓴 KD는 label-only와 비슷하거나 낮은 정확도였고, 학습 시간은 2.6–3.2배 느렸다고 보고한다(729–731행; 1279–1282행).

## 3. 주장과 분리한 근거·관측치

- **모바일 메모리·에너지 문제 설정:** 그림 2는 iPhone 15 6GB, Pixel 8 8GB/Pro 12GB, Snapdragon 8 8–12GB DRAM 등의 예를 제시하고, 본문은 모바일 앱이 공유 DRAM의 10%를 넘지 않아야 한다고 서술한다(157–212행, 220–230행). 또한 인용한 가정(모델 파라미터 10억 개당 0.1 J/token)으로 7B는 0.7 J/token, 350M 8-bit는 0.035 J/token이라고 계산한다(231–245행). 이는 저자 계산·인용 기반의 문제 동기이며, 실측 배터리 수명 결과와 동일시할 수 없다.
- **SwiGLU ablation:** 125M zero-shot reasoning 평균이 vanilla FFN 42.6에서 SwiGLU 43.9로 바뀌었다(329–336행; 표 10의 해당 행 1200행).
- **임베딩 공유 ablation:** 30층 125M 실험에서 embedding sharing은 135M→119M(16M, 약 11.8%)로 줄이고 평균 정확도는 44.8→44.6이었다. 이후 32층으로 늘린 공유 모델은 125M·45.0으로 제시된다(390–395행, 411–420행).
- **GQA ablation:** 16 query heads에서 KV heads를 16→4로 줄이면 125M에서는 유사 정확도, 350M에서는 0.2점 하락과 거의 10% 모델 크기 감소가 있었다고 서술한다. 이어 GQA와 embedding dimension 증대로 125M 정확도가 0.4점 증가했다고 한다(450–463행).
- **layer-sharing 방식별 비교:** 표 2에서 immediate / repeat-all-over / reverse를 비교한다. 예를 들어 350M의 평균은 baseline 49.6, immediate 50.2, repeat-all-over 50.7, reverse 50.1이다(544–551행). 즉 저자도 immediate가 해당 정확도 표의 최고 방식이라고 말하지 않으며, 채택 근거는 캐시 활용이다.
- **온디바이스 프로파일링:** iPhone 13(iOS 17.2.1), ExecuTorch, MPS backend, FP16 조건에서 50회 평균 실행 시간을 측정했다(732–738행). MobileLLM 125M / LS-125M / 60층 비공유의 Load·Init·Execute는 각각 39.2·1361.7·15.6ms / 43.6·1388.2·16.0ms / 68.6·3347.7·29.0ms이다(721–728행). 본문은 LS의 loading+initialization 2.2%, execution 2.6% 증가, 60층 비공유의 loading+initialization 143% 및 execution 86% 증가로 해석한다(739–747행).

## 4. 수치·정의·방법론

### 모델 및 설계 정의

- **MobileLLM 사양:** 125M은 30층·9 heads·3 KV-heads·embedding 576·hidden 1536·124.6M params, 350M은 32층·15·5·960·2560·345.3M params이다(표 9, 1170–1177행). 표 3의 LS 모델 `#Layers`는 **서로 다른 가중치를 가진 층 수**를 센다고 정의한다(552–556행).
- **GQA 정의:** KV-head 수가 query head 수의 `1/n`이고, KV-head를 `n`회 반복해 attention score·output 계산에 사용한다. `n`은 query head 수를 나누는 양의 정수다(441–449행).
- **즉시 블록 공유 정의:** transformer block은 MHSA와 FFN으로 구성되며, immediate block-wise sharing은 같은 가중치를 가진 인접 block을 즉시 두 번 연산하는 구성이다(503–514행).

### 학습·평가 방법

- **학습:** 32 A100 GPU, GPU당 batch size 32. 탐색 실험은 120k iterations/0.25T tokens, 표 3·4의 최종 모델은 480k/1T tokens다(313–318행). 본 학습은 Adam, weight decay 0.1, 초기 learning rate 2e-3, cosine decay로 기술된다(522–529행).
- **zero-shot 평가 과제:** ARC-easy, ARC-challenge, BoolQ, PIQA, SIQA, HellaSwag, OBQA, WinoGrande이며, 추가로 TriviaQA(TQA)와 RACE를 평가했다(319–326행). 기존 baseline 결과는 일관된 절차를 위해 공개 Hugging Face 모델로 평가했다고 한다(531–535행).
- **채팅 평가:** 모델과 기존 체크포인트를 동일 조건에서 fine-tune했으며, AlpacaEval(단일 턴)과 MT-Bench(다중 턴)를 사용했다(637–643행). AlpacaEval은 GPT-4가 text-davinci-001 대비 pairwise win rate를 채점하고, MT-Bench는 GPT-4가 1–10으로 채점한 2턴 평균이다(1341–1347행).
- **API 호출 평가:** 자연어 입력을 API JSON 구성으로 변환하는 과제로 정의한다(656–673행). 합성 데이터는 train 5,000, test 2,500 samples, 표본당 평균 8 conversation turns이며 4 epochs fine-tuning(Adam, 2e-5에서 선형 감쇠, weight decay 0.01)을 적용했다(674–681행). `EM_intent`/`EM_structure`는 API 호출 exact match, `R1`/`RL`은 agent response 품질의 ROUGE-1/-L이다(660–662행).
- **양자화 방법:** 0.25T token 학습 모델에 대해 weight·activation을 모두 8-bit로 하는 per-token min-max PTQ(W8A8)를 적용했다(693–700행; 1235–1240행).
- **지식증류 방법:** teacher LLaMA-v2 7B와 student 125M/350M의 logits 간 cross-entropy KD loss를 사용했고, 비교 실험은 32 A100 80G, batch 32, 120k iterations 조건이다(1241–1282행).

## 5. 원문 한계 및 확인 필요 항목

1. **실기기 지연 근거의 범위가 좁다.** 온디바이스 프로파일링은 iPhone 13·iOS 17.2.1·ExecuTorch·MPS·FP16 및 125M 계열만을 대상으로 하며(732–738행), 350M·W8A8·다른 스마트폰 SoC/NPU 또는 긴 컨텍스트에서의 속도·메모리·전력은 이 원문 실측 결과로 확인되지 않는다.
2. **에너지·배터리 및 앱 메모리 수치는 저자 가정/계산을 포함한다.** 7B와 350M의 J/token, 대화 가능 시간, ‘앱은 DRAM 10% 이내’ 서술은 인용 자료와 가정에 기초한 동기 제시다(220–245행). 제공된 원문만으로 각 기기에서의 일반화 가능한 실측 배터리 지속시간으로 검증할 수 없다.
3. **성능 비교의 재현 조건을 원문만으로 완전 복원하기 어렵다.** baseline을 Hugging Face 공개 모델로 재평가했다고 설명하지만(531–535행), 제공 텍스트에는 각 baseline의 정확한 checkpoint revision, prompt/template, decoding 설정, 하드웨어·평가 코드 세부가 모두 제시되지 않는다. 재현·공정성 검증에는 저자 코드 및 부록 밖의 실행 설정 확인이 필요하다.
4. **API 호출 결과의 외적 타당성은 제한적이다.** 데이터가 언어모델로 생성한 합성 대화이고 5,000/2,500 표본, 평균 8턴이라는 설정이다(674–681행; 1348–1351행). 실제 API 실행 성공률, 권한·도구 오류 처리, 안전성, 현실 사용자 요청 분포는 이 결과가 다루지 않는다. 또한 MobileLLM-350M은 LLaMA-v2 7B에 비해 ROUGE가 낮다(682–690행).
5. **채팅 품질의 평가는 GPT-4 judge 및 특정 reference에 의존한다.** AlpacaEval은 GPT-4 평가와 text-davinci-001 대비 승률이고, MT-Bench도 GPT-4 채점이다(612–626행; 1341–1347행). 사람 평가, 안전성, 사실성, 장기 대화 신뢰성은 이 원문의 표만으로 확정할 수 없다. 부록에 수록된 생성 사례에는 부정확하거나 부적절해 보일 수 있는 응답도 존재하지만(예: 선물 포장 답변, 1471–1487행), 저자들이 이를 체계적 오류 분석으로 정량화하지는 않는다.
6. **‘최적 깊이’ 및 설계 우위의 일반화 범위가 제한된다.** 깊이 탐색은 논문이 정한 약 125M/350M 및 특정 데이터·학습 예산·과제에서 이뤄졌고(346–363행; 1203–1208행), 다른 토크나이저·언어·데이터 규모·컨텍스트 길이·멀티모달 설정에 대한 동일한 결론은 원문에서 검증되지 않는다.
7. **논문의 중심 범위는 sub-billion이지만 부록은 1B·1.5B까지 확장한다.** 본문은 주로 125M·350M을 조사한다고 명시하고(1127–1132행), 600M·1B·1.5B 결과는 부록에 있다. 따라서 온디바이스 실측과 직접 연결된 근거는 이 확장 모델들에는 제공되지 않는다.
8. **원문 추출 품질 점검 필요:** 제공 artifact는 PDF 텍스트 추출본이며(10행), 앞부분에 표가 비정상 위치에 나타나고 표 행이 압축되어 있다(예: 157–208행). 표 숫자를 인용·재사용할 때는 원 PDF의 시각적 표와 대조 확인이 필요하다.
