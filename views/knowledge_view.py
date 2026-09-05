import os
import streamlit as st
from database.queries import (
    get_all_subjects,
    get_all_documents,
    get_document_by_id,
    delete_document,
    get_chunks_for_retrieval
)
from services.rag_service import ingest_document, reindex_document, query_knowledge_base
from services.vector_service import LocalSemanticVectorizer
import config

def format_file_size(size_bytes: int) -> str:
    """Formats bytes to KB / MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def render_knowledge_view():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="margin: 0;">📖 Knowledge Base & Document Library</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">
                Upload your GATE notes, PDFs, DOCX files, PYQs, and textbooks. JARVIS will index and vectorize them for intelligent instant retrieval.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Summary Metrics
    all_docs = get_all_documents()
    total_chunks = sum(d["chunk_count"] for d in all_docs)
    total_pages = sum(d["page_count"] for d in all_docs)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📚 Uploaded Documents", len(all_docs))
    m2.metric("🧩 Indexed Chunks", total_chunks)
    m3.metric("📄 Total Pages", total_pages)
    m4.metric("⚡ Vector Engine", "Hybrid Cosine / Cloud")

    st.markdown("---")

    # 2. Main Tabs
    tab_upload, tab_library, tab_intel, tab_search = st.tabs([
        "📤 Upload & Ingest", 
        "📂 Document Library",
        "🧠 Notes Intelligence & Artifacts",
        "🔍 Semantic Search Explorer"
    ])

    # -------------------------------------------------------------
    # TAB 1: UPLOAD & INGEST
    # -------------------------------------------------------------
    with tab_upload:
        st.subheader("📤 Upload New Study Materials")
        st.caption("Supported formats: **PDF (.pdf)**, **Word (.docx)**, **Text (.txt, .md)**")

        subjects = get_all_subjects()
        subject_options = {s["name"]: s["id"] for s in subjects}
        subject_options["General / Multi-Subject"] = None

        col_left, col_right = st.columns([2, 1])

        with col_right:
            st.markdown("#### 🏷️ Document Metadata")
            selected_subject_name = st.selectbox(
                "Assign Subject",
                options=list(subject_options.keys()),
                index=0
            )
            selected_subject_id = subject_options[selected_subject_name]

            doc_type = st.selectbox(
                "Document Type",
                options=["Notes", "PYQ / Questions", "DPP / Assignment", "Formula Sheet", "Textbook", "Syllabus"],
                index=0
            )

            st.info(
                "💡 **Tip**: Tagging by subject helps JARVIS prioritize specific formulas when you solve subject-wise DPPs and mock tests!"
            )

        with col_left:
            uploaded_files = st.file_uploader(
                "Choose files to ingest into your Knowledge Base",
                type=["pdf", "docx", "txt", "md"],
                accept_multiple_files=True
            )

            if uploaded_files:
                st.write(f"📁 Selected **{len(uploaded_files)}** file(s) for ingestion.")
                if st.button("🚀 Process & Index Documents", type="primary", use_container_width=True):
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()
                    success_count = 0

                    for idx, file in enumerate(uploaded_files):
                        status_text.text(f"Extracting & chunking: {file.name}...")
                        file_bytes = file.getvalue()
                        
                        success, message, doc_id = ingest_document(
                            file_bytes=file_bytes,
                            original_filename=file.name,
                            subject_id=selected_subject_id,
                            doc_type=doc_type
                        )

                        if success:
                            success_count += 1
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {file.name}: {message}")

                        progress_bar.progress((idx + 1) / len(uploaded_files))

                    status_text.text(f"Done! Successfully processed {success_count} / {len(uploaded_files)} files.")
                    st.rerun()

    # -------------------------------------------------------------
    # TAB 2: DOCUMENT LIBRARY
    # -------------------------------------------------------------
    with tab_library:
        st.subheader("📂 Uploaded Knowledge Base Documents")

        if not all_docs:
            st.info("No documents uploaded yet. Go to the **Upload & Ingest** tab to add your first GATE notes or textbook!")
        else:
            # Filter bar
            filter_col1, filter_col2 = st.columns([2, 1])
            with filter_col1:
                search_filter = st.text_input("🔍 Filter documents by name...", placeholder="e.g. Bernoulli, Pressure Vessels, SOM...")
            with filter_col2:
                subject_filter = st.selectbox(
                    "Filter by Subject", 
                    options=["All Subjects"] + [s["name"] for s in subjects]
                )

            filtered_docs = all_docs
            if search_filter:
                filtered_docs = [d for d in filtered_docs if search_filter.lower() in d["original_name"].lower()]
            if subject_filter != "All Subjects":
                filtered_docs = [d for d in filtered_docs if d["subject_name"] == subject_filter]

            st.caption(f"Showing {len(filtered_docs)} of {len(all_docs)} documents.")

            # Display Documents
            for doc in filtered_docs:
                with st.container():
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        type_icons = {"pdf": "📄 PDF", "docx": "📝 DOCX", "txt": "📃 TXT", "md": "📑 Markdown"}
                        icon_str = type_icons.get(doc["file_type"], "📄")
                        
                        st.markdown(f"#### {icon_str} **{doc['original_name']}**")
                        st.markdown(
                            f"🏷️ **Subject**: `{doc['subject_name']}` &nbsp;|&nbsp; "
                            f"📂 **Type**: `{doc['doc_type']}` &nbsp;|&nbsp; "
                            f"📄 **Pages**: `{doc['page_count']}` &nbsp;|&nbsp; "
                            f"🧩 **Chunks**: `{doc['chunk_count']}` &nbsp;|&nbsp; "
                            f"💾 **Size**: `{format_file_size(doc['file_size_bytes'])}` &nbsp;|&nbsp; "
                            f"🕒 **Date**: `{doc['uploaded_at'][:16]}`"
                        )

                    with col_actions:
                        c_reindex, c_delete = st.columns(2)
                        with c_reindex:
                            if st.button("🔄 Re-Index", key=f"reindex_{doc['id']}", help="Re-chunk and regenerate embeddings"):
                                with st.spinner("Re-indexing..."):
                                    ok, msg = reindex_document(doc["id"])
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

                        with c_delete:
                            if st.button("🗑️ Delete", key=f"del_{doc['id']}", type="secondary", help="Delete document and its vector chunks"):
                                delete_document(doc["id"])
                                # Delete physical file if exists
                                if os.path.exists(doc["file_path"]):
                                    try:
                                        os.remove(doc["file_path"])
                                    except Exception:
                                        pass
                                st.success(f"Deleted '{doc['original_name']}'")
                                st.rerun()

                    st.markdown("<hr style='margin: 8px 0; border-color: #334155;'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: NOTES INTELLIGENCE & MULTI-ARTIFACTS
    # -------------------------------------------------------------
    with tab_intel:
        st.subheader("🧠 Notes Intelligence: Deep Multi-Artifact Synthesis")
        st.caption("Never just store documents in RAG. Automatically synthesize 2-page executive notes, formula sheets, active recall flashcards, and linked practice DPPs for any document.")

        if not all_docs:
            st.info("No documents uploaded yet.")
        else:
            from services.notes_intel_service import generate_notes_intelligence
            import json

            doc_map = {f"{d['original_name']} ({d['subject_name']})": d["id"] for d in all_docs}
            sel_doc_label = st.selectbox("Select Document to Analyze & Generate Artifacts:", list(doc_map.keys()))
            sel_doc_id = doc_map[sel_doc_label]

            c_gen, _ = st.columns([0.4, 0.6])
            with c_gen:
                if st.button("⚡ Generate / Refresh Artifacts", use_container_width=True):
                    with st.spinner("Synthesizing Notes Intelligence..."):
                        generate_notes_intelligence(sel_doc_id)
                        st.success("Artifacts generated successfully!")
                        st.rerun()

            artifacts = generate_notes_intelligence(sel_doc_id)

            if artifacts:
                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📄 2-Page Executive Summary", "📐 High-Yield Formula Sheet", "🃏 Generated Flashcards & DPP"])
                with sub_tab1:
                    st.markdown(artifacts.get("summary_md", "Summary not generated."))
                with sub_tab2:
                    st.markdown(artifacts.get("formula_sheet_md", "Formula sheet not generated."))
                with sub_tab3:
                    st.markdown("#### 🃏 Generated Active Recall Cards")
                    try:
                        fc_list = json.loads(artifacts.get("flashcards_json", "[]"))
                        for fc in fc_list:
                            with st.expander(f"Card: {fc.get('front')[:60]}..."):
                                st.markdown(f"**Prompt**: {fc.get('front')}")
                                st.markdown(f"**Answer**: {fc.get('back')}")
                                st.caption(f"Type: `{fc.get('card_type')}`")
                    except Exception:
                        st.write(artifacts.get("flashcards_json"))

                    if artifacts.get("dpp_set_id"):
                        st.success(f"✅ Dedicated Practice DPP generated with ID #{artifacts['dpp_set_id']}. Practice this in the **📝 DPP & Practice Lab**!")

    # -------------------------------------------------------------
    # TAB 4: SEMANTIC SEARCH & CHUNK EXPLORER
    # -------------------------------------------------------------
    with tab_search:
        st.subheader("🔍 Semantic Search & Chunk Explorer")
        st.caption("Inspect how the vector database indexes your notes and tests semantic similarity scores.")

        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            test_query = st.text_input(
                "Enter a search query or engineering question:",
                value="Explain Bernoulli's equation",
                placeholder="e.g. Euler buckling load, Thin cylinder shear stress, Lame equation..."
            )
        with search_col2:
            top_k_select = st.slider("Top Results (k)", min_value=1, max_value=8, value=4)

        if test_query:
            with st.spinner("Executing hybrid semantic search..."):
                results = query_knowledge_base(test_query, top_k=top_k_select)

            if not results:
                st.warning("No matching chunks found in the Knowledge Base. Upload some documents first!")
            else:
                st.markdown(f"### 🎯 Top {len(results)} Retrieved Chunks:")
                
                for idx, res in enumerate(results, 1):
                    relevance_pct = int(res["similarity_score"] * 100)
                    
                    with st.expander(
                        f"#{idx} | {res['doc_name']} (Page {res['page_number']}) — Relevance: {relevance_pct}% [Vector: {int(res['cosine_similarity']*100)}%, Lexical: {int(res['keyword_match']*100)}%]",
                        expanded=(idx == 1)
                    ):
                        st.markdown(f"**Document**: `{res['doc_name']}` | **Subject**: `{res['subject_name']}` | **Section**: `{res['section_title']}`")
                        st.markdown(f"```text\n{res['content']}\n```")
