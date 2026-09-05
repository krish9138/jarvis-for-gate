"""
views/pyq_view.py
-----------------
PYQ Intelligence Hub for GATE JARVIS 4.0.
Dedicated interface for drilling historical GATE Mechanical exam questions (1995–2025).
Provides rich multi-dimensional filtering, authentic NAT/MSQ/MCQ interfaces,
solution derivations, and cognitive mistake logging.
"""

import json
import streamlit as st
import pandas as pd
from database.queries import (
    get_pyqs_filtered,
    get_pyq_summary_stats,
    get_all_subjects
)
from services.pyq_service import (
    seed_foundational_pyqs,
    evaluate_pyq_answer
)

def render_pyq_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">📚 PYQ Intelligence Hub</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Master real historical GATE Mechanical Engineering problems (1995–2025). Analyze concept traps, track solving speed, and eliminate recurring error patterns.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Ensure seeds
    seed_foundational_pyqs()

    stats = get_pyq_summary_stats()

    # Top KPI strip
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cataloged PYQs", stats["total_pyqs"])
    c2.metric("Total Attempts", stats["total_attempts"])
    c3.metric("Overall Accuracy", f"{stats['accuracy_pct']}%")
    c4.metric("Exam Years", f"{stats['years_covered']} Years")
    c5.metric("Target Trajectory", "AIR < 100")

    st.markdown("<hr style='margin: 14px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    tab_drill, tab_analytics = st.tabs(["🎯 Solve & Practice PYQs", "📊 PYQ Mastery & Trap Intel"])

    # -------------------------------------------------------------
    # TAB 1: SOLVE & PRACTICE PYQS
    # -------------------------------------------------------------
    with tab_drill:
        subjects = get_all_subjects()
        subj_map = {"(All Subjects)": None}
        for s in subjects:
            subj_map[s["name"]] = s["id"]

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            sel_subj = st.selectbox("Subject:", list(subj_map.keys()), index=0)
        with f2:
            sel_type = st.selectbox("Question Type:", ["(all)", "MCQ", "MSQ", "NAT"], index=0)
        with f3:
            sel_diff = st.selectbox("Difficulty:", ["(all)", "Easy", "Medium", "Hard"], index=0)
        with f4:
            sel_year = st.selectbox("Year:", ["(all)"] + list(range(2024, 2017, -1)), index=0)

        year_val = int(sel_year) if sel_year != "(all)" else None
        pyqs = get_pyqs_filtered(
            subject_id=subj_map[sel_subj],
            difficulty=sel_diff,
            question_type=sel_type,
            year=year_val,
            limit=50
        )

        st.markdown(f"**Found {len(pyqs)} matching GATE questions:**")

        if not pyqs:
            st.warning("No PYQs found matching these filter criteria. Try broadening your selection.")
        else:
            for idx, q in enumerate(pyqs):
                qid = q["id"]
                st.markdown(f"""
                    <div style="background: rgba(17, 24, 39, 0.7); border: 1px solid var(--border); border-radius: 10px; padding: 18px 22px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-weight: 700; color: var(--accent); font-size: 15px;">
                                🎯 GATE {q['year']} — {q['subject_name']} ({q.get('topic', 'Core')})
                            </span>
                            <span style="font-size: 12px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; padding: 3px 8px;">
                                {q.get('question_type', 'MCQ')} • {q.get('marks', 1.0)} Mark • {q.get('difficulty', 'Medium')}
                            </span>
                        </div>
                        <p style="margin: 8px 0 12px 0; font-size: 15px; line-height: 1.5;">{q['question_text']}</p>
                    </div>
                """, unsafe_allow_html=True)

                if q.get("tested_concept"):
                    st.caption(f"🧠 **Tested Concept**: {q['tested_concept']} | ⏳ **Target Solving Time**: {q.get('expected_time_sec', 180)} seconds")

                # Answer form per question
                q_type = q.get("question_type", "MCQ")
                ans_state_key = f"pyq_ans_{qid}"
                eval_state_key = f"pyq_eval_{qid}"

                c_input, c_action = st.columns([0.7, 0.3])
                with c_input:
                    if q_type == "MCQ":
                        try:
                            opts = json.loads(q.get("options_json", "[]"))
                        except Exception:
                            opts = ["A", "B", "C", "D"]
                        choice = st.radio(f"Select option for Q{qid}:", opts, key=f"pyq_radio_{qid}", label_visibility="collapsed")
                        curr_ans = choice[0] if choice and choice[0] in "ABCD" else choice
                    elif q_type == "MSQ":
                        try:
                            opts = json.loads(q.get("options_json", "[]"))
                        except Exception:
                            opts = ["A", "B", "C", "D"]
                        st.caption("Select all that apply:")
                        msq_sel = []
                        for o in opts:
                            if st.checkbox(o, key=f"pyq_msq_{qid}_{o}"):
                                msq_sel.append(o[0] if o and o[0] in "ABCD" else o)
                        curr_ans = json.dumps(sorted(msq_sel))
                    elif q_type == "NAT":
                        curr_ans = st.text_input("Enter Numerical Answer:", key=f"pyq_nat_{qid}", placeholder="e.g. 1.275")

                with c_action:
                    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
                    if st.button(f"Submit Answer #{idx+1}", key=f"btn_pyq_{qid}", use_container_width=True):
                        is_corr, msg = evaluate_pyq_answer(q, curr_ans)
                        st.session_state[eval_state_key] = (is_corr, msg)
                        st.rerun()

                if eval_state_key in st.session_state:
                    is_corr, msg = st.session_state[eval_state_key]
                    if is_corr:
                        st.success(msg)
                    else:
                        st.error(msg)
                    with st.expander("📖 Step-by-Step Derivation & Official Solution"):
                        st.markdown(q.get("solution_text", "Solution not available."))

                st.markdown("<hr style='margin: 16px 0; border-color: rgba(255,255,255,0.06);'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 2: PYQ MASTERY & TRAP INTEL
    # -------------------------------------------------------------
    with tab_analytics:
        st.markdown("### 📊 PYQ Topic Accuracy & Misconception Diagnostics")
        st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 14px 18px; margin-bottom: 20px;">
                <h4 style="margin: 0 0 6px 0; color: #f59e0b;">⚠️ JARVIS PYQ Trap Insight</h4>
                <p style="margin: 0; font-size: 14px; color: var(--text);">
                    Entropy and Availability PYQs exhibit a high rate of calculation errors due to temperature unit conversions (forgetting to use Kelvin instead of Celsius) and sign conventions for entropy generation ($\Delta S_{gen} \ge 0$).
                </p>
            </div>
        """, unsafe_allow_html=True)

        all_pyqs = get_pyqs_filtered(limit=200)
        if all_pyqs:
            df = pd.DataFrame(all_pyqs)
            summary = df.groupby("topic").agg(
                total_qs=("id", "count"),
                attempts=("times_attempted", "sum"),
                correct=("times_correct", "sum")
            ).reset_index()
            summary["accuracy_pct"] = summary.apply(
                lambda r: round((r["correct"] / r["attempts"] * 100), 1) if r["attempts"] > 0 else 0.0, axis=1
            )
            summary.columns = ["Topic", "Available PYQs", "Student Attempts", "Correct Answers", "Accuracy (%)"]
            st.dataframe(summary, use_container_width=True)
