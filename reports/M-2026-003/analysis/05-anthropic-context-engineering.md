# Anthropic — Effective context engineering for AI agents

- 자료: `anthropic-effective-context-engineering-for-ai-agents` (vendor)
- 원문 위치 표기: 원본 HTML의 절 제목(HTML이 minified되어 안정적 행번호 없음).

## 핵심 주장
1. context engineering은 추론 시 LLM에 들어가는 token 집합을 관리·유지하는 전략이며, 프롬프트 외의 도구·MCP·외부데이터·메시지 이력까지 다룬다. [원문: “Context engineering vs. prompt engineering”]
2. 컨텍스트는 attention budget을 소모하는 유한 자원이고 token 증가에 따라 회상 정확도가 저하하는 context rot가 있어, 작은 고신호 token 집합이 바람직하다고 주장한다. [원문: “Why context engineering…”; “The anatomy…”]
3. 장기 과업에는 compaction·구조화 노트·sub-agent architecture를 제시하며, 각각 대화 흐름·명확한 마일스톤의 반복 개발·병렬 탐색/분석에 적합하다고 제안한다. [원문: “Context engineering for long-horizon tasks”]

## 근거·방법론
- long-context의 transformer attention은 n tokens에서 n² pairwise relationship을 요구하며, 길이가 늘면 attention focus와 precision이 저하할 수 있다는 설명을 근거로 든다. [원문: “Why context engineering…”]
- just-in-time 접근은 경량 식별자(file path·stored query·web link)를 유지하고 도구로 필요 시 읽어 progressive disclosure를 수행한다. [원문: “Context retrieval and agentic search”]
- compaction은 대화 요약 뒤 새 context window를 시작하며, Claude Code 사례에서 architecture decision·unresolved bug·구현 세부를 보존하고 중복 tool output/message를 버린다고 설명한다. [원문: “Context engineering for long-horizon tasks / Compaction”]

## 정의·수치
- context: LLM sampling 때 포함되는 tokens. [원문: “Context engineering vs. prompt engineering”]
- long-horizon: token 수가 context window를 넘는 일련의 행동을 통해 coherence·goal-directedness를 유지해야 하는 과업. [원문: “Context engineering for long-horizon tasks”]
- n² 관계는 구조 설명이며 측정 성능 수치가 아니다. [원문: “Why context engineering…”]

## 한계·검증 이관
- 공식 엔지니어링 가이드로서 권고/관찰 중심이다. 일반적 인과효과 또는 특정 제품 성능의 독립 검증 근거로 해석하지 않는다.
- ‘context rot’의 벤치마크별 크기와 최적 compaction 보존율은 이 글의 해당 절에서 수치로 제시되지 않았다.
- **외부 검증 상태 이관(05-3):** compaction·구조화 노트·sub-agent의 상황별 적합성은 vendor engineering guidance의 제안이다. 세 패턴의 상대적 적합성이나 sub-agent 우위는 독립 비교로 확인되지 않았다. [원문: “Context engineering for long-horizon tasks”; 검증 기록: `verify/verification.md` §05-3, §7 잔여 보완 2]
