# GATE JARVIS 4.0 — System Architecture Document

## 1. Architectural Overview

GATE JARVIS is an adaptive AI-powered learning operating system engineered specifically for Mechanical Engineering GATE (Graduate Aptitude Test in Engineering) aspirants targeting an All India Rank under 100 (AIR < 100). The system combines local SQLite-backed persistence, localized and cloud semantic retrieval (RAG), cognitive state tracking (Mastery, Retention, Error Intelligence), interactive testing engines with negative marking, and autonomous agent orchestration in English, Hindi, and Marathi.

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                    |
|   Streamlit Frontend + Custom Dynamic Theme Manager (Midnight Aerospace System)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             GATE JARVIS ORCHESTRATOR                              |
|   Multilingual Command Interpreter (EN, HI, MR) + Intent Parser + HITL Safety     |
+-----------------------------------------------------------------------------------+
      |                      |                     |                     |
      v                      v                     v                     v
+------------+       +---------------+      +-------------+       +---------------+
| RAG & DOCS |       |  LEARNING OS  |      | TEST ENGINE |       | MISTAKE INTEL |
| Extractor  |       | Mastery Model |      | MCQ/MSQ/NAT |       | 7 Error Taxon |
| Chunker    |       | Spaced Rep.   |      | Timer/Score |       | Error Drill   |
| Vectorizer |       | Prereq Graph  |      | Diagnostics |       | Interventions |
+------------+       +---------------+      +-------------+       +---------------+
      |                      |                     |                     |
      +----------------------+---------------------+---------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                DATA LAYER (SQLite)                                |
|  gate_jarvis.db: Subjects, Notes, Chunks, Doubts, Tests, Memory, Mistakes, Plots  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Subsystems

### 2.1 Frontend Layer (`app.py`, `theme_manager.py`, `views/`)
- **Framework**: Streamlit (Python 3.10+) running locally on port 8503.
- **Visual Design**: Midnight Aerospace aesthetic with high-contrast tactical tokens (`--bg-primary: #0a0f1d`, `--accent: #38bdf8`, `--card-bg: #111827`).
- **Dynamic Theming**: Live runtime theme switcher (`theme_manager.py`) persisting user theme in session state and injecting scoped CSS.
- **Routing**: Single-page modular routing via sidebar menu radio dispatcher.

### 2.2 Autonomous Agent Engine (`agent/`)
- **`agent_core.py`**: Coordinates the cognitive cycle:
  `Listen -> Parse NLU -> Safety Permission Check -> Execute Tool -> Format Multilingual Response -> Audit Log`.
- **`command_interpreter.py`**: Script-aware natural language parsing supporting English, Devanagari Hindi, and Devanagari Marathi with regex and phonetic marker extraction.
- **`tool_registry.py`**: Human-In-The-Loop (HITL) registry with 4 security levels:
  - `LEVEL_0_READ`: Immediate execution (safe queries, stats).
  - `LEVEL_1_LOW_RISK_WRITE`: Auto-execute when enabled (task creation, note taking, study logs).
  - `LEVEL_2_USER_APPROVAL`: Pauses for explicit UI confirmation (mass deletion, database reset).
  - `LEVEL_3_BLOCKED`: Hard system block (arbitrary OS command execution).

### 2.3 Knowledge Retrieval & RAG Pipeline (`services/`)
- **`extractor_service.py`**: Ingests `.pdf`, `.docx`, `.txt`, `.md` documents with fallback heuristics.
- **`chunker_service.py`**: Sliding character window chunker (default 650 chars, 100 overlap) preserving paragraph and markdown header boundaries.
- **`vector_service.py`**: Dual-tier vectorizer:
  1. *Local Semantic Vectorizer*: Deterministic 256-dimensional subword character n-gram hashing with BM25 term weighting and cosine similarity. Runs in < 1ms with 0 network latency.
  2. *Cloud Embeddings*: Google Gemini (`text-embedding-004`) and OpenAI (`text-embedding-3-small`) with fallback resilience.
- **`rag_service.py`**: Queries SQLite chunks using cosine similarity thresholding (`0.15`), retrieves top $k$ chunks, and grounds prompts with page/document citations.

### 2.4 Test & Simulation Engine (`views/test_engine_view.py`, `views/mock_tests_view.py`)
- Supports authentic GATE question archetypes:
  - **MCQ** (Multiple Choice): Single correct option with $+1 / -0.33$ or $+2 / -0.66$ marking.
  - **MSQ** (Multiple Select): Multiple correct options, 0 partial marking, no negative marking.
  - **NAT** (Numerical Answer Type): Real-value range matching, no negative marking.
- Section-wise breakdown (Engineering Mathematics, General Aptitude, Core Mechanical).

### 2.5 Mistake Intelligence Engine (`views/mistake_view.py`, `mistake_engine.py`)
- Classifies student blunders into 11 cognitive and execution categories:
  `Concept Error`, `Formula Error`, `Calculation Error`, `Unit Error`, `Sign Error`, `Reading Error`, `Silly Mistake`, `Time Pressure`, `Wrong Assumption`, `Question Misinterpretation`, `Guessing Error`.
- Computes frequency distributions, 30-day mistake timelines, and triggers targeted corrective interventions.

---

## 3. Storage and State Architecture
- **Primary Database**: SQLite3 file (`gate_jarvis.db`) operating with WAL mode and `sqlite3.Row` dictionaries.
- **Document Store**: Stored in `data/documents/` as raw source files.
- **In-Memory State**: Streamlit `st.session_state` manages active test sets, test answers, stopwatch states, and chat histories across reruns.

---

## 4. API & LLM Provider Abstraction
- Unified dispatcher in `services/ai_service.py` selecting between:
  - `OpenAI` (`gpt-4o`, `gpt-4o-mini`) via `modules/ai_client.py`.
  - `Google Gemini` (`gemini-1.5-flash`, `gemini-1.5-pro`) via `google.generativeai`.
  - `Offline Demo Mode`: Deterministic local synthesizer synthesizing verified answers from retrieved notes without external API calls.
