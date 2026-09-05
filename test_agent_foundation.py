"""
test_agent_foundation.py
-------------------------
Automated verification suite for the JARVIS Autonomous Agent, Tool Registry,
Multilingual NLU engine, and Engineering Plot Case Study Subsystem.
"""

import sys
import io

# Set UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from database.connection import init_db, get_db_connection
from agent.tool_registry import ToolRegistry
from agent.command_interpreter import interpret_command, detect_language
from agent.agent_core import get_agent_instance
from views.case_study_plot_view import _save_case_study, _get_all_case_studies, generate_case_study_report



def run_tests():
    print("=== STARTING JARVIS AUTONOMOUS AGENT TEST SUITE ===")

    # 1. Initialize Database
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r["name"] for r in cursor.fetchall()]
    assert "agent_activity_log" in tables, "agent_activity_log table missing!"
    assert "agent_notes" in tables, "agent_notes table missing!"
    assert "plot_case_studies" in tables, "plot_case_studies table missing!"
    print("1. Database Schema & Agent Tables Verified. [PASS]")

    # 2. Test Tool Registry Execution
    registry = ToolRegistry.get_instance()
    status_res = registry.execute_tool("get_study_status")
    assert status_res["success"] is True, "get_study_status failed!"
    print(f"2. Tool 'get_study_status' executed: Total Hours = {status_res['total_hours']}. [PASS]")

    task_res = registry.execute_tool("create_study_task", title="Revise Entropy & T-s diagrams", subject_name="Thermodynamics")
    assert task_res["success"] is True, "create_study_task failed!"
    print(f"3. Tool 'create_study_task' executed: {task_res['message']}. [PASS]")

    note_res = registry.execute_tool("create_note", title="Euler Column Buckling", content="P_cr = pi^2 * E * I / (L_e)^2", subject_name="Strength of Materials")
    assert note_res["success"] is True, "create_note failed!"
    print(f"4. Tool 'create_note' executed: {note_res['message']}. [PASS]")

    # 3. Test Multilingual Language Detection & NLU Intent Classifier
    # Marathi Test
    mr_prompt = "मला आज Thermodynamics चा अभ्यास करायचा आहे 1 तास"
    assert detect_language(mr_prompt) == "mr", f"Failed language detection for Marathi: {detect_language(mr_prompt)}"
    mr_intent = interpret_command(mr_prompt)
    assert mr_intent.detected_language == "mr"
    print(f"5. Marathi NLU Intent: {mr_intent.intent_name} (Duration={mr_intent.parameters.get('duration_minutes')}m). [PASS]")

    # Hindi Test
    hi_prompt = "mujhe weak topics aur galtiyan batao"
    hi_intent = interpret_command(hi_prompt)
    assert hi_intent.intent_name == "GET_WEAK_TOPICS"
    print(f"6. Hindi NLU Intent: {hi_intent.intent_name}. [PASS]")

    # English Test
    en_prompt = "Start a 60 min study session on Fluid Mechanics"
    en_intent = interpret_command(en_prompt)
    assert en_intent.intent_name == "START_STUDY_SESSION"
    assert en_intent.parameters.get("duration_minutes") == 60.0
    print(f"7. English NLU Intent: {en_intent.intent_name} (Duration={en_intent.parameters.get('duration_minutes')}m). [PASS]")

    # 4. Test Agent Core Autonomous Loop & Audit Logging
    agent = get_agent_instance()
    exec_res = agent.process_user_input("What should I study today?")
    assert exec_res["success"] is True
    assert exec_res["log_id"] > 0
    print(f"8. Autonomous Loop Executed: Log #{exec_res['log_id']} (Latency={exec_res['duration_ms']}ms). [PASS]")

    # Test Marathi Autonomous execution
    exec_mr = agent.process_user_input("मला आजचा स्टडी प्लॅन सांग")
    assert exec_mr["detected_language"] == "mr"
    print(f"9. Marathi Autonomous Loop: '{exec_mr['response_text'][:60]}...'. [PASS]")

    # 5. Test Plot & Property Case Study Engine
    test_case = {
        "property_id": "TEST-PROP-001",
        "property_name": "Chakan MIDC Phase 2 Plot",
        "property_type": "Industrial Plot",
        "case_study_title": "Techno-Economic Feasibility for Automated Component Plant",
        "location_summary": "Chakan, Pune, Maharashtra",
        "total_area_sqft": 25000.0,
        "executive_summary": "Feasibility analysis for heavy fabrication shop floor.",
        "status": "Completed",
        "recommendations": "Deploy pre-engineered building with isolated RCC footings.",
        "report_markdown": "# Test Report"
    }
    _save_case_study(test_case)
    saved_cases = _get_all_case_studies()
    assert any(c["property_id"] == "TEST-PROP-001" for c in saved_cases)
    print("10. Engineering Plot Case Study Saved & Verified. [PASS]")

    print("\n=== ALL 10 JARVIS AGENT & FOUNDATION TESTS PASSED (100%)! ===")


if __name__ == "__main__":
    run_tests()
