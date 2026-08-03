# M-2026-003 Cross-Verify 검증표

## 판정

**합격(PASS)** — 6R2 재판정 결과, 핵심 주장 34건 중 `확인 20`, `상충 0`, `미검증 14`.

- G6R 수정으로 기존 상충 2건(04-2, 10-2)은 해소되었다. 잔여 미검증 14건은 제공자·저자의 자체 성능 보고, 비공개 내부 절차, 규범적 권고, 유일한 1차 문서의 제안 내용처럼 현재 독립 재현·감사·합의 자료가 존재하지 않아 본질적으로 독립 검증할 수 없는 항목이다. 각 항목은 검증표에서 `미검증`으로 공개했고, 사실 결론이나 검증된 우위·표준으로 승격하지 않도록 제한했으므로 조정된 게이트 기준에 따라 통과한다.

- `확인(corroborated)`: 원 출처와 다른 공개 출처에서 핵심 내용이 대조됨. 단, 자체 평가 수치의 제3자 재현까지 의미하지는 않는다.
- `상충(conflicting)`: 현재의 공식 구현·명세 또는 별도 공개본과 Reader 서술이 충돌한다.
- `미검증(unverified)`: 원문에는 있으나 독립 출처·재현 자료가 없거나, 독립 출처가 주장 전체를 지지하지 않는다.
- 원칙: 저자 프로젝트·동일 논문의 다른 호스팅은 원문 일치 확인에는 썼지만, 성능 우위의 독립 재현으로 간주하지 않았다.

## 핵심 주장별 검증표

