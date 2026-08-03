# M-2026-003 보고서 초안 — AI 에이전트 메모리·컨텍스트 관리 동향

- 대상: 장기·단기 메모리, 컨텍스트 구성·압축·검색·갱신, 장기 실행 상태 전달, 평가, 보안·프라이버시·거버넌스
- 종합일: 2026-08-03
- 근거 범위: Reader 분석 12건, Cross-Verify, Synthesis 및 수집 출처 목록만 사용했다. Cross-Verify 총괄 상태는 **확인 20건·상충 0건·미검증 14건(PASS)** 이다. 이 PASS는 미검증 항목의 사용 제한을 공개한 조정 게이트 판정이며, 미검증 주장이 확인된 사실이 되었다는 뜻은 아니다. [검증표](verify/verification.md) · [종합 노트](synthesis/synthesis.md) · [수집 목록](raw/sources.md)

## 1. 요약

1. **메모리 평가는 단일 점수보다 과업 축별로 다뤄야 한다.** LoCoMo, LongMemEval, MemoryAgentBench는 각각 장기 대화, 장기 상호작용의 5개 능력, 증분 다중 턴 형식을 다루지만 과업·단위가 달라 점수의 직접 비교는 적절하지 않다. 내부 평가는 retrieval, multi-session/temporal reasoning, update, abstention 등 시나리오별 기준선·비용·지연을 함께 기록하는 방식이 적합한 후보다. [LoCoMo](https://arxiv.org/abs/2402.17753) · [LongMemEval](https://arxiv.org/abs/2410.10813) · [MemoryAgentBench](https://arxiv.org/abs/2507.05257) · [검증표 01-2·02-1·04-1](verify/verification.md)

2. **장기 실행에서는 상태·근거 전달을 운영 산출물로 다룰 필요가 있다.** 독립 대조는 새 context session의 prior-state 상실 및 단순 압축의 세부 근거 손실 문제를 지지한다. 따라서 목표·결정·미해결 항목·trace·검증 상태를 가진 session handoff artifact를 두고, 재개 시 검토·갱신하도록 설계하는 방안을 우선 검토할 수 있다. 다만 artifact의 최적 형식·분량과 역할 분리의 상대 효과는 검증되지 않았다. [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Anthropic long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Git Context Controller](https://arxiv.org/html/2508.00031v3) · [검증표 05-3·06-1~06-3](verify/verification.md)

3. **persistent memory는 성능 논의와 별도로 보안·프라이버시·거버넌스 검토가 필요하다.** persistent/distributed memory의 cross-session poisoning·비인가 접근 위험 방향은 독립 자료로 지지되지만, dashboard·retention·memory-free mode 같은 통제의 효과는 검증되지 않았다. NIST AI RMF Generative AI Profile은 조직·용도별 적용 판단을 전제로 한 risk-management 틀로 활용할 수 있으며, 특정 safeguard의 실증 근거는 아니다. [New America](https://www.newamerica.org/insights/ai-agents-and-memory) · [Long-Term Memory Security Survey](https://arxiv.org/html/2604.16548v1) · [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) · [검증표 10-1·10-3·11-1~11-3](verify/verification.md)

## 2. 핵심 동향

### 2.0 필수 영역별 성숙도와 적용상 trade-off

성숙도 척도는 **연구**(방법·평가 제안 또는 독립 재현 부재), **초기**(구현·운영 관행은 있으나 일반화·비교효과 제한), **실무**(현재 적용 가능한 명확한 운영·거버넌스 절차)로 사용한다. `실무`는 보편적 성능 우위를 뜻하지 않는다. 아래 판정은 [Synthesis의 분류 기준](synthesis/synthesis.md)과 [검증표](verify/verification.md)의 확인·미검증 경계를 보고서 안에서 재구성한 것이다.

| 필수 영역 | 성숙도 판정 | 근거 범위 | 적용상 trade-off·경계 | 출처 |
|---|---|---|---|---|
| 메모리 아키텍처 | **연구** | A-MEM의 note/link·동적 indexing·memory evolution 및 EvoLib의 skill/insight·consolidation·weighting 메커니즘은 확인됐다. | A-MEM의 성능 우위와 EvoLib의 token 효율 우위는 독립 재현이 없으며, 저장 단위·갱신 규칙·평가 조건의 동등성도 확인되지 않았다. 따라서 채택 근거가 아니라 소규모 비교 실험의 가설로 한정한다. | [A-MEM](https://arxiv.org/abs/2502.12110) · [EvoLib](https://arxiv.org/html/2605.14477v1) · [검증표 03-1~03-3·07-1~07-3](verify/verification.md) |
| 컨텍스트 최적화 | **초기** | 긴 입력에서 정보 활용 성능 저하 방향과 context 관리 병목은 독립 자료로 지지되며, 고신호 context·just-in-time retrieval·progressive disclosure는 제공자 운영 패턴으로 제시된다. | 특정 retrieval 조합·compaction 보존율·harness 변경의 상대 우위는 일반화할 수 없다. Deep Agents의 약 65% token 감소는 특정 조건의 관찰값이고 reward CI가 0을 포함한다. | [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Deep Agents v0.7](https://www.langchain.com/blog/deep-agents-v0-7) · [검증표 05-1~05-3·08-1~08-3](verify/verification.md) |
| 평가/신뢰성 | **연구** | LoCoMo, LongMemEval, MemoryAgentBench의 과업·규모·형식은 확인됐다. | 세 벤치마크는 과업·평가 단위·역량 정의가 달라 점수를 직접 비교할 수 없다. LongMemEval의 성능 저하·검색 확장 우위는 독립 재현되지 않았고, MemoryAgentBench는 문서·commit 고정이 필요하다. | [LoCoMo](https://arxiv.org/abs/2402.17753) · [LongMemEval](https://arxiv.org/abs/2410.10813) · [MemoryAgentBench](https://arxiv.org/abs/2507.05257) · [검증표 01-2·02-1~02-3·04-1~04-3](verify/verification.md) |
| 보안/프라이버시 | **초기** | persistent/distributed memory의 cross-session poisoning·비인가 접근 위험 방향은 독립 자료로 지지된다. | dashboard·retention·memory-free mode는 정책 제안으로 통제 효과가 검증되지 않았다. NIST의 risk-management 절차는 적용 후보이나 특정 safeguard의 실증 근거는 아니며, IETF 문서는 individual Internet-Draft다. | [New America](https://www.newamerica.org/insights/ai-agents-and-memory) · [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) · [IETF Internet-Draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [검증표 10-1~10-3·11-1~11-3·12-1~12-3](verify/verification.md) |

### 2.1 장기기억 평가는 평가 단위와 과업 축을 명시하는 방향

LoCoMo는 QA·이벤트 요약·멀티모달 대화 생성을 포함하는 장기 대화 평가로, 평균 300턴·약 9K 토큰·최대 35세션을 제시한다. 이 규모와 과업 구성은 독립 후속 연구 및 프로젝트 페이지로 대조됐다. [LoCoMo](https://arxiv.org/abs/2402.17753) · [ACL 2026 후속 연구](https://aclanthology.org/2026.findings-acl.38.pdf) · [LoCoMo 프로젝트](https://snap-research.github.io/locomo) · [검증표 01-2](verify/verification.md)

LongMemEval은 정보 추출, 다중세션 추론, 시간 추론, 지식 업데이트, abstention의 5개 능력과 500개 선별 질문을 제시한다. 공개 포스터와 저장소는 이 범위·규모를 뒷받침한다. 다만 저자 보고의 지속 상호작용 정확도 30% 하락과 indexing–retrieval–reading 분해 기법의 개선 효과는 독립 재현되지 않았으므로, 일반 성능 사실이나 설계 우위로 사용하면 안 된다. [LongMemEval](https://arxiv.org/abs/2410.10813) · [ICLR 2025 포스터](https://iclr.cc/virtual/2025/poster/28290) · [LongMemEval 저장소](https://github.com/xiaowu0162/LongMemEval) · [검증표 02-1~02-3](verify/verification.md)

MemoryAgentBench는 기존 데이터의 재구성과 신규 데이터로 증분 다중 턴 평가를 구성한다. 보존된 arXiv v4 초록은 accurate retrieval, test-time learning, long-range understanding, selective forgetting을 네 역량으로 표기하지만, 현행 공식 README는 네 번째를 `Conflict Resolution`으로 표기한다. 따라서 구현 또는 인용에는 사용할 문서와 commit/version을 고정해야 한다. [MemoryAgentBench](https://arxiv.org/abs/2507.05257) · [ICLR 2026 공개 리뷰](https://cseweb.ucsd.edu/~jmcauley/reviews/iclr26c.pdf) · [공식 GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench) · [Hugging Face README](https://huggingface.co/datasets/ai-hyz/MemoryAgentBench/blob/5bd2ff1624cfe699926f6e22d165411cb400c2a8/README.md) · [검증표 04-1~04-3](verify/verification.md)

### 2.2 구조화·진화형 memory는 연구 단계의 설계 후보

A-MEM은 note 생성, 동적 indexing/linking, 새 정보에 따른 기존 memory의 표현·속성 갱신을 제안한다. 이 메커니즘은 독립 ACL 연구 및 OpenReview 메타데이터로 대조됐다. 그러나 6개 foundation model에서 기존 SOTA보다 우수했다는 결과는 독립 재현되지 않았고, 효과 크기·비용도 현재 보존 근거에서 일반화할 수 없다. [A-MEM](https://arxiv.org/abs/2502.12110) · [ACL 2026 후속 연구](https://aclanthology.org/2026.findings-acl.38.pdf) · [OpenReview](https://openreview.net/forum?id=FiM0M8gcct) · [검증표 03-1~03-3](verify/verification.md)

EvoLib은 raw experience에서 재사용 가능한 skill·reflective insight를 추출하고 consolidation과 dynamic weighting으로 knowledge library를 갱신하는 접근을 제시한다. 구성 요소 자체는 논문과 공개 구현에서 확인됐지만, retrieval/abstract memory 대비 token 효율적 우위는 저자 보고에 머물러 있다. A-MEM과 EvoLib은 모두 연결·갱신되는 지식을 다루나 저장 단위, 갱신 규칙, 평가 조건의 동등성은 확인되지 않았다. [EvoLib 블로그](https://www.microsoft.com/en-us/research/blog/evolib-turning-experience-into-evolving-knowledge/) · [EvoLib 논문](https://arxiv.org/html/2605.14477v1) · [EvoLib GitHub](https://github.com/microsoft/EvoLib) · [검증표 07-1~07-3](verify/verification.md)

### 2.3 context 구성과 token 예산은 측정 가능한 운영 변수

긴 입력에서 정보 활용 성능이 저하하는 방향은 독립 연구로 지지된다. Anthropic은 작은 고신호 context, just-in-time retrieval, progressive disclosure를 운영 패턴으로 제시한다. 이 패턴은 적용 후보이지만, 최적 retrieval 조합이나 compaction 보존율의 보편적 우위를 뜻하지 않는다. [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9) · [검증표 05-1~05-3](verify/verification.md)

LangChain은 Deep Agents v0.7에서 base input token을 약 6K에서 약 2K로 줄였다고 보고했고, 독립 기술 요약은 약 65% 감소 및 세 변경점(시스템 프롬프트 제거, tool description 43% 축소, Todo middleware 기본 제외)을 대조했다. 그러나 reward confidence interval이 모든 모델에서 0을 포함하므로, 이 관찰을 성능 동등 또는 향상의 확정 근거로 해석할 수 없다. 65%는 특정 제품·평가 조건의 관찰값이지 일반 목표값이나 보장이 아니다. [Deep Agents v0.7](https://www.langchain.com/blog/deep-agents-v0-7) · [ExplainX](https://explainx.ai/blog/langchain-deep-agents-0-7-leaner-harness-july-2026) · [daily.dev](https://daily.dev/posts/langchain-releases-deep-agents-v0-7-with-65-fewer-base-input-tokens-hkzwejbl8) · [검증표 08-1~08-3](verify/verification.md)

### 2.4 보안·프라이버시·거버넌스는 memory data flow로 연결

New America는 persistent/distributed memory가 privacy·consent·accountability의 통제를 어렵게 만든다는 정책 분석을 제시하며, compartmentalization, purpose tag, audit, dashboard, retention, memory-free mode를 권고한다. cross-session poisoning 및 비인가 접근 위험의 방향은 독립 survey와 보안 연구가 지지하지만, New America의 권고 항목은 정책 제안으로서 통제 효과가 검증된 것은 아니다. [New America](https://www.newamerica.org/insights/ai-agents-and-memory) · [Long-Term Memory Security Survey](https://arxiv.org/html/2604.16548v1) · [Unit 42](https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory) · [검증표 10-1·10-3](verify/verification.md)

NIST AI 600-1은 Govern·Map·Measure·Manage에 연결되는 suggested action을 제시하며, 적용 여부를 조직과 GAI actor의 고유 use에 따라 판단하도록 한다. 따라서 memory 운영에서는 저장·검색·공유·삭제별 expected/acceptable use, 보존기간, access 목적, audit 책임, incident 대응을 문서화하는 risk review 틀로 사용할 수 있다. 이는 특정 memory architecture나 safeguard의 효과를 실증한 자료가 아니다. [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) · [검증표 11-1~11-3](verify/verification.md)

IETF의 *Security Evaluation Benchmark for AI Agents*는 memory poisoning, cross-user/session isolation, right to be forgotten, memory integrity를 포함한 4개 1차원·55개 2차 metric을 제안한다. 다만 이는 individual Internet-Draft로서 확정 표준이나 검증된 benchmark가 아니므로, 외부 인증·점수 기준이 아니라 내부 threat-model checklist의 참고로만 제한해야 한다. [IETF Internet-Draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [IETF Datatracker](https://datatracker.ietf.org/doc/draft-han-bmwg-agent-security-benchmark/) · [검증표 12-1~12-3](verify/verification.md)

## 3. 근거·수치 정리

| 항목 | 근거·수치 | 검증 상태와 해석 | 출처 |
|---|---|---|---|
| LoCoMo 평가 규모 | 평균 300턴, 약 9K 토큰, 최대 35세션 | **확인**. 장기 대화 평가의 구성·규모이며, 다른 벤치마크와의 점수 비교 근거는 아니다. | [LoCoMo](https://arxiv.org/abs/2402.17753) · [ACL 2026](https://aclanthology.org/2026.findings-acl.38.pdf) · [검증표 01-2](verify/verification.md) |
| LongMemEval | 5개 능력, 500개 선별 질문 | **확인**. 30% 정확도 하락과 확장 기법의 개선은 **미검증**인 저자 보고다. | [LongMemEval](https://arxiv.org/abs/2410.10813) · [ICLR 2025](https://iclr.cc/virtual/2025/poster/28290) · [검증표 02-1~02-3](verify/verification.md) |
| MemoryAgentBench | incremental multi-turn 형식; 보존 arXiv v4의 4개 역량 | **확인**. `selective forgetting`/`Conflict Resolution` 용어 불일치가 있으므로 문서·commit 고정이 필요하다. | [arXiv](https://arxiv.org/abs/2507.05257) · [GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench) · [검증표 04-1~04-2](verify/verification.md) |
| A-MEM·EvoLib | note/link/evolution; skill/insight·consolidation·weighting | **구성은 확인**. 양 접근의 상대 성능·token 효율 우위는 **미검증** 저자 보고다. | [A-MEM](https://arxiv.org/abs/2502.12110) · [EvoLib](https://arxiv.org/html/2605.14477v1) · [검증표 03-2~03-3·07-2~07-3](verify/verification.md) |
| Deep Agents v0.7 | base input 약 6K→약 2K, 약 65% 감소; tool description 43% 축소 | **수치·변경점은 확인**. reward CI가 0을 포함해 성능 비열화 부재는 확정되지 않았다. | [LangChain](https://www.langchain.com/blog/deep-agents-v0-7) · [ExplainX](https://explainx.ai/blog/langchain-deep-agents-0-7-leaner-harness-july-2026) · [검증표 08-1~08-3](verify/verification.md) |
| IETF draft | 4개 1차원, 55개 2차 metric | **draft 내용은 확인**. 독립 구현·재현·test-case 타당화가 없어 표준 또는 검증 benchmark가 아니다. | [IETF draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [검증표 12-1~12-3](verify/verification.md) |

## 4. 시사점 및 적용 후보

1. **session handoff artifact를 기본화한다.** 목표·결정·미해결 항목·trace·검증 상태를 구조화하고, ownership·갱신 시점·stale 처리·재개 시 검토를 명시한다. 완료율·재작업·결정 누락을 함께 관찰한다. 이는 cross-session 상태 상실과 압축 한계에 대응하는 적용 후보이며, 최적 artifact 형식의 검증된 처방은 아니다. [Anthropic long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) · [Git Context Controller](https://arxiv.org/html/2508.00031v3) · [검증표 06-1~06-3](verify/verification.md)

2. **고신호·점진적 context retrieval baseline을 둔다.** 식별자 기반 보관과 필요 시 읽기를 적용하되, retrieval 단위·권한·freshness·fallback을 명시하고 recall·근거 누락·token·지연을 함께 측정한다. 특정 index/key/query 확장의 우위는 독립 재현 전까지 전제하지 않는다. [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [LongMemEval](https://arxiv.org/abs/2410.10813) · [검증표 02-2~02-3·05-1~05-3](verify/verification.md)

3. **단일 점수 대신 내부 scenario별 memory 평가를 설계한다.** retrieval, multi-session/temporal reasoning, update, abstention 등 과업 축별 test set과 기준선·비용·지연을 기록하고, 벤치마크 간 점수 직접 비교를 피한다. MemoryAgentBench는 구현·인용 전에 문서·commit을 고정한다. [LoCoMo](https://arxiv.org/abs/2402.17753) · [LongMemEval](https://arxiv.org/abs/2410.10813) · [MemoryAgentBench](https://arxiv.org/abs/2507.05257) · [검증표 01-2·02-1·04-1~04-2](verify/verification.md)

4. **consolidation을 소규모 비교 실험으로 한정한다.** raw log와 재사용 insight/skill을 분리하고, 원문 evidence 보존, 승격 기준·승인자·rollback·provenance를 둔다. 외부 성능 수치가 아니라 내부 비교의 관찰값으로 판단한다. [A-MEM](https://arxiv.org/abs/2502.12110) · [EvoLib](https://arxiv.org/html/2605.14477v1) · [검증표 03-1~03-3·07-1~07-3](verify/verification.md)

5. **harness token budget을 품질과 함께 점검한다.** 중복 prompt/tool description을 계측하고 middleware는 과업별 opt-in으로 평가한다. 변경 전후 동일 과업에서 base token·cost·품질 confidence interval을 함께 기록하며, 65% 감소를 내부 목표치로 전용하지 않는다. [Deep Agents v0.7](https://www.langchain.com/blog/deep-agents-v0-7) · [검증표 08-1~08-3](verify/verification.md)

6. **NIST 절차에 memory data-flow 위험검토를 연결한다.** 저장·검색·공유·삭제별 expected/acceptable use, 보존기간, access 목적, audit 책임, incident 대응을 문서화하고 용도별 적용성을 검토한다. [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) · [검증표 11-1~11-3](verify/verification.md)

7. **민감·공유 memory 통제는 pilot으로 평가한다.** 데이터 분류·동의·authorization scope·삭제/복구 정책과 공격·오남용 test 및 운영부담을 함께 기록한다. dashboard·retention·memory-free mode는 효과가 검증된 통제로 가정하지 않는다. [New America](https://www.newamerica.org/insights/ai-agents-and-memory) · [Long-Term Memory Security Survey](https://arxiv.org/html/2604.16548v1) · [검증표 10-1·10-3](verify/verification.md)

8. **IETF draft는 내부 threat-model checklist 참고로만 사용한다.** 내부 test case·pass/fail 정의와 draft 버전·날짜를 별도 기록하고, 55개 metric 또는 점수를 외부 인증·표준 준수의 근거로 사용하지 않는다. [IETF Internet-Draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [검증표 12-1~12-3](verify/verification.md)

## 5. 불확실성·반대근거·상충 지점

- **미검증 14건의 사용 경계:** LongMemEval의 30% 하락 및 검색 확장 우위, A-MEM·EvoLib의 성능 우위, MemoryAgentBench의 전 역량 미숙달, context/harness의 운영 권고, 정책 제안 및 IETF draft의 metric은 저자·제공자 보고 또는 단일 문서의 제안으로만 서술한다. 일반 성능 사실, 최선 관행, 확정 표준·검증 benchmark·통제 효과로 승격하지 않는다. [검증표 §7](verify/verification.md) · [종합 노트 §4](synthesis/synthesis.md)

- **MemoryAgentBench 용어 상충은 범위를 한정해 해소했다.** 보존 arXiv v4의 `selective forgetting`과 현행 공식 README의 `Conflict Resolution`은 서로 다르다. 본 보고서는 전자를 보존본의 저자 정의에만 한정하며, 구현·인용에서 문서와 commit/version을 고정하도록 한다. [arXiv](https://arxiv.org/abs/2507.05257) · [공식 GitHub](https://github.com/HUST-AI-HYZ/MemoryAgentBench) · [검증표 04-2](verify/verification.md)

- **MCP authorization에 대한 양극단의 단정은 피해야 한다.** New America의 ‘lack’은 해당 글의 저자 문제 제기이고, 공식 authorization 명세의 존재와 identity·upstream delegation·fine-grained policy의 잔여 과제는 분리해야 한다. 따라서 ‘authorization이 없다’ 또는 ‘authorization이 있으므로 모든 통제가 해결됐다’고 말할 근거는 이 자료에 없다. [New America](https://www.newamerica.org/insights/ai-agents-and-memory) · [MCP Authorization 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) · [Cloud Security Alliance](https://openreview.net/pdf/7db8d7d31396bd9a8cc21dbbc479c7511639f8d8.pdf) · [검증표 10-2](verify/verification.md)

- **벤치마크의 층위 차이:** LoCoMo, LongMemEval, MemoryAgentBench는 과업·평가 단위·역량 정의가 다르다. 세 결과의 점수나 순위를 하나의 memory quality 수치로 합산하거나 직접 비교하지 않는다. [LoCoMo](https://arxiv.org/abs/2402.17753) · [LongMemEval](https://arxiv.org/abs/2410.10813) · [MemoryAgentBench](https://arxiv.org/abs/2507.05257) · [종합 노트 §2](synthesis/synthesis.md)

- **NIST와 IETF의 지위 차이:** NIST AI 600-1은 use별 적용 판단을 전제한 risk-management profile이고, IETF 문서는 individual Internet-Draft다. 둘 모두 memory architecture의 상대 성능이나 safeguard 효과를 실증하는 자료는 아니다. [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) · [IETF Internet-Draft](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) · [검증표 11-3·12-1~12-3](verify/verification.md)

## 6. 출처 목록

### 수정 검증 기록 (G9R)

- 필수 네 영역의 성숙도·근거·trade-off는 본문 [§2.0](#20-필수-영역별-성숙도와-적용상-trade-off)에 같은 행으로 명시했다. 분류 기준과 추적 경로는 [Synthesis §2](synthesis/synthesis.md)에 보존돼 있다.
- 제외된 OpenAI 자료의 `published_year`는 `null`로 정정했다. 원문 페이지에서 발행일·연도를 확인하지 못했으므로 URL의 `2025`는 메타데이터 근거로 쓰지 않으며, 이 자료는 `excluded` 상태를 유지한다. [수집 출처 목록](raw/sources.md) · [sources.yaml](raw/sources.yaml)
- `selected` 자료는 12건이며, academic 4건·vendor 4건·research_org 2건·standards 2건이다. 모두 2024년 이후 발행으로 기록돼 recency는 12/12(100%)이며, SCOPE의 10건 이상·academic 2건 이상·vendor 2건 이상·research_org 1건 이상·recent 60% 이상 기준을 충족한다. [수집 출처 목록](raw/sources.md) · [SCOPE](SCOPE.md)

### 미션 산출물

1. [수집 출처 목록](raw/sources.md) — 12개 selected 자료의 URL·발행일·수집일·유형 및 제외 자료를 기록한다.
2. [Reader 분석 인덱스](analysis/README.md) — 자료별 추출 범위와 인용 경계를 정리한다.
3. [Cross-Verify 검증표](verify/verification.md) — 핵심 주장별 확인·상충·미검증 판정의 단일 기준이다.
4. [Synthesis 종합 노트](synthesis/synthesis.md) — 기술 분류·성숙도·적용 후보와 불확실성 register의 입력이다.

### 선별한 원문 12건

1. [LoCoMo — Evaluating Very Long-Term Conversational Memory of LLM Agents](https://arxiv.org/abs/2402.17753) (academic, 2024)
2. [LongMemEval — Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813) (academic, 2024)
3. [A-MEM — Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110) (academic, 2025)
4. [MemoryAgentBench — Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions](https://arxiv.org/abs/2507.05257) (academic, 2025)
5. [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (vendor, 2025)
6. [Anthropic — Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (vendor, 2025)
7. [Microsoft Research — EvoLib: Turning experience into evolving knowledge](https://www.microsoft.com/en-us/research/blog/evolib-turning-experience-into-evolving-knowledge/) (vendor, 2026)
8. [LangChain — Deep Agents v0.7](https://www.langchain.com/blog/deep-agents-v0-7) (vendor, 2026)
9. [METR — Frontier Risk Report (February to March 2026)](https://metr.org/blog/2026-05-19-frontier-risk-report) (research organization, 2026)
10. [New America — AI Agents and Memory: Privacy and Power in the MCP Era](https://www.newamerica.org/insights/ai-agents-and-memory) (research organization, 2025)
11. [NIST — AI RMF: Generative AI Profile (AI 600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) (standards, 2024)
12. [IETF — Security Evaluation Benchmark for AI Agents, draft-han-bmwg-agent-security-benchmark-00](https://www.ietf.org/archive/id/draft-han-bmwg-agent-security-benchmark-00.html) (individual Internet-Draft, 2026)

발행일·수집일·선별 상태의 정확한 메타데이터는 [수집 출처 목록](raw/sources.md)과 [sources.yaml](raw/sources.yaml)을 따른다.
