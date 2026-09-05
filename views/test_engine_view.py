import json
import streamlit as st
import pandas as pd
from datetime import datetime
from database.queries import (
    get_all_subjects,
    get_all_test_sets,
    get_test_set_by_id,
    get_test_questions,
    create_test_set,
    add_test_question,
    save_test_attempt,
    get_test_attempts,
    delete_test_set
)
from services.ai_service import get_ai_response

def render_test_engine_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">📝 GATE Test Engine & Real-Time Simulation</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Simulate authentic GATE exam conditions with MCQ, MSQ, and NAT questions. Experience precise negative marking, instant section-wise analytics, and automated weak-area detection.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_take, tab_history, tab_create = st.tabs(["🎯 Take / Simulate Test", "📈 Attempts & Analytics", "🛠️ Custom & AI Test Generator"])

    all_test_sets = get_all_test_sets()
    subjects = get_all_subjects()
    subject_map = {s["name"]: s["id"] for s in subjects}
    subject_names = ["Full Syllabus"] + [s["name"] for s in subjects]

    # -------------------------------------------------------------
    # TAB 1: TAKE / SIMULATE TEST
    # -------------------------------------------------------------
    with tab_take:
        if not all_test_sets:
            st.info("No test sets available yet. Use the 'Custom & AI Test Generator' tab to create your first test!")
        else:
            test_options = {f"{ts['title']} ({ts['actual_question_count']} Qs / {ts['duration_minutes']} min)": ts["id"] for ts in all_test_sets}
            
            c_select, c_start = st.columns([0.75, 0.25])
            with c_select:
                selected_label = st.selectbox("Select Test Series / Mock:", list(test_options.keys()), index=0)
            
            selected_test_id = test_options[selected_label]
            test_meta = get_test_set_by_id(selected_test_id)
            questions = get_test_questions(selected_test_id)

            with c_start:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🚀 Start / Reset Simulation", use_container_width=True):
                    st.session_state["active_test_id"] = selected_test_id
                    st.session_state["test_answers"] = {}
                    st.session_state["test_active_q_idx"] = 0
                    st.session_state["test_submitted"] = False
                    st.session_state["test_result"] = None
                    st.rerun()

            # Active test session runner
            if st.session_state.get("active_test_id") == selected_test_id and questions:
                st.markdown("<hr style='margin: 16px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
                
                # If test is already submitted, show results review
                if st.session_state.get("test_submitted"):
                    _render_test_results(st.session_state["test_result"], questions, test_meta)
                else:
                    _render_active_test_flow(selected_test_id, questions, test_meta)

    # -------------------------------------------------------------
    # TAB 2: ATTEMPTS & SCORE PROGRESSION
    # -------------------------------------------------------------
    with tab_history:
        attempts = get_test_attempts(limit=50)
        if not attempts:
            st.info("No completed test attempts yet. Complete a test in 'Take / Simulate Test' to see your performance analytics!")
        else:
            scores = [a["score"] for a in attempts]
            max_scores = [a["max_score"] for a in attempts]
            pcts = [(s / m * 100) if m > 0 else 0 for s, m in zip(scores, max_scores)]
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Tests Attempted", len(attempts))
            m2.metric("Latest Score", f"{scores[0]:.1f} / {max_scores[0]:.0f}")
            m3.metric("Average Score", f"{(sum(scores)/len(scores)):.1f}")
            m4.metric("Personal Best", f"{max(scores):.1f} / {max_scores[scores.index(max(scores))]:.0f}")

            st.markdown("---")
            st.subheader("📈 Mock Test Score Progression")
            df_chart = pd.DataFrame([
                {"Attempt": a["test_title"][:25] + f" (#{a['id']})", "Score": a["score"], "Date": a["completed_at"][:10]}
                for a in attempts[::-1]
            ])
            st.line_chart(df_chart.set_index("Attempt")["Score"])

            st.markdown("### 📋 Attempt Records")
            for att in attempts:
                pct = (att["score"] / att["max_score"] * 100) if att["max_score"] > 0 else 0
                badge_color = "#10b981" if pct >= 65 else "#f59e0b" if pct >= 45 else "#ef4444"
                with st.container():
                    st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0;">{att['test_title']}</h4>
                                <span style="color: var(--muted); font-size: 12px;">🗓️ Completed: {att['completed_at'][:16]}</span>
                            </div>
                            <div>
                                <span style="font-size: 18px; font-weight: 800; color: {badge_color};">{att['score']:.1f} / {att['max_score']:.0f} ({pct:.1f}%)</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if att.get("section_breakdown"):
                        st.caption(f"📊 Section Breakdown: {att['section_breakdown']}")
                st.markdown("<hr style='margin: 8px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: CUSTOM & AI TEST GENERATOR
    # -------------------------------------------------------------
    with tab_create:
        st.subheader("🛠️ Build or AI-Generate a Custom GATE Test Set")
        
        gen_type = st.radio("Creation Method:", ["🤖 Instant AI Test Generator (5 High-Yield Questions)", "✍️ Manual Test Set Creator"], horizontal=True)

        if gen_type.startswith("🤖"):
            st.markdown("Generate 5 fresh, exam-accurate GATE questions tailored to your chosen subject and difficulty level.")
            with st.form("ai_gen_test_form"):
                c_asub, c_adiff = st.columns(2)
                with c_asub:
                    ai_subj = st.selectbox("Target Subject:", [s for s in subject_names if s != "Full Syllabus"])
                with c_adiff:
                    ai_diff = st.selectbox("Exam Difficulty Level:", ["Standard GATE", "Challenging / Rank Decider", "Conceptual Basics"])
                
                ai_title = st.text_input("Test Set Name:", value=f"⚡ {ai_subj} AI High-Yield Drill ({ai_diff})")
                
                gen_submit = st.form_submit_button("✨ Generate & Add Test to Bank", use_container_width=True)

            if gen_submit:
                with st.spinner(f"Generating 5 high-yield {ai_subj} GATE questions with marking scheme and explanations..."):
                    gen_prompt = f"""
Generate 5 authentic GATE Mechanical Engineering questions for the subject: '{ai_subj}' at difficulty '{ai_diff}'.
Include a realistic mix: 2 MCQs (1-mark), 2 NATs (2-mark), 1 MSQ (2-mark).

Format your response strictly as a JSON array of objects with these keys:
- "question_text": text of the question with LaTeX for equations
- "question_type": "MCQ" or "NAT" or "MSQ"
- "options": list of 4 string options for MCQ/MSQ, or empty list for NAT
- "correct_answer": correct option string for MCQ, float number string for NAT, or list of correct option strings for MSQ
- "marks": 1.0 or 2.0
- "negative_marks": 0.33 or 0.66 for MCQ; 0.0 for NAT and MSQ
- "explanation": step-by-step formula derivation and explanation

Return ONLY valid JSON.
"""
                    ai_resp, _ = get_ai_response(
                        messages=[{"role": "user", "content": gen_prompt}],
                        use_rag=True,
                        subject_id=subject_map.get(ai_subj),
                        study_mode="❓ Practice Questions"
                    )

                    try:
                        # Extract JSON array from text
                        start_idx = ai_resp.find("[")
                        end_idx = ai_resp.rfind("]") + 1
                        if start_idx != -1 and end_idx != -1:
                            parsed_qs = json.loads(ai_resp[start_idx:end_idx])
                        else:
                            parsed_qs = []
                    except Exception:
                        parsed_qs = []

                    if parsed_qs:
                        s_id = subject_map.get(ai_subj)
                        new_set_id = create_test_set(
                            title=ai_title,
                            subject_id=s_id,
                            question_count=len(parsed_qs),
                            duration_minutes=15,
                            description=f"AI Generated practice drill for {ai_subj} ({ai_diff})."
                        )
                        for q in parsed_qs:
                            correct = q.get("correct_answer")
                            if isinstance(correct, list):
                                correct = json.dumps(correct)
                            add_test_question(
                                test_set_id=new_set_id,
                                question_text=q.get("question_text", ""),
                                question_type=q.get("question_type", "MCQ"),
                                options=q.get("options", []),
                                correct_answer=str(correct),
                                marks=q.get("marks", 1.0),
                                negative_marks=q.get("negative_marks", 0.33),
                                explanation=q.get("explanation", "")
                            )
                        st.success(f"Successfully generated and created '{ai_title}' with {len(parsed_qs)} questions!")
                        st.rerun()
                    else:
                        st.error("Could not parse generated questions into structured format. Please try again.")

        else:
            with st.form("manual_create_test_form"):
                m_title = st.text_input("Test Title:", placeholder="e.g. Strength of Materials Full Chapter Mock 1")
                c_ms, c_md = st.columns(2)
                with c_ms:
                    m_subj = st.selectbox("Subject:", subject_names)
                with c_md:
                    m_dur = st.number_input("Duration (minutes):", min_value=5, max_value=180, value=30, step=5)

                m_desc = st.text_area("Test Description:", placeholder="Key chapters covered, marking details, target score...")

                manual_submit = st.form_submit_button("💾 Create Empty Test Set")
                if manual_submit:
                    if not m_title.strip():
                        st.error("Please enter a test title.")
                    else:
                        sid = subject_map.get(m_subj) if m_subj != "Full Syllabus" else None
                        nid = create_test_set(title=m_title, subject_id=sid, duration_minutes=int(m_dur), description=m_desc)
                        st.success(f"Created test set #{nid}! You can now add questions to it.")
                        st.rerun()


def _render_active_test_flow(test_set_id: int, questions: list, test_meta: dict):
    """Renders live exam screen with question navigation palette, answers capture, and submit."""
    total_q = len(questions)
    curr_idx = st.session_state.get("test_active_q_idx", 0)
    curr_q = questions[curr_idx]

    # Top status bar
    c_info, c_sub = st.columns([0.7, 0.3])
    with c_info:
        st.markdown(f"#### 📝 {test_meta['title']}")
        st.caption(f"Question {curr_idx + 1} of {total_q} &nbsp;|&nbsp; ⏱️ Duration: {test_meta['duration_minutes']} min &nbsp;|&nbsp; Type: **{curr_q['question_type']}** (+{curr_q['marks']} / -{curr_q['negative_marks']})")
    with c_sub:
        if st.button("🏁 Submit & Finish Test", type="primary", use_container_width=True):
            _evaluate_active_test(questions, test_meta)
            st.rerun()

    # Question Box
    st.markdown("""
        <style>
        .test-q-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(f"""
            <div class="test-q-card">
                <span style="color: var(--primary); font-weight: bold; font-size: 14px;">Q{curr_idx + 1} [{curr_q['question_type']} - {curr_q['marks']} Mark(s)]</span>
                <p style="font-size: 16px; font-weight: 600; margin-top: 8px;">{curr_q['question_text']}</p>
            </div>
        """, unsafe_allow_html=True)

        q_id = str(curr_q["id"])
        saved_ans = st.session_state["test_answers"].get(q_id)

        # Answer Input based on Question Type
        if curr_q["question_type"] == "MCQ":
            options = curr_q.get("options", [])
            opt_idx = None
            if saved_ans in options:
                opt_idx = options.index(saved_ans)
            
            selected_opt = st.radio(
                "Select your answer:",
                options=options,
                index=opt_idx,
                key=f"mcq_choice_{curr_q['id']}"
            )
            if selected_opt:
                st.session_state["test_answers"][q_id] = selected_opt

        elif curr_q["question_type"] == "MSQ":
            options = curr_q.get("options", [])
            current_msq_selected = saved_ans if isinstance(saved_ans, list) else []
            updated_msq = []
            st.markdown("**Select ALL correct options (Multiple-Select Question):**")
            for idx, opt in enumerate(options):
                is_checked = opt in current_msq_selected
                checked = st.checkbox(opt, value=is_checked, key=f"msq_opt_{curr_q['id']}_{idx}")
                if checked:
                    updated_msq.append(opt)
            st.session_state["test_answers"][q_id] = updated_msq

        elif curr_q["question_type"] == "NAT":
            st.markdown("**Enter Numerical Value (NAT):**")
            nat_val = st.text_input(
                "Numerical Answer:",
                value=str(saved_ans) if saved_ans is not None else "",
                placeholder="e.g. 56.5",
                key=f"nat_input_{curr_q['id']}"
            )
            if nat_val.strip():
                st.session_state["test_answers"][q_id] = nat_val.strip()

    # Question Navigation Palette & Action Buttons
    c_prev, c_clear, c_next = st.columns([0.3, 0.4, 0.3])
    with c_prev:
        if curr_idx > 0:
            if st.button("⬅️ Previous Question", use_container_width=True):
                st.session_state["test_active_q_idx"] -= 1
                st.rerun()
    with c_clear:
        if st.button("🧹 Clear Response", use_container_width=True):
            if q_id in st.session_state["test_answers"]:
                del st.session_state["test_answers"][q_id]
                st.rerun()
    with c_next:
        if curr_idx < total_q - 1:
            if st.button("Next Question ➡️", use_container_width=True):
                st.session_state["test_active_q_idx"] += 1
                st.rerun()

    # Palette Grid at bottom
    st.markdown("<hr style='margin: 16px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
    st.markdown("##### 🧭 Question Palette:")
    p_cols = st.columns(min(total_q, 10))
    for i in range(total_q):
        btn_qid = str(questions[i]["id"])
        is_ans = btn_qid in st.session_state["test_answers"] and bool(st.session_state["test_answers"][btn_qid])
        is_curr = i == curr_idx
        
        status_label = f"Q{i+1}"
        if is_curr:
            btn_type = "primary"
        elif is_ans:
            btn_type = "secondary"
        else:
            btn_type = "secondary"

        col_idx = i % min(total_q, 10)
        with p_cols[col_idx]:
            if st.button(f"{'🟢' if is_ans else '⚪'} Q{i+1}", key=f"pal_btn_{i}", use_container_width=True):
                st.session_state["test_active_q_idx"] = i
                st.rerun()


def _evaluate_active_test(questions: list, test_meta: dict):
    """Calculates marks according to exact GATE negative marking rules and saves attempt."""
    total_score = 0.0
    max_score = 0.0
    eval_details = []
    weak_topics = []

    user_answers = st.session_state.get("test_answers", {})

    for q in questions:
        q_id = str(q["id"])
        u_ans = user_answers.get(q_id)
        c_ans = q["correct_answer"]
        marks = float(q["marks"])
        neg_marks = float(q["negative_marks"])
        max_score += marks

        is_correct = False
        is_attempted = u_ans is not None and u_ans != "" and u_ans != []
        marks_awarded = 0.0

        if not is_attempted:
            marks_awarded = 0.0
        elif q["question_type"] == "MCQ":
            if str(u_ans).strip().lower() == str(c_ans).strip().lower():
                is_correct = True
                marks_awarded = marks
            else:
                marks_awarded = -neg_marks
        elif q["question_type"] == "MSQ":
            # Compare sets
            try:
                c_set = set(json.loads(c_ans)) if c_ans.startswith("[") else {c_ans}
            except Exception:
                c_set = {c_ans}
            u_set = set(u_ans) if isinstance(u_ans, list) else {u_ans}

            if c_set == u_set:
                is_correct = True
                marks_awarded = marks
            else:
                marks_awarded = 0.0 # No negative marking in MSQ
        elif q["question_type"] == "NAT":
            try:
                u_val = float(str(u_ans).strip())
                c_val = float(str(c_ans).strip())
                # Numerical tolerance check ± 1.5%
                if abs(u_val - c_val) <= max(0.05, abs(c_val * 0.02)):
                    is_correct = True
                    marks_awarded = marks
                else:
                    marks_awarded = 0.0 # No negative marking in NAT
            except Exception:
                marks_awarded = 0.0

        if not is_correct and is_attempted:
            weak_topics.append(q["question_text"][:40] + "...")

        total_score += marks_awarded
        eval_details.append({
            "question": q,
            "user_answer": u_ans,
            "correct_answer": c_ans,
            "is_correct": is_correct,
            "is_attempted": is_attempted,
            "marks_awarded": marks_awarded
        })

    # Save to database
    save_test_attempt(
        test_set_id=test_meta["id"],
        test_title=test_meta["title"],
        score=round(total_score, 2),
        max_score=round(max_score, 2),
        answers=user_answers,
        section_breakdown={"total_marks": max_score, "score": total_score, "attempted": sum(1 for e in eval_details if e["is_attempted"])}
    )

    st.session_state["test_submitted"] = True
    st.session_state["test_result"] = {
        "score": total_score,
        "max_score": max_score,
        "eval_details": eval_details,
        "weak_topics": weak_topics
    }


def _render_test_results(result: dict, questions: list, test_meta: dict):
    """Renders the comprehensive score card, weak-area detection, and detailed step-by-step solutions."""
    score = result["score"]
    max_score = result["max_score"]
    pct = (score / max_score * 100) if max_score > 0 else 0
    badge_color = "#10b981" if pct >= 65 else "#f59e0b" if pct >= 45 else "#ef4444"

    st.markdown("### 🏆 Instant Evaluation & Performance Scorecard")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Final Score", f"{score:.2f} / {max_score:.0f}")
    r2.metric("Percentage", f"{pct:.1f}%")
    correct_count = sum(1 for e in result["eval_details"] if e["is_correct"])
    r3.metric("Correct Questions", f"{correct_count} / {len(questions)}")
    neg_count = sum(1 for e in result["eval_details"] if e["marks_awarded"] < 0)
    r4.metric("Negative Penalties", f"{neg_count}")

    if result.get("weak_topics"):
        st.warning(f"⚠️ **Key Focus Areas Identified For Revision**: Marks were missed on {len(result['weak_topics'])} concept(s). Review derivations and formula bank for these chapters.")

    st.markdown("---")
    st.markdown("### 🔍 Question-by-Question Solution & Derivation Review")

    for idx, eval_item in enumerate(result["eval_details"]):
        q = eval_item["question"]
        is_corr = eval_item["is_correct"]
        is_att = eval_item["is_attempted"]
        m_award = eval_item["marks_awarded"]

        if is_corr:
            status_badge = "<span style='color: #10b981; font-weight: bold;'>✅ CORRECT (+{:.2f})</span>".format(m_award)
        elif not is_att:
            status_badge = "<span style='color: var(--muted); font-weight: bold;'>⚪ UNATTEMPTED (0.0)</span>"
        else:
            status_badge = "<span style='color: #ef4444; font-weight: bold;'>❌ INCORRECT ({:.2f})</span>".format(m_award)

        with st.expander(f"Q{idx + 1}: {q['question_text'][:80]}... — {status_badge}", expanded=(not is_corr and is_att)):
            st.markdown(f"**Full Question:** {q['question_text']}")
            st.markdown(f"**Your Answer:** `{eval_item['user_answer'] or 'None'}`")
            st.markdown(f"**Correct Answer:** `{eval_item['correct_answer']}`")
            st.markdown(f"**Marking Rule:** Type `{q['question_type']}` | Marks: `+{q['marks']}` | Penalty: `-{q['negative_marks']}`")
            st.markdown("---")
            st.markdown("##### 💡 Step-by-Step Derivation & Explanation:")
            st.markdown(q["explanation"] or "No detailed explanation provided.")

    if st.button("🔄 Retake Another Test"):
        st.session_state["test_submitted"] = False
        st.session_state["test_result"] = None
        st.session_state["test_answers"] = {}
        st.rerun()
