"""
services/spaced_repetition_service.py
-------------------------------------
Adaptive Spaced Repetition & Active Recall Engine for GATE JARVIS 4.0.
Uses modified SuperMemo SM-2 algorithm to schedule review intervals:
Day 0 -> Day 1 -> Day 3 -> Day 7 -> Day 14 -> Day 30 -> Day 60, dynamically
lengthening upon easy recall and shortening upon cognitive lapses.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database.connection import get_db_connection
from database.queries import (
    create_flashcard,
    get_due_flashcards,
    update_flashcard_review,
    get_flashcard_stats
)

def seed_foundational_flashcards():
    """Seeds authentic Mechanical Engineering active recall flashcards if queue is empty."""
    stats = get_flashcard_stats()
    if stats["total_cards"] >= 6:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    def get_subj_id(name):
        cursor.execute("SELECT id FROM subjects WHERE name = ?", (name,))
        r = cursor.fetchone()
        return r["id"] if r else None

    cards = [
        (
            "What is the maximum shear stress theory (Tresca Criterion) formula for yielding?",
            "$\\tau_{\\max} = \\frac{\\sigma_1 - \\sigma_3}{2} = \\frac{\\sigma_y}{2} \\implies (\\sigma_1 - \\sigma_3) = \\sigma_y$. Well suited for ductile materials.",
            get_subj_id("Strength of Materials"),
            "Theories of Failure",
            "formula"
        ),
        (
            "What is the physical meaning of Prandtl Number (Pr) in Heat Transfer?",
            "$\\text{Pr} = \\frac{\\nu}{\\alpha} = \\frac{\\text{Momentum Diffusivity}}{\\text{Thermal Diffusivity}}$. It dictates the relative growth of velocity vs thermal boundary layers.",
            get_subj_id("Heat Transfer"),
            "Boundary Layers",
            "concept"
        ),
        (
            "State Clausius Theorem for any reversible cyclic thermodynamic process.",
            "$\\oint \\frac{\\delta Q_{\\text{rev}}}{T} = 0$. This proves that $\\int \\frac{\\delta Q}{T}$ is independent of path and defines a state property: Entropy ($dS$).",
            get_subj_id("Thermodynamics"),
            "Second Law",
            "definition"
        ),
        (
            "What is the relationship between Mach number (M) and pressure change in compressible duct flow?",
            "$\\frac{dA}{A} = \\frac{dP}{\\rho V^2} (1 - M^2)$. At subsonic ($M < 1$), nozzle converges ($dA < 0$). At supersonic ($M > 1$), nozzle diverges ($dA > 0$).",
            get_subj_id("Fluid Mechanics"),
            "Compressible Flow",
            "formula"
        ),
        (
            "What is the condition for complete balancing of reciprocating masses in IC engines?",
            "Primary forces ($m r \\omega^2 \\cos\\theta$) and secondary forces ($m r \\omega^2 \\frac{\\cos 2\\theta}{n}$) as well as their moments must simultaneously sum to zero.",
            get_subj_id("Theory of Machines"),
            "Balancing",
            "concept"
        ),
        (
            "What is the rank of an $m \\times n$ matrix with linearly independent columns?",
            "The rank equals $n$ (full column rank). The nullity is $n - \\text{rank} = 0$, meaning the only solution to $Ax = 0$ is the trivial zero vector.",
            get_subj_id("Engineering Mathematics"),
            "Linear Algebra",
            "concept"
        )
    ]

    for front, back, s_id, topic, c_type in cards:
        create_flashcard(
            front_prompt=front,
            back_solution=back,
            subject_id=s_id,
            topic=topic,
            card_type=c_type
        )

    conn.close()

def process_card_review(card_id: int, user_rating: str) -> Dict[str, Any]:
    """
    Processes user feedback:
    user_rating: 'again' (fail, 0%), 'hard' (struggled, 60%), 'good' (solid recall, 90%), 'easy' (mastered, 100%).
    """
    valid_ratings = ["again", "hard", "good", "easy"]
    if user_rating not in valid_ratings:
        user_rating = "good"

    update_flashcard_review(card_id, user_rating)
    return {
        "success": True,
        "rating_applied": user_rating,
        "message": f"Review recorded as '{user_rating}'. Memory interval updated!"
    }
