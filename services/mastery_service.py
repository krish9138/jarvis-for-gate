"""
services/mastery_service.py
---------------------------
Multi-Signal Mastery Engine & Prerequisite Dependency Graph for GATE JARVIS 4.0.
Tracks student progression across 8 cognitive tiers:
NOT_STARTED -> LEARNING -> UNDERSTOOD -> PRACTICING -> GATE_READY -> PYQ_MASTERED -> REVISION_STABLE -> EXAM_READY
"""

from typing import Dict, Any, List, Tuple, Optional
import math
from database.connection import get_db_connection
from database.queries import (
    get_all_concept_mastery_states,
    update_concept_mastery_state,
    get_concept_prerequisites,
    check_prerequisites_mastered
)

MASTERY_STAGES = [
    ("NOT_STARTED", "Not Started", "⚪", 0.0),
    ("LEARNING", "Learning Core Concept", "📘", 20.0),
    ("UNDERSTOOD", "Concept Understood", "💡", 40.0),
    ("PRACTICING", "Basic Practice Drill", "✍️", 55.0),
    ("GATE_READY", "GATE Level Problem Solving", "⚙️", 70.0),
    ("PYQ_MASTERED", "PYQ Mastered (Air < 100)", "🎯", 85.0),
    ("REVISION_STABLE", "Revision Stable (Spaced Rep.)", "🔄", 92.0),
    ("EXAM_READY", "Exam Ready & Trapped-Proof", "🏆", 98.0)
]

STAGE_DETAILS = {
    s[0]: {"label": s[1], "icon": s[2], "min_score": s[3]} for s in MASTERY_STAGES
}

def determine_mastery_state(composite_score: float, pyq_score: float, retention_pct: float) -> str:
    """Classifies student composite metrics into one of 8 cognitive states."""
    if composite_score >= 95.0 and pyq_score >= 90.0 and retention_pct >= 90.0:
        return "EXAM_READY"
    elif composite_score >= 88.0 and retention_pct >= 85.0:
        return "REVISION_STABLE"
    elif composite_score >= 80.0 and pyq_score >= 75.0:
        return "PYQ_MASTERED"
    elif composite_score >= 68.0:
        return "GATE_READY"
    elif composite_score >= 50.0:
        return "PRACTICING"
    elif composite_score >= 35.0:
        return "UNDERSTOOD"
    elif composite_score >= 15.0:
        return "LEARNING"
    return "NOT_STARTED"

def calculate_composite_mastery(
    concept_score: float,
    numerical_score: float,
    pyq_score: float,
    dpp_score: float,
    accuracy: float,
    retention_pct: float,
    mistake_freq: int
) -> Tuple[float, str]:
    """
    Computes weighted multi-signal mastery formulation:
    Composite = 0.25*Concept + 0.25*Numerical + 0.25*PYQ + 0.15*DPP + 0.10*Retention - (Mistake Penalty)
    """
    mistake_penalty = min(20.0, mistake_freq * 2.5)
    raw_composite = (
        (concept_score * 0.25) +
        (numerical_score * 0.25) +
        (pyq_score * 0.25) +
        (dpp_score * 0.15) +
        (retention_pct * 0.10)
    ) - mistake_penalty

    composite = max(0.0, min(100.0, round(raw_composite, 1)))
    state = determine_mastery_state(composite, pyq_score, retention_pct)
    return composite, state

