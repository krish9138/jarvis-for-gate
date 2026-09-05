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

def run_drawing_ingestion_part3():
    init_db()
    print("=== Ingesting Lectures 11 to 16 Engineering Drawing & Design Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    drawing_subject_id = subjects.get(drawing_subject_name) or subjects.get("Engineering Graphics")
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "Drawing_Lecture_11_Projection_of_Points_and_Quadrants.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_13_14_15_Projection_of_Lines_Traces_and_Trapezoid_Method.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_16_Auxiliary_Planes_and_Projections.txt",
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

    # 3. Create Test Set for Points, Lines & Auxiliary Planes
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Points, Lines%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_lines_title = "Engineering Drawing: Points, Lines & Auxiliary Planes Mastery"
    if t_lines_title not in existing_tests:
        t_id = create_test_set(
            title=t_lines_title,
            subject_id=drawing_subject_id,
            question_count=8,
            duration_minutes=20,
            description="Practice questions on Quadrant projections of points, True length and traces of lines, Trapezoid method, and Auxiliary planes (AIP, AVP, PP)."
        )

        q_list = [
            {
                "q": "If the elevation (front view) of a point P is 40 mm above the xy line and its top view is 50 mm below the xy line, what is the position of the point in space?",
                "opts": ["40 mm above HP and 50 mm in front of VP (1st Quadrant)", "40 mm below HP and 50 mm behind VP (3rd Quadrant)", "40 mm above HP and 50 mm behind VP (2nd Quadrant)", "40 mm below HP and 50 mm in front of VP (4th Quadrant)"],
                "ans": "a",
                "exp": "Elevation above xy means Above HP (40 mm). Plan below xy means In front of VP (50 mm) -> 1st Quadrant."
            },
            {
                "q": "A point P is 35 mm in front of VP and lies in the 1st quadrant. If its shortest distance from the intersection line of HP and VP (xy reference line) is 42 mm, how far is P above the HP?",
                "opts": ["sqrt(539) mm (~23.2 mm)", "sqrt(593) mm", "sqrt(395) mm", "sqrt(935) mm"],
                "ans": "a",
                "exp": "Shortest distance = sqrt(h^2 + d^2) => 42^2 = h^2 + 35^2 => h = sqrt(1764 - 1225) = sqrt(539) mm."
            },
            {
                "q": "When a straight line is inclined to both HP and VP and contained by a profile plane, what is the relationship between its true inclinations theta and phi?",
                "opts": ["theta + phi = 90°", "theta + phi = 180°", "theta = phi = 45°", "theta + phi < 90°"],
                "ans": "a",
                "exp": "Since the profile plane is perpendicular to both HP and VP, any line lying entirely within it satisfies theta + phi = 90°."
            },
            {
                "q": "In projection of lines, which of the following inequalities is ALWAYS satisfied for a line inclined to both reference planes?",
                "opts": ["alpha > theta and beta > phi", "alpha < theta and beta < phi", "alpha = theta and beta = phi", "alpha + beta = theta + phi"],
                "ans": "a",
                "exp": "Apparent inclination angles (alpha in FV, beta in TV) are always strictly greater than their true inclinations (theta with HP, phi with VP)."
            },
            {
                "q": "What is the view obtained on an Auxiliary Inclined Plane (A.I.P.) called?",
                "opts": ["Auxiliary Front View", "Auxiliary Top View", "Profile View", "Isometric View"],
                "ans": "b",
                "exp": "An A.I.P. is inclined to HP and perpendicular to VP; projection onto it yields the Auxiliary Top View."
            },
            {
                "q": "The trace of any plane surface on a reference plane is always a:",
                "opts": ["Point", "Line", "Curve", "Closed polygon"],
                "ans": "b",
                "exp": "The intersection of two flat planes is always a straight line."
            },
            {
                "q": "A 100 mm long line AB is resting in the HP and inclined to the VP. Its true length will be visible in the:",
                "opts": ["Front View only", "Top View only", "Both Front and Top Views", "Profile View only"],
                "ans": "b",
                "exp": "Since the line lies entirely in the HP (parallel to HP), its Top View (Plan) shows its full True Length (100 mm)."
            },
            {
                "q": "In the Trapezoid Method of determining True Length (TL) from end projectors distance D and coordinate differences delta_h and delta_d, what is the formula for TL?",
                "opts": ["TL = sqrt(D^2 + delta_h^2 + delta_d^2)", "TL = D + delta_h + delta_d", "TL = sqrt(D^2 + delta_h * delta_d)", "TL = sqrt(delta_h^2 + delta_d^2)"],
                "ans": "a",
                "exp": "By 3D Pythagoras theorem: TL^2 = D^2 + (h_B - h_A)^2 + (d_B - d_A)^2."
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
        print(f"Created Test Set: '{t_lines_title}' with {len(q_list)} questions.")

    print("=== Ingestion and Indexing Completed Successfully! ===")

if __name__ == "__main__":
    run_drawing_ingestion_part3()
