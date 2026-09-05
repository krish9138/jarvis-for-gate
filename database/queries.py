import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .connection import get_db_connection

# ==========================================
# SUBJECT QUERIES
# ==========================================

def get_all_subjects() -> List[Dict[str, Any]]:
    """Returns a list of all subjects with completed hours calculated."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            s.id, 
            s.name, 
            s.category, 
            s.target_hours, 
            COALESCE(SUM(ss.duration_minutes), 0) / 60.0 as completed_hours,
            COUNT(ss.id) as session_count
        FROM subjects s
        LEFT JOIN study_sessions ss ON s.id = ss.subject_id
        GROUP BY s.id
        ORDER BY s.category, s.name
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_subject(name: str, category: str = "GATE Mechanical", target_hours: float = 50.0) -> bool:
    """Adds a new subject."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO subjects (name, category, target_hours) VALUES (?, ?, ?)",
            (name.strip(), category.strip(), float(target_hours))
        )
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success


# ==========================================
# STUDY SESSIONS & STATS QUERIES
# ==========================================

def save_study_session(subject_id: Optional[int], duration_minutes: float, notes: str = "") -> bool:
    """Records a completed study session in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO study_sessions (subject_id, duration_minutes, notes) VALUES (?, ?, ?)",
            (subject_id, float(duration_minutes), notes.strip())
        )
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_recent_study_sessions(limit: int = 10) -> List[Dict[str, Any]]:
    """Gets recent study sessions joined with subject names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            ss.id,
            COALESCE(s.name, 'General Study') as subject_name,
            ss.duration_minutes,
            ss.notes,
            ss.created_at
        FROM study_sessions ss
        LEFT JOIN subjects s ON ss.subject_id = s.id
        ORDER BY ss.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_study_stats() -> Dict[str, Any]:
    """Calculates overall study statistics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total study hours
    cursor.execute("SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as total_hours FROM study_sessions")
    total_hours = round(cursor.fetchone()["total_hours"], 2)

    # Today's study hours
    cursor.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as today_hours 
        FROM study_sessions 
        WHERE DATE(created_at) = DATE('now', 'localtime')
    """)
    today_hours = round(cursor.fetchone()["today_hours"], 2)

    # Total sessions
    cursor.execute("SELECT COUNT(*) as session_count FROM study_sessions")
    session_count = cursor.fetchone()["session_count"]

    # Completed and Pending tasks
    cursor.execute("SELECT COUNT(*) as completed_tasks FROM tasks WHERE is_completed = 1")
    completed_tasks = cursor.fetchone()["completed_tasks"]

    cursor.execute("SELECT COUNT(*) as pending_tasks FROM tasks WHERE is_completed = 0")
    pending_tasks = cursor.fetchone()["pending_tasks"]

    # Knowledge Base Stats
    cursor.execute("SELECT COUNT(*) as doc_count FROM documents")
    doc_count = cursor.fetchone()["doc_count"]

    cursor.execute("SELECT COUNT(*) as chunk_count FROM document_chunks")
    chunk_count = cursor.fetchone()["chunk_count"]

    # Mock tests / Test attempts count
    cursor.execute("SELECT COUNT(*) as test_count FROM test_attempts")
    test_count = cursor.fetchone()["test_count"]

    # Doubts count
    cursor.execute("SELECT COUNT(*) as open_doubts FROM doubts WHERE status = 'open'")
    open_doubts = cursor.fetchone()["open_doubts"]

    # Solved problem sessions count
    cursor.execute("SELECT COUNT(*) as solved_problems FROM problem_sessions")
    solved_problems = cursor.fetchone()["solved_problems"]

    conn.close()
    return {
        "total_hours": total_hours,
        "today_hours": today_hours,
        "session_count": session_count,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "mock_count": test_count,
        "open_doubts": open_doubts,
        "solved_problems": solved_problems
    }


# ==========================================
# TASKS & PLANNER QUERIES
# ==========================================

