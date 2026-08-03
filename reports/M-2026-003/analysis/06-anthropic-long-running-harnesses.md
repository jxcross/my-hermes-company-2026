# Anthropic — Effective harnesses for long-running agents

- 자료: `anthropic-effective-harnesses-for-long-running-agents` (vendor)
- 원문 위치: 원본 HTML 절 제목(HTML이 minified되어 안정적 행번호 없음).

## 핵심 주장
1. 여러 context window에 걸친 장기 실행에서 새 세션은 전 세션 기억이 없으므로, 일관된 진전을 위해 세션 간 상태 전달 장치가 필요하다고 주장한다. [원문: “The long-running agent problem”]
2. compaction만으로는 충분하지 않으며 initializer agent와 이후 coding agent의 역할 분리, progress file과 git history가 새 context에서 작업 상태 이해를 돕는다고 제시한다. [원문: “The long-running agent problem”]
3. 한 번에 하나의 feature를 처리하고 깨끗한 상태·진전 요약을 남기는 incremental approach가 중요하다고 보고한다. [원문: “Incremental progress”]

## 근거·방법론
- initializer는 미래 세션에 필요한 환경·feature requirement를 준비하고, coding agent는 매 세션 incremental progress 및 structured update를 남긴다는 harness 설계다. [원문: “The long-running agent problem”; “Environment management”]
- feature list는 처음 failing으로 표기하고 후속 agent는 passes status만 변경하게 하며, JSON이 Markdown보다 부적절한 덮어쓰기에 덜 취약했다는 실험적 관찰을 제시한다. [원문: “Feature list”]
- 세션 시작 시 git log/progress file을 읽도록 하고, 기초 E2E test를 먼저 수행하게 한다. [원문: “Getting up to speed”]

## 정의·수치
- long-running 과업: hours 또는 days에 걸쳐 수행되는 복잡한 일. [원문: 도입부]
- 예시 feature list: 200개 초과 feature(특정 chat clone 사례). [원문: “Feature list”]

## 한계·검증 이관
- full-stack web-app demo에 최적화된 결과이며, 연구·금융 모델링 등 타 분야로의 일반화는 미래 과제로 명시한다. [원문: “Future work”]
- agent 분리의 성능 우위는 미확정이며, single general-purpose 대 multi-agent architecture가 더 나은지는 열려 있다고 원문이 밝힌다. [원문: “Future work”]

- **외부 검증 상태 이관(06-3):** ‘한 번에 하나의 feature’와 상태·요약 보존은 원문의 운영 권고다. 통제 실험에 의한 독립 검증은 확인되지 않았으므로 일반적 효과 사실이 아니라 적용 맥락이 있는 권고로만 사용한다. [원문: “Incremental progress”; 검증 기록: verify/verification.md §06-3, §7 잔여 보완 2]
