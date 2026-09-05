import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.connection import init_db, get_db_connection
from database.queries import (
    get_all_subjects, 
    add_subject, 
    get_all_documents,
    create_test_set,
    add_test_question
)
from services.rag_service import ingest_document

def run_drawing_ingestion_part5():
    init_db()
    print("=== Ingesting Lectures 02 to 06 Engineering Drawing & Design Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    drawing_subject_id = subjects.get(drawing_subject_name) or subjects.get("Engineering Graphics")
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "Drawing_Lecture_02_Conic_Sections_and_Eccentricity.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_03_04_Special_Curves_Cycloids_Involutes_Spirals.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_05_06_Engineering_Scales_Plain_Diagonal_Vernier.txt",
            "doc_type": "Lecture Notes"
        }
    ]

    for item in docs_to_ingest:
        fname = item["filename"]
        file_path = Path("data") / "documents" / fname
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        success, msg, doc_id = ingest_document(
            file_bytes=file_bytes,
            original_filename=fname,
            subject_id=drawing_subject_id,
            doc_type=item["doc_type"]
        )
        print(f"[{'SUCCESS' if success else 'FAILED'}] {fname} -> {msg} (Doc ID: {doc_id})")

    # 3. Create Test Set for Conics, Curves & Scales
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Conics, Curves & Scales%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_conics_title = "Engineering Drawing: Conics, Special Curves & Scales Mastery"
    if t_conics_title not in existing_tests:
        t_id = create_test_set(
            title=t_conics_title,
            subject_id=drawing_subject_id,
            question_count=8,
            duration_minutes=20,
            description="Practice questions on Conic eccentricity, Cycloids, Cardioid, Involutes, Spirals, and Scale calculations (Plain, Diagonal, Vernier, RF)."
        )

        q_list = [
            {
                "q": "The point of a parabola which is closest to its focus is known as the:",
                "opts": ["Vertex", "Latus rectum", "Directrix", "Center"],
                "ans": "a",
                "exp": "The vertex is the intersection point of the conic with its principal axis and lies closest to the focus."
            },
            {
                "q": "When a generating circle rolls without slipping along the inside of a directing circle whose diameter is twice that of the generating circle, the path traced by a point on its circumference is:",
                "opts": ["An ellipse", "A cardioid", "A straight line", "A parabola"],
                "ans": "c",
                "exp": "By the Tusi couple theorem, when R = 2r (or D_directing = 2 * D_generating), the hypocycloid degenerates into a straight line."
            },
            {
                "q": "What is the curve traced out by a point on the circumference of a circle rolling outside another circle of the SAME diameter?",
                "opts": ["Cycloid", "Cardioid", "Hypocycloid", "Involute"],
                "ans": "b",
                "exp": "When generating circle radius r equals directing circle radius R, an epicycloid forms a Cardioid (heart-shaped curve, theta = 360 deg)."
            },
            {
                "q": "In an Archimedean spiral, which of the following properties is strictly constant?",
                "opts": ["The ratio of consecutive radius vectors", "The difference between consecutive radius vectors", "The radius of curvature", "The linear acceleration"],
                "ans": "b",
                "exp": "In Archimedean spirals, r1 - r2 = r2 - r3 = constant. (In logarithmic spirals, the ratio is constant)."
            },
            {
                "q": "A rectangular plot of land having an area of 0.45 hectare is represented by a rectangle of area 5 sq. cm on a map. What is the Representative Fraction (R.F.) of the scale?",
                "opts": ["1:3000", "3:1000", "1:125", "1:30000"],
                "ans": "a",
                "exp": "1 hectare = 10^4 m^2 => 0.45 hectare = 4500 m^2 = 4500 * 10^4 cm^2. RF = sqrt(5 / 4.5*10^7) = sqrt(1 / 9*10^6) = 1/3000."
            },
            {
                "q": "Which type of scale is used to measure or construct angles when a protractor is not available?",
                "opts": ["Plain scale", "Diagonal scale", "Comparative scale", "Scale of chords"],
                "ans": "d",
                "exp": "Scale of chords is specially designed to measure and layout angles geometrically without a protractor."
            },
            {
                "q": "In a direct (forward) Vernier scale with 'n' divisions, 'n' Vernier scale divisions are equal to:",
                "opts": ["(n - 1) main scale divisions", "(n + 1) main scale divisions", "n main scale divisions", "2n main scale divisions"],
                "ans": "a",
                "exp": "Direct Vernier: n VSD = (n - 1) MSD; Retrograde Vernier: n VSD = (n + 1) MSD."
            },
            {
                "q": "The curve traced out by the free end of a thread unwound tautly from a circle or polygon is called:",
                "opts": ["Cycloid", "Epicycloid", "Involute", "Archimedean spiral"],
                "ans": "c",
                "exp": "An involute is generated by unwinding a taut, flexible string from a base circle or polygon."
            }
        ]

        for q in q_list:
            add_test_question(
                test_set_id=t_id,
                question_text=q["q"],
                options=q["opts"],
                correct_answer=q["ans"],
                explanation=q["exp"]
            )
        print(f"Created Test Set: '{t_conics_title}' with {len(q_list)} questions.")

    print("=== Ingestion of Lectures 02-06 Completed! ===")

if __name__ == "__main__":
    run_drawing_ingestion_part5()
