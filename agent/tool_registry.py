"""
agent/tool_registry.py
-----------------------
Standardized Tool Interface & Permission Gate for GATE JARVIS.
Enforces Human-in-the-Loop (HITL) safety and parameter validation.
"""

from enum import IntEnum
from typing import Dict, Any, Callable, List, Optional
import json
import sqlite3
import shutil
from datetime import datetime
from database.connection import get_db_connection
from database.queries import (
    get_study_stats,
    get_recent_study_sessions,
    save_study_session,
    add_task,
    get_tasks
)



class ToolPermissionLevel(IntEnum):
    LEVEL_0_READ = 0           # Auto-execute (safe queries)
    LEVEL_1_LOW_RISK_WRITE = 1 # Auto-execute when enabled (notes, tasks, study logs)
    LEVEL_2_USER_APPROVAL = 2  # Requires explicit UI approval (delete, large bulk edits)
    LEVEL_3_BLOCKED = 3        # Strictly prohibited


class AgentTool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        permission_level: ToolPermissionLevel,
        handler: Callable[..., Dict[str, Any]]
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.permission_level = permission_level
        self.handler = handler

    def execute(self, **kwargs) -> Dict[str, Any]:
        try:
            return self.handler(**kwargs)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error executing tool '{self.name}': {str(e)}"
            }


