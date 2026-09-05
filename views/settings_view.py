import streamlit as st
import os
import config
from api_key_manager import render_api_key_settings
from database.connection import get_db_connection

def render_settings_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">⚙️ System Diagnostics & API Key Management</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Manage API keys in-app, test provider connections, and inspect SQLite vector database health.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. In-App API Key Management Component (Live save to .env + connection test)
    render_api_key_settings()

    # 2. Database Health & Records
    st.markdown("---")
    st.subheader("📊 SQLite Database & Vector Store Health")
    st.info(f"📁 Database File: `{config.DB_PATH}` | 📂 Documents Directory: `{config.DOCUMENTS_DIR}`")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as c FROM subjects")
        s_count = cursor.fetchone()["c"]
        
        cursor.execute("SELECT COUNT(*) as c FROM study_sessions")
        ss_count = cursor.fetchone()["c"]
        
        cursor.execute("SELECT COUNT(*) as c FROM tasks")
        t_count = cursor.fetchone()["c"]
        
        cursor.execute("SELECT COUNT(*) as c FROM documents")
        d_count = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM document_chunks")
        chunk_count = cursor.fetchone()["c"]

        cursor.execute("SELECT COUNT(*) as c FROM mock_tests")
        m_count = cursor.fetchone()["c"]
        
        conn.close()

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Subjects", s_count)
        c2.metric("Study Sessions", ss_count)
        c3.metric("Tasks", t_count)
        c4.metric("Documents", d_count)
        c5.metric("Vector Chunks", chunk_count)
        c6.metric("Mock Tests", m_count)
        
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