def seed_foundational_concept_graph():
    """Ensures core Mechanical Engineering concept tree and prerequisite dependencies exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Canonical concept hierarchy with prerequisite links
    foundational_concepts = [
        # Engineering Mathematics
        ("Linear Algebra: Matrices & Eigenvalues", "Engineering Mathematics"),
        ("Calculus: Partial Derivatives & Maxima", "Engineering Mathematics"),
        ("Ordinary Differential Equations (ODE)", "Engineering Mathematics"),
        
        # Strength of Materials
        ("Stress-Strain & Hooke's Law", "Strength of Materials"),
        ("Thin Cylinders & Pressure Vessels", "Strength of Materials"),
        ("Shear Force & Bending Moment Diagrams", "Strength of Materials"),
        ("Torsion of Circular Shafts", "Strength of Materials"),
        ("Deflection of Beams & Superposition", "Strength of Materials"),
        
        # Fluid Mechanics
        ("Fluid Statics & Buoyancy", "Fluid Mechanics"),
        ("Bernoulli Equation & Energy Conservation", "Fluid Mechanics"),
        ("Laminar & Turbulent Pipe Flow", "Fluid Mechanics"),
        ("Boundary Layer Theory & Drag", "Fluid Mechanics"),
        
        # Thermodynamics & Power Cycles
        ("First Law of Thermodynamics & Energy Balance", "Thermodynamics"),
        ("Second Law of Thermodynamics & Heat Engines", "Thermodynamics"),
        ("Entropy, T-s Diagrams & Availability", "Thermodynamics"),
        ("Vapour Power Cycles (Rankine Cycle)", "Thermodynamics"),
        ("Gas Power Cycles (Otto, Diesel, Brayton)", "Thermodynamics"),
        
        # Theory of Machines & Vibrations
        ("Kinematic Pairs & Inversions", "Theory of Machines"),
        ("Gear Trains & Velocity Ratios", "Theory of Machines"),
        ("Single Degree of Freedom Free Vibrations", "Vibrations"),
        ("Damped and Forced Vibrations & Transmissibility", "Vibrations")
    ]

    concept_id_map = {}
    for c_name, subj_name in foundational_concepts:
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (subj_name,))
        subj_row = cursor.fetchone()
        subj_id = subj_row["id"] if subj_row else None

        cursor.execute("SELECT concept_id FROM learning_memory WHERE concept_name = ?", (c_name,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("""
                INSERT INTO learning_memory (concept_name, subject_id, mastery_level)
                VALUES (?, ?, 0)
            """, (c_name, subj_id))
            cid = cursor.lastrowid
        else:
            cid = existing["concept_id"]
        concept_id_map[c_name] = cid

    # Prerequisite Links: (child_concept, prerequisite_concept)
    prereq_links = [
        ("Thin Cylinders & Pressure Vessels", "Stress-Strain & Hooke's Law"),
        ("Deflection of Beams & Superposition", "Shear Force & Bending Moment Diagrams"),
        ("Ordinary Differential Equations (ODE)", "Calculus: Partial Derivatives & Maxima"),
        ("Single Degree of Freedom Free Vibrations", "Ordinary Differential Equations (ODE)"),
        ("Damped and Forced Vibrations & Transmissibility", "Single Degree of Freedom Free Vibrations"),
        ("Bernoulli Equation & Energy Conservation", "Fluid Statics & Buoyancy"),
        ("Boundary Layer Theory & Drag", "Laminar & Turbulent Pipe Flow"),
        ("Second Law of Thermodynamics & Heat Engines", "First Law of Thermodynamics & Energy Balance"),
        ("Entropy, T-s Diagrams & Availability", "Second Law of Thermodynamics & Heat Engines"),
        ("Vapour Power Cycles (Rankine Cycle)", "Entropy, T-s Diagrams & Availability"),
        ("Gas Power Cycles (Otto, Diesel, Brayton)", "First Law of Thermodynamics & Energy Balance")
    ]

    for child, prereq in prereq_links:
        child_id = concept_id_map.get(child)
        prereq_id = concept_id_map.get(prereq)
        if child_id and prereq_id:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO concept_graph (concept_id, prerequisite_id)
                    VALUES (?, ?)
                """, (child_id, prereq_id))
            except Exception:
                pass

    conn.commit()
    conn.close()

def evaluate_prerequisite_safety(concept_id: int, threshold: float = 60.0) -> Dict[str, Any]:
    """
    Checks if a student has sufficiently mastered all prerequisites before proceeding.
    Returns structured safety advice.
    """
    all_met, weak_list = check_prerequisites_mastered(concept_id, threshold=threshold)
    if all_met:
        return {
            "safe": True,
            "warning": False,
            "message": "All prerequisite concepts are solidly understood. You are clear to proceed!",
            "weak_prerequisites": []
        }
    else:
        names = [f"**{p['concept_name']}** ({p['mastery_level']}%)" for p in weak_list]
        return {
            "safe": False,
            "warning": True,
            "message": f"⚠️ **Prerequisite Alert**: Your foundation in {', '.join(names)} is below {threshold}% threshold. Revising this prerequisite is recommended before continuing.",
            "weak_prerequisites": weak_list
        }

def log_concept_practice_event(
    concept_id: int,
    event_type: str, # 'concept_quiz' | 'dpp' | 'pyq' | 'test'
    score_pct: float,
    is_correct: bool = True,
    mistake_category: Optional[str] = None
):
    """Updates concept state based on real-time activity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concept_mastery_states WHERE concept_id = ?", (concept_id,))
    existing = cursor.fetchone()
    conn.close()

    c_score = existing["concept_score"] if existing else 20.0
    num_score = existing["numerical_score"] if existing else 10.0
    pyq_score = existing["pyq_score"] if existing else 0.0
    dpp_score = existing["dpp_score"] if existing else 0.0
    acc = existing["accuracy"] if existing else 50.0
    retention = existing["retention_pct"] if existing else 100.0
    mistakes = existing["mistake_freq"] if existing else 0

    if event_type == "concept_quiz":
        c_score = round(c_score * 0.7 + score_pct * 0.3, 1)
    elif event_type == "dpp":
        dpp_score = round(dpp_score * 0.6 + score_pct * 0.4, 1)
        num_score = round(num_score * 0.7 + score_pct * 0.3, 1)
    elif event_type == "pyq":
        pyq_score = round(pyq_score * 0.6 + score_pct * 0.4, 1)
        num_score = round(num_score * 0.7 + score_pct * 0.3, 1)
    
    if not is_correct:
        mistakes += 1
        acc = max(0.0, acc - 5.0)
    else:
        acc = min(100.0, acc + 3.0)

    composite, state = calculate_composite_mastery(
        c_score, num_score, pyq_score, dpp_score, acc, retention, mistakes
    )

    update_concept_mastery_state(
        concept_id=concept_id,
        state_enum=state,
        concept_score=c_score,
        numerical_score=num_score,
        pyq_score=pyq_score,
        dpp_score=dpp_score,
        accuracy=acc,
        avg_solving_time=120.0,
        retention_pct=retention,
        mistake_freq=mistakes,
        composite_mastery=composite
    )
