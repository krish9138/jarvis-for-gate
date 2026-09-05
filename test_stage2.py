import os
import io
from database.connection import init_db
from database.queries import (
    get_all_documents,
    get_document_by_id,
    delete_document,
    get_study_stats,
    get_all_subjects
)
from services.rag_service import ingest_document, reindex_document, query_knowledge_base
from services.ai_service import get_ai_response
from services.extractor_service import extract_document_text
from services.chunker_service import chunk_text

def run_tests():
    print("=== STARTING STAGE 2 COMPREHENSIVE TESTS ===")
    
    # 1. Test Database & Stats
    stats = get_study_stats()
    print(f"1. Database Stats: Docs={stats['doc_count']}, Chunks={stats['chunk_count']}")
    assert stats["doc_count"] >= 4, "Should have at least 4 documents seeded"
    assert stats["chunk_count"] >= 20, "Should have at least 20 chunks indexed"
    print("   [PASS] Database & Stats Verification")

    # 2. Test Semantic Retrieval for Bernoulli
    print("\n2. Testing Semantic Retrieval: 'Explain Bernoulli equation'")
    results_bernoulli = query_knowledge_base("Explain Bernoulli's equation", top_k=3)
    assert len(results_bernoulli) > 0, "Should retrieve at least 1 chunk for Bernoulli"
    print(f"   Top Match: {results_bernoulli[0]['doc_name']} (Page {results_bernoulli[0]['page_number']}) - Score: {results_bernoulli[0]['similarity_score']}")
    assert "Bernoulli" in results_bernoulli[0]['doc_name'] or "Fluid" in results_bernoulli[0]['doc_name']
    print("   [PASS] Bernoulli's Equation Retrieval")

    # 3. Test Semantic Retrieval for Lame's Equations
    print("\n3. Testing Semantic Retrieval: 'Lame equation for thick cylinders'")
    results_lame = query_knowledge_base("Lame's equation thick cylinders", top_k=3)
    assert len(results_lame) > 0
    print(f"   Top Match: {results_lame[0]['doc_name']} - Score: {results_lame[0]['similarity_score']}")
    assert "Thick" in results_lame[0]['doc_name'] or "SOM" in results_lame[0]['doc_name']
    print("   [PASS] Thick Cylinder / Lame's Equation Retrieval")

    # 4. Test Semantic Retrieval for Pure Shear in Pressure Vessels
    print("\n4. Testing Semantic Retrieval: 'Pure shear in thin cylindrical tank'")
    results_shear = query_knowledge_base("Pure shear in thin cylindrical tank", top_k=3)
    assert len(results_shear) > 0
    print(f"   Top Match: {results_shear[0]['doc_name']} - Score: {results_shear[0]['similarity_score']}")
    print("   [PASS] Pure Shear Retrieval")

    # 5. Test AI RAG Response Generation & Sources Output
    print("\n5. Testing AI RAG Pipeline with Sources Used")
    messages = [{"role": "user", "content": "Explain Bernoulli's equation and its assumptions"}]
    response, sources = get_ai_response(messages, use_rag=True)
    print(f"   Response Length: {len(response)} chars")
    print(f"   Sources Count: {len(sources)}")
    assert len(sources) > 0, "RAG pipeline should return citation sources"
    print(f"   Source 1: {sources[0]['doc_name']}, Page: {sources[0]['page_number']}")
    print("   [PASS] AI RAG Response & Sources Citations")

    # 6. Test In-memory Ingestion, Re-indexing, and Deletion
    print("\n6. Testing Document Ingestion Lifecycle (Ingest -> Reindex -> Delete)")
    sample_text = b"# Thermodynamics First Law Notes\nFor a closed system undergoing a cycle, net heat transfer equals net work done: \xef\xbf\xbdQ = \xef\xbf\xbdW.\n\nFor a process: dQ = dU + dW.\nInternal energy U is a point function and extensive property."
    success, msg, temp_doc_id = ingest_document(
        file_bytes=sample_text,
        original_filename="Test_Thermo_Notes.txt",
        subject_id=1,
        doc_type="Notes"
    )
    assert success, f"Ingestion failed: {msg}"
    print(f"   Ingested temp document: ID={temp_doc_id}")

    # Reindex
    reindex_ok, reindex_msg = reindex_document(temp_doc_id)
    assert reindex_ok, f"Reindex failed: {reindex_msg}"
    print(f"   Re-indexed temp document: {reindex_msg}")

    # Delete
    del_ok = delete_document(temp_doc_id)
    assert del_ok, "Failed to delete temp document"
    print(f"   Deleted temp document: ID={temp_doc_id}")
    print("   [PASS] Document Ingestion, Reindex, and Deletion Lifecycle")

    print("\n=== ALL STAGE 2 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
