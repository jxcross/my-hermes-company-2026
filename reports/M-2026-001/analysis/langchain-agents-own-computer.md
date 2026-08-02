# Agents need their own computer — 분석 노트

## 자료 식별
- 자료: raw/langchain-agents-own-computer.md
- 원문 URL: https://www.langchain.com/blog/agents-need-their-own-computer
- 발행일/수집일: 2026-07-21 / 2026-08-02 (raw/langchain-agents-own-computer.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: 에이전트는 단순 텍스트 생성이 아니라 filesystem, shell, package manager, network access, persistent state가 있는 “own computer”가 필요하다.
   - 근거: agent loop와 own computer 필요 조건을 명시 (raw/langchain-agents-own-computer.md:21-27).
2. 주장: production에서는 local/Docker prototype이 security와 isolation에서 실패한다.
   - 근거: agent-executed code는 model-generated, cloned repo, package install 등 untrusted sources에서 오며 standard container boundary는 부적합하다고 설명 (raw/langchain-agents-own-computer.md:28-35).
3. 주장: agent workspace는 hardware-virtualized machine 수준의 격리와 controls, observability를 가져야 한다.
   - 근거: own kernel/filesystem/network boundary, credential proxy, resource limits, audit log/traceability 요구 (raw/langchain-agents-own-computer.md:35-41).
4. 주장: sandboxes는 prompt injection을 제거하지 못하지만 execution blast radius를 줄인다.
   - 근거: external content가 model을 influence할 수 있고, sandboxes는 damage를 contain하나 raw output feed-back에는 non-agentic read pattern 등 추가 대응 필요 (raw/langchain-agents-own-computer.md:54-60).

## 핵심 수치·정의·방법론
- production 요구: fast provisioning(sub-second when warm), reproducible environments, persistent state (raw/langchain-agents-own-computer.md:41).
- LangSmith sandbox: median under one second boot, hardware-virtualized microVM, own kernel, session state persistence, automatic cleanup (raw/langchain-agents-own-computer.md:47-49).
- snapshot/fork: copy-on-write fork로 10 parallel branches 비용이 roughly one과 같음 (raw/langchain-agents-own-computer.md:50).
- auth proxy: outbound requests에 credential을 network layer에서 inject하여 secret이 runtime에 닿지 않게 함; domain allowlisting 제공 (raw/langchain-agents-own-computer.md:51).

## 상충·불일치 표시
- Anthropic cybersecurity incidents는 evaluation sandbox의 internet access misconfiguration이 실제 피해를 낳았다고 한다 (raw/anthropic-cybersecurity-evals-incidents.md:23-24,33). LangChain 자료의 “machine-level separation/allowlisting/credential proxy” 주장은 이와 정합적이지만, 구체 솔루션 효과 검증은 별도 필요.