def get_tasks(is_completed: Optional[int] = None, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves tasks with optional filters."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            t.id,
            t.title,
            t.subject_id,
            COALESCE(s.name, 'General') as subject_name,
            t.priority,
            t.task_type,
            t.is_completed,
            t.due_date,
            t.created_at
        FROM tasks t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if is_completed is not None:
        query += " AND t.is_completed = ?"
        params.append(is_completed)
    if task_type is not None:
        query += " AND t.task_type = ?"
        params.append(task_type)

    query += " ORDER BY t.is_completed ASC, CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, t.created_at DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def add_task(title: str, subject_id: Optional[int], priority: str = "Medium", task_type: str = "Study", due_date: str = "") -> bool:
    """Adds a new study task or revision item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tasks (title, subject_id, priority, task_type, due_date) VALUES (?, ?, ?, ?, ?)",
            (title.strip(), subject_id, priority, task_type, due_date)
        )
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def toggle_task_status(task_id: int, is_completed: int) -> bool:
    """Toggles task completion status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (is_completed, task_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def delete_task(task_id: int) -> bool:
    """Deletes a task from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success


# ==========================================
# CHAT HISTORY QUERIES
# ==========================================

def save_chat_message(role: str, content: str, sources: Optional[List[Dict[str, Any]]] = None):
    """Saves a conversation turn to SQLite along with optional RAG sources."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sources_json = json.dumps(sources or [])
    
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col["name"] for col in cursor.fetchall()]
    if "sources_json" not in columns:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN sources_json TEXT DEFAULT '[]'")
        conn.commit()

    cursor.execute(
        "INSERT INTO chat_history (role, content, sources_json) VALUES (?, ?, ?)", 
        (role, content, sources_json)
    )
    conn.commit()
    conn.close()

def get_chat_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Loads previous chat messages and their sources."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col["name"] for col in cursor.fetchall()]
    has_sources = "sources_json" in columns

    if has_sources:
        cursor.execute("SELECT role, content, sources_json FROM chat_history ORDER BY id ASC LIMIT ?", (limit,))
        rows = []
        for r in cursor.fetchall():
            try:
                sources = json.loads(r["sources_json"]) if r["sources_json"] else []
            except Exception:
                sources = []
            rows.append({"role": r["role"], "content": r["content"], "sources": sources})
    else:
        cursor.execute("SELECT role, content FROM chat_history ORDER BY id ASC LIMIT ?", (limit,))
        rows = [{"role": row["role"], "content": row["content"], "sources": []} for row in cursor.fetchall()]

    conn.close()
    return rows

def clear_chat_history():
    """Clears all chat history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()


# ==========================================
# KNOWLEDGE BASE & DOCUMENT QUERIES
# ==========================================

def save_document(
    filename: str,
    original_name: str,
    file_type: str,
    subject_id: Optional[int],
    doc_type: str,
    file_size_bytes: int,
    page_count: int,
    file_path: str
) -> int:
    """Inserts a new document record and returns the document ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (
            filename, original_name, file_type, subject_id, 
            doc_type, file_size_bytes, page_count, chunk_count, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (filename, original_name, file_type, subject_id, doc_type, file_size_bytes, page_count, file_path))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def update_document_chunk_count(doc_id: int, chunk_count: int):
    """Updates chunk count for a document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE documents SET chunk_count = ? WHERE id = ?", (chunk_count, doc_id))
    conn.commit()
    conn.close()

def get_all_documents() -> List[Dict[str, Any]]:
    """Retrieves all documents with subject information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            d.id,
            d.filename,
            d.original_name,
            d.file_type,
            d.subject_id,
            COALESCE(s.name, 'General / Multi-Subject') as subject_name,
            d.doc_type,
            d.file_size_bytes,
            d.page_count,
            d.chunk_count,
            d.file_path,
            d.uploaded_at
        FROM documents d
        LEFT JOIN subjects s ON d.subject_id = s.id
        ORDER BY d.uploaded_at DESC
    """
    cursor.execute(query)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single document by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            d.*,
            COALESCE(s.name, 'General') as subject_name
        FROM documents d
        LEFT JOIN subjects s ON d.subject_id = s.id
        WHERE d.id = ?
    """, (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_document(doc_id: int) -> bool:
    """Deletes a document and all its chunks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def save_document_chunks(chunks_data: List[Dict[str, Any]]) -> bool:
    """Bulk saves chunks to the document_chunks table."""
    if not chunks_data:
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany("""
            INSERT INTO document_chunks (
                doc_id, chunk_index, page_number, section_title, content, embedding_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (
                c["doc_id"],
                c["chunk_index"],
                c.get("page_number", 1),
                c.get("section_title", ""),
                c["content"],
                c.get("embedding_json", "[]")
            )
            for c in chunks_data
        ])
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def delete_chunks_by_doc_id(doc_id: int) -> bool:
    """Deletes all chunks belonging to a document (used before re-indexing)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))
        cursor.execute("UPDATE documents SET chunk_count = 0 WHERE id = ?", (doc_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_chunks_for_retrieval(subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves all indexed chunks with document and subject metadata for similarity matching."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            c.id as chunk_id,
            c.doc_id,
            c.chunk_index,
            c.page_number,
            c.section_title,
            c.content,
            c.embedding_json,
            d.original_name as doc_name,
            d.doc_type,
            d.subject_id,
            COALESCE(s.name, 'General') as subject_name
        FROM document_chunks c
        JOIN documents d ON c.doc_id = d.id
        LEFT JOIN subjects s ON d.subject_id = s.id
    """
    params = []
    if subject_id is not None:
        query += " WHERE d.subject_id = ?"
        params.append(subject_id)

    query += " ORDER BY c.doc_id ASC, c.chunk_index ASC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


# ==========================================
# 1. DOUBT ENGINE QUERIES
# ==========================================

def log_doubt(subject_id: Optional[int], question: str) -> int:
    """Logs a new quick doubt in open status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doubts (subject_id, question, status)
        VALUES (?, ?, 'open')
    """, (subject_id, question.strip()))
    doubt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doubt_id

