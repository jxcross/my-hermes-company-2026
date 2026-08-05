# M-2026-005 — 검색 전략

- 작성일: 2026-08-05
- 단계: Search Strategy (원문 수집·중복 제거·관련성/품질 판정은 후속 단계 범위)
- 주제: LLM 에이전트 파이프라인에서 객관적 규칙 기반 게이트와 LLM 검증자의 이중 게이트 설계 및 역할 분담
- 기준 연도: 2026
- 허용 공개 원문: 학술 논문·학회 proceedings·출판사 version of record·공개 preprint. 검색 결과/블로그/요약 페이지는 후보 발견용이며 원문으로 보존하지 않는다.

## 정책을 검색에 적용하는 방법

- recent: 발행 연도 2023년 이상(현재 연도 - 3)이다. 최종 `selected`의 50% 이상을 이 기간으로 확보한다.
- hard block: 2011년 미만 자료는 `seminal: true`가 필요한 기초 원전 외 후보에서 제외한다.
- 필수 최소 분배: `peer_reviewed` 6편, `preprint` 2편, `survey` 1편; 합계 N=9 이상이다. `dataset_code`·`standards`·`web`은 발견 보조/선택 항목으로, 이 전략의 필수 후보에는 포함하지 않는다.
- 분류 기준: 동일 연구에 학회판과 arXiv판이 함께 있으면, 수집 단계에서 학회/출판사 공개 원문을 우선하고 한 연구는 하나의 `peer_reviewed` 항목으로 기록한다. preprint는 정식 출판 여부를 다시 확인한다.
- 날짜: Collection 단계가 원문 화면의 발행일·연도와 접근성을 다시 확인한다. 발행 연도를 원문에서 확인하지 못하면 `status: excluded`로 기록하고 N 및 recent 계산에서 제외한다.

## 연구질문별 하위 주제와 검색식

| ID | RQ | 하위 주제 | 검색식 | 우선 DB/원문 |
|---|---|---|---|---|
| Q1-1 | RQ1 | 규칙/실행 기반 검증과 LLM 의미 검증의 책임 경계 | `("LLM agent" OR "language agent") (verification OR validation OR evaluator) (rule-based OR executable OR test)` | ACL Anthology, ICLR, NeurIPS, arXiv |
| Q1-2 | RQ1 | 주장·인용·사실 정합성 확인 | `("large language model" OR LLM) (factuality OR attribution OR citation) (verification OR fact-checking) 2023..2026` | ACL Anthology, arXiv |
| Q1-3 | RQ1 | 외부 도구/증거를 사용하는 비판·수정 | `("large language model" OR LLM) (critique OR self-correction) (tool-interactive OR external feedback OR retrieval) 2023..2026` | ICLR, ACL Anthology, arXiv |
| Q2-1 | RQ2 | 다단계 검증 순서와 독립 질문/검토 | `("chain of verification" OR "multi-stage verification") "large language model"` | ACL Anthology, arXiv |
| Q2-2 | RQ2 | 에이전트 workflow·역할·메시지 경계 | `("LLM-based multi-agent" OR "multi-agent conversation") (workflow OR role OR protocol OR review) 2023..2026` | ICLR, COLM, IJCAI, Springer |
| Q2-3 | RQ2 | 객관적 oracle/테스트에 의한 결과 확인 | `("language model agent" OR "LLM agent") (benchmark OR evaluation) (test OR executable OR verifier) 2023..2026` | ICLR, NeurIPS, arXiv |
| Q3-1 | RQ3 | 자기 수정·자기 평가 한계 | `("large language model" OR LLM) ("self-correct" OR "self-verification") (limitation OR reliability OR bias) 2023..2026` | ICLR, ACL Anthology, OpenReview |
| Q3-2 | RQ3 | 독립 judge/critic 및 LLM-as-a-Judge | `("LLM-as-a-Judge" OR "language model judge") (bias OR consistency OR reliability OR human) 2024..2026` | ACL Anthology, ICLR, arXiv |
| Q3-3 | RQ3 | 다중 에이전트의 오류 전파·책임 분리 | `("LLM multi-agent" OR "language model multi-agent") (reliability OR error propagation OR independent review) 2024..2026` | IJCAI, Springer, arXiv |
| Q4-1 | RQ4 | LLM 판정의 비결정성·편향·설명 가능성 | `("LLM judge" OR "LLM evaluator") (non-determinism OR inconsistency OR position bias OR explainability) 2024..2026` | ACL Anthology, ICLR, arXiv |
| Q4-2 | RQ4 | 사람 승인·human-in-the-loop·재검토 비용 | `("LLM agent" OR "AI agent") ("human-in-the-loop" OR "human oversight" OR approval) (verification OR review) 2023..2026` | ACL Anthology, ICLR, arXiv |
| Q4-3 | RQ4 | 규칙 기반 검증의 적용 한계 | `("formal verification" OR "rule-based validation" OR "executable verification") (LLM OR "language model") 2023..2026` | arXiv, proceedings, standards (보조) |

