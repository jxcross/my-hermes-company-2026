# Search Strategy: M-2026-008

## Mission Objective
Identify recent trends (last 2 years) in Knowledge Graphs, GraphRAG, memory architectures for LLM agents, and metrics for knowledge reusability.

## 1. Key Research Pillars & Query Sets

### Pillar 1: GraphRAG & KG-based RAG
*Focus: Integration of structured KGs with RAG pipelines.*
- `"GraphRAG" AND "LLM"`
- `"Knowledge Graph" AND "Retrieval Augmented Generation" AND (trend OR architecture)`
- `"KG-based RAG" AND "agentic workflow"`
- `"structural knowledge retrieval" topic:LLM`

### Pillar 2: Agent Memory Architectures
*Focus: Context engineering, long-term memory, semantic/working memory.*
- `"LLM agent" AND ("memory architecture" OR "long-term memory")`
- `"context engineering" for "autonomous agents"`
- `"semantic memory" AND "LLM agents" AND (persistence OR architecture)`
- `"hierarchical memory" AND "agentic reasoning"`

### Pillar 3: Knowledge Reusability & Efficiency Metrics
*Focus: How to measure the value/utility of constructed KGs/wikis.*
- `"measuring effectiveness" of "knowledge base" for LLM`
- `"reusability metric" AND "LLM agent knowledge"`
- `"evaluation framework" for "GraphRAG"`
- `"cost-effectiveness" of KG construction in RAG`

## 2. Target Source Taxonomy & Strategy

| Type | Target Sources (Examples) | Search Strategy |
| :--- | :--- | :--- |
| `academic` | arXiv, ACL Anthology, ICLR, NeurIPS, ICML | Paper title/abstract search via `arxiv` tool and Google Scholar/Semantic Scholar. |
| `vendor` | OpenAI, Anthotic, Microsoft Research (GraphRAG), LangChain, LlamaIndex | Official engineering blogs, system cards, and documentation updates. |
| `research_org` | METR, AI Safety institutes, DeepMind, FAIR | Technical reports and foundational research papers. |
| `news/tech` | TechCrunch, VentureBeat, specialized AI newsletters | Monitoring high-signal AI news for new tool releases (e.g., LlamaIndex updates). |

## 3. Search Parameters & Constraints
- **Recency Filter:** Focus on $2024$-$2026$ content ($>60\%$ of sources).
- **Language:** English (Primary) + Korean (Secondary for local context).
- **Exclusion:** Avoid general RAG tutorials; prioritize architectural/structural advancements.

## 4. Execution Plan (Scout)
1. **Phase A (Academic):** Use `arxiv` and `web_search` to identify seminal/recent papers in GraphRRAG and Memory Architectures.
2. **Phase B (Vendor):** Scrape Microsoft, Anthropic, and LangChain blogs for productized implementations of KG-based RAG.
3. **Phase C (Synthesis):** Compile findings into `raw/sources.yaml` and `raw/sources.md`.
