import os
from pathlib import Path
from database.connection import init_db, get_db_connection
from database.queries import get_all_subjects, get_all_documents
from services.rag_service import ingest_document

def seed():
    init_db()
    
    docs_to_seed = [
        {
            "filename": "SOM_DPP01_Pressure_Vessels.txt",
            "subject": "Strength of Materials (SOM)",
            "doc_type": "DPP / Assignment"
        },
        {
            "filename": "SOM_DPP02_Thick_Cylinders.txt",
            "subject": "Strength of Materials (SOM)",
            "doc_type": "DPP / Assignment"
        },
        {
            "filename": "SOM_DPP01_Columns.txt",
            "subject": "Strength of Materials (SOM)",
            "doc_type": "DPP / Assignment"
        },
        {
            "filename": "Fluid_Mechanics_Bernoullis_Equation.txt",
            "subject": "Fluid Mechanics & Hydraulics",
            "doc_type": "Notes"
        }
    ]

    subjects = {s["name"]: s["id"] for s in get_all_subjects()}
    existing_docs = {d["original_name"]: d["id"] for d in get_all_documents()}

    print(f"Existing indexed documents: {len(existing_docs)}")

    for item in docs_to_seed:
        fname = item["filename"]
        if fname in existing_docs:
            print(f"Skipping already indexed: {fname}")
            continue

        file_path = Path("data") / "documents" / fname
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        subject_id = subjects.get(item["subject"], None)
        success, msg, doc_id = ingest_document(
            file_bytes=file_bytes,
            original_filename=fname,
            subject_id=subject_id,
            doc_type=item["doc_type"]
        )
        print(f"Ingested {fname}: {msg} (Doc ID: {doc_id})")

if __name__ == "__main__":
    seed()
