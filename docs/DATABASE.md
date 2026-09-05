# GATE JARVIS 4.0 — Database Schema & Data Dictionary

Database Engine: **SQLite 3**  
Database File: `gate_jarvis.db`  
Connection Factory: `database/connection.py` -> `get_db_connection()`  

---

## 1. Table Catalog & Schema Definitions

### 1.1 Core Learning & Taxonomy
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `subjects` | Canonical subject catalog (GATE ME + First Year) | `id`, `name`, `category`, `target_hours` |
| `study_sessions` | Logged study sessions with duration and notes | `id`, `subject_id`, `duration_minutes`, `notes`, `created_at` |
| `tasks` | Actionable study, revision, and test tasks | `id`, `title`, `subject_id`, `priority`, `is_completed`, `task_type`, `due_date` |

### 1.2 Knowledge Base & Semantic Search (RAG)
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `documents` | Metadata of ingested study files (PDF, DOCX, TXT) | `id`, `filename`, `original_name`, `file_type`, `subject_id`, `doc_type`, `page_count`, `chunk_count`, `file_path` |
| `document_chunks` | Indexed text segments with vector embeddings | `id`, `doc_id`, `chunk_index`, `page_number`, `section_title`, `content`, `embedding_json` |
| `chat_history` | Historical interactions with RAG citations | `id`, `role`, `content`, `sources_json`, `created_at` |

### 1.3 Interactive Engines & Tutoring
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `doubts` | Doubt engine tickets with AI resolutions & chunks | `id`, `subject_id`, `question`, `status`, `ai_answer`, `source_chunks_json`, `resolved_at` |
| `problem_sessions` | Step-by-step problem solver sessions | `id`, `subject_id`, `problem_statement`, `steps_json`, `final_answer`, `difficulty` |
| `test_sets` | Practice test series and mock paper containers | `id`, `title`, `subject_id`, `question_count`, `duration_minutes`, `description` |
| `test_questions` | Individual MCQ/MSQ/NAT items with marking rules | `id`, `test_set_id`, `question_text`, `question_type`, `options_json`, `correct_answer`, `marks`, `negative_marks`, `explanation` |
| `test_attempts` | Student test submissions and score reports | `id`, `test_set_id`, `test_title`, `score`, `max_score`, `answers_json`, `section_breakdown_json` |

### 1.4 Learning Memory & Spaced Repetition OS
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `learning_memory` | Granular concept mastery & review intervals | `concept_id`, `concept_name`, `subject_id`, `mastery_level`, `last_reviewed`, `next_review_date`, `review_interval_days`, `times_reviewed`, `times_wrong` |
| `concept_mastery_states` | Multi-signal 8-tier cognitive state tracking | `id`, `concept_id`, `cognitive_state`, `composite_score`, `accuracy`, `retention_pct`, `mistake_count`, `last_updated` |
| `concept_graph` | Prerequisite dependency links between concepts | `id`, `concept_id`, `prerequisite_id` |
| `revision_schedule` | Scheduled spaced recall dates and outcomes | `id`, `concept_id`, `scheduled_date`, `completed`, `result` |
| `flashcards` | Active recall cards generated from notes & formulas | `id`, `doc_id`, `subject_id`, `front_prompt`, `back_solution`, `card_type`, `interval_days`, `ease_factor`, `repetitions` |
| `spaced_repetition_cards`| Dynamic SM-2 interval tracking queue | `id`, `card_id`, `last_reviewed`, `next_due`, `review_count`, `streak` |
| `pyq_master` | Historical GATE exam questions catalog | `id`, `year`, `subject_id`, `topic`, `subtopic`, `question_type`, `marks`, `difficulty`, `concept_tested`, `formula_hint`, `question_text`, `solution_text`, `correct_answer`, `expected_time_sec`, `times_attempted`, `times_correct` |
| `mistake_log` | Systematic error tracker with 11 taxonomies | `id`, `question_text`, `user_answer`, `correct_answer`, `mistake_category`, `concept_id`, `subject_id`, `source`, `notes`, `created_at` *(Categories: Concept Error, Formula Error, Calculation Error, Unit Error, Sign Error, Reading Error, Silly Mistake, Time Pressure, Wrong Assumption, Question Misinterpretation, Guessing Error)* |

