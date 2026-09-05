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
    print("=== Ingesting Lectures 17 to 21 Engineering Drawing & Design Study Materials ===")

    # 1. Ensure Subject exists
    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    drawing_subject_id = subjects.get(drawing_subject_name) or subjects.get("Engineering Graphics")
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    # 2. Ingest Documents into RAG Knowledge Base
    docs_to_ingest = [
        {
            "filename": "Drawing_Lecture_17_Projection_of_Planes_and_Traces.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_18_19_Projection_of_Solids_and_Special_Cases.txt",
            "doc_type": "Lecture Notes"
        },
        {
            "filename": "Drawing_Lecture_20_21_Section_of_Solids_and_Development.txt",
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

    # 3. Create Test Set for Section of Solids & Planes
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM test_sets WHERE title LIKE '%Planes & Section%'")
    existing_tests = {r["title"]: r["id"] for r in cursor.fetchall()}
    conn.close()

    t_sec_title = "Engineering Drawing: Planes, Solids & Sectioning Mastery"
    if t_sec_title not in existing_tests:
        t_id = create_test_set(
            title=t_sec_title,
            subject_id=drawing_subject_id,
            question_count=8,
            duration_minutes=20,
            description="Practice questions on Projection of Planes, Solids of Revolution, Frustum vs Truncated solids, and Sectioning rules (Ribs, Shafts, Hatching)."
        )

        q_list = [
            {
                "q": "Which type of sectional view is most suitable for showing both internal and external features of a symmetrical assembly in a single view?",
                "opts": ["Full section", "Half section", "Broken-out section", "Revolved section"],
                "ans": "b",
                "exp": "Half sections remove one quarter of a symmetrical object, showing internal details on one half and external features on the other."
            },
            {
                "q": "When a cutting plane passes longitudinally through a thin rib or web, how is the rib represented in the sectional view?",
                "opts": ["Hatched with standard 45° section lines", "Left unsectioned (no section lines)", "Drawn in double thick lines", "Hatched with horizontal lines"],
                "ans": "b",
                "exp": "Thin ribs and webs cut longitudinally across their thickness are left unsectioned to avoid false impression of solid thickness."
            },
            {
                "q": "Which of the following machine parts are typically left UNSECTIONED when a cutting plane passes longitudinally along their axes?",
                "opts": ["Screws, bolts, shafts, and gear teeth", "Hollow cylinders and housings", "Flanged pipe connections", "Piston cylinders"],
                "ans": "a",
                "exp": "Standard fasteners and solid shafts (bolts, nuts, studs, shafts, keys, cotters, rivets, gear teeth) are left unsectioned when cut along their axis."
            },
            {
                "q": "When a solid cone is cut by a section plane parallel to its base and the apex portion is removed, the remaining lower solid is called:",
                "opts": ["Truncated cone", "Frustum of a cone", "Oblique cone", "Segmented cone"],
                "ans": "b",
                "exp": "Cutting parallel to the base gives a Frustum; cutting inclined to the base gives a Truncated solid."
            },
            {
                "q": "If a plane is perpendicular to both the Horizontal Plane (HP) and Vertical Plane (VP), in which view is its true shape seen?",
                "opts": ["Front View", "Top View", "Side / Profile View", "Isometric View"],
                "ans": "c",
                "exp": "A profile plane perpendicular to both HP and VP appears as a line in both FV and TV, and reveals its true shape in the Profile (Side) View."
            },
            {
                "q": "What is the true shape of the section when a right circular cone is cut by an auxiliary plane parallel to its profile plane / axis?",
                "opts": ["Ellipse", "Parabola", "Hyperbola", "Circle"],
                "ans": "c",
                "exp": "A plane cutting a cone parallel to its axis produces a Hyperbola (or Rectangular Hyperbola if 2*theta = 90 deg)."
            },
            {
                "q": "A pentagonal prism lying on HP on one of its rectangular faces is cut by a section plane such that the cut surface has the maximum possible number of edges. How many edges does the cut section have?",
                "opts": ["5 edges", "6 edges", "7 edges", "8 edges"],
                "ans": "c",
                "exp": "Cutting through all 5 lateral faces and both 2 end bases yields 5 + 2 = 7 edges."
            },
            {
                "q": "In standard engineering drawing, section (hatching) lines are drawn as continuous thin lines inclined at what angle to the horizontal?",
                "opts": ["30°", "45°", "60°", "90°"],
                "ans": "b",
                "exp": "Standard section hatching lines are drawn at 45° to horizontal and spaced uniformly 2-3 mm apart."
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
        print(f"Created Test Set: '{t_sec_title}' with {len(q_list)} questions.")

    print("=== Lectures 17-21 Ingestion and Indexing Completed! ===")

if __name__ == "__main__":
    run_drawing_ingestion()
