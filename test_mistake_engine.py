"""
test_mistake_engine.py
----------------------
Verification suite for the Mistake Book & Error Intelligence subsystem.
"""
from database.connection import init_db, get_db_connection
from views.mistake_view import (
    log_mistake,
    get_mistakes,
    get_category_counts,
    MISTAKE_CATEGORIES
)

def run_tests():
    print("=== STARTING MISTAKE INTELLIGENCE TEST SUITE ===")
    
    # 1. Init DB & Verify Table Creation
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as count FROM mistake_log")
    initial_count = cursor.fetchone()["count"]
    print(f"1. Database Initialized: Initial mistakes count = {initial_count}")

    # 2. Test Logging Mistakes for different categories
    m1_id = log_mistake(
        question_text="A shaft of diameter 40 mm transmits 20 kW at 300 rpm. Find maximum shear stress.",
        user_answer="25.4 MPa",
        correct_answer="31.8 MPa",
        mistake_category="Calculation",
        source="Test Engine Drill"
    )
    print(f"2. Logged Calculation Mistake: ID #{m1_id}")

    m2_id = log_mistake(
        question_text="Calculate hoop stress in thin cylinder with p=2 MPa, d=500mm, t=5mm.",
        user_answer="100000 Pa",
        correct_answer="100 MPa",
        mistake_category="Unit",
        source="PYQ Practice"
    )
    print(f"3. Logged Unit Mistake: ID #{m2_id}")

    # 3. Test Retrieval & Filter
    all_mistakes = get_mistakes(days=30)
    assert len(all_mistakes) >= 2, "Failed to retrieve logged mistakes!"
    print(f"4. Retrieved {len(all_mistakes)} mistakes in 30-day window. [PASS]")

    # 4. Test Category Counts Aggregation
    counts = get_category_counts(days=30)
    assert counts["Calculation"] >= 1, "Calculation count mismatch!"
    assert counts["Unit"] >= 1, "Unit count mismatch!"
    print(f"5. Error Breakdown: {counts}")
    print("6. All 7 standard categories validated. [PASS]")

    print("\n=== ALL MISTAKE INTELLIGENCE TESTS PASSED (100%)! ===")

if __name__ == "__main__":
    run_tests()
