## 3. Synthesized Themes & Key Technologies

### 3.1 Verification-Based Mitigation (e.g., CoVe)
*   **Mechanism:** A multi-step pipeline comprising baseline generation, verification planning, independent execution, and final revision.
*   **Maturity: Research/Early Implementation.** Primarily benchmarked on specific tasks like Wikidata and MultiSpanQA.
*   **Key Evidence:** 
    *   Dhuliawala et al. (2024) demonstrates precision increase from 0.17 to 0.36 for Wikidata using a two-step CoVe variant.
    *   Reduction in hallucinations is achieved by enabling models to deliberate on their own errors.
*   **Challenges:** Increases computational overhead due to multiple LLM inference calls.

### 3.2 Attribution & Retrofitting (e.g., RARR)
*   **Mechanism:** A model-agnostic system that uses retrieval and revision to attach attribution to generated text and fix unsupported claims while preserving original content.
*   **MND/Efficiency:** Uses few-shot prompting with large models (PaLM 540B, GPT-3) as editors/query generators.
*   **Key Evidence:**
    *   Gao et al. (20	3) shows RARR maintains original intent >90% of the time, significantly outperforming EFEC and LaMDA methods (which range from 6-40%).
    *   Scaling the editor stage is more critical for performance than scaling query generation.
*   **Challenges/Constraints:** Performance is bounded by the effectiveness of the search and the limitations of the editing model.

### 3.3 Consistency & Self-Refinement (e.g., SelfCheckGPT, Self-Refine)
*   **Mechanism:** Leveraging output consistency or iterative feedback loops to detect discrepancies without external retrieval.
*   **Maturity: Emerging/Research.**
*   **Key Evidence:** Manakul et al. (2023) uses output consistency as a black-box metric for uncertainty estimation.
