"""
views/dpp_view.py
-----------------
Dedicated DPP & Practice Lab for GATE JARVIS 4.0.
Features interactive practice drilling, per-question timing, instant step-by-step review,
automatic negative marking & mistake logging, and multi-source DPP ingestion.
"""

import json
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from database.queries import (
    get_all_dpp_sets,
    get_dpp_questions,
    get_dpp_attempts,
    get_all_subjects
)
from services.dpp_service import (
    seed_foundational_dpps,
    evaluate_dpp_submission,
    parse_and_import_dpp_text
)

def render_dpp_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">📝 DPP & Practice Lab</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Daily Practice Problems (DPP) dedicated training station. Solve curated GATE Mechanical drills with live timing, instant grading, and automated error classification.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Ensure seeds
    seed_foundational_dpps()

    tab_practice, tab_import, tab_history = st.tabs([
        "🎯 Daily Practice & Drill",
        "📥 Upload & Import DPP",
        "📊 Practice History & Analytics"
    ])

    all_dpps = get_all_dpp_sets()

    # -------------------------------------------------------------
    # TAB 1: DAILY PRACTICE & DRILL
    # -------------------------------------------------------------
    with tab_practice:
        if not all_dpps:
            st.info("No DPP sets currently available. Use 'Upload & Import DPP' to create your first practice drill.")
        else:
            dpp_options = {f"{d['title']} ({d['actual_question_count']} Qs • {d['difficulty']} • {d['subject_name']})": d["id"] for d in all_dpps}
            
            c_select, c_btn = st.columns([0.75, 0.25])
            with c_select:
                selected_label = st.selectbox("Select Practice DPP:", list(dpp_options.keys()), index=0)
            
            selected_dpp_id = dpp_options[selected_label]
            questions = get_dpp_questions(selected_dpp_id)

            with c_btn:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Reset / Start Drill", use_container_width=True):
                    st.session_state[f"dpp_answers_{selected_dpp_id}"] = {}
                    st.session_state[f"dpp_start_time_{selected_dpp_id}"] = time.time()
                    st.session_state[f"dpp_result_{selected_dpp_id}"] = None
                    st.rerun()

            # Initialize session state for this DPP
            ans_key = f"dpp_answers_{selected_dpp_id}"
            time_key = f"dpp_start_time_{selected_dpp_id}"
            result_key = f"dpp_result_{selected_dpp_id}"

            if ans_key not in st.session_state:
                st.session_state[ans_key] = {}
            if time_key not in st.session_state:
                st.session_state[time_key] = time.time()

            # Timer Header
            elapsed_sec = int(time.time() - st.session_state[time_key])
            mins = elapsed_sec // 60
            secs = elapsed_sec % 60

            st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid var(--border); border-radius: 8px; padding: 10px 16px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: var(--accent);">⏱️ Elapsed Time: {mins:02d}:{secs:02d}</span>
                    <span style="font-size: 13px; color: var(--muted);">{len(questions)} Total Questions | Standard GATE Marking Rules</span>
                </div>
            """, unsafe_allow_html=True)

            # Display Questions Form
            with st.form(key=f"dpp_form_{selected_dpp_id}"):
                for idx, q in enumerate(questions):
                    qid = str(q["id"])
                    st.markdown(f"#### Q{idx + 1}. ({q['question_type']} • {q['marks']} Mark{'s' if q['marks']>1 else ''})")
                    st.markdown(q["question_text"])

                    if q.get("formula_hint"):
                        with st.expander("💡 View Formula Hint"):
                            st.latex(q["formula_hint"])

                    q_type = q["question_type"]
                    current_val = st.session_state[ans_key].get(qid, "")

                    if q_type == "MCQ":
                        try:
                            opts = json.loads(q.get("options_json", "[]"))
                        except Exception:
                            opts = ["A", "B", "C", "D"]
                        
                        opt_map = {"(Not Attempted)": ""}
                        for o in opts:
                            key_char = o[0] if o and o[0] in "ABCD" else o
                            opt_map[o] = key_char

                        default_idx = 0
                        for i, (k, v) in enumerate(opt_map.items()):
                            if v == current_val and current_val != "":
                                default_idx = i
                                break

                        choice = st.radio(f"Select option for Q{idx+1}:", list(opt_map.keys()), index=default_idx, key=f"mcq_{selected_dpp_id}_{qid}")
                        st.session_state[ans_key][qid] = opt_map[choice]

                    elif q_type == "MSQ":
                        try:
                            opts = json.loads(q.get("options_json", "[]"))
                        except Exception:
                            opts = ["A", "B", "C", "D"]
                        st.caption("Multiple choices may be correct. No negative marking.")
                        selected_msq = []
                        for opt in opts:
                            key_char = opt[0] if opt and opt[0] in "ABCD" else opt
                            is_checked = key_char in current_val if isinstance(current_val, list) else False
                            if st.checkbox(opt, value=is_checked, key=f"msq_{selected_dpp_id}_{qid}_{opt}"):
                                selected_msq.append(key_char)
                        st.session_state[ans_key][qid] = selected_msq

                    elif q_type == "NAT":
                        st.caption("Enter exact numerical value (NAT). No negative marking.")
                        nat_val = st.text_input("Numerical Answer:", value=str(current_val), key=f"nat_{selected_dpp_id}_{qid}", placeholder="e.g. 50.0")
                        st.session_state[ans_key][qid] = nat_val.strip()

                    st.markdown("<hr style='margin: 12px 0; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

                submitted = st.form_submit_button("🚀 Submit DPP & Evaluate", use_container_width=True)

            if submitted:
                duration_sec = int(time.time() - st.session_state[time_key])
                result = evaluate_dpp_submission(
                    dpp_set_id=selected_dpp_id,
                    user_answers=st.session_state[ans_key],
                    time_taken_sec=duration_sec,
                    auto_log_mistakes=True
                )
                st.session_state[result_key] = result
                st.rerun()

            # Render Results If Available
            if st.session_state.get(result_key):
                res = st.session_state[result_key]
                st.markdown("### 🏆 DPP Performance Summary")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Score", f"{res['score']} / {res['max_score']}")
                c2.metric("Accuracy", f"{res['accuracy']}%")
                c3.metric("Correct / Wrong", f"{res['correct_count']} / {res['wrong_count']}")
                c4.metric("Mistakes Logged", f"{res['mistakes_logged']} errors")

                st.markdown("#### 🔍 Step-by-Step Question Breakdown")
                for d in res["details"]:
                    icon = "✅" if d["is_correct"] else ("⚪" if not d["is_attempted"] else "❌")
                    status_str = "Correct" if d["is_correct"] else ("Unattempted" if not d["is_attempted"] else "Wrong")
                    with st.expander(f"{icon} Q: {d['question_text'][:70]}... — **{status_str}**"):
                        st.markdown(f"**Question**: {d['question_text']}")
                        st.markdown(f"**Your Answer**: `{d['submitted'] or '(None)'}` | **Correct Answer**: `{d['correct_answer']}`")
                        st.info(f"**Explanation**: {d['explanation']}")

    # -------------------------------------------------------------
    # TAB 2: UPLOAD & IMPORT DPP
    # -------------------------------------------------------------
    with tab_import:
        st.markdown("#### 📥 Import or Create Custom DPP")
        st.caption("Paste questions in standard text format or upload a practice assignment. JARVIS parses questions, detects type (MCQ/MSQ/NAT), and seeds it into the Practice Lab.")

        subjects = get_all_subjects()
        subj_map = {s["name"]: s["id"] for s in subjects}

        col_t, col_s = st.columns([0.6, 0.4])
        with col_t:
            import_title = st.text_input("DPP Title:", placeholder="e.g. SOM DPP 03: Torsion & Shafts")
            import_topic = st.text_input("Topic:", placeholder="e.g. Torsion of Shafts")
        with col_s:
            selected_subj_name = st.selectbox("Subject:", list(subj_map.keys()))
            selected_subj_id = subj_map[selected_subj_name]

        pasted_text = st.text_area(
            "Paste DPP Text / Questions:",
            height=200,
            placeholder="""Q1: A solid circular shaft of diameter 50 mm is subjected to a torque of 2 kNm. Find the maximum shear stress.