## DB·소스 탐색 순서

1. **학회/출판사 원문:** ACL Anthology, ICLR proceedings/OpenReview, COLM OpenReview, IJCAI proceedings, Springer version of record. `peer_reviewed`와 `survey` 후보의 venue·발행일 확인에 우선 사용한다.
2. **arXiv:** `preprint` 후보와 학회판의 공개 사전본 발견에 사용한다. 학회판이 확인되면 같은 연구의 arXiv 사본을 중복 후보로 표시한다.
3. **Semantic Scholar:** DOI·venue·동일 논문 버전 탐색 보조로만 사용한다. 원문 보존 URL로 사용하지 않는다.
4. **학회 proceedings 검색:** ICLR/COLM/ACL/IJCAI의 논문명·저자 검색으로 검색 결과가 가리키는 버전의 venue와 발행 연도를 재확인한다.

## 1차 수집 후보

아래 목록은 공개 원문 URL, 제목, 연도/venue 단서를 검색 단계에서 확인한 후보다. 수집 단계는 각 후보의 정확한 발행일·저자·venue·공개 접근성 및 동일 연구의 중복 버전을 원문에서 재검증한다. 표의 `후보 분류`는 SCOPE의 source-balance taxonomy이며, `raw/sources.yaml`의 최종 상태 판정이 아니다.

| 우선 | 예상 ID | 제목 | URL | 검색 확인 연도·venue | 후보 분류 | 연결 RQ | 수집 시 확인 |
|---:|---|---|---|---|---|---|---|
| 1 | `rarr-researching-and-revising-language-models` | RARR: Researching and Revising What Language Models Say, Using Language Models | https://aclanthology.org/2023.acl-long.910 | 2023, ACL | peer_reviewed | RQ1, RQ2 | ACL 원문 및 DOI/발행일 |
| 2 | `critic-tool-interactive-critiquing` | CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing | https://arxiv.org/abs/2305.11738 | 2024, ICLR 표기 | peer_reviewed | RQ1, RQ3 | ICLR proceedings 원문 우선; arXiv는 보조 |
| 3 | `llms-cannot-self-correct-reasoning-yet` | Large Language Models Cannot Self-Correct Reasoning Yet | https://arxiv.org/abs/2310.01798 | 2024, ICLR 표기 | peer_reviewed | RQ3, RQ4 | ICLR proceedings 원문 우선; arXiv는 보조 |
| 4 | `agentbench-evaluating-llms-as-agents` | AgentBench: Evaluating LLMs as Agents | https://proceedings.iclr.cc/paper_files/paper/2024/file/e9df36b21ff4ee211a8b71ee8b7e9f57-Paper-Conference.pdf | 2024, ICLR | peer_reviewed | RQ2, RQ4 | proceedings 페이지·PDF의 연도/venue |
| 5 | `metagpt-multi-agent-collaborative-framework` | MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework | https://iclr.cc/virtual/2024/oral/19756 | 2024, ICLR | peer_reviewed | RQ2, RQ3 | ICLR 원문/발행 정보 |
| 6 | `autogen-multi-agent-conversations` | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversations | https://openreview.net/forum?id=BAakY1hNKS | 2024, COLM | peer_reviewed | RQ2, RQ3 | OpenReview 공개 PDF와 2024-07-10 게시일 |
| 7 | `chain-of-verification-reduces-hallucination` | Chain-of-Verification Reduces Hallucination in Large Language Models | https://aclanthology.org/2024.findings-acl.212 | 2024, Findings of ACL | peer_reviewed | RQ1, RQ2, RQ3 | ACL 원문/발행일 |
| 8 | `judgelm-scalable-judges` | JudgeLM: Fine-tuned Large Language Models are Scalable Judges | https://proceedings.iclr.cc/paper_files/paper/2025/file/7f8f73134e253845a8f82983219a8452-Paper-Conference.pdf | 2025, ICLR | peer_reviewed | RQ3, RQ4 | proceedings PDF의 최종 venue/연도 |
| 9 | `swe-bench-real-world-github-issues` | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? | https://arxiv.org/abs/2310.06770 | 2024, ICLR 표기 | peer_reviewed | RQ1, RQ2 | ICLR proceedings 원문 우선; 실행 테스트의 역할 범위 |
| 10 | `llms-as-judges-comprehensive-survey` | LLMs-as-Judges: A Comprehensive Survey on LLM-Based Evaluation Methods | https://arxiv.org/abs/2412.05579 | 2024, arXiv | preprint | RQ3, RQ4 | arXiv submission history와 정식 출판 여부 |
| 11 | `responsible-llm-empowered-multi-agent-systems` | Position: Towards a Responsible LLM-empowered Multi-Agent Systems | https://arxiv.org/abs/2502.01714 | 2025, arXiv | preprint | RQ3, RQ4 | arXiv submission history와 정식 출판 여부 |
| 12 | `survey-llm-based-multi-agent-systems-workflow` | A survey on LLM-based multi-agent systems: workflow, infrastructure, and challenges | https://link.springer.com/article/10.1007/s44336-024-00009-2 | 2024, Vicinagearth | survey | RQ2, RQ3, RQ4 | version of record의 2024-10-08·DOI·공개 본문 여부 |
| 13 | `survey-llm-autonomous-agents` | A survey on large language model based autonomous agents | https://link.springer.com/article/10.1007/s11704-024-40231-1 | 2024, Frontiers of Computer Science | survey | RQ1, RQ2 | version of record의 2024-03-22·DOI·공개 본문 여부 |

