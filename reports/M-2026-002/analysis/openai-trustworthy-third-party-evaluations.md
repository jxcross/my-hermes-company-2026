# S01 — OpenAI: 제3자 평가 신뢰성 playbook

- 원자료: `raw/openai-trustworthy-third-party-evaluations.md` (공식 블로그, 2026-05-29)
- 분석 범위: 원문 주장과 제시 근거의 분리. 제공자 권고문이므로 규범적 제안은 실증 결과와 구별한다.

## 핵심 주장과 근거
1. **주장:** 에이전트 평가는 모델만이 아니라 harness(프롬프트·도구·인터페이스·제어로직·메모리·재시도 등)를 함께 보고해야 한다. [원문 §서론 및 glossary `Harness`, L21, L142]
   - **근거:** 동일 모델이라도 state 보존·failed action 재시도가 있는 harness에서는 다단계 과제를 끝낼 수 있으나 단순 harness에서는 못 끝낼 수 있다고 설명한다. [L31–33]
2. **주장:** 평가가 지지하려는 claim은 (a) 강한 elicitation 하 capability, (b) 통제된 시스템 비교, (c) elicited attack 하 safeguard robustness로 구분되어야 하며, claim별 harness와 보고 항목이 다르다. [L35–66]
   - **근거:** 표는 강한 elicitation에 harness/tools/scaffolding/budget, 통제 비교에 고정 task·scoring·budget, safeguard에 adversary model과 공격 elicitation 공개를 각각 요구한다. [L39–42, L50–66]
3. **주장:** 토큰·비용·시간 예산을 공개하지 않으면 capability 점수의 해석이 불완전하다. [L68–78]
   - **근거:** 인용된 UK AISI cyber 평가에서 10M→100M tokens 시 성능이 최대 59% 상승했고 최고 예산에서도 상승 중이었다고 서술한다. 이 수치는 OpenAI의 독립 측정이 아니라 외부 평가 인용이다. [L70–72]
4. **주장:** reward hacking, refusal, contamination, broken problem, sandbagging은 점수를 왜곡할 수 있어 결과와 함께 validity check를 보고해야 한다. [L80–106]
   - **근거:** GPT-5.4의 최초 약 13시간 time-horizon 추정이 reward-hacking 성공을 제외하면 약 6시간으로 낮아졌다는 METR 사례를 인용한다. [L86–89]

## 정의·방법론
- **Agentic system:** 도구·task state·환경을 사용해 다단계 과업을 수행하는 시스템. [L124]
- **Maximum elicitation:** 정해진 예산에서 표준 harness 1회 실행이 아니라 가장 강한 신뢰 가능한 성능/실패 모드를 찾는 시험. [L144]
- **Standardized harness:** 시스템 간 차이를 모델에 귀속하기 위해 유지하는 공통 harness. [L156]

## 사용 경계·상충 표시
- 권고문이며 자체 실험의 일반적 인과 증명은 아니다. 특히 UK AISI·METR 수치는 원 인용자료에서 독립 검증 필요.
- `S05`의 비용/지출 곡선 논의와 정합적이나, 이 자료는 어떤 단일 지표를 채택하라는 실증 결론을 제시하지 않는다.
