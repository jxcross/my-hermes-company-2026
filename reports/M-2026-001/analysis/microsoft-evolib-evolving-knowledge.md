# EvoLib: Turning experience into evolving knowledge — 분석 노트

## 자료 식별
- 자료: raw/microsoft-evolib-evolving-knowledge.md
- 원문 URL: https://www.microsoft.com/en-us/research/blog/evolib-turning-experience-into-evolving-knowledge/
- 발행일/수집일: 2026-07-30 / 2026-08-02 (raw/microsoft-evolib-evolving-knowledge.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: EvoLib는 inference 중 자체 경험에서 학습하며 ground-truth labels나 external feedback이 필요 없다.
   - 근거: “Self-supervised… without requiring ground-truth labels or external feedback” (raw/microsoft-evolib-evolving-knowledge.md:19).
2. 주장: 단순 memory archive는 learning이 아니며, EvoLib는 raw experience를 reusable skills와 reflective insights로 변환한다.
   - 근거: memory alone is not learning이라고 설명하고, EvoLib가 raw experience를 evolving library of knowledge로 변환한다고 제시 (raw/microsoft-evolib-evolving-knowledge.md:24,26,28).
3. 주장: EvoLib는 모델 weight 업데이트 없이 API 기반 black-box LLM/AI systems에도 적용 가능하다.
   - 근거: “does not require model updates… any black-box language models and AI systems deployed through APIs” (raw/microsoft-evolib-evolving-knowledge.md:23,26).
4. 주장: EvoLib는 retrieval-based memory approaches 및 abstract memory mechanisms보다 더 효율적인 token usage와 성능을 보인다.
   - 근거: 다양한 challenging tasks에서 top retrieval-based memory approaches와 other abstract memory mechanisms를 outperform한다고 서술 (raw/microsoft-evolib-evolving-knowledge.md:32-37).

## 핵심 수치·정의·방법론
- 지식 단위: successful solution에서 distilled reusable skill 또는 mistakes에서 learned reflective insight (raw/microsoft-evolib-evolving-knowledge.md:28).
- 핵심 메커니즘: Consolidation(유사 지식 통합), Weighting mechanism(현재 utility와 미래 useful knowledge 기여도를 기준으로 중요도 갱신) (raw/microsoft-evolib-evolving-knowledge.md:29-31).
- 평가 task 유형: efficiency constraints가 있는 code writing, long-horizon environment interaction/decision-making (raw/microsoft-evolib-evolving-knowledge.md:32-34).
- 수치: 추출본에는 구체 점수·표본 수 없음. Figure 2의 정량 곡선 설명만 있음 (raw/microsoft-evolib-evolving-knowledge.md:36-38).

## 상충·불일치 표시
- SkillOpt는 skills를 validation-gated optimization으로 훈련한다고 주장하고, EvoLib는 self-supervised evolving knowledge library를 강조한다. 둘 다 model weights를 바꾸지 않는 적응층을 말하지만, 최적화 단위와 feedback 구조가 다르다 (raw/microsoft-skillopt-agent-skills.md:19-21,27-28; raw/microsoft-evolib-evolving-knowledge.md:19,28-30). 판정하지 않음.
