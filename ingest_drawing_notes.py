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

def run_drawing_ingestion():
    init_db()
    print("=== Starting Ingestion of ESE/GATE Engineering Drawing & Design Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    if drawing_subject_name not in subjects:
        # Check if 'Engineering Graphics' exists
        if "Engineering Graphics" in subjects:
            drawing_subject_id = subjects["Engineering Graphics"]
        else:
            print(f"Adding Subject: '{drawing_subject_name}'...")
            add_subject(drawing_subject_name, category="ESE General Studies & Drawing", target_hours=30.0)
            subjects = {s["name"]: s["id"] for s in get_all_subjects()}
            drawing_subject_id = subjects.get(drawing_subject_name)
    else:
        drawing_subject_id = subjects.get(drawing_subject_name)
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "Drawing_Lecture_22_Development_and_Intersection_of_Surfaces.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_23_Axonometric_Isometric_Projections_and_Dimensioning.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_24_Sheet_Sizes_Pencils_Instruments_and_Polygons.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_25_26_ESE_PYQs_and_Core_Concepts_2017_2026.txt",
            "doc_type": "PYQ Bank & Notes"
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

    # 3. Create Test Sets for Drawing Practice
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Engineering Drawing%' OR title LIKE '%Drawing%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    # ESE Drawing PYQ Mock Test
    t_drawing_title = "UPSC ESE Engineering Drawing: 2017-2026 PYQs"
    if t_drawing_title not in existing_tests:
        t_id = create_test_set(
            title=t_drawing_title,
            subject_id=drawing_subject_id,
            question_count=10,
            duration_minutes=25,
            description="Comprehensive PYQ test covering Scales (RF), Oblique/Isometric Projections, Conic Sections, Traces of Lines, and Development of Solids."
        )

        q_list = [
            {
                "q": "In a plain scale, if 1.5 inches = 1 foot and it can measure up to 4 feet, what is the representative fraction (R.F.) of the scale?",
                "opts": ["1/8", "1/4", "1/1.5", "1/2"],
                "ans": "a",
                "exp": "RF = Drawing Size / Actual Size = 1.5 in / (1 ft * 12 in/ft) = 1.5 / 12 = 1/8."
            },
            {
                "q": "If the development of the lateral surface of a right cone is a semicircle, what is the relation between the slant height and base diameter?",
                "opts": ["Slant height < base diameter", "Slant height > base diameter", "Slant height = base diameter", "Slant height > base radius"],
                "ans": "c",
                "exp": "theta = 360 * (r / L). For semicircle theta = 180 deg => 180 = 360 * (r / L) => L = 2r = d."
            },
            {
                "q": "Which line type is used in standard engineering drawing to represent the outlines of adjacent parts or alternative and extreme positions of movable parts?",
                "opts": ["Continuous thick line", "Continuous thin line", "Chain thin double-dashed line", "Dashed thin line"],
                "ans": "c",
                "exp": "Chain thin double-dashed line (Type K) denotes adjacent parts and extreme positions of movable assemblies."
            },
            {
                "q": "A line is inclined to the H.P. and parallel to the V.P. What traces does it possess?",
                "opts": ["No trace", "Only V.T. but no H.T.", "Both H.T. and V.T.", "Only H.T. but no V.T."],
                "ans": "d",
                "exp": "Since it is inclined to HP, it meets HP at a point (Horizontal Trace HT). Since it is parallel to VP, it never intersects VP (no VT)."
            },
            {
                "q": "When a cone resting on its base in HP is cut by a section plane inclined to the axis and parallel to one of its generators, what is the true shape of the section?",
                "opts": ["Ellipse", "Parabola", "Hyperbola", "Circle"],
                "ans": "b",
                "exp": "A section plane parallel to a generator of a cone produces a Parabola."
            },
            {
                "q": "In an oblique projection, when the receding lines are drawn to full size scale (1:1), the projection is known as:",
                "opts": ["Cabinet projection", "Vertical projection", "Cavalier projection", "Isometric projection"],
                "ans": "c",
                "exp": "Cavalier projection uses full-scale receding lines; Cabinet projection uses half-scale (0.5) receding lines."
            },
            {
                "q": "The exact Representative Fraction (R.F.) / foreshortening ratio of an isometric scale is:",
                "opts": ["9/11", "0.815", "0.8165 (sqrt(2)/sqrt(3))", "sqrt(3)/sqrt(2)"],
                "ans": "c",
                "exp": "RF = cos 45 / cos 30 = (1/sqrt(2)) / (sqrt(3)/2) = sqrt(2)/sqrt(3) ~= 0.8165."
            },
            {
                "q": "A string is wound around a hexagonal prism having base side 20 mm and axis 50 mm long, connecting opposite ends of the same longer edge. The minimum length of the string required is:",
                "opts": ["110 mm", "120 mm", "130 mm", "140 mm"],
                "ans": "c",
                "exp": "When unfolded, the perimeter is 6 * 20 = 120 mm. Hypotenuse = sqrt(120^2 + 50^2) = sqrt(14400 + 2500) = sqrt(16900) = 130 mm."
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
        print(f"Created Test Set: '{t_drawing_title}' with {len(q_list)} questions.")

    print("=== Engineering Drawing Ingestion and Indexing Completed! ===")

if __name__ == "__main__":
    run_drawing_ingestion()
