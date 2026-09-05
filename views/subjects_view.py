import streamlit as st
import pandas as pd
from database.queries import (
    get_all_subjects, 
    add_subject, 
    get_tasks, 
    add_task, 
    toggle_task_status, 
    delete_task
)

def render_subjects_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">📚 Subjects & Study Planner</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Complete curriculum tracking for <strong>GATE Mechanical</strong> and <strong>First Year</strong> engineering courses.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📋 Task Planner", 
        "🏛️ Subjects & Curriculum", 
        "🔄 College ↔ GATE Dual-Track Matrix"
    ])

    # ==========================================
    # TAB 1: TASK PLANNER
    # ==========================================
    with tab1:
        st.subheader("Manage Tasks & Milestones")

        # Form to Add New Task
        with st.expander("➕ Add New Study Task / Revision / Test Goal", expanded=False):
            subjects = get_all_subjects()
            subject_map = {s["name"]: s["id"] for s in subjects}

            with st.form("add_task_form"):
                task_title = st.text_input("Task Title / Topic:", placeholder="e.g., Solve 20 PYQs on Rankine Cycle / Mohr's Circle")
                
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    selected_subj = st.selectbox("Subject:", options=list(subject_map.keys()))
                with f_col2:
                    priority = st.selectbox("Priority:", ["High", "Medium", "Low"], index=1)
                with f_col3:
                    task_type = st.selectbox("Type:", ["Study", "Revision", "Test", "PYQ Practice", "Assignment"], index=0)

                due_date = st.date_input("Target Date (Optional):")
                
                submitted = st.form_submit_button("Add Task")
                if submitted:
                    if not task_title.strip():
                        st.error("Please enter a task title.")
                    else:
                        subject_id = subject_map.get(selected_subj)
                        success = add_task(
                            title=task_title,
                            subject_id=subject_id,
                            priority=priority,
                            task_type=task_type,
                            due_date=str(due_date)
                        )
                        if success:
                            st.success("Task added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add task.")

        # Filter active vs completed
        active_tab, completed_tab = st.tabs(["⏳ Pending Tasks", "✅ Completed Tasks"])
        
        with active_tab:
            pending_tasks = get_tasks(is_completed=0)
            if not pending_tasks:
                st.info("No pending tasks! Click 'Add New Study Task' above to schedule your next study target.")
            else:
                for t in pending_tasks:
                    c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
                    with c1:
                        if st.button("✔", key=f"p_done_{t['id']}", help="Mark as Completed"):
                            toggle_task_status(t['id'], 1)
                            st.rerun()
                    with c2:
                        st.markdown(f"**{t['title']}**")
                        st.caption(f"📚 {t['subject_name']} | 🏷️ {t['task_type']} | ⚡ {t['priority']} Priority | 🗓️ Due: {t['due_date'] or 'N/A'}")
                    with c3:
                        if st.button("🗑️", key=f"del_{t['id']}", help="Delete Task"):
                            delete_task(t['id'])
                            st.rerun()
                    st.divider()

        with completed_tab:
            done_tasks = get_tasks(is_completed=1)
            if not done_tasks:
                st.info("No completed tasks yet.")
            else:
                for t in done_tasks:
                    c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
                    with c1:
                        if st.button("↩", key=f"undo_{t['id']}", help="Mark as Incomplete"):
                            toggle_task_status(t['id'], 0)
                            st.rerun()
                    with c2:
                        st.markdown(f"~~{t['title']}~~")
                        st.caption(f"📚 {t['subject_name']} | 🏷️ {t['task_type']} (Completed)")
                    with c3:
                        if st.button("🗑️", key=f"del_done_{t['id']}", help="Delete Task"):
                            delete_task(t['id'])
                            st.rerun()
                    st.divider()

    # ==========================================
    # TAB 2: SUBJECTS CATALOG
    # ==========================================
    with tab2:
        st.subheader("Curriculum & Subject Progress")

        # Category Filter Tabs
        cat_tab_all, cat_tab_gate, cat_tab_first = st.tabs([
            "📂 All Subjects", 
            "⚙️ GATE Mechanical (13 Subjects)", 
            "🎓 First Year (7 Subjects)"
        ])

        all_subjects = get_all_subjects()

        def render_subject_cards(subj_list):
            for subj in subj_list:
                pct = int(min(1.0, subj['completed_hours'] / subj['target_hours']) * 100) if subj['target_hours'] > 0 else 0
                
                with st.container():
                    col_a, col_b = st.columns([0.75, 0.25])
                    with col_a:
                        cat_badge = "⚙️ GATE ME" if subj['category'] == "GATE Mechanical" else "🎓 First Year"
                        st.markdown(f"#### {subj['name']} &nbsp; <span style='font-size: 12px; background: #334155; padding: 2px 8px; border-radius: 6px;'>{cat_badge}</span>", unsafe_allow_html=True)
                        st.caption(f"Target: **{subj['target_hours']:.0f} hours** | Sessions Logged: **{subj['session_count']}**")
                        st.progress(min(1.0, subj['completed_hours'] / subj['target_hours']) if subj['target_hours'] > 0 else 0.0)
                    with col_b:
                        st.metric(
                            label="Completed",
                            value=f"{pct}%",
                            delta=f"{subj['completed_hours']:.1f} / {subj['target_hours']:.0f} hrs"
                        )
                st.markdown("<hr style='margin: 8px 0; border-color: #334155;'/>", unsafe_allow_html=True)

        with cat_tab_all:
            render_subject_cards(all_subjects)

        with cat_tab_gate:
            gate_subjs = [s for s in all_subjects if s["category"] == "GATE Mechanical"]
            render_subject_cards(gate_subjs)

        with cat_tab_first:
            first_subjs = [s for s in all_subjects if s["category"] == "First Year"]
            render_subject_cards(first_subjs)

        # Custom subject creation
        with st.expander("➕ Add Custom Subject"):
            with st.form("add_subject_form"):
                new_subj_name = st.text_input("Subject Name:", placeholder="e.g., Robotics & Automation")
                new_subj_cat = st.selectbox("Category:", ["GATE Mechanical", "First Year", "Elective", "General Aptitude"])
                new_target = st.number_input("Target Hours:", min_value=10.0, max_value=200.0, value=50.0, step=5.0)
                
                if st.form_submit_button("Save Subject"):
                    if not new_subj_name.strip():
                        st.error("Please enter a subject name.")
                    else:
                        if add_subject(new_subj_name, new_subj_cat, new_target):
                            st.success(f"Added {new_subj_name}!")
                            st.rerun()
                        else:
                            st.error("Subject already exists or could not be added.")

    # ==========================================
    # TAB 3: COLLEGE ↔ GATE DUAL-TRACK MATRIX (Audit F-11)
    # ==========================================
    with tab3:
        st.subheader("🔄 University Curriculum ↔ GATE ME Dual-Track Alignment")
        st.caption("A Mechanical Engineering aspirant must conquer both university semester exams (GPA > 8.5) and GATE ME (AIR < 100). This mapping ensures college effort directly compounds into GATE preparation:")

        dual_track_mappings = [
            {
                "college_course": "Engineering Mechanics (Sem 1)",
                "gate_subject": "Engineering Mechanics",
                "sem": "Sem 1",
                "gate_weight": "4–6 Marks",
                "overlap": "85% (Direct)",
                "strategy": "College focuses on equilibrium proofs; GATE tests friction wedges & truss zero-force members."
            },
            {
                "college_course": "Engineering Mathematics I & II (Sem 1/2)",
                "gate_subject": "Engineering Mathematics",
                "sem": "Sem 1 & 2",
                "gate_weight": "13–15 Marks",
                "overlap": "90% (Direct)",
                "strategy": "Highest GATE weightage! Master Calculus maxima-minima, Linear Algebra rank/eigenvalues, and ODEs."
            },
            {
                "college_course": "Mechanics of Solids / SOM (Sem 3)",
                "gate_subject": "Strength of Materials",
                "sem": "Sem 3",
                "gate_weight": "8–10 Marks",
                "overlap": "95% (Exact)",
                "strategy": "College derivations (flexure formula, torsion) feed directly into GATE Mohr circle and deflection NATs."
            },
            {
                "college_course": "Thermodynamics (Sem 3)",
                "gate_subject": "Basic Thermodynamics",
                "sem": "Sem 3",
                "gate_weight": "7–9 Marks",
                "overlap": "90% (Direct)",
                "strategy": "College demands state property tables; GATE tests closed-system work, availability, and entropy generation."
            },
            {
                "college_course": "Fluid Mechanics (Sem 4)",
                "gate_subject": "Fluid Mechanics & Machinery",
                "sem": "Sem 4",
                "gate_weight": "8–10 Marks",
                "overlap": "85% (Direct)",
                "strategy": "College emphasizes Navier-Stokes derivations; GATE focuses on Bernoulli, pipe friction, and boundary layer drag."
            },
            {
                "college_course": "Engineering Graphics & CAD (Sem 1/2)",
                "gate_subject": "General Engineering / Skill Only",
                "sem": "Sem 1",
                "gate_weight": "N/A (Skill)",
                "strategy": "Keep in College track only. Not tested in GATE ME; essential for core industry placement & CAD/FEA design."
            },
            {
                "college_course": "ICT / Computing & Python (Sem 1/2)",
                "gate_subject": "General Aptitude / Numerical Methods",
                "sem": "Sem 2",
                "gate_weight": "2–3 Marks",
                "overlap": "40% (Partial)",
                "strategy": "Leverage Python for numerical ODE algorithms in Engg Math; separate IT/Satellite topics from GATE answer context."
            }
        ]

        df_dual = pd.DataFrame(dual_track_mappings)
        df_dual.columns = ["College Course", "Mapped GATE Subject", "Semester", "GATE Weight", "Curriculum Overlap", "Study Strategy"]
        st.dataframe(df_dual, use_container_width=True, hide_index=True)

        st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; padding: 16px; margin-top: 16px;">
                <h4 style="margin: 0 0 8px 0; color: #38bdf8;">💡 Strategic Rule for Dual-Track Balance</h4>
                <p style="font-size: 13px; color: #cbd5e1; line-height: 1.6; margin: 0;">
                    • <b>During Semesters 1 to 4:</b> Every semester subject that overlaps with GATE (Maths, Mechanics, SOM, Thermo, Fluids) must be studied from standard GATE textbooks simultaneously.<br>
                    • <b>Preserve Pure College Tracks:</b> Subjects like <i>Engineering Graphics, College Workshops, and ICT</i> build crucial practical engineering skills, but are segregated from GATE mock diagnostic engines to protect ranking accuracy.
                </p>
            </div>
        """, unsafe_allow_html=True)
