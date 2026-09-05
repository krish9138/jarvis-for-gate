import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.connection import init_db
from database.queries import get_all_subjects
from services.rag_service import ingest_document

def run_drawing_ingestion_part6():
    init_db()
    print("=== Ingesting Lecture 01 Engineering Drawing & Design Study Materials ===")

    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    drawing_subject_name = "Engineering Graphics & Design (Drawing & Safety)"
    drawing_subject_id = subjects.get(drawing_subject_name) or subjects.get("Engineering Graphics")
    
    print(f"Subject '{drawing_subject_name}' ID: {drawing_subject_id}")

    fname = "Drawing_Lecture_01_Conic_Sections_Cone_Geometry_and_Degenerate_Conics.txt"
    file_path = Path("data") / "documents" / fname
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    success, msg, doc_id = ingest_document(
        file_bytes=file_bytes,
        original_filename=fname,
        subject_id=drawing_subject_id,
        doc_type="Lecture Notes"
    )
    print(f"[{'SUCCESS' if success else 'FAILED'}] {fname} -> {msg} (Doc ID: {doc_id})")
    print("=== Ingestion Completed! ===")

if __name__ == "__main__":
    run_drawing_ingestion_part6()