### 1.5 DPP & Practice Lab and Notes Intelligence
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `dpp_sets` | Daily Practice Problem sets container | `id`, `title`, `subject_id`, `topic`, `difficulty`, `source`, `total_questions`, `created_at` |
| `dpp_questions` | Individual DPP questions with hints & scoring | `id`, `dpp_set_id`, `question_text`, `question_type`, `options_json`, `correct_answer`, `marks`, `negative_marks`, `explanation`, `formula_hint`, `concept_tested` |
| `dpp_attempts` | Student DPP practice attempts with analytics | `id`, `dpp_set_id`, `score`, `max_score`, `accuracy`, `time_taken_sec`, `answers_json`, `mistakes_logged_count`, `attempted_at` |
| `notes_artifacts` | Synthesized outputs per uploaded document | `id`, `doc_id`, `summary_md`, `formula_sheet_md`, `flashcards_json`, `dpp_set_id`, `created_at` |

### 1.6 Study Plan Master Seeds (GATE ME MasterPlan 2026)
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `subject_weightage` | Historical marks weightage & NPTEL references | `id`, `subject`, `avg_marks`, `priority`, `phase`, `difficulty`, `nptel_course` |
| `plan_months` | 8-month phase roadmaps and checklists | `id`, `month_label`, `phase`, `study_hrs_per_week`, `target_hours`, `key_focus`, `checklist_json` |
| `skills_tracker` | Engineering & computational skills milestones | `id`, `skill_name`, `target_months`, `weekly_hours`, `progress_pct` |
| `study_resources` | Curated standard reference books and links | `id`, `name`, `resource_type`, `subjects`, `link` |
| `weekly_timetable` | Time-blocked weekly routine grid | `id`, `time_slot`, `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun` |
| `study_tactics` | Tactical GATE ME preparation strategies | `id`, `name`, `detail` |
| `subject_progress` | High-level subject milestone tracking | `id`, `subject`, `target_score`, `pyqs_done`, `formula_sheet_ready` |

### 1.6 Agent Execution & Property Case Studies
| Table Name | Description | Key Columns |
| :--- | :--- | :--- |
| `agent_activity_log` | Immutable audit log of autonomous actions | `id`, `timestamp`, `user_prompt`, `detected_language`, `intent`, `tool_name`, `result_status`, `approval_level`, `user_approved`, `duration_ms` |
| `agent_notes` | Autonomous and manual agent notebook entries | `id`, `title`, `content`, `subject_id`, `tags`, `importance_level` |
| `automation_rules` | Scheduled event-driven triggers | `id`, `name`, `trigger_event`, `action_type`, `is_enabled`, `approval_required` |
| `plot_case_studies` | Isolated engineering land & feasibility studies | `id`, `property_id`, `property_name`, `case_study_title`, `status`, `engineering_analysis_json`, `risk_assessment_json` |
| `property_details` | Detailed technical attributes per case study | `id`, `case_study_id`, `section_name`, `details_json` |

---

## 2. Database Indexes

To maintain sub-millisecond query latency across thousands of records, the following indexes are maintained:
- `idx_chunks_doc_id` on `document_chunks(doc_id)`
- `idx_docs_subject_id` on `documents(subject_id)`
- `idx_doubts_status` on `doubts(status)`
- `idx_test_q_set` on `test_questions(test_set_id)`
- `idx_memory_next_review` on `learning_memory(next_review_date)`
- `idx_graph_concept` on `concept_graph(concept_id)`
- `idx_mistake_created` on `mistake_log(created_at)`
- `idx_mistake_concept` on `mistake_log(concept_id)`
- `idx_pyq_subject_topic` on `pyq_master(subject_id, topic)`
- `idx_revision_date` on `revision_schedule(scheduled_date, completed)`
- `idx_agent_activity_time` on `agent_activity_log(timestamp)`
- `idx_plot_case_prop_id` on `plot_case_studies(property_id)`
