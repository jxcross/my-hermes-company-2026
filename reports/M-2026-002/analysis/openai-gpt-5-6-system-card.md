# S02 — OpenAI GPT-5.6 System Card

- 원자료: `raw/openai-gpt-5-6-system-card.md` (공식 system card, 2026-07-09)
- 성격: 제공자 자기보고. 수치·비교는 해당 card의 평가 설정 안에서만 해석한다.

## 핵심 주장과 근거
1. **주장:** GPT-5.6 평가는 단일 점수 대신 reasoning effort 수준별 curve를 제시해야 한다. [§1, L97–101]
   - **근거:** effort가 문제 풀이에 쓰는 thinking 양이며 capability와 필요한 effort를 함께 보이기 위함이라고 설명한다. [L97–101]
2. **주장:** production-prompt 기반 deployment simulation은 방향성 신호를 제공하나 저빈도 행동의 정밀도에는 한계가 있다. [§3.1.2, L210–232]
   - **근거:** GPT-5.5 대화 prefix의 final turn을 GPT-5.6 Sol로 resample하고 자동 label했으며, low-prevalence behavior label은 제한적 precision일 수 있다고 명시한다. [L226–232]
   - **수치:** harassment 정책 위반은 100,000 production turns당 약 8.6으로 추정. simulation의 median symmetric multiplicative error는 1.2x. [L234–238, L271–277]
3. **주장:** direct model robustness와 production safety stack의 효과를 구분한다. [§4.1, L372–402]
   - **근거:** jailbreak 평가는 full production safeguards 없이 model layer를 시험하며, 실제 배포에는 classifier 등 추가 safeguards가 있다고 설명한다. comparative 결과는 ‘directional rather than definitive’라고 한정한다. [L374–402]
4. **주장:** prompt injection 평가는 connector 및 search/function-calling 공격을 별도 측정한다. [§4.2, L411–427]
   - **근거/수치:** Table 5에서 gpt-5.6 Sol은 Connectors 1.000, Search and Function-Calling 0.910; Terra는 1.000/0.946, Luna는 0.999/0.897로 보고된다. [L424–427]

## 핵심 수치·정의
- automated universal-jailbreak 탐색에 700,000 A100e GPU-hours 이상을 투입했다고 서술한다. [§1, L79–85]
- challenging production benchmark의 primary metric은 `not_unsafe`; 이 benchmark의 error rate는 평균 production traffic을 대표하지 않는다고 명시한다. [§3.1.1, L154–174]

## 사용 경계·상충 표시
- 이전 모델 score는 policy·grader·dataset·measurement detail 변화 때문에 직접 비교 불가할 수 있다. [L176–183]
- `S03`의 GPT-Red robustness 수치와 모두 OpenAI 자기보고이며 독립 재현 근거가 아니다. Cross-Verify에서 원 평가 설정과 외부 시험을 분리할 필요가 있다.
