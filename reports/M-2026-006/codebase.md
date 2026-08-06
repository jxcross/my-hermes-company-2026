# Codebase Analysis: /work/company/scripts

## Overview
This document provides a structured analysis of the `/work/company/scripts` codebase for the purpose of generating high-quality documentation (API Reference, Architecture, ADR, and Tutorials) as specified in `SCOPE.md`.

## 1. Core Components & Logic

### 1.1 Gate Mechanisms (`/work/company/scripts/gates/*`)
*   **Role:** Systemic enforcement of verification gates within the 11-step pipeline.
*   **Key Logic (from `gate_keeper.py`):**
    *   **Functionality:** Monitors task progress; if a VERDICT (`FAIL` or specific rejection keywords like "수정요청") is detected in a verifier's output, it prevents downstream tasks from proceeding and triggers a revision loop.
    *   **Fail-closed Principle:** If no clear `PASS` signal is found, the gate defaults to `FAIL`.
    *   **Mechanism:** Uses graph-based mapping (parents=producer, children=downstream) rather than title parsing.
    *   **Key Claims/Evidence:** Implements "rejection automation" to prevent unblocked downstream tasks when a verifier completes a task but requests changes.

### 1.2 Utility Scripts (`/work/company/scripts/*.py`)
#### `usage_report.py`
*   **Role:** Pre-mission health check. Reports cumulative usage and quota exhaustion.
*   **Key Logic:**
    *   **Functions:** Checks for LLM quota exhaustion (for `codex` backend) by parsing worker logs (`*.log`). For `ollama` backend, it checks server reachability and the presence of required models via `/api/tags`.
    *   **Claims/Evidence:** 
        *   "Unmanaged resources are not managed." - Created because users weren't aware of usage limits causing mission stalls.
        *   "LLM call-less check" - Does not use LLM to check LLM limits (avoids recursive failure).
    *   **Metrics/Definitions:** 
        *   `LIMIT_RE`: Regex for `usage_limit_reached` or `rate_limit`.
        *   `OLLAMA_URL`: Default target for local backend probing.

#### `set_backend.py` (referenced in imports)
*   **Role:** Configures the active LLM backend (e.g., shifting from `codex` to `ollama`).
*   **Key Logic:** Handles environment variables and configuration updates for the pipeline's interaction with different model providers.

### 1.3 Tooling (`/work/company/scripts/tools/*`)
*   **Role:** Specialized utilities for pipeline support (e.g., `relevance_score.py`, `monitor_state.py`).

## 2. Documentation Requirements Summary

| Requirement | Detail from SCOPE.md |
| :--- | :--- |
| **Target Path** | `/work/company/scripts` |
| **Doc Types** | `api-ref`, `architecture`, `adr`, `tutorial` |
| **API Threshold** | 9-90% coverage for public APIs; 80% overall symbol coverage. |
| **Min Symbol Body** | 40 characters per documentation entry. |
| **Integrity** | Minimum 3 cross-links between different doc types required. |
| **Exclusions** | `.git`, `__pycache__`, `tests`, third-party libraries. |

## 3. Identified Patterns & Definitions
*   **VERDICT:** A standardized response signal (`PASS` or `FAIL`) parsed from verifier task outputs.
*   **Revision Loop:** Automatic creation of new tasks when a gate fails, targeting the original producer.
*   **Backend State Detection:** The logic follows checking `launchctl` (intent) vs. actual server banner/API output (reality).
