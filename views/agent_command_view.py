"""
views/agent_command_view.py
---------------------------
JARVIS Autonomous Agent Command Center View for GATE JARVIS.
Provides real-time multilingual voice/text command execution, tool registry inspection,
and autonomous activity audit log timelines.
"""

import time
import json
import streamlit as st
from agent.agent_core import get_agent_instance
from agent.tool_registry import ToolRegistry
from database.connection import get_db_connection
from services.voice_service import render_voice_input_widget, speak_text


def _get_recent_activity(limit: int = 15):
    """Fetches recent agent audit logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM agent_activity_log 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def _get_agent_notes(limit: int = 10):
    """Fetches saved agent notes and memories."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.*, COALESCE(s.name, 'General') as subject_name
        FROM agent_notes n
        LEFT JOIN subjects s ON n.subject_id = s.id
        ORDER BY n.created_at DESC 
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def render_agent_command_view():
    """Renders the JARVIS Autonomous Agent Command Center."""
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.15), rgba(30, 41, 59, 0.7)); 
                    border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px; padding: 18px 24px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="margin:0; color: #22d3ee; display:flex; align-items:center; gap:10px;">
                        🎙️ JARVIS Autonomous Agent Command Center
                    </h2>
                    <p style="margin:4px 0 0 0; color: #cbd5e1; font-size:14px;">
                        Multilingual AI Study Mentor & Executive Operating System (English • Hindi • Marathi)
                    </p>
                </div>
                <div style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 20px; padding: 4px 14px; color: #10b981; font-weight: 700; font-size: 12px;">
                    ● AGENT LIVE
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    agent = get_agent_instance()
    registry = ToolRegistry.get_instance()

    tab_interact, tab_audit, tab_memory, tab_tools = st.tabs([
        "💬 Interactive Voice & Command",
        "📜 Agent Activity Audit Log",
        "🧠 Agent Memory & Notes",
        "🛠️ Registered Tools & Permissions"
    ])

    # --- TAB 1: INTERACTIVE COMMAND & VOICE ---
    with tab_interact:
        col_left, col_right = st.columns([1.6, 1.0])

        with col_left:
            st.markdown("#### 🎙️ Voice Input Gateway")
            render_voice_input_widget()

            st.markdown("#### ✍️ Natural Language Command")
            with st.form("jarvis_agent_prompt_form", clear_on_submit=False):
                user_cmd = st.text_input(
                    "Speak or type in English, Hindi, or Marathi:",
                    placeholder="e.g. 'Jarvis, start a 45 min SOM session' or 'मला आजचा स्टडी प्लॅन सांग' or 'Entropy explain karo'",
                    key="agent_cmd_input"
                )
                col_btn1, col_btn2 = st.columns([1, 1])
                submitted = col_btn1.form_submit_button("⚡ Execute Autonomous Action", use_container_width=True)
                tts_enabled = col_btn2.checkbox("🔊 Speak Response (Audio Feedback)", value=True)

            if submitted and user_cmd.strip():
                with st.spinner("🤖 JARVIS processing command..."):
                    res = agent.process_user_input(prompt=user_cmd.strip())
                    
                st.markdown("##### 🎯 Agent Execution Result")
                status_color = "#10b981" if res["success"] else "#ef4444"
                st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.85); border-left: 4px solid {status_color}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                        <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">
                            Language: <b>{res['detected_language'].upper()}</b> | Intent: <b>{res['intent']}</b> | Tool: <b>{res['tool_name']}</b> | Latency: <b>{res['duration_ms']} ms</b>
                        </div>
                        <div style="font-size: 14px; color: #f8fafc; font-weight: 500; line-height: 1.5;">
                            {res['response_text']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if tts_enabled:
                    speak_text(res['response_text'], lang=res['detected_language'])

        with col_right:
            st.markdown("#### ⚡ Quick Command Shortcuts")
            quick_cmds = [
                ("📊 What Should I Study Today?", "What should I study today? Give me today's plan."),
                ("⏱️ Start 45-Min SOM Study", "Start a 45 minute study session for Strength of Materials."),
                ("❌ Show My Weak Topics", "Show my weak topics and mistakes."),
                ("💾 Backup Database", "Backup database now."),
                ("मराठी: आजचा प्लॅन सांगा", "मला आजचा स्टडी प्लॅन सांग."),
                ("हिंदी: आज क्या पढ़ना है?", "आज मुझे क्या पढ़ना है?"),
            ]
            for label, q_text in quick_cmds:
                if st.button(label, key=f"quick_btn_{label}", use_container_width=True):
                    with st.spinner("Executing shortcut..."):
                        res = agent.process_user_input(prompt=q_text)
                    st.success(res["response_text"])
                    if tts_enabled:
                        speak_text(res['response_text'], lang=res['detected_language'])

    # --- TAB 2: AUDIT LOG ---
    with tab_audit:
        st.markdown("#### 📜 Verifiable Agent Action Audit Trail")
        st.caption("Every automated agent action is recorded immutably with timestamp, parameters, and permission levels.")
        logs = _get_recent_activity(limit=25)
        if not logs:
            st.info("No agent actions recorded yet. Issue your first command in the Interactive tab!")
        else:
            for l in logs:
                stat_badge = "🟢 SUCCESS" if l["result_status"] == "SUCCESS" else "🔴 FAILED"
                with st.expander(f"[{l['timestamp']}] {l['intent']} ({stat_badge}) — {l['user_prompt'][:50]}...", expanded=False):
                    st.write(f"**Prompt:** {l['user_prompt']}")
                    st.write(f"**Tool Executed:** `{l['tool_name']}` | **Permission Level:** `{l['approval_level']}`")
                    st.write(f"**Input Parameters:** `{l['input_summary']}`")
                    st.write(f"**Result Summary:** {l['result_summary']}")
                    st.caption(f"Execution Duration: {l['duration_ms']} ms | Detected Language: {l['detected_language']}")

    # --- TAB 3: AGENT MEMORY & NOTES ---
    with tab_memory:
        st.markdown("#### 🧠 Persistent Concept Notes & Memory Bank")
        notes = _get_agent_notes(limit=20)
        if not notes:
            st.info("No concept notes saved yet. Say 'Note this: [your formula/concept]' to save notes via JARVIS.")
        else:
            for n in notes:
                with st.expander(f"📌 [{n['importance_level']}] {n['title']} ({n['subject_name']})", expanded=False):
                    st.markdown(n['content'])
                    st.caption(f"Saved on {n['created_at']} | ID: #{n['id']}")

    # --- TAB 4: TOOLS & PERMISSIONS ---
    with tab_tools:
        st.markdown("#### 🛠️ Tool Registry & Human-in-the-Loop Safeguards")
        tools_list = registry.list_tools()
        st.write(f"**{len(tools_list)} tools registered** in the active sandbox:")
        for t in tools_list:
            lvl = t["permission_level"]
            lvl_label = "Level 0 (Read - Auto)" if lvl == 0 else ("Level 1 (Low Risk Write - Auto)" if lvl == 1 else "Level 2 (User Approval Required)")
            st.markdown(f"""
                - **`{t['name']}`**: {t['description']}  
                  *(Permission: `{lvl_label}`)*
            """)
