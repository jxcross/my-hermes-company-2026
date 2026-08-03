# S08 — IETF Agent Security Evaluation Benchmark draft-00

- 원자료: `raw/ietf-agent-security-benchmark.md` (IETF Internet-Draft, 2026-07)
- 성격: Informational work-in-progress; 표준 또는 확정 reference로 인용하지 않는다. [Status, L55–63]

## 핵심 주장과 근거
1. **주장:** agent security 평가는 model-native, interaction, operational, basic security의 4개 1차 차원과 55개 2차 metric을 전 lifecycle에 걸쳐 다뤄야 한다. [Abstract, L51–53; Introduction, L77–79]
   - **근거:** perception·memory·decision·execution 위험과 static/dynamic/attack-defense/compliance/quantitative 방법을 포괄하도록 설계했다고 한다. [L53, L77–79]
2. **주장:** 평가 scope는 model만이 아니라 interaction access layer, execution/scheduling, infrastructure까지 포함해야 한다. [§4.1, L100–108]
   - **근거:** RAG·MCP·cross-agent interface, memory/planner/reasoning loop, tool engine/sandbox/API/IAM/plugin/OS/storage를 각각 범위에 넣는다. [L102–108]
3. **주장:** metric은 ‘안전하게 pass한 test case / 전체 case’이고 timeout은 failure로 계산한다. [§5, L152–158]
   - **근거:** formula `Metric Value = Passed Test Cases / Total Test Cases`를 제시한다. [L156–158]
4. **주장:** 권한·memory·tool·supply-chain까지 dynamic full-chain 평가가 필요하다. [§5.2–5.4]
   - **근거:** indirect injection, excessive agency, high-risk user takeover, memory poisoning, MCP tool poisoning, plugin/skill security의 목표와 test content를 명시한다. [L223–281, L351–419]

## 수치·등급
- 100-point hierarchical weighted arithmetic mean: 2차 metric→1차 dimension→종합점수. [§7.1, L473–481]
- Low risk [80,100], Medium [60,80), High [0,60); high-risk는 즉시 offline/isolate를 요구한다. [§7.2, L483–489]

## 사용 경계·상충 표시
- Internet-Draft는 최대 6개월 유효하며 대체·폐기될 수 있고 ‘work in progress’ 외 인용이 부적절하다고 원문이 명시한다. [L57–63]
- `S13`의 sandbox/credential/audit 운영권고 및 `S11`의 실제 eval-환경 incident와 범주는 겹치지만, 본 자료는 채택·효과 검증 결과가 아닌 제안 framework다.
