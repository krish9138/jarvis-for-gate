import streamlit as st
from datetime import datetime
from database.queries import (
    get_all_subjects, 
    log_doubt, 
    get_doubts, 
    resolve_doubt, 
    delete_doubt
)
from services.ai_service import get_ai_response

def render_doubt_engine_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">❓ Doubt Engine & Quick Capture</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Log study doubts instantly without breaking your concentration flow. Resolve immediately or batch-solve with AI and grounded RAG notes.
            </p>
        </div>
    """, unsafe_allow_html=True)

    subjects = get_all_subjects()
    subject_map = {s["name"]: s["id"] for s in subjects}
    subject_names = ["General Mechanical"] + [s["name"] for s in subjects]

    # -------------------------------------------------------------
    # 1. QUICK-CAPTURE BAR
    # -------------------------------------------------------------
    with st.container():
        st.markdown("### ⚡ Quick-Capture Doubt")
        with st.form("quick_doubt_form", clear_on_submit=True):
            col_q, col_s, col_btn = st.columns([0.60, 0.25, 0.15])
            with col_q:
                doubt_text = st.text_input(
                    "Doubt Question",
                    placeholder="e.g. Why is longitudinal stress zero in an open-ended thin cylinder?",
                    label_visibility="collapsed"
                )
            with col_s:
                selected_subj_name = st.selectbox(
                    "Subject",
                    options=subject_names,
                    index=0,
                    label_visibility="collapsed"
                )
            with col_btn:
                submit_doubt = st.form_submit_button("📌 Log Doubt", use_container_width=True)

            if submit_doubt:
                if not doubt_text.strip():
                    st.warning("Please enter your question before logging.")
                else:
                    subj_id = subject_map.get(selected_subj_name) if selected_subj_name != "General Mechanical" else None
                    new_id = log_doubt(subject_id=subj_id, question=doubt_text.strip())
                    st.success(f"Doubt #{new_id} logged successfully! Resolve now or review later.")
                    st.rerun()

    st.markdown("<hr style='margin: 16px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 2. STATS & FILTERS
    # -------------------------------------------------------------
    all_doubts = get_doubts(status="All")
    open_count = sum(1 for d in all_doubts if d["status"] == "open")
    resolved_count = sum(1 for d in all_doubts if d["status"] == "resolved")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Doubts", len(all_doubts))
    m2.metric("🟡 Open Queue", open_count)
    m3.metric("🟢 Resolved Archive", resolved_count)

    st.markdown("### 📋 Doubts Queue & Archive")
    
    col_filter1, col_filter2, col_filter3 = st.columns([0.35, 0.35, 0.30])
    with col_filter1:
        status_filter = st.selectbox("Filter Status", ["All", "Open", "Resolved"], index=0)
    with col_filter2:
        subject_filter_name = st.selectbox("Filter Subject", ["All Subjects"] + subject_names, index=0)
    with col_filter3:
        search_query = st.text_input("🔍 Search Doubts", placeholder="Search keywords...")

    filter_subj_id = None
    if subject_filter_name != "All Subjects" and subject_filter_name != "General Mechanical":
        filter_subj_id = subject_map.get(subject_filter_name)

    filtered_doubts = get_doubts(
        status=status_filter if status_filter != "All" else None,
        subject_id=filter_subj_id,
        search_query=search_query
    )

    if not filtered_doubts:
        st.info("No doubts found matching your filters. Use the quick-capture bar above to log your first doubt!")
        return

    # -------------------------------------------------------------
    # 3. DOUBT CARDS LISTING
    # -------------------------------------------------------------
    for doubt in filtered_doubts:
        is_open = doubt["status"] == "open"
        border_color = "var(--accent)" if is_open else "var(--primary)"
        badge_text = "🟡 OPEN" if is_open else "🟢 RESOLVED"

        with st.container():
            c_header, c_action = st.columns([0.80, 0.20])
            with c_header:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                        <span style="font-weight: 700; font-size: 16px;">#{doubt['id']}: {doubt['question']}</span>
                        <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: {border_color}; color: var(--background); font-weight: 700;">{badge_text}</span>
                    </div>
                """, unsafe_allow_html=True)
                st.caption(f"📚 Subject: **{doubt['subject_name']}** | 🗓️ Logged: {doubt['created_at'][:16]}")

            with c_action:
                if is_open:
                    if st.button("🔍 Resolve Now", key=f"resolve_btn_{doubt['id']}", use_container_width=True):
                        with st.spinner("Retrieving notes & generating structured explanation..."):
                            doubt_prompt = f"Resolve this specific GATE doubt concisely with physical insight and key formulas: {doubt['question']}"
                            answer, sources = get_ai_response(
                                messages=[{"role": "user", "content": doubt_prompt}],
                                use_rag=True,
                                subject_id=doubt["subject_id"],
                                study_mode="💡 Concept Explanation"
                            )
                            resolve_doubt(doubt["id"], ai_answer=answer, status="resolved", sources=sources)
                            st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"del_doubt_{doubt['id']}", use_container_width=True):
                        delete_doubt(doubt["id"])
                        st.rerun()

            # If resolved or has answer, display collapsible explanation
            if doubt["ai_answer"]:
                with st.expander("📖 View Resolution & Grounded Notes", expanded=is_open):
                    st.markdown(doubt["ai_answer"])
                    if doubt.get("source_chunks"):
                        st.markdown("##### 📚 Grounded Knowledge Base Sources:")
                        for src in doubt["source_chunks"]:
                            st.caption(f"- **{src.get('doc_name', 'Note')}** (Page {src.get('page_number', 1)}) — Similarity: {int(src.get('similarity_score', 0)*100)}%")

            st.markdown("<hr style='margin: 8px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
