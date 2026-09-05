import json
import streamlit as st
from database.queries import (
    get_all_subjects, 
    save_problem_session, 
    get_problem_sessions, 
    delete_problem_session
)
from services.ai_service import get_ai_response

SAMPLE_GATE_PROBLEMS = [
    {
        "title": "SOM: Bar with Step Changes in Diameter (Axial Deflection)",
        "subject": "Strength of Materials",
        "difficulty": "Medium",
        "statement": "A steel bar of circular cross-section consists of two segments: Segment 1 (length L1 = 1 m, diameter d1 = 20 mm) and Segment 2 (length L2 = 1.5 m, diameter d2 = 40 mm). If an axial tensile force P = 40 kN is applied at the free end and Young's modulus E = 200 GPa, calculate the total axial extension in mm."
    },
    {
        "title": "Thermodynamics: Brayton Gas Turbine Thermal Efficiency",
        "subject": "Thermodynamics",
        "difficulty": "Medium",
        "statement": "An ideal Brayton cycle operates with a pressure ratio of rp = 6.25. If the working fluid is air with specific heat ratio γ = 1.4, calculate the thermal efficiency of the cycle in percentage."
    },
    {
        "title": "Fluid Mechanics: Venturimeter Flow Rate",
        "subject": "Fluid Mechanics",
        "difficulty": "Hard",
        "statement": "Water (ρ = 1000 kg/m³) flows through a horizontal pipe of diameter D1 = 100 mm fitted with a venturimeter having throat diameter D2 = 50 mm. A differential mercury manometer (ρ_m = 13600 kg/m³) connected across the inlet and throat indicates a deflection h = 200 mm. Taking coefficient of discharge Cd = 0.98, find the discharge in liters per second (L/s)."
    },
    {
        "title": "Machine Design: Thin Cylindrical Pressure Vessel",
        "subject": "Machine Design",
        "difficulty": "Easy",
        "statement": "A cylindrical boiler drum of inside diameter 1.2 m and wall thickness 12 mm is subjected to internal steam pressure of 2.5 MPa. Calculate the maximum shear stress induced in the cylinder wall in MPa."
    }
]

