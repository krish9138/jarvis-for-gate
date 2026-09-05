import sqlite3
import json
from pathlib import Path
from typing import Optional
from config import DB_PATH, DEFAULT_SUBJECTS, BASE_DIR

def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Configures row_factory to sqlite3.Row for dictionary-like column access.
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes database tables if they do not exist, and ensures
    all GATE Mechanical & Study Plan seed data are synced in the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            target_hours REAL DEFAULT 50.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Study Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            duration_minutes REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 3. Tasks / Study Plan table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject_id INTEGER,
            priority TEXT DEFAULT 'Medium',
            is_completed INTEGER DEFAULT 0,
            task_type TEXT DEFAULT 'Study', -- 'Study', 'Revision', 'Test'
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 4. Chat history table for the AI assistant
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources_json TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Documents table (Knowledge Base)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,       -- 'pdf', 'docx', 'txt', 'md'
            subject_id INTEGER,
            doc_type TEXT DEFAULT 'Notes', -- 'Notes', 'PYQ', 'Book', 'DPP', 'Syllabus'
            file_size_bytes INTEGER DEFAULT 0,
            page_count INTEGER DEFAULT 1,
            chunk_count INTEGER DEFAULT 0,
            file_path TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 6. Document Chunks table (Vector Store)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            page_number INTEGER DEFAULT 1,
            section_title TEXT DEFAULT '',
            content TEXT NOT NULL,
            embedding_json TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # 7. Mock Tests Table (Legacy / Quick logger)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mock_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            score REAL NOT NULL,
            max_score REAL DEFAULT 100,
            section_breakdown_json TEXT DEFAULT '{}',
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)

    # 8. Doubt Engine Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doubts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER REFERENCES subjects(id),
            question TEXT NOT NULL,
            status TEXT DEFAULT 'open',          -- 'open' | 'answered' | 'resolved'
            ai_answer TEXT,
            source_chunks_json TEXT DEFAULT '[]', -- RAG sources used
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 9. Problem-Solving Engine Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problem_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER REFERENCES subjects(id),
            problem_statement TEXT NOT NULL,
            steps_json TEXT,                     -- ordered list of {step_number, step_title, explanation, formula_used}
            final_answer TEXT,
            difficulty TEXT DEFAULT 'Medium',    -- 'Easy' | 'Medium' | 'Hard'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 10. Test Engine Tables (Full Interactive Test Engine)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject_id INTEGER REFERENCES subjects(id),   -- NULL for full-syllabus mocks
            question_count INTEGER DEFAULT 10,
            duration_minutes INTEGER DEFAULT 30,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_set_id INTEGER NOT NULL REFERENCES test_sets(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'MCQ',                  -- 'MCQ' | 'MSQ' | 'NAT'
            options_json TEXT DEFAULT '[]',                   -- list of options for MCQ/MSQ
            correct_answer TEXT NOT NULL,                      -- string or json list for MSQ
            marks REAL DEFAULT 1.0,
            negative_marks REAL DEFAULT 0.33,
            explanation TEXT DEFAULT '',
            FOREIGN KEY (test_set_id) REFERENCES test_sets(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_set_id INTEGER REFERENCES test_sets(id) ON DELETE SET NULL,
            test_title TEXT DEFAULT 'Mock Test',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            score REAL DEFAULT 0.0,
            max_score REAL DEFAULT 100.0,
            answers_json TEXT DEFAULT '{}',                   -- {question_id: submitted_answer}
            section_breakdown_json TEXT DEFAULT '{}'          -- {maths: x, core: y, aptitude: z}
        )
    """)

    # 11. Study Plan Master Tables (From GATE_ME_MasterPlan_2026.pdf)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_weightage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL UNIQUE,
            avg_marks TEXT,
            priority TEXT,
            phase TEXT,
            difficulty TEXT,
            nptel_course TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plan_months (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month_label TEXT NOT NULL UNIQUE,           -- e.g. 'June 2025'
            phase TEXT,                                 -- Foundation | Application | Revision | Simulation
            weekday_hrs REAL,
            weekend_hrs REAL,
            study_hrs_per_week REAL,
            total_hrs_per_month REAL,
            target_hours REAL,
            key_focus TEXT,
            primary_subjects TEXT,                      -- JSON list or string
            secondary_subjects TEXT,                    -- JSON list or string
            checklist_json TEXT                         -- JSON list of {item: str, done: bool}
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL UNIQUE,
            target_months TEXT,
            weekly_hours REAL,
            what_to_learn TEXT,
            progress_pct REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            resource_type TEXT,
            subjects TEXT,
            link TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_slot TEXT NOT NULL,
            mon TEXT,
            tue TEXT,
            wed TEXT,
            thu TEXT,
            fri TEXT,
            sat TEXT,
            sun TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_tactics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            detail TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL UNIQUE,
            target_months TEXT,
            current_score REAL DEFAULT 0,
            target_score REAL DEFAULT 8,
            pyqs_done INTEGER DEFAULT 0,
            formula_sheet_ready INTEGER DEFAULT 0,
            weak_topics TEXT DEFAULT ''
        )
    """)

    # 12. Learning Memory OS Tables (Stage 3+)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_memory (
            concept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_name TEXT NOT NULL UNIQUE,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            mastery_level REAL DEFAULT 0,          -- 0-100
            last_reviewed TIMESTAMP,
            next_review_date DATE,
            review_interval_days INTEGER DEFAULT 1, -- current spaced-rep interval
            times_reviewed INTEGER DEFAULT 0,
            times_wrong INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concept_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL REFERENCES learning_memory(concept_id) ON DELETE CASCADE,
            prerequisite_id INTEGER NOT NULL REFERENCES learning_memory(concept_id) ON DELETE CASCADE,
            UNIQUE(concept_id, prerequisite_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mistake_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT,
            user_answer TEXT,
            correct_answer TEXT,
            mistake_category TEXT NOT NULL,   -- Concept | Formula | Calculation | Unit | Reading | Time-management | Guessing
            concept_id INTEGER REFERENCES learning_memory(concept_id) ON DELETE SET NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            source TEXT DEFAULT 'manual',     -- 'test_engine' | 'problem_solver' | 'manual'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pyq_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            topic TEXT,
            concept_id INTEGER REFERENCES learning_memory(concept_id) ON DELETE SET NULL,
            difficulty TEXT DEFAULT 'Medium', -- Easy | Medium | Hard
            question_text TEXT NOT NULL,
            solution_text TEXT,
            times_attempted INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL REFERENCES learning_memory(concept_id) ON DELETE CASCADE,
            scheduled_date DATE NOT NULL,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            result TEXT                       -- 'remembered' | 'forgot' | 'partial'
        )
    """)

    # 13. Agent OS & Automation Tables (Stage 4+)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_prompt TEXT,
            detected_language TEXT DEFAULT 'en',   -- 'en' | 'hi' | 'mr'
            intent TEXT NOT NULL,
            tool_name TEXT,
            input_summary TEXT,
            result_status TEXT DEFAULT 'SUCCESS',  -- 'SUCCESS' | 'FAILED' | 'PENDING_APPROVAL'
            result_summary TEXT,
            approval_level INTEGER DEFAULT 0,      -- 0=Read, 1=LowRisk, 2=ApprovalRequired
            user_approved INTEGER DEFAULT 1,       -- 1=Approved/Auto, 0=Rejected
            duration_ms REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            concept_name TEXT,
            tags TEXT DEFAULT '[]',                -- JSON array of tags
            importance_level TEXT DEFAULT 'Medium',-- 'Low' | 'Medium' | 'High' | 'Critical'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automation_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            trigger_event TEXT NOT NULL,           -- 'DAILY_MORNING' | 'REVISION_DUE' | 'TOPIC_WEAK' | 'WEEKLY_REVIEW'
            conditions_json TEXT DEFAULT '{}',
            action_type TEXT NOT NULL,             -- 'GENERATE_PLAN' | 'CREATE_TASK' | 'SCHEDULE_REVISION' | 'GENERATE_REPORT'
            is_enabled INTEGER DEFAULT 1,
            approval_required INTEGER DEFAULT 0,
            last_run TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engineering_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            problem_statement TEXT,
            objective TEXT,
            domain TEXT DEFAULT 'Mechanical CAD/Design',
            status TEXT DEFAULT 'Research',        -- 'Idea' | 'Research' | 'Design' | 'Development' | 'Testing' | 'Completed'
            technologies TEXT DEFAULT '',
            milestones_json TEXT DEFAULT '[]',
            documentation_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 14. Isolated Engineering Property & Plot Case Studies
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plot_case_studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT UNIQUE NOT NULL,
            property_name TEXT NOT NULL,
            property_type TEXT DEFAULT 'Industrial / Commercial Plot',
            location_summary TEXT,
            total_area_sqft REAL DEFAULT 0,
            case_study_title TEXT NOT NULL,
            status TEXT DEFAULT 'Draft',           -- 'Draft' | 'Completed' | 'Archived'
            executive_summary TEXT,
            engineering_analysis_json TEXT DEFAULT '{}',
            risk_assessment_json TEXT DEFAULT '{}',
            financial_summary_json TEXT DEFAULT '{}',
            recommendations TEXT,
            full_report_markdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS property_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_study_id INTEGER REFERENCES plot_case_studies(id) ON DELETE CASCADE,
            section_name TEXT NOT NULL,            -- e.g. 'BASIC', 'LOCATION', 'DIMENSIONS', 'LEGAL', 'INFRASTRUCTURE'
            details_json TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 15. GATE JARVIS 4.0 — DPP & Practice Lab Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dpp_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            topic TEXT DEFAULT '',
            difficulty TEXT DEFAULT 'Medium',
            source TEXT DEFAULT 'ai_generated', -- 'upload' | 'ai_generated' | 'notes_pipeline' | 'manual'
            total_questions INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dpp_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dpp_set_id INTEGER NOT NULL REFERENCES dpp_sets(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'MCQ',   -- 'MCQ' | 'MSQ' | 'NAT'
            options_json TEXT DEFAULT '[]',
            correct_answer TEXT NOT NULL,
            marks REAL DEFAULT 1.0,
            negative_marks REAL DEFAULT 0.33,
            explanation TEXT DEFAULT '',
            formula_hint TEXT DEFAULT '',
            concept_tested TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dpp_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dpp_set_id INTEGER REFERENCES dpp_sets(id) ON DELETE SET NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            score REAL DEFAULT 0.0,
            max_score REAL DEFAULT 10.0,
            accuracy REAL DEFAULT 0.0,
            time_taken_sec INTEGER DEFAULT 0,
            answers_json TEXT DEFAULT '{}',
            mistakes_logged INTEGER DEFAULT 0
        )
    """)

    # 16. Notes Intelligence Multi-Artifacts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
            summary_md TEXT DEFAULT '',
            formula_sheet_md TEXT DEFAULT '',
            flashcards_json TEXT DEFAULT '[]',
            key_concepts_json TEXT DEFAULT '[]',
            dpp_set_id INTEGER REFERENCES dpp_sets(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 17. Multi-Signal Concept Mastery States (8 Cognitive Stages)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concept_mastery_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER NOT NULL UNIQUE REFERENCES learning_memory(concept_id) ON DELETE CASCADE,
            state_enum TEXT DEFAULT 'NOT_STARTED', -- NOT_STARTED | LEARNING | UNDERSTOOD | PRACTICING | GATE_READY | PYQ_MASTERED | REVISION_STABLE | EXAM_READY
            concept_score REAL DEFAULT 0.0,
            numerical_score REAL DEFAULT 0.0,
            pyq_score REAL DEFAULT 0.0,
            dpp_score REAL DEFAULT 0.0,
            accuracy REAL DEFAULT 0.0,
            avg_solving_time REAL DEFAULT 0.0,
            retention_pct REAL DEFAULT 100.0,
            mistake_freq INTEGER DEFAULT 0,
            composite_mastery REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 18. Spaced Repetition Flashcards & Active Recall Queue
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concept_id INTEGER REFERENCES learning_memory(concept_id) ON DELETE SET NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            topic TEXT DEFAULT '',
            front_prompt TEXT NOT NULL,
            back_solution TEXT NOT NULL,
            card_type TEXT DEFAULT 'concept',
            last_interval_days INTEGER DEFAULT 1,
            ease_factor REAL DEFAULT 2.5,
            review_count INTEGER DEFAULT 0,
            lapses INTEGER DEFAULT 0,
            last_reviewed TIMESTAMP,
            next_review_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Safe column additions for pyq_master
    for col_def in [
        ("marks", "REAL DEFAULT 1.0"),
        ("question_type", "TEXT DEFAULT 'MCQ'"),
        ("expected_time_sec", "INTEGER DEFAULT 180"),
        ("tested_concept", "TEXT DEFAULT ''"),
        ("required_formula", "TEXT DEFAULT ''"),
        ("correct_answer", "TEXT DEFAULT 'A'"),
        ("options_json", "TEXT DEFAULT '[]'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE pyq_master ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(doc_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_subject_id ON documents(subject_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doubts_status ON doubts(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_test_q_set ON test_questions(test_set_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_next_review ON learning_memory(next_review_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_graph_concept ON concept_graph(concept_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mistake_created ON mistake_log(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mistake_concept ON mistake_log(concept_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pyq_subject_topic ON pyq_master(subject_id, topic)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_revision_date ON revision_schedule(scheduled_date, completed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_activity_time ON agent_activity_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_plot_case_prop_id ON plot_case_studies(property_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dpp_set_subj ON dpp_sets(subject_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dpp_q_set ON dpp_questions(dpp_set_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_flashcards_next_rev ON flashcards(next_review_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mastery_state_cid ON concept_mastery_states(concept_id)")

    conn.commit()

    # Sync and insert all default GATE Mechanical & First Year subjects
    for subj in DEFAULT_SUBJECTS:
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (subj["name"],))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO subjects (name, category, target_hours) VALUES (?, ?, ?)",
                (subj["name"], subj["category"], subj["target_hours"])
            )
        else:
            cursor.execute(
                "UPDATE subjects SET category = ? WHERE name = ?",
                (subj["category"], subj["name"])
            )

    conn.commit()

    # Seed study plan data if not populated
    _seed_master_plan_data(conn)
    _seed_initial_tests_and_problems(conn)

    conn.close()


