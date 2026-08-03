# New America — AI Agents and Memory

- 자료: `new-america-ai-agents-and-memory` (research_org)
- 원문 위치: `raw/new-america-ai-agents-and-memory.html`의 절 제목(HTML 구조상 절 제목 인용).

## 핵심 주장
1. MCP 기반 agent memory는 여러 tool·device·session에 걸친 persistent/distributed memory로 이동해, privacy·consent·accountability의 통제를 어렵게 만든다고 주장한다. [원문: `raw/new-america-ai-agents-and-memory.html` “The Shift in Memory: From Local to Persistent and Distributed”, l.218–219]
2. **New America 글의 저자 문제 제기**는 MCP가 agent authentication/delegated API access의 표준화 방식과 intermediate permission 보안 계층이 부족하다는 것이다. 이 글은 binary access가 과도한 위임과 기능 상실의 양자택일을 만든다고 서술한다. 이는 MCP 규격의 현재 사실 판정이 아니다. [원문: `raw/new-america-ai-agents-and-memory.html` “Security / Lack of Identity and Access Standards”, l.297–300]
3. transparency/user control을 우선하고, memory dashboard·민감 memory 기본 retention limit·고위험 영역 memory-free mode를 권고한다. [원문: `raw/new-america-ai-agents-and-memory.html` “Policy Recommendations / 1. Foundational User Protections”]

## 근거·방법론
- 보고서는 agent가 여러 서비스에서 데이터를 재조합하고 session 간 기억을 유지하는 가상 사용 사례로 privacy 영향(불투명성·cross-service leakage·행동/감정 추론)을 설명한다. [원문: “Privacy”]
- 보안 권고는 per-user/per-session/per-tool memory compartmentalization, 각 access 때 purpose tag 검증, signed action log와 audit trail을 포함한다. [원문: “Policy Recommendations / 2. Infrastructure Safeguards”]

## 정의·수치
- MCP: 본문에서 agent가 external tool과 interface하는 technical standard인 Model Context Protocol로 한정해 사용한다. [원문: `raw/new-america-ai-agents-and-memory.html` “What is MCP?”, l.203–205]
- 수치적 실험·성능 지표는 제시하지 않는 정책 분석 자료다.
- 시간 메타데이터: 페이지는 2025-11-05 발행, 2026-02-17 수정으로 보존되어 있다. 해당 보존본만으로는 “lack” 서술이 어느 MCP specification 버전을 대상으로 했는지 확정할 수 없다. [원문: `raw/new-america-ai-agents-and-memory.html` l.15, l.27, l.122]

## 한계·검증 이관
- 권고·위험 분석이며 통제의 실증 효과를 측정한 benchmark가 아니다.
- ‘MCP lacks…’는 이 정책 분석의 저자 주장으로만 기록하며, 현행 MCP specification의 최신 상태 판정에는 사용하지 않는다. 특히 2025-06 및 2025-11 MCP authorization specification 이후의 지원 범위와의 관계는 본 원문만으로 판정할 수 없다. [교차검증 이관 메모: `verify/verification.md` §10-2, §6.2]
- 후속 검증은 (a) agent identity, (b) upstream/delegated authorization, (c) scoped·context-aware/fine-grained policy를 분리해 각각 명세 버전·원문 위치를 대조해야 한다. 이는 본 자료의 결론이 아니라 검증 단계를 위한 분해 항목이다.
- **외부 검증 상태 이관(10-3):** dashboard·retention limit·memory-free mode는 정책 제안이며, 통제 효과 또는 독립 정책 합의가 확인되지 않았다. [원문: “Policy Recommendations / 1. Foundational User Protections”; 검증 기록: `verify/verification.md` §10-3, §7 잔여 보완 2]