def render_problem_solver_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">🧮 Guided Numerical Problem-Solving Engine</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Master GATE numericals with rigorous step-by-step formula derivations, unit checks, and NAT format accuracy.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_solve, tab_verify, tab_bank = st.tabs([
        "⚡ 10-Step Engineering Lab", 
        "🔍 Verify My Solution (Auditor)", 
        "📚 Saved Worked-Examples Bank"
    ])

    subjects = get_all_subjects()
    subject_map = {s["name"]: s["id"] for s in subjects}
    subject_names = ["General Mechanical"] + [s["name"] for s in subjects]

    # -------------------------------------------------------------
    # TAB 1: 10-STEP ENGINEERING CALCULATION LAB
    # -------------------------------------------------------------
    with tab_solve:
        st.markdown("### 📝 Enter or Choose a GATE Numerical Problem")

        # Quick preset selector
        preset_cols = st.columns([0.7, 0.3])
        with preset_cols[0]:
            preset_choice = st.selectbox(
                "Or load a high-yield classic problem:",
                ["Custom Problem"] + [f"{p['title']} ({p['subject']})" for p in SAMPLE_GATE_PROBLEMS],
                index=0
            )

        initial_statement = ""
        initial_subject = "General Mechanical"
        initial_diff = "Medium"

        if preset_choice != "Custom Problem":
            idx = [f"{p['title']} ({p['subject']})" for p in SAMPLE_GATE_PROBLEMS].index(preset_choice)
            sample = SAMPLE_GATE_PROBLEMS[idx]
            initial_statement = sample["statement"]
            initial_subject = sample["subject"] if sample["subject"] in subject_names else "General Mechanical"
            initial_diff = sample["difficulty"]

        with st.form("problem_solver_form"):
            problem_text = st.text_area(
                "Problem Statement:",
                value=initial_statement,
                height=130,
                placeholder="Paste the problem statement here. Include all given numerical values, dimensions, boundary conditions, and what needs to be calculated."
            )

            c_sub, c_diff, c_btn = st.columns([0.45, 0.25, 0.30])
            with c_sub:
                selected_subject = st.selectbox("Subject:", options=subject_names, index=subject_names.index(initial_subject) if initial_subject in subject_names else 0)
            with c_diff:
                difficulty = st.selectbox("Difficulty:", ["Easy", "Medium", "Hard"], index=["Easy", "Medium", "Hard"].index(initial_diff))
            with c_btn:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                solve_submitted = st.form_submit_button("🚀 Solve in 10-Step Format", use_container_width=True)

        if solve_submitted:
            if not problem_text.strip():
                st.error("Please enter a problem statement.")
            else:
                with st.spinner("Analyzing problem, validating dimensions, and breaking into rigorous 10-step engineering format..."):
                    solver_prompt = f"""
You are the GATE Mechanical Engineering Problem-Solving Engine & Verification Authority.
Solve the following numerical problem in the strict 10-step Mechanical Engineering format:

Problem:
{problem_text}

Subject: {selected_subject}
Difficulty: {difficulty}

Follow this exact 10-step protocol:
1. **Given Parameters**: Extract all numerical values and convert explicitly into standard SI units.
2. **Required Unknowns**: State precisely what quantity is to be determined with target units.
3. **Explicit Assumptions**: State physical and mathematical assumptions (e.g., ideal gas, steady 1D flow, thin cylinder t < D/20, isotropic material).
4. **Governing Concept & Laws**: State the fundamental physical principle (e.g., First Law of Thermodynamics, Hooke's Law).
5. **Exact Governing Equations**: Provide the formula in clean LaTeX notation.
6. **Step-by-Step Substitution**: Show clean numerical substitution with units explicitly attached.
7. **Intermediate Calculations**: Show clear algebraic and arithmetic steps.
8. **Final Result & GATE NAT Format**: State the exact numerical answer, acceptable precision tolerance range (e.g. [24.5, 25.5]), and SI units.
9. **Dimensional Analysis & Unit Consistency**: Verify that LHS units equal RHS units.
10. **Engineering Sanity Check**: Provide physical plausibility checks (e.g., efficiency <= Carnot limit, stress <= yield stress).
"""
                    subj_id = subject_map.get(selected_subject)
                    ai_reply, sources = get_ai_response(
                        messages=[{"role": "user", "content": solver_prompt}],
                        use_rag=True,
                        subject_id=subj_id,
                        study_mode="🔢 Step-by-Step Numerical"
                    )

                    st.session_state["latest_solved_problem"] = {
                        "subject_id": subj_id,
                        "subject_name": selected_subject,
                        "problem_statement": problem_text,
                        "solution_text": ai_reply,
                        "difficulty": difficulty,
                        "sources": sources
                    }

        # Render current solution if available
        if "latest_solved_problem" in st.session_state:
            curr = st.session_state["latest_solved_problem"]
            st.markdown("<hr style='margin: 20px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
            st.markdown(f"### 🎯 Step-by-Step Solution Breakdown ({curr['difficulty']})")
            
            st.markdown(curr["solution_text"])

            if curr.get("sources"):
                with st.expander("📚 Knowledge Base Chunks Consulted"):
                    for s in curr["sources"]:
                        st.caption(f"- **{s.get('doc_name')}** (Page {s.get('page_number')}) — Similarity {int(s.get('similarity_score', 0)*100)}%")

            # Save to practice bank action
            c_save, _ = st.columns([0.35, 0.65])
            with c_save:
                if st.button("💾 Save to Practice Log", use_container_width=True):
                    # Save into problem_sessions table
                    steps_data = [{"step_number": 1, "step_title": "Detailed Numerical Solution", "formula_used": "See full derivation", "explanation": curr["solution_text"]}]
                    save_problem_session(
                        subject_id=curr["subject_id"],
                        problem_statement=curr["problem_statement"],
                        steps=steps_data,
                        final_answer="Solved (See Steps)",
                        difficulty=curr["difficulty"]
                    )
                    st.success("Successfully saved to your Worked-Examples Bank!")

    # -------------------------------------------------------------
    # TAB 2: VERIFY MY SOLUTION (Audit Finding F-10)
    # -------------------------------------------------------------
    with tab_verify:
        st.markdown("### 🔍 Mechanical Engineering Solution Auditor")
        st.caption("Upload or paste your hand-written derivation, calculations, and final answer. JARVIS will audit your equations, units, assumptions, and algebra to pinpoint the exact line of divergence.")

        with st.form("verify_solution_form"):
            v_problem = st.text_area(
                "Original Problem Statement:",
                height=90,
                placeholder="Paste the problem statement here..."
            )
            v_student_steps = st.text_area(
                "Your Attempted Solution / Derivation:",
                height=160,
                placeholder="Paste your line-by-line derivation, equations, numerical substitutions, or final answer here..."
            )
            v_sub_col, v_btn_col = st.columns([0.6, 0.4])
            with v_sub_col:
                v_subject = st.selectbox("Subject Domain:", options=subject_names, key="v_subject")
            with v_btn_col:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                v_submitted = st.form_submit_button("🔬 Run Verification Audit", use_container_width=True)

        if v_submitted:
            if not v_problem.strip() or not v_student_steps.strip():
                st.error("Please provide both the original problem statement and your attempted solution.")
            else:
                with st.spinner("Auditing equations, verifying algebra, checking units, and cross-referencing physical assumptions..."):
                    auditor_prompt = f"""
You are the GATE Mechanical Engineering Solution Verification Auditor.
Perform an objective, rigorous mathematical audit of the student's solution against the original problem.

Problem Statement:
{v_problem}

Subject Domain: {v_subject}

Student's Attempted Derivation:
{v_student_steps}

Audit Protocol:
1. **Physical Assumptions Audit**: Did the student use valid physical assumptions? (e.g. constant specific heats, thin vs thick cylinder limit, incompressible flow).
2. **Governing Equation Check**: Are the initial mathematical and physical equations correct?
3. **Algebraic & Arithmetic Verification**: Check line-by-line substitutions and arithmetic.
4. **Unit & Dimensional Consistency**: Check if units were converted properly (e.g. mm to m, bar to Pa, rpm to rad/s).
5. **Divergence Point**: If the answer or steps are incorrect, state the EXACT LINE of divergence.
6. **Error Taxonomy Classification**: Classify the error into exactly one of: [CONCEPT_ERROR, FORMULA_ERROR, CALCULATION_ERROR, UNIT_ERROR, SIGN_ERROR, ASSUMPTION_ERROR, QUESTION_MISINTERPRETATION, GUESSING_ERROR, CARELESS_ERROR, NONE_CORRECT].
7. **Corrected Concise Derivation**: Show the exact correct path to the GATE NAT answer.
"""
                    v_reply, _ = get_ai_response(
                        messages=[{"role": "user", "content": auditor_prompt}],
                        use_rag=True,
                        subject_id=subject_map.get(v_subject),
                        study_mode="🔬 Solution Verification Audit"
                    )

                    st.markdown("### 📋 Verification Audit Report")
                    st.markdown(v_reply)

    # -------------------------------------------------------------
    # TAB 3: WORKED-EXAMPLES BANK
    # -------------------------------------------------------------
    with tab_bank:
        st.subheader("📚 Personal Worked-Examples Bank")
        
        f1, f2, f3 = st.columns([0.35, 0.30, 0.35])
        with f1:
            bank_subj_filter = st.selectbox("Filter by Subject", ["All Subjects"] + subject_names, key="bank_subj_filter")
        with f2:
            bank_diff_filter = st.selectbox("Filter by Difficulty", ["All", "Easy", "Medium", "Hard"], key="bank_diff_filter")
        with f3:
            bank_search = st.text_input("🔍 Search Problems", placeholder="Keywords...", key="bank_search")

        filter_sid = subject_map.get(bank_subj_filter) if bank_subj_filter not in ["All Subjects", "General Mechanical"] else None
        saved_sessions = get_problem_sessions(
            subject_id=filter_sid,
            difficulty=bank_diff_filter if bank_diff_filter != "All" else None,
            search_query=bank_search
        )

        if not saved_sessions:
            st.info("No saved worked-examples yet. Solve any problem in Tab 1 and click 'Save to Practice Log' to build your repository.")
        else:
            st.markdown(f"**Found {len(saved_sessions)} worked problem(s)**")
            for sess in saved_sessions:
                diff_badge = "#10b981" if sess['difficulty'] == 'Easy' else "#f59e0b" if sess['difficulty'] == 'Medium' else "#ef4444"
                with st.container():
                    c_text, c_del = st.columns([0.85, 0.15])
                    with c_text:
                        st.markdown(f"""
                            <div style="margin-bottom: 6px;">
                                <span style="font-size: 11px; padding: 2px 8px; border-radius: 10px; background: {diff_badge}; color: var(--background); font-weight: 700;">{sess['difficulty'].upper()}</span>
                                <strong style="margin-left: 8px;">{sess['subject_name']}</strong>
                                <span style="color: var(--muted); font-size: 12px; margin-left: 12px;">🗓️ {sess['created_at'][:16]}</span>
                            </div>
                            <p style="font-size: 15px; margin-bottom: 8px; font-weight: 500;">{sess['problem_statement']}</p>
                        """, unsafe_allow_html=True)
                    with c_del:
                        if st.button("🗑️ Delete", key=f"del_prob_{sess['id']}", use_container_width=True):
                            delete_problem_session(sess["id"])
                            st.rerun()

                    with st.expander("📖 View Step-by-Step Derivation & Formula Steps"):
                        for stp in sess.get("steps", []):
                            st.markdown(f"#### {stp.get('step_title', 'Step')}")
                            if stp.get("formula_used"):
                                st.markdown(f"**Governing Formula:** {stp.get('formula_used')}")
                            st.markdown(stp.get("explanation", ""))
                            st.markdown("---")

                st.markdown("<hr style='margin: 10px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