def get_doubts(status: Optional[str] = None, subject_id: Optional[int] = None, search_query: str = "") -> List[Dict[str, Any]]:
    """Retrieves doubts filtered by status, subject, or text query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            d.id,
            d.subject_id,
            COALESCE(s.name, 'General Mechanical') as subject_name,
            d.question,
            d.status,
            d.ai_answer,
            d.source_chunks_json,
            d.created_at,
            d.resolved_at
        FROM doubts d
        LEFT JOIN subjects s ON d.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if status and status != "All":
        query += " AND d.status = ?"
        params.append(status.lower())
    if subject_id is not None:
        query += " AND d.subject_id = ?"
        params.append(subject_id)
    if search_query.strip():
        query += " AND (d.question LIKE ? OR d.ai_answer LIKE ?)"
        params.append(f"%{search_query.strip()}%")
        params.append(f"%{search_query.strip()}%")

    query += " ORDER BY CASE d.status WHEN 'open' THEN 1 WHEN 'answered' THEN 2 ELSE 3 END, d.created_at DESC"
    cursor.execute(query, params)
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["source_chunks"] = json.loads(item["source_chunks_json"]) if item["source_chunks_json"] else []
        except Exception:
            item["source_chunks"] = []
        rows.append(item)
    conn.close()
    return rows

def resolve_doubt(doubt_id: int, ai_answer: str, status: str = "resolved", sources: Optional[List[Dict[str, Any]]] = None) -> bool:
    """Updates a doubt with its AI response / resolution."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sources_json = json.dumps(sources or [])
    try:
        cursor.execute("""
            UPDATE doubts 
            SET ai_answer = ?, status = ?, source_chunks_json = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ai_answer.strip(), status.lower(), sources_json, doubt_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def delete_doubt(doubt_id: int) -> bool:
    """Deletes a doubt from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM doubts WHERE id = ?", (doubt_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success


# ==========================================
# 2. PROBLEM-SOLVING ENGINE QUERIES
# ==========================================

def save_problem_session(
    subject_id: Optional[int],
    problem_statement: str,
    steps: List[Dict[str, Any]],
    final_answer: str,
    difficulty: str = "Medium"
) -> int:
    """Saves a step-by-step solved problem into problem_sessions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    steps_json = json.dumps(steps)
    cursor.execute("""
        INSERT INTO problem_sessions (subject_id, problem_statement, steps_json, final_answer, difficulty)
        VALUES (?, ?, ?, ?, ?)
    """, (subject_id, problem_statement.strip(), steps_json, final_answer.strip(), difficulty))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_problem_sessions(
    subject_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    search_query: str = ""
) -> List[Dict[str, Any]]:
    """Retrieves all worked numerical problem sessions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            ps.id,
            ps.subject_id,
            COALESCE(s.name, 'General Core') as subject_name,
            ps.problem_statement,
            ps.steps_json,
            ps.final_answer,
            ps.difficulty,
            ps.created_at
        FROM problem_sessions ps
        LEFT JOIN subjects s ON ps.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if subject_id is not None:
        query += " AND ps.subject_id = ?"
        params.append(subject_id)
    if difficulty and difficulty != "All":
        query += " AND ps.difficulty = ?"
        params.append(difficulty)
    if search_query.strip():
        query += " AND (ps.problem_statement LIKE ? OR ps.final_answer LIKE ?)"
        params.append(f"%{search_query.strip()}%")
        params.append(f"%{search_query.strip()}%")

    query += " ORDER BY ps.created_at DESC"
    cursor.execute(query, params)
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["steps"] = json.loads(item["steps_json"]) if item["steps_json"] else []
        except Exception:
            item["steps"] = []
        rows.append(item)
    conn.close()
    return rows

def delete_problem_session(session_id: int) -> bool:
    """Deletes a problem session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM problem_sessions WHERE id = ?", (session_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success


# ==========================================
# 3. TEST ENGINE QUERIES
# ==========================================

def get_all_test_sets() -> List[Dict[str, Any]]:
    """Retrieves all test sets with question count and subject name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            ts.id,
            ts.title,
            ts.subject_id,
            COALESCE(s.name, 'Full Syllabus') as subject_name,
            ts.duration_minutes,
            ts.description,
            ts.created_at,
            COUNT(tq.id) as actual_question_count,
            COALESCE(SUM(tq.marks), 0) as total_marks
        FROM test_sets ts
        LEFT JOIN subjects s ON ts.subject_id = s.id
        LEFT JOIN test_questions tq ON ts.id = tq.test_set_id
        GROUP BY ts.id
        ORDER BY ts.created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_test_set_by_id(test_set_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single test set details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            ts.*,
            COALESCE(s.name, 'Full Syllabus') as subject_name
        FROM test_sets ts
        LEFT JOIN subjects s ON ts.subject_id = s.id
        WHERE ts.id = ?
    """, (test_set_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_test_set(title: str, subject_id: Optional[int], question_count: int = 10, duration_minutes: int = 30, description: str = "") -> int:
    """Creates a new test set."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO test_sets (title, subject_id, question_count, duration_minutes, description)
        VALUES (?, ?, ?, ?, ?)
    """, (title.strip(), subject_id, question_count, duration_minutes, description.strip()))
    test_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return test_id

def add_test_question(
    test_set_id: int,
    question_text: str,
    question_type: str = "MCQ",
    options: Optional[List[str]] = None,
    correct_answer: str = "",
    marks: float = 1.0,
    negative_marks: float = 0.33,
    explanation: str = ""
) -> int:
    """Adds a question to a test set."""
    conn = get_db_connection()
    cursor = conn.cursor()
    options_json = json.dumps(options or [])
    cursor.execute("""
        INSERT INTO test_questions (test_set_id, question_text, question_type, options_json, correct_answer, marks, negative_marks, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_set_id, question_text.strip(), question_type.upper(), options_json, correct_answer.strip(), float(marks), float(negative_marks), explanation.strip()))
    q_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return q_id

def get_test_questions(test_set_id: int) -> List[Dict[str, Any]]:
    """Retrieves all questions for a given test set."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM test_questions WHERE test_set_id = ? ORDER BY id ASC
    """, (test_set_id,))
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["options"] = json.loads(item["options_json"]) if item["options_json"] else []
        except Exception:
            item["options"] = []
        rows.append(item)
    conn.close()
    return rows

