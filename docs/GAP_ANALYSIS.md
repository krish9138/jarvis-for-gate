# GATE JARVIS 4.0 — Comprehensive Gap Analysis

This document identifies the technical, algorithmic, and UI gaps between the current prototype and the GATE JARVIS 4.0 vision.

---

## 1. Executive Summary of Gaps

While the current GATE JARVIS prototype boasts an impressive foundation (RAG pipeline, local vectorizer, test engine with negative marking, autonomous agent loop, and mistake intelligence), it currently acts primarily as an **information and tracking tool** rather than a **proactive, adaptive learning operating system**.

To reach JARVIS 4.0, the system must bridge three major technological frontiers:
1. **From Static Statuses to Cognitive State Tracking**: Transition from binary "completed/pending" tracking to multi-signal mastery models ($0-100\%$, retention half-life, mistake propensity, solving velocity).
2. **From Generic Document Storage to Deep Content Synthesis**: Upgrading note ingestion from pure chunk retrieval to structured artifacts (formula sheets, flashcards, automated DPPs, active recall cues).
3. **From Flat Module Lists to an Intelligent Hierarchical Graph**: Structuring subjects into `Topic -> Subtopic -> Concept -> Question` with prerequisite blocking and dual-track (College vs GATE) alignment.

---

## 2. Deep-Dive Gap Categorization

### Gap Category A: Mastery & Cognitive Engine (P0 - Critical)
- **Current State**: `learning_memory` table has `mastery_level` (REAL) and basic review intervals. `views/dashboard_view.py` computes a simple aggregate score.
- **Missing Capabilities**:
  - Multi-signal mastery calculation incorporating:
    - Concept comprehension (active recall score)
    - Numerical accuracy (NAT performance)
    - PYQ mastery percentage
    - Mistake recurrence penalty
    - Retention degradation over time ($R = e^{-t/S}$)
  - Formal 8-tier cognitive state progression:
    `NOT_STARTED` -> `LEARNING` -> `UNDERSTOOD` -> `PRACTICING` -> `GATE_READY` -> `PYQ_MASTERED` -> `REVISION_STABLE` -> `EXAM_READY`.
  - Prerequisite dependency alerts: If student initiates an advanced topic (e.g., *Entropy & Availability*) while prerequisite mastery (*First & Second Laws*) is $< 60\%$, proactively issue a warning and suggest a prerequisite refresher.

### Gap Category B: DPP & Practice Lab (P0 - Critical)
- **Current State**: DPP questions are scattered inside the generic Knowledge Base document tables or bundled inside Test Sets. There is no dedicated DPP practice station.
- **Missing Capabilities**:
  - Independent Sidebar Module: **📝 DPP & Practice Lab**.
  - Multi-source DPP Ingestion: Direct PDF, image/scanned, text, or AI-generated DPP creation.
  - Interactive Daily/Topic DPP solving interface with per-question timers, instant step-by-step checks, automatic mistake classification, and accuracy analytics.

### Gap Category C: Notes Intelligence Pipeline (P0 - Critical)
- **Current State**: Documents uploaded in Knowledge Base are chunked into 650-character chunks for semantic cosine search.
- **Missing Capabilities**:
  - Multi-artifact generation upon note upload:
    1. Executive 2-page high-yield summary
    2. Comprehensive formula & sign-convention sheet
    3. Active recall flashcards (spaced repetition queue)
    4. Diagnostic 10-question practice DPP
    5. Direct linkage to related historical GATE PYQs.

### Gap Category D: PYQ Intelligence Engine (P0 - Critical)
- **Current State**: `pyq_master` table contains basic question and solution text with year and topic.
- **Missing Capabilities**:
  - Rich question-level metadata: Year (1995–2025), Paper, Subtopic, Question Type (MCQ/MSQ/NAT), Marks (1 or 2), Difficulty (1–5), Tested Concept, Required Formula, Ideal Time, Student Attempt History, and Error Pattern.
  - Topic-wise and difficulty-wise PYQ drilling with instant analytics: *"You have solved 18 Thermodynamics PYQs, but your entropy-related PYQs have only 43% accuracy."*

### Gap Category E: Pedagogical Modes & Engineering Calculation Lab (P1)
- **Current State**: Problem solver (`views/problem_solver_view.py`) generates general markdown steps.
- **Missing Capabilities**:
  - Strict 10-step Mechanical Engineering calculation format:
    `Given -> Assumptions -> Concept -> Equation -> Substitution -> Units -> Calculation -> Final Answer -> Dimensional Check -> Sanity Check`.
  - **Teach-Back Mode**: Student explains concept in voice/text without notes; JARVIS grades completeness, terminology, and spots conceptual blind spots.
  - **Verify My Solution**: Upload or paste student derivation; JARVIS highlights the exact line of divergence (algebraic error, unit mismatch, or incorrect assumption).

---

## 3. High-Priority Actionable Gaps Summary

| Priority | Feature / Gap | Impact on GATE Aspirant | Engineering Effort |
|:---:|:---|:---|:---:|
| **P0** | **Mastery Engine & Prerequisite Graph** | Stops student from jumping ahead before mastering basics; provides true AIR < 100 readiness | Medium |
| **P0** | **Dedicated DPP & Practice Lab** | Provides daily question solving habit with timing and accuracy analytics | Medium |
| **P0** | **Notes Intelligence Multi-Artifact Generator** | Transforms passive lecture PDFs into active flashcards, formula sheets, and DPPs | Medium |
| **P0** | **PYQ Intelligence Engine** | Enables year-wise and topic-wise historical GATE drilling with error tagging | Medium |
| **P0** | **Dynamic Spaced Repetition Queue** | Eliminates forgetting of formulas and critical definitions before the exam | Low |
| **P1** | **Engineering Calculation Lab & Solution Verifier** | Eliminates calculation and unit errors in NAT questions | Medium |
| **P1** | **Teach-Back Learning Mode** | Enforces active learning over passive reading | Low |
| **P1** | **Hierarchical Sidebar Navigation Reorganization** | Organizes 16+ pages into clean, intuitive functional groups | Low |