A) 81.5 MPa
B) 100 MPa
C) 50 MPa
D) 120 MPa
Answer: A
Explanation: Torsion formula tau = 16T / (pi * d^3).

Q2: Find the polar moment of inertia for the shaft.
Answer: 613592
"""
        )

        if st.button("📥 Parse & Import DPP into Practice Lab", use_container_width=True):
            if not import_title or not pasted_text.strip():
                st.error("Please provide both a DPP title and questions text.")
            else:
                new_dpp_id = parse_and_import_dpp_text(
                    raw_text=pasted_text,
                    title=import_title,
                    subject_id=selected_subj_id,
                    topic=import_topic
                )
                st.success(f"✅ DPP '{import_title}' successfully parsed and imported with ID #{new_dpp_id}!")
                st.rerun()

    # -------------------------------------------------------------
    # TAB 3: PRACTICE HISTORY & ANALYTICS
    # -------------------------------------------------------------
    with tab_history:
        st.markdown("#### 📊 Recent DPP Attempts")
        attempts = get_dpp_attempts(limit=30)
        if not attempts:
            st.info("No DPP attempts logged yet. Complete a practice drill above to view analytics.")
        else:
            df = pd.DataFrame(attempts)
            df_display = df[["dpp_title", "subject_name", "score", "max_score", "accuracy", "time_taken_sec", "completed_at"]].copy()
            df_display.columns = ["DPP Title", "Subject", "Score", "Max", "Accuracy (%)", "Time (s)", "Completed At"]
            st.dataframe(df_display, use_container_width=True)

            avg_acc = round(df["accuracy"].mean(), 1)
            total_time_min = round(df["time_taken_sec"].sum() / 60.0, 1)
            m1, m2, m3 = st.columns(3)
            m1.metric("Drills Completed", len(attempts))
            m2.metric("Average DPP Accuracy", f"{avg_acc}%")
            m3.metric("Total Practice Time", f"{total_time_min} mins")
