import streamlit as st
from database.queries import save_chat_message, get_chat_history, clear_chat_history, get_all_subjects
from services.ai_service import get_ai_response, get_configured_provider
from modules.ai_client import get_masked_api_key, is_openai_configured

def render_assistant_view():
    provider_name, is_configured = get_configured_provider()

    st.markdown("""
        <div style="margin-bottom: 16px;">
            <h2 style="margin: 0;">💬 GATE JARVIS — AI Study Assistant & Mentor</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 0 0;">
                Your 24/7 personal Mechanical Engineering professor and GATE coach. Powered by OpenAI / Gemini with Knowledge Base RAG.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # API Status Banner with Masked Key (Zero key leakage)
    if not is_configured:
        st.warning(
            "⚠️ **API Key Not Configured Yet**: Running in **Offline Knowledge Base Mode**. "
            "JARVIS can still retrieve and quote your uploaded notes directly! "
            "To enable live OpenAI GPT-4o reasoning, add your `OPENAI_API_KEY` in `.env`."
        )
    else:
        masked_key = get_masked_api_key() if provider_name == "OpenAI" else "Configured"
        st.success(f"⚡ Active AI Engine: **{provider_name}** (`{masked_key}`) &nbsp;|&nbsp; **Stage 2 Knowledge Base Connected**")

    # RAG & Study Mode Controls Header
    subjects = get_all_subjects()
    subject_map = {s["name"]: s["id"] for s in subjects}

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.2, 1.2, 1.2])
    with ctrl_col1:
        use_rag = st.checkbox("📚 Search My Uploaded Notes First (RAG)", value=True, help="When enabled, JARVIS prioritizes your uploaded notes and textbooks.")
    with ctrl_col2:
        subject_filter_name = st.selectbox(
            "Filter Knowledge by Subject",
            options=["All Uploaded Documents"] + list(subject_map.keys()),
            index=0,
            disabled=not use_rag
        )
        selected_subject_id = subject_map.get(subject_filter_name, None) if subject_filter_name != "All Uploaded Documents" else None
    with ctrl_col3:
        study_mode = st.selectbox(
            "🎯 Study Mode",
            options=[
                "Standard Explanation",
                "💡 Concept Explanation",
                "🔢 Step-by-Step Numerical",
                "📝 Short Notes & Formulas",
                "❓ Practice Questions",
                "📊 Test Analysis & Traps"
            ],
            index=0,
            help="Directs JARVIS to tailor the explanation style for GATE exam preparation."
        )

    # Quick Starter Chips
    st.markdown("**💡 Quick Question Starters (Click to test):**")
    col1, col2, col3, col4 = st.columns(4)
    
    starter_prompts = [
        "Explain Bernoulli's equation",
        "Explain Lame's equations for thick cylinders with boundary conditions",
        "Solve numerical: A thick cylinder with 150mm inner dia and 450mm outer dia under 160 MPa internal and 80 MPa external pressure. Find longitudinal stress.",
        "Give me short revision notes and formulas for Euler buckling of columns"
    ]
    
    selected_prompt = None
    with col1:
        if st.button("💧 Bernoulli's Equation", use_container_width=True):
            selected_prompt = starter_prompts[0]
    with col2:
        if st.button("⭕ Lame's Equations", use_container_width=True):
            selected_prompt = starter_prompts[1]
    with col3:
        if st.button("🔢 Thick Cylinder Problem", use_container_width=True):
            selected_prompt = starter_prompts[2]
    with col4:
        if st.button("📝 Column Buckling Notes", use_container_width=True):
            selected_prompt = starter_prompts[3]

    # Load persistent chat history from DB into session state if not loaded
    if "messages" not in st.session_state:
        st.session_state.messages = get_chat_history()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Display sources if stored
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📚 Sources Used ({len(sources)} citations)", expanded=False):
                    for idx, s in enumerate(sources, 1):
                        relevance = int(s.get('similarity_score', 0) * 100)
                        st.markdown(
                            f"**[{idx}] {s.get('doc_name', 'Document')}** (Page {s.get('page_number', 1)}) — *Relevance: {relevance}%*\n\n"
                            f"> {s.get('content', '')[:250]}..."
                        )

    # Handle starter prompt click or chat input
    user_input = st.chat_input("Ask any Mechanical Engineering / GATE question from your notes...")
    
    query_to_send = selected_prompt or user_input

    if query_to_send:
        # 1. Add user message
        st.session_state.messages.append({"role": "user", "content": query_to_send, "sources": []})
        save_chat_message("user", query_to_send)
        with st.chat_message("user"):
            st.markdown(query_to_send)

        # 2. Get AI Response with RAG & Study Mode
        with st.chat_message("assistant"):
            with st.spinner("JARVIS is analyzing engineering principles & searching knowledge base..."):
                response_text, sources_used = get_ai_response(
                    st.session_state.messages, 
                    use_rag=use_rag, 
                    subject_id=selected_subject_id,
                    study_mode=study_mode
                )
                st.markdown(response_text)

                # Show sources immediately under current response
                if sources_used:
                    with st.expander(f"📚 Sources Used ({len(sources_used)} citations)", expanded=True):
                        for idx, s in enumerate(sources_used, 1):
                            relevance = int(s.get('similarity_score', 0) * 100)
                            st.markdown(
                                f"**[{idx}] `{s.get('doc_name', 'Document')}`** &nbsp;|&nbsp; "
                                f"📄 Page {s.get('page_number', 1)} &nbsp;|&nbsp; "
                                f"🏷️ Subject: `{s.get('subject_name', 'General')}` &nbsp;|&nbsp; "
                                f"🎯 Match: `{relevance}%`\n\n"
                                f"> *\"{s.get('content', '')[:280]}...\"*"
                            )
                
        # 3. Save Assistant Message and Sources
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text, 
            "sources": sources_used
        })
        save_chat_message("assistant", response_text, sources=sources_used)

    # Chat controls (Clear History)
    if st.session_state.messages:
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", type="secondary"):
            clear_chat_history()
            st.session_state.messages = []
            st.rerun()