def save_test_attempt(
    test_set_id: Optional[int],
    test_title: str,
    score: float,
    max_score: float,
    answers: Dict[str, Any],
    section_breakdown: Optional[Dict[str, Any]] = None
) -> int:
    """Saves a user's completed test attempt and score."""
    conn = get_db_connection()
    cursor = conn.cursor()
    answers_json = json.dumps(answers)
    section_json = json.dumps(section_breakdown or {})
    cursor.execute("""
        INSERT INTO test_attempts (test_set_id, test_title, score, max_score, answers_json, section_breakdown_json, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (test_set_id, test_title.strip(), float(score), float(max_score), answers_json, section_json))
    attempt_id = cursor.lastrowid

    # Also log into legacy mock_tests table for backward compatibility
    cursor.execute("""
        INSERT INTO mock_tests (test_name, score, max_score, section_breakdown_json, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (test_title.strip(), float(score), float(max_score), section_json, f"Test Engine Attempt #{attempt_id}"))

    conn.commit()
    conn.close()
    return attempt_id

def get_test_attempts(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves past test attempts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM test_attempts ORDER BY completed_at DESC LIMIT ?
    """, (limit,))
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["answers"] = json.loads(item["answers_json"]) if item["answers_json"] else {}
        except Exception:
            item["answers"] = {}
        try:
            item["section_breakdown"] = json.loads(item["section_breakdown_json"]) if item["section_breakdown_json"] else {}
        except Exception:
            item["section_breakdown"] = {}
        rows.append(item)
    conn.close()
    return rows

def delete_test_set(test_set_id: int) -> bool:
    """Deletes a test set and all its questions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM test_questions WHERE test_set_id = ?", (test_set_id,))
        cursor.execute("DELETE FROM test_sets WHERE id = ?", (test_set_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_all_mock_tests() -> List[Dict[str, Any]]:
    """Retrieves all logged mock tests from mock_tests table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mock_tests ORDER BY taken_at DESC")
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["section_breakdown"] = json.loads(item["section_breakdown_json"]) if item.get("section_breakdown_json") else {}
        except Exception:
            item["section_breakdown"] = {}
        rows.append(item)
    conn.close()
    return rows

def save_mock_test(test_name: str, score: float, max_score: float = 100.0, section_breakdown: Optional[Dict[str, Any]] = None, notes: str = "") -> int:
    """Saves a mock test record into mock_tests table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    section_json = json.dumps(section_breakdown or {})
    cursor.execute("""
        INSERT INTO mock_tests (test_name, score, max_score, section_breakdown_json, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (test_name.strip(), float(score), float(max_score), section_json, notes.strip()))
    mock_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return mock_id

def delete_mock_test(test_id: int) -> bool:
    """Deletes a mock test from mock_tests table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM mock_tests WHERE id = ?", (test_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success



# ==========================================
# 4. STUDY PLAN DASHBOARD QUERIES
# ==========================================

def get_subject_weightage() -> List[Dict[str, Any]]:
    """Retrieves subject weightage and NPTEL course recommendations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subject_weightage ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_plan_months() -> List[Dict[str, Any]]:
    """Retrieves all 8 monthly plans and milestone checklists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plan_months ORDER BY id ASC")
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        try:
            item["primary_subjects"] = json.loads(item["primary_subjects"]) if item["primary_subjects"] else []
        except Exception:
            item["primary_subjects"] = [item["primary_subjects"]]
        try:
            item["secondary_subjects"] = json.loads(item["secondary_subjects"]) if item["secondary_subjects"] else []
        except Exception:
            item["secondary_subjects"] = [item["secondary_subjects"]]
        try:
            item["checklist"] = json.loads(item["checklist_json"]) if item["checklist_json"] else []
        except Exception:
            item["checklist"] = []
        rows.append(item)
    conn.close()
    return rows

def update_month_checklist(month_id: int, checklist: List[Dict[str, Any]]) -> bool:
    """Saves updated checklist item state for a specific month."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE plan_months SET checklist_json = ? WHERE id = ?", (json.dumps(checklist), month_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_skills_tracker() -> List[Dict[str, Any]]:
    """Retrieves 8 engineering skills tracker items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills_tracker ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_skill_progress(skill_id: int, progress_pct: float) -> bool:
    """Updates progress percentage of a skill."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE skills_tracker SET progress_pct = ? WHERE id = ?", (float(progress_pct), skill_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_study_resources(subject_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves study resources filterable by subject."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if subject_filter and subject_filter != "All":
        cursor.execute("SELECT * FROM study_resources WHERE subjects LIKE ? OR subjects = 'All Subjects' ORDER BY id ASC", (f"%{subject_filter}%",))
    else:
        cursor.execute("SELECT * FROM study_resources ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_weekly_timetable() -> List[Dict[str, Any]]:
    """Retrieves the weekly timetable slots."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM weekly_timetable ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_timetable_slot(slot_id: int, mon: str, tue: str, wed: str, thu: str, fri: str, sat: str, sun: str) -> bool:
    """Updates custom schedule for a timetable slot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE weekly_timetable
            SET mon = ?, tue = ?, wed = ?, thu = ?, fri = ?, sat = ?, sun = ?
            WHERE id = ?
        """, (mon, tue, wed, thu, fri, sat, sun, slot_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_study_tactics() -> List[Dict[str, Any]]:
    """Retrieves core study tactics from the master plan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_tactics ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_subject_progress() -> List[Dict[str, Any]]:
    """Retrieves subject progress tracker rows."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subject_progress ORDER BY id ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_subject_progress(progress_id: int, current_score: float, pyqs_done: int, formula_sheet_ready: int, weak_topics: str) -> bool:
    """Updates subject progress row."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE subject_progress
            SET current_score = ?, pyqs_done = ?, formula_sheet_ready = ?, weak_topics = ?
            WHERE id = ?
        """, (float(current_score), int(pyqs_done), int(formula_sheet_ready), weak_topics.strip(), progress_id))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def get_monthly_study_comparison() -> List[Dict[str, Any]]:
    """
    Compares planned target hours from plan_months with actual study_sessions logged per month.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    months = get_plan_months()
    
    results = []
    for m in months:
        label = m["month_label"] # e.g. "June 2025"
        # Extract year and month number if matching format
        try:
            dt = datetime.strptime(label, "%B %Y")
            year_month_str = dt.strftime("%Y-%m")
            cursor.execute("""
                SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as actual_hrs
                FROM study_sessions
                WHERE strftime('%Y-%m', created_at) = ?
            """, (year_month_str,))
            actual_row = cursor.fetchone()
            actual_hrs = round(actual_row["actual_hrs"] if actual_row else 0.0, 1)
        except Exception:
            actual_hrs = 0.0

        results.append({
            "month": label,
            "phase": m["phase"],
            "planned_hours": m["target_hours"],
            "actual_hours": actual_hrs,
            "completion_pct": round((actual_hrs / m["target_hours"]) * 100, 1) if m["target_hours"] > 0 else 0
        })

    conn.close()
    return results


# ====================================================================
# GATE JARVIS 4.0 P0 QUERY EXTENSIONS
# ====================================================================

# --- 1. DPP & Practice Lab ---
def log_mistake(question_text: str, user_answer: str, correct_answer: str, mistake_category: str, subject_id=None, source: str = "manual") -> int:
    """Inserts a new mistake record into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO mistake_log
           (question_text, user_answer, correct_answer, mistake_category, subject_id, source)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (question_text, user_answer, correct_answer, mistake_category, subject_id, source),
    )
    conn.commit()
    mistake_id = cursor.lastrowid
    conn.close()
    return mistake_id

def create_dpp_set(title: str, subject_id: Optional[int] = None, topic: str = "", difficulty: str = "Medium", source: str = "ai_generated", total_questions: int = 10) -> int:
    """Creates a new DPP set container and returns its id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dpp_sets (title, subject_id, topic, difficulty, source, total_questions)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, subject_id, topic, difficulty, source, total_questions))
    conn.commit()
    dpp_id = cursor.lastrowid
    conn.close()
    return dpp_id

def add_dpp_question(
    dpp_set_id: int,
    question_text: str,
    question_type: str = "MCQ",
    options_json: str = "[]",
    correct_answer: str = "A",
    marks: float = 1.0,
    negative_marks: float = 0.33,
    explanation: str = "",
    formula_hint: str = "",
    concept_tested: str = ""
) -> int:
    """Adds a question to a DPP set."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dpp_questions (
            dpp_set_id, question_text, question_type, options_json, correct_answer,
            marks, negative_marks, explanation, formula_hint, concept_tested
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dpp_set_id, question_text, question_type, options_json, correct_answer, marks, negative_marks, explanation, formula_hint, concept_tested))
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid

def get_all_dpp_sets(subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Fetches all DPP sets with question counts and subject names."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT d.*, COALESCE(s.name, 'General Mechanical') as subject_name,
               (SELECT COUNT(*) FROM dpp_questions q WHERE q.dpp_set_id = d.id) as actual_question_count
        FROM dpp_sets d
        LEFT JOIN subjects s ON d.subject_id = s.id
    """
    params = []
    if subject_id:
        query += " WHERE d.subject_id = ?"
        params.append(subject_id)
    query += " ORDER BY d.id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dpp_questions(dpp_set_id: int) -> List[Dict[str, Any]]:
    """Fetches all questions for a DPP set."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dpp_questions WHERE dpp_set_id = ? ORDER BY id ASC", (dpp_set_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_dpp_attempt(dpp_set_id: int, score: float, max_score: float, accuracy: float, time_taken_sec: int, answers_json: str, mistakes_logged: int = 0) -> int:
    """Records a completed DPP practice attempt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dpp_attempts (
            dpp_set_id, completed_at, score, max_score, accuracy, time_taken_sec, answers_json, mistakes_logged
        ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
    """, (dpp_set_id, score, max_score, accuracy, time_taken_sec, answers_json, mistakes_logged))
    conn.commit()
    att_id = cursor.lastrowid
    conn.close()
    return att_id

def get_dpp_attempts(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches recent DPP attempt reports."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, d.title as dpp_title, COALESCE(s.name, 'General') as subject_name
        FROM dpp_attempts a
        LEFT JOIN dpp_sets d ON a.dpp_set_id = d.id
        LEFT JOIN subjects s ON d.subject_id = s.id
        ORDER BY a.id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- 2. Notes Intelligence Multi-Artifacts ---
def save_notes_artifacts(doc_id: int, summary_md: str, formula_sheet_md: str, flashcards_json: str, key_concepts_json: str, dpp_set_id: Optional[int] = None) -> int:
    """Saves or updates generated notes intelligence artifacts for a document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes_artifacts (doc_id, summary_md, formula_sheet_md, flashcards_json, key_concepts_json, dpp_set_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(doc_id) DO UPDATE SET
            summary_md = excluded.summary_md,
            formula_sheet_md = excluded.formula_sheet_md,
            flashcards_json = excluded.flashcards_json,
            key_concepts_json = excluded.key_concepts_json,
            dpp_set_id = COALESCE(excluded.dpp_set_id, notes_artifacts.dpp_set_id),
            updated_at = CURRENT_TIMESTAMP
    """, (doc_id, summary_md, formula_sheet_md, flashcards_json, key_concepts_json, dpp_set_id))
    conn.commit()
    art_id = cursor.lastrowid
    conn.close()
    return art_id

def get_notes_artifacts(doc_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves generated notes artifacts for a given document."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes_artifacts WHERE doc_id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- 3. Multi-Signal Concept Mastery & Prerequisite Graph ---
def get_all_concept_mastery_states() -> List[Dict[str, Any]]:
    """Fetches all tracked concepts with their 8-stage mastery status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.concept_id, m.concept_name, m.subject_id, COALESCE(s.name, 'General') as subject_name,
               COALESCE(cms.state_enum, 'NOT_STARTED') as state_enum,
               COALESCE(cms.composite_mastery, m.mastery_level) as composite_mastery,
               COALESCE(cms.concept_score, 0.0) as concept_score,
               COALESCE(cms.numerical_score, 0.0) as numerical_score,
               COALESCE(cms.pyq_score, 0.0) as pyq_score,
               COALESCE(cms.dpp_score, 0.0) as dpp_score,
               COALESCE(cms.accuracy, 0.0) as accuracy,
               COALESCE(cms.retention_pct, 100.0) as retention_pct,
               COALESCE(cms.mistake_freq, m.times_wrong) as mistake_freq,
               m.last_reviewed, m.next_review_date
        FROM learning_memory m
        LEFT JOIN subjects s ON m.subject_id = s.id
        LEFT JOIN concept_mastery_states cms ON m.concept_id = cms.concept_id
        ORDER BY composite_mastery ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_concept_mastery_state(
    concept_id: int,
    state_enum: str,
    concept_score: float,
    numerical_score: float,
    pyq_score: float,
    dpp_score: float,
    accuracy: float,
    avg_solving_time: float,
    retention_pct: float,
    mistake_freq: int,
    composite_mastery: float
):
    """Upserts multi-signal mastery metrics for a concept."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO concept_mastery_states (
            concept_id, state_enum, concept_score, numerical_score, pyq_score,
            dpp_score, accuracy, avg_solving_time, retention_pct, mistake_freq,
            composite_mastery, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(concept_id) DO UPDATE SET
            state_enum = excluded.state_enum,
            concept_score = excluded.concept_score,
            numerical_score = excluded.numerical_score,
            pyq_score = excluded.pyq_score,
            dpp_score = excluded.dpp_score,
            accuracy = excluded.accuracy,
            avg_solving_time = excluded.avg_solving_time,
            retention_pct = excluded.retention_pct,
            mistake_freq = excluded.mistake_freq,
            composite_mastery = excluded.composite_mastery,
            last_updated = CURRENT_TIMESTAMP
    """, (concept_id, state_enum, concept_score, numerical_score, pyq_score, dpp_score, accuracy, avg_solving_time, retention_pct, mistake_freq, composite_mastery))
    # Also keep learning_memory.mastery_level synced
    cursor.execute("UPDATE learning_memory SET mastery_level = ? WHERE concept_id = ?", (composite_mastery, concept_id))
    conn.commit()
    conn.close()

def get_concept_prerequisites(concept_id: int) -> List[Dict[str, Any]]:
    """Returns all prerequisites for a given concept."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lm.concept_id, lm.concept_name, lm.mastery_level, COALESCE(cms.state_enum, 'NOT_STARTED') as state_enum
        FROM concept_graph cg
        JOIN learning_memory lm ON cg.prerequisite_id = lm.concept_id
        LEFT JOIN concept_mastery_states cms ON lm.concept_id = cms.concept_id
        WHERE cg.concept_id = ?
    """, (concept_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def check_prerequisites_mastered(concept_id: int, threshold: float = 60.0) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Checks if all prerequisites for concept_id meet the mastery threshold.
    Returns (all_met: bool, weak_prerequisites: list).
    """
    prereqs = get_concept_prerequisites(concept_id)
    weak = [p for p in prereqs if p["mastery_level"] < threshold]
    return (len(weak) == 0, weak)


# --- 4. Flashcards & Spaced Repetition Queue ---
def create_flashcard(
    front_prompt: str,
    back_solution: str,
    concept_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    topic: str = "",
    card_type: str = "concept"
) -> int:
    """Inserts a flashcard into the active recall queue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO flashcards (
            concept_id, subject_id, topic, front_prompt, back_solution, card_type, next_review_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (concept_id, subject_id, topic, front_prompt, back_solution, card_type, today_str))
    conn.commit()
    card_id = cursor.lastrowid
    conn.close()
    return card_id

def get_due_flashcards(target_date: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches flashcards due on or before target_date."""
    if not target_date:
        target_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.*, COALESCE(s.name, 'General') as subject_name
        FROM flashcards f
        LEFT JOIN subjects s ON f.subject_id = s.id
        WHERE f.next_review_date <= ? OR f.next_review_date IS NULL
        ORDER BY f.next_review_date ASC, f.lapses DESC
        LIMIT ?
    """, (target_date, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_flashcard_review(card_id: int, rating: str):
    """
    Updates flashcard review schedule according to modified SuperMemo (SM-2):
    rating: 'again' (fail), 'hard' (subtle fail/slow), 'good' (passed), 'easy' (mastered).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,))
    card = cursor.fetchone()
    if not card:
        conn.close()
        return

    interval = card["last_interval_days"] or 1
    ease = card["ease_factor"] or 2.5
    reviews = (card["review_count"] or 0) + 1
    lapses = card["lapses"] or 0

    if rating == "again":
        interval = 1
        lapses += 1
        ease = max(1.3, ease - 0.2)
    elif rating == "hard":
        interval = max(1, int(interval * 1.2))
        ease = max(1.3, ease - 0.15)
    elif rating == "good":
        if reviews == 1:
            interval = 1
        elif reviews == 2:
            interval = 3
        else:
            interval = max(int(interval * ease), interval + 1)
    elif rating == "easy":
        if reviews == 1:
            interval = 4
        else:
            interval = max(int(interval * ease * 1.3), interval + 3)
        ease = min(3.0, ease + 0.15)

    from datetime import timedelta
    next_date = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")

    cursor.execute("""
        UPDATE flashcards
        SET last_interval_days = ?, ease_factor = ?, review_count = ?, lapses = ?,
            last_reviewed = CURRENT_TIMESTAMP, next_review_date = ?
        WHERE id = ?
    """, (interval, round(ease, 2), reviews, lapses, next_date, card_id))
    conn.commit()
    conn.close()

def get_flashcard_stats() -> Dict[str, Any]:
    """Returns summary stats of flashcard learning queue."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) as total FROM flashcards")
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) as due FROM flashcards WHERE next_review_date <= ?", (today_str,))
    due = cursor.fetchone()["due"]
    cursor.execute("SELECT COUNT(*) as learned FROM flashcards WHERE review_count >= 3 AND last_interval_days >= 7")
    learned = cursor.fetchone()["learned"]
    conn.close()
    return {"total_cards": total, "due_today": due, "mastered_cards": learned}


# --- 5. PYQ Intelligence Hub Queries ---
def get_pyqs_filtered(
    subject_id: Optional[int] = None,
    topic: Optional[str] = None,
    year: Optional[int] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieves PYQs matching flexible criteria."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT p.*, COALESCE(s.name, 'General Mechanical') as subject_name
        FROM pyq_master p
        LEFT JOIN subjects s ON p.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if subject_id:
        query += " AND p.subject_id = ?"
        params.append(subject_id)
    if topic and topic != "(all)":
        query += " AND p.topic LIKE ?"
        params.append(f"%{topic}%")
    if year:
        query += " AND p.year = ?"
        params.append(year)
    if difficulty and difficulty != "(all)":
        query += " AND p.difficulty = ?"
        params.append(difficulty)
    if question_type and question_type != "(all)":
        query += " AND p.question_type = ?"
        params.append(question_type)

    query += " ORDER BY p.year DESC, p.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def record_pyq_attempt(pyq_id: int, is_correct: bool, student_answer: str = ""):
    """Updates PYQ attempt count and accuracy."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pyq_master
        SET times_attempted = times_attempted + 1,
            times_correct = times_correct + (CASE WHEN ? THEN 1 ELSE 0 END)
        WHERE id = ?
    """, (1 if is_correct else 0, pyq_id))
    conn.commit()
    conn.close()

def get_pyq_summary_stats() -> Dict[str, Any]:
    """Computes aggregate PYQ statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_pyqs,
            SUM(times_attempted) as total_attempts,
            SUM(times_correct) as total_correct,
            COUNT(DISTINCT year) as years_covered,
            COUNT(DISTINCT subject_id) as subjects_covered
        FROM pyq_master
    """)
    row = cursor.fetchone()
    conn.close()
    attempts = row["total_attempts"] or 0
    correct = row["total_correct"] or 0
    accuracy = round((correct / attempts) * 100, 1) if attempts > 0 else 0.0
    return {
        "total_pyqs": row["total_pyqs"] or 0,
        "total_attempts": attempts,
        "total_correct": correct,
        "accuracy_pct": accuracy,
        "years_covered": row["years_covered"] or 0,
        "subjects_covered": row["subjects_covered"] or 0
    }

