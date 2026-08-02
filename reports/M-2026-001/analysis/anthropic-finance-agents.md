# Agents for financial services — 분석 노트

## 자료 식별
- 자료: raw/anthropic-finance-agents.md
- 원문 URL: https://www.anthropic.com/news/finance-agents
- 발행일/수집일: 2026-07-15 / 2026-08-02 (raw/anthropic-finance-agents.md:3-9)

## 주장(claim)과 근거(evidence)
1. 주장: Anthropic은 금융서비스의 시간 소모 작업을 위한 10개 ready-to-run agent templates를 출시했다.
   - 근거: pitchbooks, KYC files, month-end close 등 10 templates를 release한다고 서술 (raw/anthropic-finance-agents.md:16,22-32).
2. 주장: 각 template은 skills, connectors, subagents를 패키징한 reference architecture다.
   - 근거: “packages three things: skills…, connectors…, subagents…” (raw/anthropic-finance-agents.md:20).
3. 주장: Claude는 Microsoft Excel, PowerPoint, Word, Outlook(coming soon) add-ins로 업무 context를 앱 간에 유지한다.
   - 근거: Microsoft 365 add-ins와 context carry 설명 (raw/anthropic-finance-agents.md:17,37-40,61).
4. 주장: Claude Opus 4.7은 금융 tasks에서 Vals AI Finance Agent benchmark 64.37%로 industry leading이라고 제시된다.
   - 근거: “leads the industry… at 64.37%” (raw/anthropic-finance-agents.md:19).

## 핵심 수치·정의·방법론
- agent template 10종: Pitch builder, Meeting preparer, Earnings reviewer, Model builder, Market researcher, Valuation reviewer, General ledger reconciler, Month-end closer, Statement auditor, KYC screener (raw/anthropic-finance-agents.md:22-32).
- template 구성요소 정의: skills=task instructions/domain knowledge, connectors=governed data access, subagents=specific sub-task Claude models (raw/anthropic-finance-agents.md:20).
- 배포 방식: Claude Cowork/Claude Code plugin 또는 Claude Managed Agents cookbook (raw/anthropic-finance-agents.md:21,33-35,60).
- 운영통제: users stay in the loop reviewing/approving before client/file/action (raw/anthropic-finance-agents.md:36).
- 데이터 접근: FactSet, S&P Capital IQ, MSCI, PitchBook, Morningstar, Chronograph, LSEG, Daloopa 등 connector 언급 (raw/anthropic-finance-agents.md:41-46).

## 상충·불일치 표시
- 같은 Anthropic 자료군에서 finance agents는 실무 배포와 human-in-the-loop를 강조한다 (raw/anthropic-finance-agents.md:35-36). agentic misalignment 자료는 minimal human oversight와 sensitive info access 조합에 caution을 제기한다 (raw/anthropic-agentic-misalignment.md:20). 사용 맥락이 다르므로 검증 단계에서 함께 검토 필요.