| ID | Reader 핵심 주장(요약) | 판정 | 독립 대조 및 근거 |
|---|---|---|---|
| 01-1 | 기존 장기 대화 연구가 최대 5세션에 치우쳐 LoCoMo 이전의 장기 맥락 연구가 부족했다. | 미검증 | 후속 ACL 논문은 LoCoMo의 장기 대화 용도를 확인하지만, 선행연구가 “최대 5세션”이었다는 문헌 전수 범위는 독립 확인하지 않는다: [ACL 2026 후속 연구](https://aclanthology.org/2026.findings-acl.38.pdf). |
| 01-2 | LoCoMo는 QA·이벤트 요약·멀티모달 생성을 평가하고, 평균 300턴·9K 토큰·최대 35세션이다. | 확인 | 독립 후속 ACL 논문이 50 dialogues, 평균 300 turns, 최대 35 sessions, 약 9,000 tokens와 LoCoMo의 장기기억 평가 용도를 재기술한다: [ACL 2026](https://aclanthology.org/2026.findings-acl.38.pdf). 프로젝트 페이지도 세 과업을 명시한다: [LoCoMo project](https://snap-research.github.io/locomo). 다만 인간 대비 격차의 크기는 독립 재현되지 않았다. |
| 02-1 | LongMemEval은 5개 장기기억 능력과 500개 선별 질문을 평가한다. | 확인 | ICLR 2025 공식 포스터 페이지가 다섯 능력과 500개 질문을 명시한다: [ICLR 2025](https://iclr.cc/virtual/2025/poster/28290). 공개 저장소에도 500개 인스턴스와 평가 파일이 있다: [LongMemEval GitHub](https://github.com/xiaowu0162/LongMemEval). |
| 02-2 | 상용 챗봇·long-context LLM의 지속 상호작용 기억 정확도가 30% 하락했다. | 미검증 | ICLR 페이지와 저자 프로젝트는 30% 또는 30–60% 하락을 반복하지만 모두 동일 저자 평가의 재게시다: [ICLR](https://iclr.cc/virtual/2025/poster/28290), [project](https://xiaowu0162.github.io/long-mem-eval). 독립 재현·분산·동일 기준 비교는 찾지 못했다. |
| 02-3 | indexing–retrieval–reading 분해와 세션/키/query 확장이 recall·QA를 개선한다. | 미검증 | 프레임워크와 개선 주장은 ICLR 원고·저자 저장소에서 일치하나 제3자 ablation 재현은 확인되지 않았다: [ICLR](https://iclr.cc/virtual/2025/poster/28290), [GitHub](https://github.com/xiaowu0162/LongMemEval). |
| 03-1 | 기존 메모리는 저장·검색 중심이고 조직화·적응적 업데이트가 부족하다. | 확인 | 독립 ACL 논문이 기존 시스템이 storage/retrieval에 집중하고 적응적·지속적 업데이트가 부족하다고 정리한다: [ACL 2026](https://aclanthology.org/2026.findings-acl.38.pdf). |
| 03-2 | A-MEM은 Zettelkasten 기반 note·link·memory evolution 구조다. | 확인 | 독립 ACL 논문이 A-MEM을 Zettelkasten 기반의 evolving, self-linked knowledge notes로 설명한다: [ACL 2026](https://aclanthology.org/2026.findings-acl.38.pdf). OpenReview 메타데이터도 note construction, link generation, memory evolution을 명시한다: [OpenReview](https://openreview.net/forum?id=FiM0M8gcct). |
| 03-3 | 6개 foundation model에서 기존 SOTA보다 우수했다. | 미검증 | OpenReview/저자 저장소는 6개 모델과 우위를 보고하지만 독립 재현 결과가 아니다: [OpenReview](https://openreview.net/forum?id=FiM0M8gcct), [A-MEM GitHub](https://github.com/agiresearch/a-mem). 지표·효과크기·비용의 외부 재현을 찾지 못했다. |
| 04-1 | MemoryAgentBench는 정적 long-context의 한계를 지적하고 incremental multi-turn 형식으로 평가한다. | 확인 | ICLR 2026 공개 리뷰가 기존 정적 평가의 한계, 기존 데이터 재구성, 신규 데이터, incremental multi-turn 설계를 요약한다: [공개 리뷰 PDF](https://cseweb.ucsd.edu/~jmcauley/reviews/iclr26c.pdf). |
| 04-2 | **보존된 arXiv v4 초록의 저자 정의**는 retrieval, test-time learning, long-range understanding, selective forgetting이다. | 확인 | 독립 Liner 리뷰가 `selective forgetting` 및 FactConsolidation을 해당 역량의 평가로 재기술한다: [Liner review](https://liner.com/review/evaluating-memory-in-llm-agents-via-incremental-multiturn-interactions). 한편 현재 공식 저장소·데이터셋 README는 네 번째를 **Conflict Resolution**으로 표기한다: [공식 GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench), [Hugging Face README](https://huggingface.co/datasets/ai-hyz/MemoryAgentBench/blob/5bd2ff1624cfe699926f6e22d165411cb400c2a8/README.md). Reader가 주장을 arXiv v4 보존본에 한정하고 구현 시 version/commit 고정을 요구했으므로 기존 상충은 해소되었다. |
| 04-3 | 현 방법은 네 역량 모두를 숙달하지 못했다. | 미검증 | ICLR 리뷰와 저자 초록이 한계를 보고하지만, 네 역량 전체에 대한 독립 재현은 확인되지 않았다: [공개 리뷰 PDF](https://cseweb.ucsd.edu/~jmcauley/reviews/iclr26c.pdf), [OpenReview](https://openreview.net/forum?id=DT7JyQC3MR). |
| 05-1 | context engineering은 프롬프트를 넘어 추론 시 제공되는 도구·데이터·이력 전체의 관리다. | 확인 | 독립 GCC 연구는 context를 transient token stream이 아니라 지속·탐색 가능한 memory workspace로 관리해야 하는 대상으로 다루며, 장기 agent workflow에서 context management를 병목으로 확인한다: [Git Context Controller](https://arxiv.org/html/2508.00031v3). |
| 05-2 | 긴 컨텍스트에서 정보 활용 정확도가 저하하므로 작은 고신호 컨텍스트가 중요하다. | 확인 | TACL 논문은 입력이 길어질수록 성능이 감소하고 중간 위치 정보 이용이 크게 저하함을 실험으로 보인다: [Lost in the Middle, ACL Anthology](https://aclanthology.org/2024.tacl-1.9), [본문](https://ar5iv.labs.arxiv.org/html/2307.03172). 이는 “context rot”의 일반 방향을 독립 지지하지만 모든 모델·과업에 동일한 감소율을 뜻하지 않는다. |
| 05-3 | 장기 과업에 compaction·구조화 노트·sub-agent가 각각 특정 상황에 적합하다. | 미검증 | GCC는 구조화·버전 관리된 상태의 유용성을 독립 지지하지만, Anthropic이 제시한 세 패턴의 상대적 적합성과 sub-agent 우위까지 비교하지 않는다: [GCC](https://arxiv.org/html/2508.00031v3). |
| 06-1 | 새 context session은 이전 상태를 잃으므로 세션 간 상태 전달이 필요하다. | 확인 | GCC는 새 세션이 prior goals·preferences·instructions를 잃는 문제를 명시하고 persistent workspace로 복구·전달한다: [GCC](https://arxiv.org/html/2508.00031v3). |
| 06-2 | compaction만으로 부족하며 progress artifact와 git-style history가 연속성을 돕는다. | 확인 | GCC는 단순 compression이 세부 근거를 잃는다고 지적하고 roadmap, commit summary, execution trace, metadata를 이용한 cross-session continuity를 구현·평가한다: [GCC](https://arxiv.org/html/2508.00031v3). |
| 06-3 | 한 번에 한 feature를 처리하고 깨끗한 상태·요약을 남기는 방식이 중요하다. | 미검증 | 독립 실무 글도 plan/progress file과 structured handoff를 권하지만 Anthropic의 “one feature” 규칙을 통제 실험으로 검증하지 않는다: [Long-running Agents](https://addyosmani.com/blog/long-running-agents). |
| 07-1 | raw memory archive만으로는 일반화·학습이 어렵다. | 확인 | EvoLib 연구 원문은 raw trajectory 검색이 generalized knowledge/skills 유도를 방해한다고 별도 논문 형태로 설명한다: [EvoLib paper](https://arxiv.org/html/2605.14477v1). 이는 Microsoft 블로그와 다른 공개 산출물이나 동일 연구팀의 주장임을 유의해야 한다. |
| 07-2 | EvoLib은 skill/reflective insight를 추출하고 consolidation·dynamic weighting으로 library를 갱신한다. | 확인 | 논문 본문과 공개 구현이 modular skills, reflective insights, consolidation, Information Gain/Future IG weighting을 구체화한다: [paper](https://arxiv.org/html/2605.14477v1), [GitHub](https://github.com/microsoft/EvoLib). |
| 07-3 | 세 벤치마크에서 retrieval/abstract memory보다 token 효율적으로 우수하다. | 미검증 | 논문은 3개 벤치마크에서 5–10% 및 token 효율 우위를 자체 보고하지만, 외부 재현·독립 benchmark report를 찾지 못했다: [paper](https://arxiv.org/html/2605.14477v1). |
| 08-1 | Deep Agents v0.7은 비슷한 성능에서 base input token을 약 65%(6k→2k) 줄였다. | 확인 | 독립 기술 요약이 65%, 6k→2k와 “reward held steady”를 재확인하고 통계적 한계도 명시한다: [ExplainX](https://explainx.ai/blog/langchain-deep-agents-0-7-leaner-harness-july-2026), [daily.dev](https://daily.dev/posts/langchain-releases-deep-agents-v0-7-with-65-fewer-base-input-tokens-hkzwejbl8). 단, LangChain 원시 run의 제3자 재실행은 아니다. |
| 08-2 | system prompt 제거, tool description 43% 축소, Todo 기본 제외가 변경점이다. | 확인 | 두 독립 요약이 세 변경사항과 43%를 동일하게 보고한다: [ExplainX](https://explainx.ai/blog/langchain-deep-agents-0-7-leaner-harness-july-2026), [daily.dev](https://daily.dev/posts/langchain-releases-deep-agents-v0-7-with-65-fewer-base-input-tokens-hkzwejbl8). |
| 08-3 | reward CI는 모든 모델에서 0을 가로지르고, 특정 Luna는 token −34%, cost −15%, reward +4%다. | 확인 | 독립 해설이 모든 모델 reward CI가 0을 span하고 통계적으로 명확한 것은 일부 token/cost 감소뿐이라고 확인한다: [ExplainX](https://explainx.ai/blog/langchain-deep-agents-0-7-leaner-harness-july-2026). 따라서 “comparable performance”는 무회귀 확정이 아니라 **유의한 차이를 검출하지 못함**으로 제한해야 한다. |
| 09-1 | METR은 2026-02~03 내부 agent misalignment pilot을 Anthropic·Google·Meta·OpenAI와 수행했다. | 확인 | 제3자 공개 요약이 4개 참여사, 내부 모델 접근, misalignment/rogue deployment 평가를 재기술한다: [LinkedIn 공개 요약](https://www.linkedin.com/posts/jonasfreund_metr-frontier-risk-report-activity-7462601636113317889-Q7gl). METR의 별도 Substack 배포본도 일치한다: [Substack](https://metr.substack.com/p/frontier-risk-report-february-to). |
| 09-2 | 평가는 entity-based이고 공개 릴리스에 묶이지 않으며 주기적 반복을 목표로 한다. | 미검증 | 이 절차는 METR의 자체 보고서·미러에는 명시되지만 독립 기관의 방법 감사는 찾지 못했다: [METR report](https://metr.org/blog/2026-05-19-frontier-risk-report). |
| 10-1 | persistent/distributed memory는 privacy·consent·accountability와 cross-session 보안 위험을 키운다. | 확인 | 독립 보안 survey가 persistence, statefulness, propagation, cross-session poisoning/unauthorized access를 별도 보안 문제로 정리한다: [Long-Term Memory Security Survey](https://arxiv.org/html/2604.16548v1). Palo Alto Unit 42도 cross-session memory poisoning과 이후 대화 exfiltration PoC를 보고한다: [Unit 42](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory). |
| 10-2 | **New America 글의 저자 문제 제기**는 MCP의 agent identity·delegated access·중간 permission 공백이며, 현행 명세의 현재 사실 판정은 아니다. | 확인 | 독립 CSA 보고서는 기존 OAuth가 agent identity 인식·추적 가능한 위임·context-aware fine-grained control에 불충분하다고 분석한다: [Cloud Security Alliance](https://openreview.net/pdf/7db8d7d31396bd9a8cc21dbbc479c7511639f8d8.pdf). Axiomatics도 2025-11 명세의 OAuth 2.1 authorization이 존재함을 전제로 agent identity/user delegation 전파와 dynamic fine-grained policy가 추가로 필요하다고 구분한다: [Axiomatics](https://axiomatics.com/blog/securing-the-ai-frontier-a-cisos-guide-to-access-control-for-mcp). 공식 명세상 authorization 자체는 존재한다: [MCP 2025-11-25 Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization). Reader가 이를 저자 주장으로 한정하고 최신 규격 사실로 쓰지 않았으므로 기존 상충은 해소되었다. |
| 10-3 | memory dashboard·retention limit·고위험 memory-free mode를 권고한다. | 미검증 | 이는 정책 제안의 존재는 원문에서 확인되지만, 통제 효과나 독립 정책 합의는 확인되지 않았다: [New America](https://www.newamerica.org/insights/ai-agents-and-memory). |
| 11-1 | NIST AI 600-1 action은 Govern/Map/Measure/Manage에 연결되며 적용성은 조직·용도별로 판단한다. | 확인 | NIST RMF 공식 페이지는 프로파일이 조직 목표·우선순위에 맞는 GAI risk action을 제안한다고 설명하고, 독립 해설도 4개 기능에 매핑되는 cross-sectoral profile로 정리한다: [NIST RMF](https://www.nist.gov/itl/ai-risk-management-framework), [Modulos 설명](https://www.modulos.ai/nist-ai-rmf). |
| 11-2 | 네 우선 고려사항은 Governance, Content Provenance, Pre-deployment Testing, Incident Disclosure다. | 확인 | 독립 요약이 네 항목을 그대로 명시한다: [Jarvis Registry](https://jarvisregistry.com/explore-agentic/glossary/nist-ai-rmf). NIST 배포 PDF 검색 결과와도 일치한다: [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf). |
| 11-3 | MS-2.7-001은 backdoor·dependency·breach·MITM·reverse engineering·autonomous agents·model theft 등을 평가한다. | 미검증 | 문구는 NIST PDF에서 직접 일치하지만, 해당 나열 전체를 별도 독립 출처가 정확히 재현·검증한 자료는 찾지 못했다: [NIST AI 600-1 p.33](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf). |
| 12-1 | IETF draft는 4개 1차원·55개 2차 metric과 5종 방법론의 agent security benchmark를 제안한다. | 미검증 | Datatracker가 문구와 수치를 직접 확인하지만 이는 같은 draft의 공식 렌더링이다. 제3자 검토·구현·재현은 찾지 못했다: [IETF Datatracker](https://datatracker.ietf.org/doc/html/draft-han-bmwg-agent-security-benchmark-00). |
| 12-2 | personalized agent, RAG·MCP·history·tool-chain input을 평가 범위에 포함한다. | 미검증 | 범위는 draft 본문에서 확인되지만 독립 구현/검토가 없다: [IETF Datatracker](https://datatracker.ietf.org/doc/html/draft-han-bmwg-agent-security-benchmark-00). |
| 12-3 | memory poisoning·cross-user/session isolation·right to be forgotten·integrity를 독립 평가 항목으로 둔다. | 미검증 | 장기기억 보안 survey가 이 위험들의 실재성과 중요성은 독립 지지하지만, 이 draft의 metric 구성이나 채점 타당성을 검증하지 않는다: [security survey](https://arxiv.org/html/2604.16548v1), [draft](https://datatracker.ietf.org/doc/html/draft-han-bmwg-agent-security-benchmark-00). |

## 수치·정의·버전 점검

1. **MemoryAgentBench 용어 충돌(수정 확인)**: 로컬 보존본은 arXiv `2507.05257v4`(updated 2026-06-28)이며 `selective forgetting`을 쓴다. 반면 현재 공식 GitHub/Hugging Face는 `Conflict Resolution`을 쓴다. Reader가 보존본 추출과 현재 구현을 분리하고 version/commit 고정을 요구해 왜곡 위험을 해소했다.
2. **MCP 시점 왜곡 위험(수정 확인)**: New America 자료는 2025-11-05 발행, 2026-02-17 수정본이다. Reader가 “lack”을 저자 문제 제기로만 한정하고, authorization 존재 여부와 agent identity·upstream delegation·fine-grained policy를 분리 검증하도록 수정했다.
3. **Deep Agents 통계 해석**: reward CI가 모든 모델에서 0을 포함하므로 `comparable performance`는 “성능 동일성 입증”이나 “향상”이 아니다. 검정에서 유의한 reward 차이를 확인하지 못했다는 수준으로 써야 한다.
4. **IETF 지위**: 해당 문서는 `Active Internet-Draft (individual)`이며 Datatracker가 “not endorsed by the IETF / no formal standing”이라고 명시한다. 2026-07-05 공개, 2027-01-06 만료 예정이다: [Datatracker](https://datatracker.ietf.org/doc/html/draft-han-bmwg-agent-security-benchmark-00).
5. **자체 성능 주장**: LongMemEval 30% 하락, A-MEM SOTA, EvoLib 우위는 원문·저자 공개물 간에는 일치하지만 독립 재현이 없어 성능 설계 근거로 승격하지 않는다.

## 6R2 재판정 및 Reader 사용 제한

- **수정 확인:** MemoryAgentBench arXiv v4와 현재 구현의 용어 충돌을 본문에 병기했다.
- **수정 확인:** New America의 MCP 평가는 저자 문제 제기로 한정하고, 명세의 authorization 지원과 잔여 권한 공백을 분리했다.
- **본질적 독립 검증 불가 — 자체 평가(5건):** 02-2·02-3·03-3·04-3·07-3은 제공자·저자의 성능/숙달 보고이고 제3자 재현 자료가 없다. 독립 실행 결과가 새로 공개되기 전에는 확인 판정할 수 없다. synthesis에서 사실 결론이나 설계 우위 근거로 사용하지 말고 `저자 보고·독립 재현 없음`을 문장 안에 유지한다.
- **본질적 독립 검증 불가 — 비폐쇄·규범·내부 절차(5건):** 01-1의 문헌 전수 범위는 닫힌 검증 모집단이 아니며, 05-3·06-3·10-3은 상대 적합성·운영 중요성·정책 효과에 관한 규범/권고, 09-2는 METR의 내부 평가 절차 자기보고다. 공개된 독립 비교·감사 자료가 없는 현재 각각 관찰·권고·정책 제안·기관 자기보고로만 유지한다.
- **본질적 독립 검증 불가 — 유일 1차 문서의 내용(4건):** 11-3·12-1·12-2·12-3은 원문 일치는 확인했지만, 해당 NIST 항목 및 IETF 개인 초안의 제안 구성을 독립적으로 구현·검토한 자료가 없다. 특히 IETF draft의 55개 metric은 제안 목록일 뿐 검증된 benchmark/표준이 아니며, test case·inter-rater·reproducibility 근거 부재를 synthesis에 명시한다.
- **최종 판정:** 미해소 상충은 없고, 독립 검증 가능한 주장은 모두 확인했다. 잔여 14건은 위와 같이 독립 검증 불가의 성격과 사용 제한을 공개했으므로 `PASS`다.
