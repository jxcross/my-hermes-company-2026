# Microsoft Research — EvoLib

- 자료: `microsoft-evolib-evolving-knowledge` (vendor, 위키 재사용 원문)
- 원문: `/work/llm-wiki/raw/mission-m-2026-001/microsoft-evolib-evolving-knowledge.md`.

## 핵심 주장
1. 단순 memory archive는 새 과업에 관련 지식을 찾고 개선하기 어렵고, memory 자체는 learning이 아니라는 문제 제기다. [원문: l.24–26]
2. EvoLib은 raw experience를 재사용 가능한 skill/reflective insight로 추출한 뒤 consolidation·dynamic weighting으로 발전하는 knowledge library를 제안한다. [원문: l.26, l.28–31]
3. 코드·long-horizon 환경 상호작용 과업에서 retrieval-based memory 및 다른 abstract memory보다 token 효율적으로 성능이 높았다고 주장한다. [원문: l.32–38]

## 근거·방법론
- consolidation: 최근 경험에서 추출한 새 knowledge와 library 내 유사 knowledge를 찾아 더 일반적·재사용 가능한 지식으로 통합한다. [원문: l.28–29]
- weighting: 현 과업의 즉시 유용성뿐 아니라 향후 useful knowledge 생성 기여로 각 knowledge unit의 중요도를 갱신한다. [원문: l.30]
- heterogeneous task set을 서로 다른 순서로 실행해 task-order 안정성을 평가했다고 서술한다. [원문: l.39]

## 정의·수치
- knowledge unit: 성공 해법에서 증류된 재사용 skill 또는 실수에서 얻은 reflective insight. [원문: l.28]
- black-box API 모델에도 모델 업데이트 없이 적용 가능하다고 설명한다. [원문: l.23]
- ‘all three benchmarks’에서 compute 증가에 따라 성능 개선이 더 빠르다고 주장하나, 절대 수치는 본문에 없다. [원문: l.36–38]

## 한계·검증 이관
- 블로그 요약은 벤치마크명·점수·분산·비용 세부를 제공하지 않는다. ‘일관되게 우수’는 저자 주장으로만 기록한다.
- A-MEM의 동적 연결/갱신과 유사한 방향성을 보이지만 동일한 저장 단위·평가 설정인지는 본 자료만으로 판단 불가.
- **외부 검증 상태 이관(07-3):** 세 벤치마크에서 retrieval/abstract memory보다 token 효율적으로 우수했다는 것은 저자 보고이며 외부 재현·독립 benchmark report가 확인되지 않았다. [원문: l.32–38; 검증 기록: `verify/verification.md` §07-3, §7 잔여 보완 1]
