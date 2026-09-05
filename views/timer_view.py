import streamlit as st
import time
from database.queries import get_all_subjects, save_study_session
from services.timer_service import format_seconds_to_hms

def render_timer_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">⏱️ Deep Work Study Timer</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Track your focused study blocks. Consistent deep work is the foundation for a top 100 AIR rank.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Initialize session states for timer
    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
    if "timer_elapsed_seconds" not in st.session_state:
        st.session_state.timer_elapsed_seconds = 0
    if "timer_last_timestamp" not in st.session_state:
        st.session_state.timer_last_timestamp = None

    subjects = get_all_subjects()
    subject_options = {s["name"]: s["id"] for s in subjects}

    col_timer, col_details = st.columns([1.2, 1])

    with col_timer:
        st.markdown("""
            <div style="background: #0f172a; padding: 30px; border-radius: 16px; text-align: center; border: 2px solid #334155; margin-bottom: 20px;">
                <h4 style="color: #94a3b8; margin: 0; text-transform: uppercase; letter-spacing: 2px;">Study Stopwatch</h4>
                <h1 style="font-family: monospace; font-size: 64px; color: #38bdf8; margin: 15px 0;">
        """ + format_seconds_to_hms(st.session_state.timer_elapsed_seconds) + """
                </h1>
            </div>
        """, unsafe_allow_html=True)

        # Timer Controls
        c1, c2, c3 = st.columns(3)
        with c1:
            if not st.session_state.timer_running:
                if st.button("▶️ Start Timer", use_container_width=True, type="primary"):
                    st.session_state.timer_running = True
                    st.session_state.timer_last_timestamp = time.time()
                    st.rerun()
            else:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.timer_running = False
                    st.session_state.timer_last_timestamp = None
                    st.rerun()
        
        with c2:
            if st.button("🔄 Reset Timer", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.timer_elapsed_seconds = 0
                st.session_state.timer_last_timestamp = None
                st.rerun()

        with c3:
            # Quick increment (+15 mins) for manual tracking
            if st.button("➕ Add 15 Mins", use_container_width=True):
                st.session_state.timer_elapsed_seconds += 15 * 60
                st.rerun()

        # If running, auto-update elapsed time
        if st.session_state.timer_running:
            time.sleep(1)
            now = time.time()
            if st.session_state.timer_last_timestamp:
                delta = int(now - st.session_state.timer_last_timestamp)
                if delta > 0:
                    st.session_state.timer_elapsed_seconds += delta
                    st.session_state.timer_last_timestamp = now
            st.rerun()

    with col_details:
        st.subheader("📝 Session Details")
        
        selected_subject_name = st.selectbox(
            "Associate with Subject:",
            options=list(subject_options.keys()),
            index=0 if subject_options else None
        )
        
        subject_id = subject_options.get(selected_subject_name) if selected_subject_name else None

        manual_minutes = st.number_input(
            "Or enter manual duration (minutes):",
            min_value=0.0,
            max_value=600.0,
            value=round(st.session_state.timer_elapsed_seconds / 60.0, 1),
            step=5.0
        )

        session_notes = st.text_area(
            "Topic / Concepts Covered:",
            placeholder="e.g., Solved 10 numericals on Otto Cycle and Carnot efficiency..."
        )

        if st.button("💾 Save Session to Database", type="primary", use_container_width=True):
            duration_to_save = manual_minutes
            if duration_to_save <= 0:
                st.error("Please ensure the study duration is greater than 0 minutes.")
            else:
                success = save_study_session(
                    subject_id=subject_id,
                    duration_minutes=duration_to_save,
                    notes=session_notes
                )
                if success:
                    st.success(f"🎉 Saved **{duration_to_save} minutes** for **{selected_subject_name}**!")
                    # Reset timer
                    st.session_state.timer_running = False
                    st.session_state.timer_elapsed_seconds = 0
                    st.session_state.timer_last_timestamp = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to save session to database.")