def _seed_master_plan_data(conn: sqlite3.Connection):
    """Loads and seeds study_plan_seed_data.json into sqlite database."""
    seed_file = BASE_DIR / "data" / "study_plan_seed_data.json"
    if not seed_file.exists():
        seed_file = BASE_DIR / "study_plan_seed_data.json"
    
    if not seed_file.exists():
        return

    try:
        with open(seed_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        cursor = conn.cursor()

        # 1. Subject weightage
        for item in data.get("subject_weightage", []):
            cursor.execute("""
                INSERT OR IGNORE INTO subject_weightage (subject, avg_marks, priority, phase, difficulty, nptel_course)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item["subject"], item["avg_marks"], item["priority"], item["phase"], item["difficulty"], item["nptel_course"]))

        # 2. Monthly Planner & Roadmap Milestones combined into plan_months
        monthly_map = {m["month"]: m for m in data.get("monthly_planner", [])}
        roadmap_map = {r["month"]: r for r in data.get("roadmap_milestones", [])}

        all_months = list(monthly_map.keys())
        for m_name in all_months:
            m_info = monthly_map.get(m_name, {})
            r_info = roadmap_map.get(m_name, {})
            
            target_hrs = m_info.get("total_hrs_per_month") or 180.0
            raw_checklist = r_info.get("checklist", [])
            # Convert list of string checklist items to list of {item, done} objects if needed
            checklist_items = [{"item": c, "done": False} for c in raw_checklist]

            cursor.execute("SELECT id FROM plan_months WHERE month_label = ?", (m_name,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO plan_months (
                        month_label, phase, weekday_hrs, weekend_hrs, study_hrs_per_week,
                        total_hrs_per_month, target_hours, key_focus, primary_subjects,
                        secondary_subjects, checklist_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m_name,
                    m_info.get("phase", "Foundation"),
                    m_info.get("weekday_hrs_per_day", 3),
                    m_info.get("weekend_hrs_per_day", 7),
                    m_info.get("study_hrs_per_week", 29),
                    m_info.get("total_hrs_per_month", target_hrs),
                    target_hrs,
                    m_info.get("key_focus", ""),
                    json.dumps(r_info.get("primary_subjects", [])),
                    json.dumps(r_info.get("secondary_subjects", [])),
                    json.dumps(checklist_items)
                ))

        # 3. Skills Tracker
        for sk in data.get("skills_tracker", []):
            cursor.execute("""
                INSERT OR IGNORE INTO skills_tracker (skill_name, target_months, weekly_hours, what_to_learn, progress_pct)
                VALUES (?, ?, ?, ?, ?)
            """, (sk["skill"], sk["months"], sk["weekly_hours"], sk["what_to_learn"], sk.get("progress_pct", 0)))

        # 4. Resources
        for res in data.get("resources", []):
            cursor.execute("""
                INSERT OR IGNORE INTO study_resources (name, resource_type, subjects, link)
                VALUES (?, ?, ?, ?)
            """, (res["name"], res["type"], res["subjects"], res["link"]))

        # 5. Weekly Timetable
        cursor.execute("SELECT COUNT(*) as count FROM weekly_timetable")
        if cursor.fetchone()["count"] == 0:
            slots = data.get("sample_week_timetable", {}).get("slots", [])
            for slot in slots:
                cursor.execute("""
                    INSERT INTO weekly_timetable (time_slot, mon, tue, wed, thu, fri, sat, sun)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    slot.get("time", ""),
                    slot.get("MON", ""),
                    slot.get("TUE", ""),
                    slot.get("WED", ""),
                    slot.get("THU", ""),
                    slot.get("FRI", ""),
                    slot.get("SAT", ""),
                    slot.get("SUN", "")
                ))

        # 6. Study Tactics
        for tac in data.get("study_tactics", []):
            cursor.execute("""
                INSERT OR IGNORE INTO study_tactics (name, detail)
                VALUES (?, ?)
            """, (tac["name"], tac["detail"]))

        # 7. Subject Progress Tracker
        for row in data.get("subject_progress_tracker_template", {}).get("rows_seed", []):
            cursor.execute("""
                INSERT OR IGNORE INTO subject_progress (subject, target_months, current_score, target_score, pyqs_done, formula_sheet_ready, weak_topics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (row["subject"], row.get("target_months", "All"), 0, row.get("target_score", 8), 0, 0, ""))

        conn.commit()
    except Exception as e:
        print(f"Error seeding study plan data: {e}")


def _seed_initial_tests_and_problems(conn: sqlite3.Connection):
    """Seeds rich starter GATE tests and problem-solving examples."""
    cursor = conn.cursor()

    # 1. Check if test_sets has items
    cursor.execute("SELECT COUNT(*) as count FROM test_sets")
    if cursor.fetchone()["count"] == 0:
        # Create Test 1: Full High-Yield GATE ME Diagnostic Drill
        cursor.execute("""
            INSERT INTO test_sets (title, question_count, duration_minutes, description)
            VALUES (?, ?, ?, ?)
        """, (
            "🎯 GATE ME High-Yield Rapid Simulation (10 Questions - 15 Marks)",
            10,
            25,
            "Speed & accuracy diagnostic covering Maths, SOM, Thermo, Fluids, Theory of Machines & Aptitude. Follows strict GATE marking (+1/-0.33, +2/-0.66, NAT/MSQ no negative)."
        ))
        test_set_1_id = cursor.lastrowid

        questions_set_1 = [
            (
                test_set_1_id,
                "For a 2x2 real symmetric matrix A with trace 8 and determinant 12, what are the eigenvalues of A?",
                "MCQ",
                json.dumps(["2 and 6", "3 and 4", "1 and 12", "4 and 4"]),
                "2 and 6",
                1.0,
                0.33,
                "Sum of eigenvalues = trace = 8. Product of eigenvalues = determinant = 12. Roots of λ² - 8λ + 12 = 0 are (λ - 2)(λ - 6) = 0 => λ = 2, 6."
            ),
            (
                test_set_1_id,
                "A cantilever beam of length L is subjected to a concentrated point load W at its free end. What is the maximum deflection at the free end? (EI is flexural rigidity)",
                "MCQ",
                json.dumps(["WL³ / (3EI)", "WL³ / (8EI)", "WL⁴ / (8EI)", "WL³ / (48EI)"]),
                "WL³ / (3EI)",
                1.0,
                0.33,
                "Standard cantilever deflection under end point load is δ = WL³ / (3EI). For UDL it is wL⁴ / (8EI)."
            ),
            (
                test_set_1_id,
                "In an ideal Otto cycle with compression ratio r = 8 and specific heat ratio γ = 1.4, calculate the air standard thermal efficiency in percentage (round off to 1 decimal place).",
                "NAT",
                "[]",
                "56.5",
                2.0,
                0.0,
                "η_Otto = 1 - 1/(r^(γ-1)) = 1 - 1/(8^(0.4)) = 1 - 1/2.2974 = 1 - 0.4352 = 0.5647 = 56.5%."
            ),
            (
                test_set_1_id,
                "Which of the following flow characteristics are REQUIRED for Bernoulli's equation $P/(\\rho g) + V^2/(2g) + z = \\text{constant}$ to hold valid? (Select ALL correct statements)",
                "MSQ",
                json.dumps([
                    "Flow is steady",
                    "Flow is incompressible",
                    "Flow is inviscid (frictionless)",
                    "Flow is along a streamline"
                ]),
                json.dumps([
                    "Flow is steady",
                    "Flow is incompressible",
                    "Flow is inviscid (frictionless)",
                    "Flow is along a streamline"
                ]),
                2.0,
                0.0,
                "All 4 assumptions (steady, incompressible, inviscid, streamline) are fundamental prerequisites for Euler's equation integration to yield Bernoulli's equation."
            ),
            (
                test_set_1_id,
                "A thin cylinder of internal diameter 1 m and wall thickness 10 mm is subjected to internal fluid pressure 2 MPa. What is the hoop (circumferential) stress induced in MPa?",
                "NAT",
                "[]",
                "100",
                2.0,
                0.0,
                "Hoop stress σ_h = P*d / (2*t) = (2 MPa * 1000 mm) / (2 * 10 mm) = 100 MPa."
            ),
            (
                test_set_1_id,
                "For a slider-crank mechanism with crank radius r = 100 mm rotating at constant angular velocity ω = 20 rad/s, what is the maximum velocity of the slider when the connecting rod is very long? (in m/s)",
                "NAT",
                "[]",
                "2.0",
                1.0,
                0.0,
                "When connecting rod is very long (n -> ∞), slider velocity v = r*ω*sin(θ). Maximum occurs at θ = 90° => v_max = r*ω = 0.1 m * 20 rad/s = 2.0 m/s."
            ),
            (
                test_set_1_id,
                "In orthogonal cutting with rake angle α = 10° and shear angle β = 30°, what is the chip thickness ratio r?",
                "MCQ",
                json.dumps(["0.563", "0.642", "0.785", "0.450"]),
                "0.563",
                1.0,
                0.33,
                "Chip thickness ratio r = sin(β) / cos(β - α) = sin(30°) / cos(30° - 10°) = 0.5 / cos(20°) = 0.5 / 0.9397 = 0.532 or approx 0.56."
            ),
            (
                test_set_1_id,
                "A Carnot heat engine operates between temperatures of 1000 K and 300 K. What is its theoretical maximum thermal efficiency in percentage?",
                "NAT",
                "[]",
                "70",
                1.0,
                0.0,
                "η_Carnot = 1 - T_L / T_H = 1 - 300/1000 = 0.70 = 70%."
            ),
            (
                test_set_1_id,
                "What is the rank of the 3x3 identity matrix $I_3$?",
                "NAT",
                "[]",
                "3",
                1.0,
                0.0,
                "The identity matrix $I_3$ has 3 linearly independent row vectors, hence its rank is 3."
            ),
            (
                test_set_1_id,
                "If 'A' is 20% more than 'B', then by what percentage is 'B' less than 'A'?",
                "MCQ",
                json.dumps(["16.67%", "20%", "25%", "15%"]),
                "16.67%",
                1.0,
                0.33,
                "Let B = 100. Then A = 120. B is less than A by (20 / 120) * 100% = 16.67%."
            )
        ]

        for q in questions_set_1:
            cursor.execute("""
                INSERT INTO test_questions (test_set_id, question_text, question_type, options_json, correct_answer, marks, negative_marks, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, q)

    # 2. Check if problem_sessions has starter examples
    cursor.execute("SELECT COUNT(*) as count FROM problem_sessions")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("SELECT id FROM subjects WHERE name = 'Strength of Materials'")
        som_row = cursor.fetchone()
        som_id = som_row["id"] if som_row else None

        steps_sample = [
            {
                "step_number": 1,
                "step_title": "Identify Given Parameters & Convert to Consistent SI Units",
                "formula_used": "Unit conversion: $d = 20\\text{ mm} = 0.02\\text{ m}$, $L = 2\\text{ m}$, $P = 50\\text{ kN} = 50 \\times 10^3\\text{ N}$, $E = 200\\text{ GPa} = 200 \\times 10^9\\text{ N/m}^2$",
                "explanation": "A solid circular steel bar has diameter $d = 20\\text{ mm}$, length $L = 2\\text{ m}$, subjected to an axial tensile load $P = 50\\text{ kN}$. Young's modulus $E = 200\\text{ GPa}$."
            },
            {
                "step_number": 2,
                "step_title": "Calculate Cross-Sectional Area (A)",
                "formula_used": "$A = \\frac{\\pi d^2}{4}$",
                "explanation": "$A = \\frac{\\pi \\times (0.02)^2}{4} = \\frac{\\pi \\times 0.0004}{4} = 3.14159 \\times 10^{-4}\\text{ m}^2 = 314.16\\text{ mm}^2$."
            },
            {
                "step_number": 3,
                "step_title": "Calculate Axial Stress (σ)",
                "formula_used": "$\\sigma = \\frac{P}{A}$",
                "explanation": "$\\sigma = \\frac{50 \\times 10^3\\text{ N}}{314.16 \\times 10^{-6}\\text{ m}^2} = 159.155 \\times 10^6\\text{ N/m}^2 = 159.15\\text{ MPa}$."
            },
            {
                "step_number": 4,
                "step_title": "Calculate Total Elongation (ΔL)",
                "formula_used": "$\\Delta L = \\frac{P L}{A E} = \\frac{\\sigma L}{E}$",
                "explanation": "$\\Delta L = \\frac{159.155 \\times 10^6 \\times 2}{200 \\times 10^9} = 1.59155 \\times 10^{-3}\\text{ m} = 1.59\\text{ mm}$."
            },
            {
                "step_number": 5,
                "step_title": "Verification & Final NAT Result",
                "formula_used": "GATE NAT Format check",
                "explanation": "Result is $1.59\\text{ mm}$. Tensile elongation is positive."
            }
        ]

        cursor.execute("""
            INSERT INTO problem_sessions (subject_id, problem_statement, steps_json, final_answer, difficulty)
            VALUES (?, ?, ?, ?, ?)
        """, (
            som_id,
            "A solid cylindrical steel bar of diameter 20 mm and length 2 m is subjected to an axial tensile pull of 50 kN. If Young's modulus E = 200 GPa, determine the total axial elongation in mm.",
            json.dumps(steps_sample),
            "1.59 mm",
            "Easy"
        ))

    # 3. Check doubts table starter example
    cursor.execute("SELECT COUNT(*) as count FROM doubts")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("SELECT id FROM subjects WHERE name = 'Fluid Mechanics'")
        fm_row = cursor.fetchone()
        fm_id = fm_row["id"] if fm_row else None

        cursor.execute("""
            INSERT INTO doubts (subject_id, question, status, ai_answer)
            VALUES (?, ?, ?, ?)
        """, (
            fm_id,
            "Why is the friction factor 'f' for laminar pipe flow 64/Re in Darcy-Weisbach equation, but 16/Re in Fanning friction factor?",
            "resolved",
            "**Key Distinction:**\n- **Darcy-Weisbach Friction Factor ($f_D$)**: Defined by $h_f = \\frac{f_D L V^2}{2 g D}$. For laminar flow, Hagen-Poiseuille equation yields $\\Delta P = \\frac{32 \\mu L V}{D^2} = \\rho g h_f$. Equating the two gives $f_D = \\frac{64}{Re}$.\n- **Fanning Friction Factor ($f_F$)**: Defined in chemical engineering based on wall shear stress $\\tau_w = \\frac{1}{2} f_F \\rho V^2$. Here $f_D = 4 f_F$, so $f_F = \\frac{16}{Re}$.\n- **GATE Rule**: Unless explicitly specified as Fanning, standard Mechanical GATE always uses Darcy-Weisbach ($f = 64/Re$)."
        ))

    conn.commit()
