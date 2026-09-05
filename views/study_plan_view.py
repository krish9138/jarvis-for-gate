import json
import streamlit as st
import pandas as pd
from database.queries import (
    get_plan_months,
    update_month_checklist,
    get_skills_tracker,
    update_skill_progress,
    get_study_resources,
    get_weekly_timetable,
    update_timetable_slot,
    get_subject_weightage,
    get_study_tactics,
    get_monthly_study_comparison,
    get_all_subjects
)

PHASE_COLORS = {
    "Foundation": "#38bdf8",
    "Application": "#f59e0b",
    "Revision": "#a855f7",
    "Simulation": "#ef4444"
}

def render_study_plan_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">🗓️ GATE 2026 Master Plan & Strategy Dashboard</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Directly seeded from your <strong>GATE ME MasterPlan 2026</strong>. 8-Month Roadmap (928.8 Target Hours), Phase Milestones, Weekly Timetable, and Engineering Skills Tracker.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_timeline, tab_timetable, tab_skills, tab_weightage, tab_resources = st.tabs([
        "🗓️ 8-Month Roadmap & Milestones",
        "⏰ Weekly Timetable Grid",
        "💻 Engineering Skills Tracker",
        "📊 Subject Weightage & Strategy",
        "🌐 Curated Free Resources"
    ])

    # -------------------------------------------------------------
    # TAB 1: 8-MONTH ROADMAP & MILESTONES
    # -------------------------------------------------------------
    with tab_timeline:
        months_data = get_plan_months()
        if not months_data:
            st.warning("No study plan data found in database. Initializing database seed...")
            return

        # Top summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Planned Hours", "928.8 hrs")
        m2.metric("Duration", "8 Months (Jun 2025 – Feb 2026)")
        m3.metric("Target Exam Score", "> 75 / 100")
        m4.metric("Target AIR", "< 100 (IIT/PSU)")

        st.markdown("<hr style='margin: 14px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

        # Month Selector Chips
        st.markdown("### 📍 Select Study Month & Phase:")
        month_labels = [m["month_label"] for m in months_data]
        selected_month_label = st.radio(
            "Month Selector",
            options=month_labels,
            horizontal=True,
            index=0,
            label_visibility="collapsed"
        )

        selected_month = next((m for m in months_data if m["month_label"] == selected_month_label), months_data[0])
        phase_color = PHASE_COLORS.get(selected_month["phase"], "var(--primary)")

        # Month Overview Card
        with st.container():
            st.markdown(f"""
                <div style="background-color: var(--surface); border: 1px solid var(--border); border-left: 5px solid {phase_color}; padding: 18px; border-radius: 10px; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0;">📅 {selected_month['month_label']}</h3>
                        <span style="background: {phase_color}; color: var(--background); font-weight: 800; padding: 4px 12px; border-radius: 14px; font-size: 13px;">
                            {selected_month['phase'].upper()} PHASE
                        </span>
                    </div>
                    <p style="margin: 8px 0 4px 0; font-size: 15px; font-weight: 600; color: var(--text);">🎯 Key Focus: {selected_month['key_focus']}</p>
                    <div style="display: flex; gap: 20px; color: var(--muted); font-size: 13px; margin-top: 6px;">
                        <span>⏱️ Target: <strong>{selected_month['target_hours']:.1f} hrs</strong></span>
                        <span>📅 Weekdays: <strong>{selected_month['weekday_hrs']:.0f} hrs/day</strong></span>
                        <span>🏖️ Weekends: <strong>{selected_month['weekend_hrs']:.0f} hrs/day</strong></span>
                        <span>📊 Weekly Study: <strong>{selected_month['study_hrs_per_week']:.0f} hrs/wk</strong></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_sub1, c_sub2 = st.columns(2)
            with c_sub1:
                st.markdown("#### 📘 Primary Subjects")
                for ps in selected_month.get("primary_subjects", []):
                    st.info(f"🔹 {ps}")
            with c_sub2:
                st.markdown("#### 📙 Secondary / Parallel Subjects")
                for ss in selected_month.get("secondary_subjects", []):
                    st.info(f"🔸 {ss}")

            # Interactive Checklist
            st.markdown("#### ✅ Monthly Milestone Checklist (Saves Automatically):")
            checklist = selected_month.get("checklist", [])
            updated = False
            for idx, item in enumerate(checklist):
                is_done = item.get("done", False)
                item_text = item.get("item", "")
                
                chk = st.checkbox(item_text, value=is_done, key=f"chk_{selected_month['id']}_{idx}")
                if chk != is_done:
                    checklist[idx]["done"] = chk
                    updated = True

            if updated:
                update_month_checklist(selected_month["id"], checklist)
                st.toast("Milestone progress saved!", icon="💾")
                st.rerun()

        # Monthly Planned vs Actual Hours Tracker Chart
        st.markdown("<hr style='margin: 24px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
        st.markdown("### 📊 Planned vs. Actual Study Hours")
        comp_data = get_monthly_study_comparison()
        df_comp = pd.DataFrame(comp_data)
        
        st.bar_chart(df_comp.set_index("month")[["planned_hours", "actual_hours"]])

    # -------------------------------------------------------------
    # TAB 2: WEEKLY TIMETABLE GRID
    # -------------------------------------------------------------
    with tab_timetable:
        st.markdown("### ⏰ Master Sample Weekly Timetable (27–36 hrs/week)")
        st.caption("Weekday Pattern: 3 hrs GATE + 1 hr Skill | Weekend Pattern: 7 hrs GATE + 1 hr Skill")

        slots = get_weekly_timetable()
        if not slots:
            st.info("No timetable slots configured.")
        else:
            # Render as clean table
            df_table = pd.DataFrame([
                {
                    "Time Slot": s["time_slot"],
                    "Monday": s["mon"],
                    "Tuesday": s["tue"],
                    "Wednesday": s["wed"],
                    "Thursday": s["thu"],
                    "Friday": s["fri"],
                    "Saturday": s["sat"],
                    "Sunday": s["sun"]
                }
                for s in slots
            ])
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            # Custom Slot Editor Expander
            with st.expander("✏️ Edit Timetable Slot Content"):
                slot_options = {s["time_slot"]: s for s in slots}
                edit_slot_name = st.selectbox("Choose Slot to Edit:", list(slot_options.keys()))
                target_slot = slot_options[edit_slot_name]

                with st.form("edit_timetable_form"):
                    e_c1, e_c2 = st.columns(2)
                    with e_c1:
                        e_mon = st.text_input("Monday:", value=target_slot["mon"])
                        e_tue = st.text_input("Tuesday:", value=target_slot["tue"])
                        e_wed = st.text_input("Wednesday:", value=target_slot["wed"])
                        e_thu = st.text_input("Thursday:", value=target_slot["thu"])
                    with e_c2:
                        e_fri = st.text_input("Friday:", value=target_slot["fri"])
                        e_sat = st.text_input("Saturday:", value=target_slot["sat"])
                        e_sun = st.text_input("Sunday:", value=target_slot["sun"])

                    save_tt = st.form_submit_button("💾 Save Slot Changes")
                    if save_tt:
                        update_timetable_slot(
                            slot_id=target_slot["id"],
                            mon=e_mon, tue=e_tue, wed=e_wed, thu=e_thu,
                            fri=e_fri, sat=e_sat, sun=e_sun
                        )
                        st.success("Timetable updated successfully!")
                        st.rerun()

    # -------------------------------------------------------------
    # TAB 3: SKILLS TRACKER
    # -------------------------------------------------------------
    with tab_skills:
        st.markdown("### 💻 Parallel Engineering Skills (1 hr/day track)")
        st.caption("Crucial for IIT M.Tech interviews, BARC/DRDO technical interviews, and industrial mechanical readiness.")

        skills = get_skills_tracker()
        for sk in skills:
            with st.container():
                c_s1, c_s2 = st.columns([0.65, 0.35])
                with c_s1:
                    st.markdown(f"#### ⚙️ {sk['skill_name']}")
                    st.markdown(f"**Target Months**: `{sk['target_months']}` &nbsp;|&nbsp; **Weekly Hours**: `{sk['weekly_hours']} hrs/wk`")
                    st.markdown(f"**Curriculum Focus**: {sk['what_to_learn']}")
                with c_s2:
                    current_val = float(sk.get("progress_pct", 0.0))
                    new_val = st.slider(
                        f"Progress ({sk['skill_name']})",
                        min_value=0.0,
                        max_value=100.0,
                        value=current_val,
                        step=5.0,
                        key=f"skill_slider_{sk['id']}"
                    )
                    if new_val != current_val:
                        update_skill_progress(sk["id"], new_val)
                        st.toast(f"Updated {sk['skill_name']} to {new_val:.0f}%", icon="🎯")
                st.markdown("<hr style='margin: 12px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 4: SUBJECT WEIGHTAGE & STRATEGY
    # -------------------------------------------------------------
    with tab_weightage:
        st.markdown("### 📊 Subject Weightage & IIT NPTEL Mapping")
        st.caption("Prioritize CRITICAL (Maths, Aptitude, SOM, Thermo, Fluids, Mfg) for guaranteed 70+ marks.")

        weightage = get_subject_weightage()
        if weightage:
            df_w = pd.DataFrame(weightage)
            st.dataframe(
                df_w[["subject", "avg_marks", "priority", "difficulty", "phase", "nptel_course"]],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")
        st.markdown("### 🧠 Master Study Tactics Cheat Sheet")
        tactics = get_study_tactics()
        t_cols = st.columns(2)
        for idx, t in enumerate(tactics):
            col = t_cols[idx % 2]
            with col:
                st.markdown(f"""
                    <div style="background-color: var(--surface); border: 1px solid var(--border); padding: 14px; border-radius: 8px; margin-bottom: 12px;">
                        <h4 style="margin: 0 0 6px 0; color: var(--primary);">💡 {t['name']}</h4>
                        <p style="margin: 0; font-size: 13.5px; line-height: 1.4;">{t['detail']}</p>
                    </div>
                """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 5: CURATED RESOURCES
    # -------------------------------------------------------------
    with tab_resources:
        st.markdown("### 🌐 Recommended Free Study Resources & Tools")
        
        c_rf, _ = st.columns([0.4, 0.6])
        with c_rf:
            res_subj_filter = st.selectbox("Filter Resources by Subject:", ["All", "Maths", "Thermodynamics", "Strength of Materials", "Fluid Mechanics", "Manufacturing Science", "All Subjects"])

        res_list = get_study_resources(subject_filter=res_subj_filter if res_subj_filter != "All" else None)

        r_cols = st.columns(2)
        for idx, r in enumerate(res_list):
            c = r_cols[idx % 2]
            with c:
                st.markdown(f"""
                    <div style="background-color: var(--surface); border: 1px solid var(--border); padding: 16px; border-radius: 10px; margin-bottom: 14px;">
                        <span style="font-size: 11px; padding: 2px 8px; border-radius: 8px; background: var(--primary); color: var(--background); font-weight: bold;">{r['resource_type'].upper()}</span>
                        <h4 style="margin: 6px 0 4px 0;">{r['name']}</h4>
                        <p style="margin: 0 0 8px 0; font-size: 13px; color: var(--muted);">Target: {r['subjects']}</p>
                        <a href="{r['link']}" target="_blank" style="color: var(--accent); font-weight: 600; text-decoration: none;">🔗 Open Resource ({r['link']})</a>
                    </div>
                """, unsafe_allow_html=True)
