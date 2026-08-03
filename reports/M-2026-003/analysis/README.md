# M-2026-003 심층 분석 인덱스

- 범위: `raw/sources.yaml`에서 `status: selected`인 12개 자료.
- 방법: 자료별로 주장·근거/방법론·수치/정의·한계/검증 이관을 분리했다. 모든 추출 항목은 원문 파일과 행/쪽/절 위치를 병기했다.
- 주의: arXiv 4건은 보존본이 Atom 초록뿐이므로 상세 실험 수치·표·ablation은 이 분석의 범위 밖이다.

## 자료 간 확인 필요 표지(판정하지 않음)

1. 벤치마크 범주: LongMemEval은 5 abilities, MemoryAgentBench는 4 competencies, LoCoMo는 QA·요약·멀티모달 생성 과업을 쓴다. 동일한 memory quality를 측정하는지 및 점수 비교 가능성은 Cross-Verify 단계에서 확인해야 한다.
2. 메모리 구조: A-MEM과 EvoLib 모두 연결·갱신되는 지식을 서술하지만, 저장 단위·갱신 규칙·평가 조건의 동등성은 확인되지 않았다.
3. 운영 권고: Anthropic의 context/harness 글은 vendor engineering guidance, New America는 policy analysis, NIST는 risk-management profile, IETF는 Internet-Draft다. 규범적 권고와 실험적 성능 근거를 혼합하지 않는다.
4. IETF draft는 그 자체로 “work in progress”이며 확정 표준으로 다루지 않는다. [원문: `12-ietf-agent-security.md`의 원문 위치 l.55–63]
5. MemoryAgentBench 역량 용어: 보존한 arXiv `2507.05257v4` 초록은 네 번째 역량을 `selective forgetting`으로 쓰지만, fact-checker가 확인한 현재 공식 구현 문서는 `Conflict Resolution`으로 표기한다. 본 분석의 원문 추출과 현행 구현 요건을 혼동하지 않으며, 인용/구현 전 version·commit 고정이 필요하다. [분석: `04-memoryagentbench.md`; 검증 이관: `verify/verification.md` §04-2, §6.1]
6. New America MCP 보안 서술: 2025-11-05 발행·2026-02-17 수정 보존본의 저자 문제 제기이며, 최신 MCP authorization 지원 여부의 판정 근거로 쓰지 않는다. agent identity·upstream delegation·fine-grained policy별 명세 대조는 Cross-Verify 단계에 이관한다. [분석: `10-new-america-memory-privacy.md`; 검증 이관: `verify/verification.md` §10-2, §6.2]

## GR 보완 — 미검증 주장 사용 경계

- Cross-Verify가 독립 재현·외부 검토 부재로 표시한 14개 주장은 자료별 노트의 `외부 검증 상태 이관` 항목에 보존했다. 이 항목들은 원문 주장을 삭제하거나 판정하지 않고, synthesis에서 **저자 보고·관찰·권고·제안**으로만 표현하도록 범위를 제한한다. [검증 기록: `verify/verification.md` §7]
- 성능/숙달 주장: 02-2·02-3·03-3·04-3·07-3 — 독립 재현 없음.
- 문헌 범위·운영/정책 주장: 01-1·05-3·06-3·09-2·10-3 — 독립 검토 또는 통제 효과 확인 없음.
- 표준/벤치마크 제안: 11-3·12-1·12-2·12-3 — 원문 일치와 독립 검증을 구분하며, 특히 IETF draft의 metric은 제안 목록이지 확정 표준 또는 검증 완료 benchmark가 아니다.
