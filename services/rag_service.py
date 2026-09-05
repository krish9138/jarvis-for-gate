import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import config
from database.queries import (
    save_document,
    update_document_chunk_count,
    get_document_by_id,
    get_all_documents,
    delete_chunks_by_doc_id,
    save_document_chunks,
    get_chunks_for_retrieval
)
from .extractor_service import extract_document_text
from .chunker_service import chunk_text
from .vector_service import generate_embedding, rank_chunks

def ingest_document(
    file_bytes: bytes, 
    original_filename: str, 
    subject_id: Optional[int] = None, 
    doc_type: str = "Notes"
) -> Tuple[bool, str, Optional[int]]:
    """
    Complete ingestion pipeline:
    Save file -> Extract text -> Chunk -> Generate Embeddings -> Save to SQLite.
    Returns: (success: bool, message: str, doc_id: Optional[int])
    """
    try:
        # 1. Determine file extension and generate safe storage filename
        file_ext = Path(original_filename).suffix.lower().replace(".", "")
        if not file_ext:
            file_ext = "txt"

        safe_filename = f"{uuid.uuid4().hex[:8]}_{Path(original_filename).stem}.{file_ext}"
        saved_file_path = config.DOCUMENTS_DIR / safe_filename

        # Write to disk
        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        file_size_bytes = len(file_bytes)

        # 2. Extract text page by page
        pages = extract_document_text(str(saved_file_path), file_ext)
        if not pages or all(len(p.get("text", "").strip()) == 0 for p in pages):
            return (False, f"No extractable text found in '{original_filename}'. Check if it is a scanned image without OCR.", None)

        page_count = len(pages)

        # 3. Save document record in DB
        doc_id = save_document(
            filename=safe_filename,
            original_name=original_filename,
            file_type=file_ext,
            subject_id=subject_id,
            doc_type=doc_type,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            file_path=str(saved_file_path)
        )

        # 4. Chunk text
        chunks = chunk_text(pages, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
        if not chunks:
            # Single fallback chunk
            full_text = "\n\n".join([p["text"] for p in pages if p["text"]])
            chunks = [{
                "chunk_index": 0,
                "page_number": 1,
                "section_title": "Full Document",
                "content": full_text[:1000],
                "char_count": len(full_text)
            }]

        # 5. Generate embeddings and prepare DB batch
        chunks_to_save = []
        for c in chunks:
            emb = generate_embedding(c["content"], is_query=False)
            chunks_to_save.append({
                "doc_id": doc_id,
                "chunk_index": c["chunk_index"],
                "page_number": c.get("page_number", 1),
                "section_title": c.get("section_title", ""),
                "content": c["content"],
                "embedding_json": json.dumps(emb)
            })

        # 6. Save chunks to SQLite
        save_document_chunks(chunks_to_save)
        update_document_chunk_count(doc_id, len(chunks_to_save))

        return (True, f"Successfully ingested '{original_filename}' ({page_count} pages, {len(chunks_to_save)} chunks indexed).", doc_id)

    except Exception as e:
        return (False, f"Ingestion error: {str(e)}", None)


def reindex_document(doc_id: int) -> Tuple[bool, str]:
    """
    Re-extracts, re-chunks, and re-embeds an existing document.
    """
    doc = get_document_by_id(doc_id)
    if not doc:
        return (False, f"Document ID {doc_id} not found.")

    file_path = doc["file_path"]
    if not os.path.exists(file_path):
        return (False, f"Document file missing at {file_path}.")

    try:
        # 1. Delete old chunks
        delete_chunks_by_doc_id(doc_id)

        # 2. Extract
        pages = extract_document_text(file_path, doc["file_type"])
        
        # 3. Chunk
        chunks = chunk_text(pages, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)

        # 4. Re-embed
        chunks_to_save = []
        for c in chunks:
            emb = generate_embedding(c["content"], is_query=False)
            chunks_to_save.append({
                "doc_id": doc_id,
                "chunk_index": c["chunk_index"],
                "page_number": c.get("page_number", 1),
                "section_title": c.get("section_title", ""),
                "content": c["content"],
                "embedding_json": json.dumps(emb)
            })

        # 5. Save
        save_document_chunks(chunks_to_save)
        update_document_chunk_count(doc_id, len(chunks_to_save))

        return (True, f"Re-indexed '{doc['original_name']}': {len(chunks_to_save)} chunks updated.")
    except Exception as e:
        return (False, f"Re-indexing failed: {str(e)}")


def query_knowledge_base(
    query: str, 
    top_k: int = config.TOP_K_RESULTS, 
    subject_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Performs semantic retrieval across all indexed chunks in the Knowledge Base.
    Returns ranked chunk matches.
    """
    chunks = get_chunks_for_retrieval(subject_id=subject_id)
    if not chunks:
        return []

    # Generate query embedding
    query_vector = generate_embedding(query, is_query=True)

    # Rank chunks
    ranked = rank_chunks(query, query_vector, chunks, top_k=top_k)
    return ranked


def build_rag_context_and_prompt(
    user_query: str, 
    retrieved_chunks: List[Dict[str, Any]],
    similarity_threshold: float = config.SIMILARITY_THRESHOLD
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Constructs the grounded RAG prompt and filters sources above similarity threshold.
    Strictly instructs the model:
    - Prefer uploaded notes when relevant.
    - Do not invent information.
    - If not present in documents, explicitly say so before providing general engineering knowledge.
    """
    valid_sources = [c for c in retrieved_chunks if c["similarity_score"] >= similarity_threshold]

    if not valid_sources:
        rag_prompt = f"""The student asked: "{user_query}"

NOTE: No relevant notes or matching documents were found in the uploaded Knowledge Base for this query.

INSTRUCTIONS:
1. Clearly inform the student: "⚠️ **Note**: This specific topic is not found in your uploaded knowledge base documents."
2. Then, provide a comprehensive, first-principles Mechanical Engineering explanation based on standard GATE curriculum knowledge.
3. Maintain your signature GATE JARVIS rigor, mathematical derivations, GATE trap warnings, and 1 check-for-understanding question.
"""
        return rag_prompt, []

    # Assemble knowledge base context with explicit track classification
    context_blocks = []
    for idx, s in enumerate(valid_sources, 1):
        subj_name = s.get('subject_name', 'General')
        track = "College / Allied Track" if any(k in subj_name.lower() for k in ["ict", "satellite", "graphics", "safety", "electrical", "civil"]) else "GATE ME Core Track"
        context_blocks.append(
            f"--- [SOURCE {idx}]: Document: '{s['doc_name']}' | Subject: {subj_name} [{track}] | Page: {s['page_number']} | Relevance: {int(s['similarity_score'] * 100)}% ---\n"
            f"{s['content']}"
        )

    full_context = "\n\n".join(context_blocks)

    rag_prompt = f"""You are answering a question using the student's **Uploaded Personal Knowledge Base** for GATE Mechanical Engineering (AIR < 100 Mission).

=== UPLOADED KNOWLEDGE BASE CONTEXT ===
{full_context}
=======================================

STUDENT'S QUESTION:
"{user_query}"

MANDATORY PROVENANCE ARCHITECTURE (Audit F-01 & F-22):
Structure your response into these 3 explicit sections:

### 📚 FROM YOUR UPLOADED NOTES
- Cite the exact document title(s) and page number(s) where applicable.
- Quote or summarize what is directly found in the student's materials.
- If the document is from College/Allied track (e.g. ICT, Graphics), clarify its connection or distinction from core GATE ME topics.

### ⚙️ FROM VERIFIED GATE SYLLABUS
- Provide standard GATE Mechanical Engineering concepts, formulas (LaTeX), sign conventions, and standard assumptions not covered in the uploaded note.

### 💡 AI-GENERATED EXPLANATION & EXAM INSIGHTS
- Explain physics intuition and common GATE traps/calculation blunders.
- End with exactly 1 diagnostic Check-for-Understanding question to test active recall.
"""
    return rag_prompt, valid_sources
