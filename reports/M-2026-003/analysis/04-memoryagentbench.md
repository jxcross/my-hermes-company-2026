# MemoryAgentBench — 자료별 분석 노트

- 자료: `memoryagentbench-incremental-multi-turn-interactions` (academic)
- 원문 범위: arXiv Atom 초록만 보존됨.

## 핵심 주장
1. 메모리 메커니즘을 갖춘 ‘memory agents’의 memory는 under-evaluated이며, 기존 벤치마크는 제한된 context 또는 정적 long-context에 맞춰져 누적·상호작용 특성을 반영하지 못한다고 주장한다. [원문: `raw/memoryagentbench-incremental-multi-turn-interactions.xml` l.16; arXiv `2507.05257v4`, updated 2026-06-28, l.11–16]
2. **arXiv v4 초록의 저자 정의**는 memory agent의 핵심 역량을 accurate retrieval, test-time learning, long-range understanding, selective forgetting의 4개로 둔다. [원문: `raw/memoryagentbench-incremental-multi-turn-interactions.xml` l.16]
3. 현 방법들은 위 arXiv v4 초록의 네 역량 모두를 숙달하지 못한다고 저자들이 실험 결과로 보고한다. [원문: `raw/memoryagentbench-incremental-multi-turn-interactions.xml` l.16]

## 근거·방법론
- 기존 long-context dataset을 변환하고 새 dataset을 추가 구축해, 증분 정보처리를 모사하는 multi-turn 형식으로 구성한다. [원문: XML l.16]
- 단순 context 기반·RAG부터 외부 메모리 모듈/도구 통합 agent까지 다양한 memory agent를 평가한다. [원문: XML l.16]

## 정의·수치
- 4 competencies (본 보존본/arXiv v4 기준): accurate retrieval, test-time learning, long-range understanding, selective forgetting. [원문: `raw/memoryagentbench-incremental-multi-turn-interactions.xml` l.11–16]
- 정량 점수·데이터셋 규모는 초록에 미기재.

## 한계·검증 이관
- 네 역량의 조작적 정의·채점방식·모델별 결과가 원문 보존본에 없어 구현 요구사항으로 바로 전환할 수 없다.
- `LongMemEval`의 5 abilities와 이름/범위가 다르다. 상호 포괄성 여부는 판정하지 않고 교차검증으로 이관한다.
- **버전/용어 불일치(판정하지 않음):** fact-checker가 확인한 현재 공식 GitHub·Hugging Face README는 네 번째 역량을 `Conflict Resolution`으로 표기한다. 이는 본 보존본의 arXiv `2507.05257v4` 초록의 `selective forgetting`과 다르다. 본 노트의 추출값은 전자(현재 구현)가 아니라 **보존된 arXiv v4 초록**에만 한정한다. 구현·인용 시에는 사용할 문서와 commit/version을 고정한 뒤 교차검증 단계에서 처리해야 한다. [교차검증 이관 메모: `verify/verification.md` §04-2, §6.1; 본 노트 원문 근거: XML l.11–16]
- **외부 검증 상태 이관(04-3):** 네 역량 모두를 숙달하지 못했다는 결과는 저자 실험 보고이며, 네 역량 전체에 대한 독립 재현이 확인되지 않았다. [원문: XML l.16; 검증 기록: `verify/verification.md` §04-3, §7 잔여 보완 1]
