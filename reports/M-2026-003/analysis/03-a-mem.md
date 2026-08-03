# A-MEM — 자료별 분석 노트

- 자료: `a-mem-agentic-memory-for-llm-agents` (academic)
- 원문 범위: arXiv Atom 초록만 보존됨.

## 핵심 주장
1. 기존 메모리 시스템은 기본 저장·검색은 가능하지만 정교한 조직화가 부족하고, 고정된 연산/구조가 다양한 과업에 대한 적응성을 제한한다는 문제 제기다. [원문: XML l.16]
2. A-MEM은 Zettelkasten 원칙에 따라 동적 indexing/linking으로 상호연결 지식망을 만드는 agentic memory를 제안한다. [원문: XML l.16]
3. 6개 foundation model 실험에서 기존 SOTA baseline 대비 우수한 개선을 보였다고 주장한다. [원문: XML l.16]

## 근거·방법론
- 새 메모리마다 맥락 설명·키워드·태그 등 구조화 속성을 담은 note를 만들고, 과거 메모리를 분석해 의미 있는 연결을 만든다. [원문: XML l.16]
- 새 메모리 통합이 기존 메모리의 맥락 표현·속성 업데이트를 유발하여 network가 지속 정제되도록 설계한다. [원문: XML l.16]

## 정의·수치
- memory evolution: 새 정보가 들어오며 과거 메모리의 표현·속성을 갱신하는 과정. [원문: XML l.16]
- 실험 foundation model 수: 6. [원문: XML l.16]

## 한계·검증 이관
- SOTA 대비 개선의 지표·크기·벤치마크·비용은 초록에 없으므로 정량적 우위로 재인용 불가.
- ‘Zettelkasten’의 구체 자료구조·링크 규칙은 보존본에서 확인되지 않아 설계 세부사항으로 확장하면 안 된다.
- **외부 검증 상태 이관(03-3):** 6개 foundation model에서의 SOTA 대비 우위는 저자 보고이며, 지표·효과크기·비용을 포함한 독립 재현이 확인되지 않았다. [원문: XML l.16; 검증 기록: `verify/verification.md` §03-3, §7 잔여 보완 1]
