# S03 — OpenAI GPT-Red 자동 red teaming

- 원자료: `raw/openai-gpt-red-robustness.md` (공식 블로그, 2026-07-15)
- 성격: 제공자 자체 연구·자체 benchmark 결과. 공격 모델과 일부 환경은 비공개다.

## 핵심 주장과 근거
1. **주장:** human red teaming만으로는 공격 데이터의 양·다양성을 확장하기 어려우며, GPT-Red를 자동 red-teamer로 학습해 GPT-5.6 학습에 사용했다. [§Summary, L21–47]
   - **근거:** GPT-Red는 prompt 전송→응답 관찰→반복을 수행하고, production model training에 직접 편입했다고 기술한다. [L43–47]
2. **주장:** self-play RL은 red-teamer와 defender를 동시 학습시켜 점점 강한 공격을 탐색하게 한다. [§Training GPT-Red through self-play, L92–100]
   - **근거:** GPT-Red의 reward는 valid failure elicitation, defender의 reward는 공격 저항과 원 task 완수이며, 위협모델은 local file·web banner·email·tool output 중 attacker가 통제하는 부분과 성공 정의를 명시한다. [L94–98]
3. **주장:** GPT-Red가 novel scenario에도 일반화할 수 있다고 보고한다. [§How strong, L102–108]
   - **근거/수치:** Dziemian et al. (2025) arena 복제 환경에서 GPT-5.1 대상 성공 scenario 비율을 GPT-Red 84%, human red-teamers 13%로 보고한다. internal mirror와 복제 환경 결과임을 유지해야 한다. [L104–108]
4. **주장:** GPT-Red 기반 학습 후 direct prompt injection robustness가 개선되었다. [§Improving robustness, L124–138]
   - **근거/수치:** hardest direct benchmark에서 4개월 전 최선 production model 대비 실패가 6배 적었다고 하며, GPT-Red direct injection 실패율은 0.05%, Fake-CoT 공격은 GPT-5.1에서 95% 이상→GPT-5.6 Sol에서 10% 미만이라고 서술한다. [L45–47, L126–132]

## 정의·방법론
- **Valid failure:** successful prompt injection 같은, 사전 위협모델이 정의한 공격 성공. [L94–98]
- 제품 모델과 GPT-Red를 분리해 malicious capability를 배포하지 않는다고 한다. [L98–100]

## 사용 경계·상충 표시
- 84%/13%, 0.05%, 6x는 evaluator·defender·held-out 환경의 구성과 공개 여부가 제한된 OpenAI 보고 수치다.
- `S02` 역시 jailbreak 결과를 directional로 한정한다. 두 자료 모두 robustness의 독립 일반화를 확증하지 않는다.