class ToolRegistry:
    _instance = None

    def __init__(self):
        self._tools: Dict[str, AgentTool] = {}
        self.autonomy_level = ToolPermissionLevel.LEVEL_1_LOW_RISK_WRITE

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ToolRegistry()
            register_default_tools(cls._instance)
        return cls._instance

    def register(self, tool: AgentTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[AgentTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission_level": int(t.permission_level),
                "parameters": t.parameters
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, name: str, user_approved: bool = False, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found."}

        # Check permission constraints
        if tool.permission_level == ToolPermissionLevel.LEVEL_3_BLOCKED:
            return {"success": False, "error": f"Tool '{name}' is permanently blocked for safety."}

        if tool.permission_level == ToolPermissionLevel.LEVEL_2_USER_APPROVAL and not user_approved:
            return {
                "success": False,
                "requires_approval": True,
                "tool_name": name,
                "input_summary": json.dumps(kwargs),
                "message": f"Tool '{name}' requires user confirmation before execution."
            }

        result = tool.execute(**kwargs)
        return result


# --- HANDLERS FOR DEFAULT TOOLS ---

def _handle_get_study_status(**kwargs) -> Dict[str, Any]:
    stats = get_study_stats()
    tasks = get_tasks()
    pending = [t for t in tasks if not t.get("is_completed")]
    return {
        "success": True,
        "total_hours": stats.get("total_hours", 0),
        "today_hours": stats.get("today_hours", 0),
        "completed_tasks": stats.get("completed_tasks", 0),
        "pending_tasks": len(pending),
        "top_pending_tasks": [t["title"] for t in pending[:3]],
        "message": f"Total study time: {stats.get('total_hours', 0)}h. Today: {stats.get('today_hours', 0)}h. Pending tasks: {len(pending)}."
    }


def _handle_start_study_session(subject_name: str = "General Study", duration_minutes: float = 45.0, notes: str = "", **kwargs) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
    row = cursor.fetchone()
    subject_id = row["id"] if row else None
    conn.close()

    ok = save_study_session(subject_id, float(duration_minutes), notes or f"Logged via JARVIS Agent ({subject_name})")
    return {
        "success": ok,
        "subject": subject_name,
        "duration_minutes": duration_minutes,
        "message": f"Successfully recorded {duration_minutes} min study session for {subject_name}."
    }


def _handle_create_study_task(title: str, subject_name: str = "", priority: str = "Medium", task_type: str = "Study", **kwargs) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    subject_id = None
    if subject_name:
        cursor.execute("SELECT id FROM subjects WHERE name LIKE ?", (f"%{subject_name}%",))
        row = cursor.fetchone()
        if row:
            subject_id = row["id"]
    conn.close()

    ok = add_task(title=title, subject_id=subject_id, priority=priority, task_type=task_type)
    return {
        "success": ok,
        "title": title,
        "subject": subject_name or "General",
        "message": f"Created task: '{title}' [{priority}]"
    }


def _handle_get_weak_topics(**kwargs) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check mistakes first
    cursor.execute("""
        SELECT mistake_category, COUNT(*) as cnt 
        FROM mistake_log 
        GROUP BY mistake_category 
        ORDER BY cnt DESC
    """)
    mistakes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT concept_name, mastery_level, times_wrong 
        FROM learning_memory 
        WHERE mastery_level < 60 OR times_wrong > 0 
        ORDER BY mastery_level ASC, times_wrong DESC 
        LIMIT 5
    """)
    weak_nodes = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "success": True,
        "weak_concepts": weak_nodes,
        "primary_error_patterns": mistakes,
        "message": f"Found {len(weak_nodes)} weak concept nodes and {len(mistakes)} mistake patterns."
    }


def _handle_create_note(title: str, content: str, subject_name: str = "", importance: str = "Medium", **kwargs) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    subject_id = None
    if subject_name:
        cursor.execute("SELECT id FROM subjects WHERE name LIKE ?", (f"%{subject_name}%",))
        row = cursor.fetchone()
        if row:
            subject_id = row["id"]

    cursor.execute("""
        INSERT INTO agent_notes (title, content, subject_id, importance_level)
        VALUES (?, ?, ?, ?)
    """, (title.strip(), content.strip(), subject_id, importance))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "note_id": note_id,
        "title": title,
        "message": f"Saved note #{note_id}: '{title}'."
    }


def _handle_search_knowledge_base(query: str, subject_filter: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    try:
        from services.rag_service import rag_search_and_answer
        ans, sources = rag_search_and_answer(query=query, subject_name=subject_filter or "")
        return {
            "success": True,
            "answer": ans,
            "sources_count": len(sources),
            "sources": sources[:3],
            "message": f"Found {len(sources)} grounded sources from knowledge base."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Search failed: {str(e)}"
        }


def _handle_backup_database(**kwargs) -> Dict[str, Any]:
    from config import DB_PATH, BASE_DIR
    backup_dir = BASE_DIR / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"gate_jarvis_backup_{stamp}.db"
    shutil.copy2(DB_PATH, target)
    return {
        "success": True,
        "backup_path": str(target),
        "message": f"Database safely backed up to '{target.name}'."
    }


def register_default_tools(registry: ToolRegistry):
    registry.register(AgentTool(
        name="get_study_status",
        description="Retrieves current study statistics, completed hours, and top pending tasks.",
        parameters={},
        permission_level=ToolPermissionLevel.LEVEL_0_READ,
        handler=_handle_get_study_status
    ))

    registry.register(AgentTool(
        name="start_study_session",
        description="Records a completed study session with duration and notes for a subject.",
        parameters={"subject_name": "str", "duration_minutes": "float", "notes": "str"},
        permission_level=ToolPermissionLevel.LEVEL_1_LOW_RISK_WRITE,
        handler=_handle_start_study_session
    ))

    registry.register(AgentTool(
        name="create_study_task",
        description="Creates a new study or revision task in the planner.",
        parameters={"title": "str", "subject_name": "str", "priority": "str", "task_type": "str"},
        permission_level=ToolPermissionLevel.LEVEL_1_LOW_RISK_WRITE,
        handler=_handle_create_study_task
    ))

    registry.register(AgentTool(
        name="get_weak_topics",
        description="Identifies weak concepts and primary error patterns from mistake log and learning memory.",
        parameters={},
        permission_level=ToolPermissionLevel.LEVEL_0_READ,
        handler=_handle_get_weak_topics
    ))

    registry.register(AgentTool(
        name="create_note",
        description="Saves an important concept note, formula, or reflection into Agent Memory.",
        parameters={"title": "str", "content": "str", "subject_name": "str", "importance": "str"},
        permission_level=ToolPermissionLevel.LEVEL_1_LOW_RISK_WRITE,
        handler=_handle_create_note
    ))

    registry.register(AgentTool(
        name="search_knowledge_base",
        description="Performs semantic RAG search across uploaded engineering PDFs, notes, and DPPs.",
        parameters={"query": "str", "subject_filter": "str"},
        permission_level=ToolPermissionLevel.LEVEL_0_READ,
        handler=_handle_search_knowledge_base
    ))

    registry.register(AgentTool(
        name="backup_database",
        description="Creates a timestamped snapshot of the SQLite database in data/backups.",
        parameters={},
        permission_level=ToolPermissionLevel.LEVEL_1_LOW_RISK_WRITE,
        handler=_handle_backup_database
    ))
