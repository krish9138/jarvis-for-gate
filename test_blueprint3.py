import json
import sys
import io

# Ensure UTF-8 output in Windows PowerShell / cmd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from database.connection import init_db, get_db_connection
from database.queries import (
    get_all_subjects,
    get_doubts,
    log_doubt,
    resolve_doubt,
    get_problem_sessions,
    save_problem_session,
    get_all_test_sets,
    get_test_questions,
    save_test_attempt,
    get_test_attempts,
    get_subject_weightage,
    get_plan_months,
    get_skills_tracker,
    get_study_resources,
    get_weekly_timetable,
    get_study_tactics,
    get_subject_progress,
    get_monthly_study_comparison
)

def test_blueprint3_suite():
    print("=== STARTING BLUEPRINT 3 COMPREHENSIVE TEST SUITE ===")
    init_db()
    
    # 1. Verify Study Plan Seed Data Loaded
    print("\n1. Testing Study Plan Dashboard Seed Tables:")
    months = get_plan_months()
    print(f"   [x] Plan Months count: {len(months)} (Expected: 8)")
    assert len(months) == 8, f"Expected 8 months, got {len(months)}"
    
    skills = get_skills_tracker()
    print(f"   [x] Skills Tracker count: {len(skills)} (Expected: 8)")
    assert len(skills) >= 8, f"Expected >=8 skills, got {len(skills)}"
    
    weightage = get_subject_weightage()
    print(f"   [x] Subject Weightage items: {len(weightage)} (Expected: 11)")
    assert len(weightage) == 11, f"Expected 11 subject weightages, got {len(weightage)}"
    
    resources = get_study_resources()
    print(f"   [x] Recommended Resources: {len(resources)} items")
    assert len(resources) >= 12, f"Expected >=12 resources, got {len(resources)}"
    
    timetable = get_weekly_timetable()
    print(f"   [x] Weekly Timetable Slots: {len(timetable)} slots")
    assert len(timetable) >= 5, f"Expected >=5 timetable slots, got {len(timetable)}"

    progress = get_subject_progress()
    print(f"   [x] Subject Progress Tracker: {len(progress)} subjects")
    assert len(progress) == 11, f"Expected 11 subjects in tracker, got {len(progress)}"

    # 2. Test Doubt Engine Database & Workflow
    print("\n2. Testing Doubt Engine Workflow:")
    doubt_id = log_doubt(subject_id=1, question="What is the condition for pure shear in thin cylinder?")
    print(f"   [x] Logged Doubt ID: {doubt_id}")
    
    doubts_open = get_doubts(status="open")
    assert any(d["id"] == doubt_id for d in doubts_open), "Logged doubt should be in open queue"
    
    res_ok = resolve_doubt(doubt_id, ai_answer="Pure shear occurs when longitudinal stress equals negative hoop stress or on planes at 45 degrees.", status="resolved")
    assert res_ok, "Failed to resolve doubt"
    
    doubts_resolved = get_doubts(status="resolved")
    assert any(d["id"] == doubt_id for d in doubts_resolved), "Resolved doubt should be in resolved archive"
    print("   [PASS] Doubt Engine Logging and Resolution Verified")

    # 3. Test Problem Solving Engine
    print("\n3. Testing Problem-Solving Engine:")
    steps = [
        {"step_number": 1, "step_title": "Identify Given Parameters", "explanation": "Inner radius r1=50mm, Outer radius r2=100mm, Internal pressure Pi=20MPa", "formula_used": "Given data"},
        {"step_number": 2, "step_title": "Apply Lame's Equations", "explanation": "Radial stress and hoop stress distribution constants A and B", "formula_used": "sigma_r = A - B/r^2, sigma_theta = A + B/r^2"},
        {"step_number": 3, "step_title": "Solve for Maximum Hoop Stress", "explanation": "Maximum hoop stress occurs at inner surface r=r1", "formula_used": "sigma_max = Pi*(r2^2 + r1^2)/(r2^2 - r1^2)"}
    ]
    prob_id = save_problem_session(
        subject_id=1,
        problem_statement="A thick cylinder with r1=50mm and r2=100mm is subjected to internal pressure 20MPa. Find max hoop stress.",
        steps=steps,
        final_answer="33.33 MPa",
        difficulty="Medium"
    )
    print(f"   [x] Problem Session Saved: ID {prob_id}")
    sessions = get_problem_sessions()
    assert any(s["id"] == prob_id for s in sessions), "Problem session should exist in practice log"
    print("   [PASS] Problem-Solving Engine Session Verified")

    # 4. Test Test Engine
    print("\n4. Testing Test Engine (Mocks, Questions, Scoring):")
    test_sets = get_all_test_sets()
    print(f"   [x] Test Sets count: {len(test_sets)}")
    assert len(test_sets) >= 1, "Should have at least 1 seeded test set"
    
    sample_set = test_sets[0]
    questions = get_test_questions(sample_set["id"])
    print(f"   [x] Questions in Test Set '{sample_set['title']}': {len(questions)}")
    assert len(questions) > 0, "Test set should contain questions"

    attempt_id = save_test_attempt(
        test_set_id=sample_set["id"],
        test_title=sample_set["title"],
        score=2.67,
        max_score=len(questions),
        answers={"1": "A", "2": "B"},
        section_breakdown={"Core Mechanical": 2.67}
    )
    print(f"   [x] Saved Test Attempt ID: {attempt_id}")
    attempts = get_test_attempts()
    assert any(a["id"] == attempt_id for a in attempts), "Attempt should be recorded in test_attempts"
    print("   [PASS] Test Engine Complete Flow Verified")

    print("\n=== ALL BLUEPRINT 3 TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    test_blueprint3_suite()
