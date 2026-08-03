# S13 — LangChain: agents need their own computer (wiki 재사용)

- 원자료: `raw/langchain-agents-own-computer.md`; canonical: `/work/llm-wiki/raw/mission-m-2026-001/langchain-agents-own-computer.md`
- 성격: 운영 설계 권고·제품 설명. 독립 보안 평가 결과가 아니다.

## 핵심 주장과 근거
1. **주장:** agent가 실제 검증 loop를 수행하려면 filesystem·shell·package manager·network·persistent state를 갖는 실행환경이 필요하다. [원문 L22–28]
   - **근거:** code agent의 clone→install→test→patch→retest, data/research agent의 실제 artifact 생성·검증 사례를 든다. [L23–28]
2. **주장:** model-generated code, cloned repo, mid-task package, arbitrary file를 다루는 agent 실행은 untrusted로 보고 machine-level separation을 기본으로 해야 한다. [L29–39]
   - **근거:** standard container boundary가 untrusted model-generated execution을 위한 것이 아니며, hardware-virtualized machine·separate kernel/filesystem/network boundary를 권고한다. [L29–36]
3. **주장:** credential proxy, resource cap, network allowlist, audit/reproducibility가 isolation과 함께 필요하다. [L37–42]
   - **근거:** proxy가 runtime에 token을 노출하지 않고 credential을 주입하며, CPU/memory/network limit가 runaway cost를 막고 trace가 known state 재실행을 돕는다고 설명한다. [L38–42]
4. **주장:** sandbox는 execution blast radius를 줄이지만 agent context로 되돌아오는 untrusted output의 prompt injection을 제거하지 않는다. [L55–61]
   - **근거:** downloaded document/execution output의 instruction이 downstream action에 영향을 줄 수 있으므로 non-agentic read, least privilege를 권고하며 prompting만으로 injection 탐지를 기대하지 말라고 한다. [L55–61]

## 수치·제품 주장
- LangSmith sandbox median boot time under 1 second, microVM, persistent state라고 제품 특성을 서술한다. [L48–52]

## 상충 표시
- `S08` security draft의 sandbox·JIT permission·audit metric과 실천 항목이 겹치나, S13은 vendor 권고이고 S08은 draft framework다. `S11`은 evaluation infrastructure의 실제 containment failure를 제공한다.
