"""
services/dpp_service.py
-----------------------
Daily Practice Problem (DPP) & Practice Lab Engine for GATE JARVIS 4.0.
Supports multi-source ingestion (PDF, text, AI generation), interactive evaluation,
per-question timing, automatic grading, and mistake logging.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from database.connection import get_db_connection
from database.queries import (
    create_dpp_set,
    add_dpp_question,
    get_all_dpp_sets,
    get_dpp_questions,
    save_dpp_attempt,
    log_mistake
)

def seed_foundational_dpps():
    """Seeds authentic Mechanical Engineering DPP sets if database is empty."""
    existing_sets = get_all_dpp_sets()
    if existing_sets:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. DPP 01: Thin Cylinders & Pressure Vessels (SOM)
    cursor.execute("SELECT id FROM subjects WHERE name = 'Strength of Materials'")
    som_row = cursor.fetchone()
    som_id = som_row["id"] if som_row else None

    dpp1_id = create_dpp_set(
        title="DPP 01: Thin & Thick Cylinders Stress Analysis",
        subject_id=som_id,
        topic="Thin Cylinders & Pressure Vessels",
        difficulty="Medium",
        source="curated_gate",
        total_questions=4
    )

    q1_options = json.dumps([
        "A) Circumferential stress = 2 * Longitudinal stress",
        "B) Circumferential stress = Longitudinal stress",
        "C) Circumferential stress = 0.5 * Longitudinal stress",
        "D) Radial stress is maximum at the outer radius"
    ])
    add_dpp_question(
        dpp_set_id=dpp1_id,
        question_text="For a thin-walled cylindrical pressure vessel with internal pressure p, internal diameter d, and wall thickness t, what is the relation between hoop stress and longitudinal stress?",
        question_type="MCQ",
        options_json=q1_options,
        correct_answer="A",
        marks=1.0,
        negative_marks=0.33,
        explanation="Hoop stress $\\sigma_h = pd / (2t)$ and longitudinal stress $\\sigma_L = pd / (4t)$. Therefore, $\\sigma_h = 2 \\sigma_L$.",
        formula_hint="\\sigma_h = pd / (2t), \\sigma_L = pd / (4t)",
        concept_tested="Thin Cylinder Stress State"
    )

    add_dpp_question(
        dpp_set_id=dpp1_id,
        question_text="A thin cylindrical vessel of internal diameter 1000 mm and wall thickness 10 mm is subjected to an internal fluid pressure of 2 MPa. Calculate the longitudinal stress (in MPa) developed in the cylinder wall.",
        question_type="NAT",
        options_json="[]",
        correct_answer="50",
        marks=2.0,
        negative_marks=0.0,
        explanation="Longitudinal stress $\\sigma_L = pd / (4t) = (2 \\text{ MPa} \\times 1000 \\text{ mm}) / (4 \\times 10 \\text{ mm}) = 2000 / 40 = 50\\text{ MPa}$.",
        formula_hint="\\sigma_L = pd / (4t)",
        concept_tested="Longitudinal Stress in Cylinders"
    )

    q3_options = json.dumps([
        "A) Maximum shear stress occurs in the plane of surface",
        "B) In-plane maximum shear stress is pd / (8t)",
        "C) Absolute maximum shear stress is pd / (4t)",
        "D) Radial stress across the thickness is completely ignored"
    ])
    add_dpp_question(
        dpp_set_id=dpp1_id,
        question_text="Select all correct statements regarding stress states in thin cylindrical pressure vessels:",
        question_type="MSQ",
        options_json=q3_options,
        correct_answer=json.dumps(["B", "C", "D"]),
        marks=2.0,
        negative_marks=0.0,
        explanation="In-plane max shear stress $\\tau_{in} = (\\sigma_h - \\sigma_L) / 2 = pd / (8t)$. Out-of-plane absolute max shear stress $\\tau_{max, abs} = (\\sigma_h - 0) / 2 = pd / (4t)$. Radial stress is taken as 0.",
        formula_hint="\\tau_{max, in} = pd / (8t), \\tau_{max, abs} = pd / (4t)",
        concept_tested="3D Mohr Circle for Thin Cylinders"
    )

    # 2. DPP 02: Fluid Mechanics (Bernoulli & Continuity)
    cursor.execute("SELECT id FROM subjects WHERE name = 'Fluid Mechanics'")
    fm_row = cursor.fetchone()
    fm_id = fm_row["id"] if fm_row else None

    dpp2_id = create_dpp_set(
        title="DPP 02: Bernoulli Equation & Pipe Flow Dynamics",
        subject_id=fm_id,
        topic="Bernoulli Equation & Continuity",
        difficulty="Medium",
        source="curated_gate",
        total_questions=3
    )

    q4_options = json.dumps([
        "A) Steady flow along a streamline",
        "B) Incompressible and inviscid fluid",
        "C) No shaft work or heat exchange",
        "D) Highly turbulent boundary layer with separation"
    ])
    add_dpp_question(
        dpp_set_id=dpp2_id,
        question_text="Which of the following is NOT an assumption of Euler's equation leading to Bernoulli's equation?",
        question_type="MCQ",
        options_json=q4_options,
        correct_answer="D",
        marks=1.0,
        negative_marks=0.33,
        explanation="Bernoulli's equation requires inviscid (frictionless) flow. Turbulent boundary layers with separation violate this.",
        formula_hint="P/\\rho + v^2/2 + gz = \\text{constant}",
        concept_tested="Bernoulli Assumptions"
    )

    add_dpp_question(
        dpp_set_id=dpp2_id,
        question_text="Water flows through a horizontal pipe reducing from diameter $D_1 = 0.2\\text{ m}$ to $D_2 = 0.1\\text{ m}$. If the velocity at section 1 is $2\\text{ m/s}$, find the velocity at section 2 in m/s.",
        question_type="NAT",
        options_json="[]",
        correct_answer="8",
        marks=2.0,
        negative_marks=0.0,
        explanation="By continuity for incompressible flow: $A_1 V_1 = A_2 V_2 \\implies V_2 = V_1 \\times (D_1/D_2)^2 = 2 \\times (0.2 / 0.1)^2 = 2 \\times 4 = 8\\text{ m/s}$.",
        formula_hint="A_1 V_1 = A_2 V_2",
        concept_tested="Continuity Equation"
    )

    # 3. DPP 03: Thermodynamics (Entropy & 2nd Law)
    cursor.execute("SELECT id FROM subjects WHERE name = 'Thermodynamics'")
    th_row = cursor.fetchone()
    th_id = th_row["id"] if th_row else None

    dpp3_id = create_dpp_set(
        title="DPP 03: Second Law & Clausius Inequality",
        subject_id=th_id,
        topic="Second Law & Entropy",
        difficulty="Hard",
        source="curated_gate",
        total_questions=2
    )

    q6_options = json.dumps([
        "A) Reversible cycle",
        "B) Irreversible cycle",
        "C) Impossible cycle",
        "D) Adiabatic process"
    ])
    add_dpp_question(
        dpp_set_id=dpp3_id,
        question_text="In a cyclic thermodynamic process, if $\\oint \\frac{\\delta Q}{T} < 0$, the cycle is:",
        question_type="MCQ",
        options_json=q6_options,
        correct_answer="B",
        marks=1.0,
        negative_marks=0.33,
        explanation="By Clausius Inequality: $\\oint \\delta Q / T = 0$ (Reversible), $\\oint \\delta Q / T < 0$ (Irreversible), $\\oint \\delta Q / T > 0$ (Impossible).",
        formula_hint="\\oint \\delta Q / T \\le 0",
        concept_tested="Clausius Inequality"
    )

    add_dpp_question(
        dpp_set_id=dpp3_id,
        question_text="A reversible heat engine receives 1000 kJ of heat from a reservoir at 800 K and rejects heat to a sink at 400 K. What is the work output (in kJ)?",
        question_type="NAT",
        options_json="[]",
        correct_answer="500",
        marks=2.0,
        negative_marks=0.0,
        explanation="Thermal efficiency eta = 1 - (400/800) = 0.5. Work output W = eta * Q_in = 0.5 * 1000 kJ = 500 kJ.",
        formula_hint="W = Q_1 (1 - T_2/T_1)",
        concept_tested="Carnot Engine Work Output"
    )

    conn.close()

def parse_and_import_dpp_text(raw_text: str, title: str, subject_id: Optional[int] = None, topic: str = "") -> int:
    """
    Parses pasted text or OCR-extracted DPP questions into structured database rows.
    Format heuristics:
    Q1: ...
    A) ... B) ... C) ... D) ...
    Answer: A
    Explanation: ...
    """
    dpp_id = create_dpp_set(
        title=title or "Imported Custom DPP",
        subject_id=subject_id,
        topic=topic or "General Practice",
        difficulty="Medium",
        source="upload",
        total_questions=0
    )

    # Regex splitting on Question markers (e.g. Q1:, Question 1., 1.)
    q_blocks = re.split(r'(?:^|\n)(?:Q(?:uestion)?\s*\d+[\.\:]|\d+[\.\:])\s*', raw_text, flags=re.IGNORECASE)
    valid_qs = [b.strip() for b in q_blocks if len(b.strip()) > 15]

    count = 0
    for block in valid_qs:
        # Extract Answer
        ans_match = re.search(r'(?:Ans(?:wer)?|Correct)\s*[\:\-]?\s*([A-D0-9\.\-]+)', block, re.IGNORECASE)
        correct_ans = ans_match.group(1).strip().upper() if ans_match else "A"

        # Extract Options
        options = []
        opt_matches = re.findall(r'([A-D]\))\s*([^A-D\n\r]+)', block)
        if opt_matches:
            options = [f"{m[0]} {m[1].strip()}" for m in opt_matches]
            q_type = "MCQ"
        else:
            q_type = "NAT" if re.match(r'^-?\d+(\.\d+)?$', correct_ans) else "MCQ"

        # Question text: everything before options or answer
        clean_text = re.split(r'(?:[A-D]\)|Ans(?:wer)?[\:\-])', block)[0].strip()

        add_dpp_question(
            dpp_set_id=dpp_id,
            question_text=clean_text or block[:200],
            question_type=q_type,
            options_json=json.dumps(options),
            correct_answer=correct_ans,
            marks=1.0 if q_type == "MCQ" else 2.0,
            negative_marks=0.33 if q_type == "MCQ" else 0.0,
            explanation="Extracted from uploaded practice sheet.",
            formula_hint="",
            concept_tested=topic or "Engineering Practice"
        )
        count += 1

    # Update count
    conn = get_db_connection()
    conn.execute("UPDATE dpp_sets SET total_questions = ? WHERE id = ?", (count, dpp_id))
    conn.commit()
    conn.close()
    return dpp_id

def evaluate_dpp_submission(
    dpp_set_id: int,
    user_answers: Dict[str, Any], # {str(q_id): user_answer}
    time_taken_sec: int,
    auto_log_mistakes: bool = True
) -> Dict[str, Any]:
    """
    Evaluates student DPP responses, calculates score and accuracy,
    and logs errors into the Mistake Intelligence system.
    """
    questions = get_dpp_questions(dpp_set_id)
    total_marks = sum(q["marks"] for q in questions)
    score = 0.0
    correct_cnt = 0
    wrong_cnt = 0
    mistakes_logged = 0

    results_detail = []

    for q in questions:
        qid_str = str(q["id"])
        submitted = user_answers.get(qid_str, "").strip()
        correct_ref = q["correct_answer"].strip()
        q_type = q["question_type"]

        is_correct = False
        if not submitted:
            is_attempted = False
        else:
            is_attempted = True
            if q_type == "MCQ":
                is_correct = (submitted.upper() == correct_ref.upper())
            elif q_type == "MSQ":
                try:
                    ref_list = sorted(json.loads(correct_ref))
                    sub_list = sorted(json.loads(submitted) if isinstance(submitted, list) else [s.strip() for s in submitted.split(",")])
                    is_correct = (ref_list == sub_list)
                except Exception:
                    is_correct = (submitted.upper() == correct_ref.upper())
            elif q_type == "NAT":
                try:
                    is_correct = abs(float(submitted) - float(correct_ref)) < 0.05
                except ValueError:
                    is_correct = False

        if is_attempted:
            if is_correct:
                score += q["marks"]
                correct_cnt += 1
            else:
                score -= q["negative_marks"]
                wrong_cnt += 1
                if auto_log_mistakes:
                    # Categorize mistake
                    cat = "Calculation" if q_type == "NAT" else "Concept"
                    log_mistake(
                        question_text=q["question_text"],
                        user_answer=str(submitted),
                        correct_answer=str(correct_ref),
                        mistake_category=cat,
                        subject_id=None,
                        source="dpp_practice"
                    )
                    mistakes_logged += 1

        results_detail.append({
            "question_id": q["id"],
            "question_text": q["question_text"],
            "question_type": q_type,
            "submitted": submitted,
            "correct_answer": correct_ref,
            "is_correct": is_correct,
            "is_attempted": is_attempted,
            "explanation": q["explanation"]
        })

    accuracy = round((correct_cnt / max(1, (correct_cnt + wrong_cnt))) * 100, 1)
    final_score = max(0.0, round(score, 2))

    attempt_id = save_dpp_attempt(
        dpp_set_id=dpp_set_id,
        score=final_score,
        max_score=total_marks,
        accuracy=accuracy,
        time_taken_sec=time_taken_sec,
        answers_json=json.dumps(user_answers),
        mistakes_logged=mistakes_logged
    )

    return {
        "attempt_id": attempt_id,
        "score": final_score,
        "max_score": total_marks,
        "accuracy": accuracy,
        "correct_count": correct_cnt,
        "wrong_count": wrong_cnt,
        "unattempted_count": len(questions) - (correct_cnt + wrong_cnt),
        "mistakes_logged": mistakes_logged,
        "details": results_detail
    }
