# Search Strategy for M-2026-007

## Overview
This document outlines the search strategy to collect materials for report M-2026-007. The strategy will guide data collection from multiple sources and categorize findings by year, source type, and taxonomy.

## Search Scope
Collect academic papers, preprints, conference proceedings, vendor documentation, and research reports related to AI agent architectures (LLM-based agents).

## Data Sources
1. **arXiv** - Research papers on agent architectures and LLM applications
2. **Semantic Scholar** - Academic papers across computer science domains
3. **Conference Proceedings** - ACL, NeurIPS, ICML, EMNLP, AAAI papers related to agents
4. **Vendor Documentation** - System cards from AI companies (e.g., OpenAI, Anthropic)
5. **Research Organizations** - Reports from independent AI safety/research groups
6. **Standards Bodies** - Drafts and specifications from IETF, NIST, ISO

## Search Timeframe
Primary focus: 2018-2026
Historical context: Older papers referenced in key findings

## Source Type Taxonomy
Sources will be categorized using the following taxonomy:

### Primary Categories (source_type)
- `academic` - arXiv, conference proceedings, journal articles, preprints
- `vendor` - Official documentation from AI companies (e.g., system cards, technical reports)
- `research_org` - Reports from independent research organizations and safety groups
- `standards` - Drafts, specifications, and guidelines from standards bodies
- `news` - Credible media coverage of significant developments

### Categorization Fields
Each source entry will include:
1. **ID** - Unique identifier (filename without extension)
2. **Title** - Full title of the work
3. **URL** - Direct link to the source
4. **Published Year** - Year of publication [required]
5. **Source Type** - Primary category from taxonomy above [required]
6. **Collected At** - Date when the resource was collected (format: YYYY-MM-DD)
7. **Status** - Selected / Failed / Excluded [required for sources.yaml]
8. **Seminal Flag** - True if the paper is a foundational work or key reference

## Search String Templates

### Academic Sources
```
arxiv.org OR semantic-scholar.org filetype:pdf "agent" AND ("LLM" OR "large language model") AND ("architecture" OR "system")
("autonomous agent" OR "AI agent") filetype:pdf intitle:"arXiv"
"agent" AND "multi-agent system" AND "language model" filetype:pdf
```

### Vendor Documentation
```site:openai.com OR site:anthropic.com OR site:mistral.ai OR site:google.com/filetype:md "system card" OR "technical report"
site:microsoft.com OR site:meta.com "agent architecture" filetype:md OR filetype:pdf
```

### Conference Proceedings
```site:aclweb.org OR site:nips.cc OR site:icml.cc OR site:emnlp.org OR site:aai.org "agent"
site:aclweb.org/anthology "language model" AND "agent" filetype:pdf
```

### Research Organizations
```site:arxiv.org OR site:ssrn.com OR site:safety-research.org ("LLM agent" OR "autonomous system") 
"AI safety" AND "agent architecture" filetype:pdf
```

## Recency and Source Balance Requirements
- **Recency**: Focus on papers published 2018-present, with emphasis on past 2 years
- **Source Balance**: Maintain a balanced distribution across source types:
  - Academic (40-50%)
  - Vendor (20-30%)
  - Research Org/Standards (20-30%)
  - News/Commentary (10% max for context)

## Output Structure
Collected sources will be organized in:
1. **raw/sources.yaml** - Structured metadata following the YAML specification
2. **raw/sources.md** - Human-readable table format with detailed information
3. Individual source files - Raw content saved as individual .md or .pdf files

## Validation Criteria
Each collected source must meet:
1. Direct relevance to AI agent architectures
2. Clear publication date
3. Authoritative source (academic, vendor, research org)
4. No duplicate content from previously collected sources

## Seminal Paper Identification
Longstanding foundational works should be marked with `seminal: true`:
- Classic papers that continue to influence current research
- Milestone achievements in the field  
- Highly cited works (≥100 citations) or widely adopted architectures