## 후보 분배와 여유분

| 후보 분류 | 최소 선별 수 | 1차 후보 수 | 후보 우선 번호 |
|---|---:|---:|---|
| peer_reviewed | 6 | 9 | 1–9 |
| preprint | 2 | 2 | 10–11 |
| survey | 1 | 2 | 12–13 |
| dataset_code | 0 | 0 | — |
| standards | 0 | 0 | — |
| web | 0 | 0 | — |

- 1차 후보는 총 13건으로 최소 N=9보다 4건의 여유를 둔다.
- 모든 1차 후보의 검색 확인 연도는 2023년 이상이다. 단, 이 값은 수집 단계에서 원문 기준으로 재검증한다.
- 10–11번은 각각 `preprint`로 수집하여 최소치를 채운다. 정식 출판본이 확인되더라도 이 단계의 병합 전에는 동일 연구를 중복으로 추가하지 않는다.
- 12–13번은 `survey` 분류의 후보이며, 하나 이상 공개 원문과 날짜를 확인해 선별한다.

## 수집 인계 규칙

1. `peer_reviewed`, `preprint`, `survey`별로 공개 원문을 `raw/<id>.md`에 보존한다. 논문은 proceedings/출판사 공개 PDF 또는 HTML을 우선한다.
2. 각 보존물은 원문 파일에 분석 메모를 섞지 않는다. URL·발행일/연도·수집일·저자·venue·후보 분류·접근 상태는 `raw/sources.yaml`에 기록한다.
3. `raw/sources.yaml`은 SCOPE의 source-balance taxonomy를 사용한다. 필수 필드는 `id`, `title`, `url`, `published_year`, `source_type`, `collected_at`, `status`이며, 필요 시 저자·venue·raw 파일 경로를 추가한다.
4. `published_year` 미상, 원문 접근 실패, 또는 같은 연구의 더 권위 있는 공개 proceedings/version-of-record가 확인된 후보는 삭제하지 말고 `failed` 또는 `excluded`로 표시한다. 중복·저품질·관련성의 최종 판정은 Curator 단계에 넘긴다.
5. 검색 결과, Semantic Scholar 레코드, 블로그/뉴스, 벤더 설명 페이지는 원문 후보 URL을 찾는 용도로만 사용하며 독립 수집 항목으로 만들지 않는다.
6. Collection 종료 전 `selected`가 N=9, peer_reviewed 6, preprint 2, survey 1 및 recent 50% 요건을 충족하는지 기계적으로 점검할 수 있게 source_type·published_year·status를 누락 없이 기록한다.
