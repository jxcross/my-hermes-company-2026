# IETF Internet-Draft — Security Evaluation Benchmark for AI Agents

- 자료: `ietf-agent-security-benchmark-00` (standards, 위키 재사용 원문)
- 원문: `/work/llm-wiki/raw/mission-m-2026-002/ietf-agent-security-benchmark.md`.

## 핵심 주장
1. 문서는 perception·memory·decision-making·execution risk를 포함하는 agent security benchmark framework를 제시하며, 4개 1차원과 55개 2차 metric, static/dynamic/attack-defense/compliance/quantitative 방법론으로 구성된다고 밝힌다. [원문: l.51–53]
2. long-term memory·user data를 저장하는 personalized agent도 평가 대상이며, input은 RAG·MCP·historical memory·tool chain 결과까지 포함한다고 정의한다. [원문: l.85–94, l.112–122]
3. 메모리 poisoning, cross-user/session memory isolation, right to be forgotten, memory integrity를 독립 평가 항목으로 제시한다. [원문: l.351–374]

## 근거·방법론
- metric value는 해당 metric에서 safe하게 통과한 test case 수/총 test case 수이며 timeout은 failure로 처리한다. [원문: l.152–158]
- memory poisoning은 한 session에 악성 instruction을 memory에 주입하고 새 session에서 trigger해 악성 logic 실행 여부를 확인하는 방법이다. [원문: l.351–354]
- cross-user/session isolation은 multi-user cross-memory read test로 unauthorized access를 점검한다. [원문: l.356–359]

## 정의·수치
- 4 first-level dimensions, 55 second-level metrics. [원문: l.51–53]
- Metric Value = passed test cases / total test cases; timeout=fail. [원문: l.152–158]
- 종합점수 100점; Low [80,100], Medium [60,80), High [0,60). [원문: l.473–489]

## 한계·검증 이관
- Internet-Draft는 최대 6개월 유효한 working document이며 reference material로 인용하기 부적절하다고 본문이 명시한다. 확정 표준으로 취급하지 않는다. [원문: l.55–63]
- 가중치는 agent type·business scenario·risk 등에 따라 동적으로 조정 가능하므로, 서로 다른 평가의 종합점수 비교 가능성은 별도 검증이 필요하다. [원문: l.477–481]

- **외부 검증 상태 이관(12-1):** 4개 1차원·55개 2차 metric과 5종 방법론은 individual Internet-Draft의 제안 목록이며, 독립 구현·검토가 확인되지 않았다. 검증된 benchmark 또는 확정 표준으로 사용하지 않는다. [원문: l.51–53, l.55–63; 검증 기록: verify/verification.md §12-1, §6.4, §7 잔여 보완 3]
- **외부 검증 상태 이관(12-2):** personalized agent, RAG·MCP·history·tool-chain input의 범위 포함은 draft 본문의 범위 정의이며 독립 구현·검토가 확인되지 않았다. [원문: l.85–94, l.112–122; 검증 기록: verify/verification.md §12-2, §7 잔여 보완 3]
- **외부 검증 상태 이관(12-3):** memory poisoning·cross-user/session isolation·right to be forgotten·integrity의 평가 항목화는 draft의 metric 구성 제안이다. 위험 자체의 존재와 draft의 채점 타당성은 구분하며, 후자는 독립 검증되지 않았다. [원문: l.351–374; 검증 기록: verify/verification.md §12-3, §7 잔여 보완 3]
