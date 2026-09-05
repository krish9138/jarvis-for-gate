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

def run_drawing_ingestion_part4():
    init_db()
    print("=== Ingesting Lectures 07, 08, 09, 10 & 12 Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    drawing_subject_id = subjects.get(drawing_subject_name) or subjects.get("Engineering Graphics")
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "Drawing_Lecture_07_08_09_10_12_Foundations_of_Projection_and_Lines.txt",
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

    # 3. Create Test Set for Projections Theory & Line Foundations
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Projections Theory%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_proj_title = "Engineering Drawing: Projections Theory & Line Foundations"
    if t_proj_title not in existing_tests:
        t_id = create_test_set(
            title=t_proj_title,
            subject_id=drawing_subject_id,
            question_count=6,
            duration_minutes=15,
            description="Practice questions on Projection classifications (Orthographic vs Oblique vs Perspective), 1st vs 3rd angle view positions, and fundamental line conditions."
        )

        q_list = [
            {
                "q": "In the First Angle projection system, the Right-Hand Side View (R.H.S.V.) of an object is drawn:",
                "opts": ["Above the elevation (Front View)", "Below the elevation", "To the left of the elevation", "To the right of the elevation"],
                "ans": "c",
                "exp": "In 1st angle projection, RHSV is projected on the left profile plane, positioned to the left of the Front View."
            },
            {
                "q": "Why are 2nd and 4th angle projections not practically used in technical engineering drawing?",
                "opts": ["They require 3 scales", "Top View and Front View overlap each other when planes rotate", "They distort circular features", "They are not supported by CAD software"],
                "ans": "b",
                "exp": "When the HP rotates 90° clockwise, in the 2nd quadrant both HP and VP lie above xy, and in the 4th quadrant both lie below xy, resulting in overlapping views."
            },
            {
                "q": "In technical drawing conventions, how is the Top View (Plan) of a point P represented?",
                "opts": ["Capital letter P", "Small letter with dash (p')", "Small letter without dash (p)", "Small letter with double dash (p'')"],
                "ans": "c",
                "exp": "Object = P; Front View (Elevation) = p'; Top View (Plan) = p; Side View = p''."
            },
            {
                "q": "Which type of projection represents the visual appearance of an object as seen by the human eye or a camera, where projectors converge at a single station point?",
                "opts": ["Perspective projection", "Orthographic projection", "Isometric projection", "Oblique projection"],
                "ans": "a",
                "exp": "Perspective (central) projection mimics human vision and photography with converging visual rays."
            },
            {
                "q": "A vertical line AB of length 75 mm is on HP. Another line AC of length 100 mm is on HP and parallel to VP. What is the spatial length of the line joining B and C?",
                "opts": ["120 mm", "125 mm", "130 mm", "135 mm"],
                "ans": "b",
                "exp": "AB is perpendicular to HP and AC lies in HP => angle BAC = 90 deg. Hypotenuse BC = sqrt(75^2 + 100^2) = sqrt(5625 + 10000) = 125 mm."
            },
            {
                "q": "If a line is resting on a plane, its projection on that plane represents:",
                "opts": ["A single point", "The True Length (TL) of the line", "A foreshortened length", "A trace curve"],
                "ans": "b",
                "exp": "A line resting on a plane is parallel to that plane and therefore projects its full True Length onto it."
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
        print(f"Created Test Set: '{t_proj_title}' with {len(q_list)} questions.")

    print("=== Foundations Ingestion and Indexing Completed! ===")

if __name__ == "__main__":
    run_drawing_ingestion_part4()
