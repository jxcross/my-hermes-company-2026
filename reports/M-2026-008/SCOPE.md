# SCOPE.md - M-2026-008

## 1. Mission Overview
**Mission ID:** M-2026-008
**Topic:** LLM 에이전트를 위한 지식베이스·위키 구축 동향 — 지식 그래프·GraphRAG·메모리 아키텍처·재사용률 측정

The mission is to produce a high-quality trend report focusing on the evolving landscape of knowledge base and wiki construction for LLM agents. The primary technical focus areas include Knowledge Graphs, GraphRAG, memory architectures (context engineering/memory architecture), and the measurement of reusability/efficiency in these systems.

## 2. Mission Specifications

### A. Core Objectives
- Synthesize recent advancements in RAG (Retrieval-Augmented Generation) techniques that leverage structured knowledge (Knowledge Graphs).
- Analyze emerging memory architectures for LLM agents, specifically regarding context engineering and long-term memory persistence.
- Evaluate methods for measuring the effectiveness and reusability of constructed knowledge bases/wikis.

### B. Completion Criteria (Definition of Done)
A completed mission must satisfy:
1. **Content Coverage:** Comprehensive coverage of key technologies (GraphRAG, KG-based RAG, Semantic Memory).
2. **Pattern & Completeness:** Identification of clear architectural patterns and a structured breakdown of the technology stack.
3. **Recency/Source Balance Check:**
    - **Recency:** At least 60% of sources must be from within the last 2 years (cutoff: -2 years offset). No sources older than 5 years unless they are seminal works.
    /   **Balance:** Minimum requirements per category:
        - `academic`: $\ge$ 2
        - `vendor`: $\ge$ 2
        - `research_organziation`: $\ge$ 1
4. **Verification (Gate Level):** Successfully passed through Stage 6 (Cross-Verify) and Stage 9 (Independent Review).

### C. Constraints & Policies
- **Source Policy:** Adherence to the balance requirements defined in `pipeline.json` is mandatory.
- **Format:** Final report must follow the standard 7-stage structure: Overview, Technology Classification, Maturity, Application Candidates, etc.
- **Documentation:** All findings and analysis must be documented in the `analysis/` directory as per the pipeline stages.

## 3. Pipeline Reference
The execution follows the defined `pipeline.json` from Stage 1 (Scoping) to Stage 11 (Deliver). This task (t_b00904e6) is the foundation for all subsequent search and analysis strategies.
