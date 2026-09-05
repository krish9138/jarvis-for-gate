import streamlit as st

def render_resources_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">🏆 GATE Mechanical — Strategy & Case Studies</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Proven high-rank preparation archetypes, exam blueprint, subject weightage, and high-yield study tactics.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Exam Blueprint & Weightage",
        "👥 Topper Strategy Profiles",
        "🗺️ 4-Year Roadmap Skeleton",
        "⚡ Study Tactics & EV Calculator",
        "📚 Official Syllabus Links"
    ])

    # -------------------------------------------------------------
    # TAB 1: EXAM BLUEPRINT & WEIGHTAGE
    # -------------------------------------------------------------
    with tab1:
        st.subheader("1. GATE Mechanical Exam Pattern at a Glance")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Duration", "180 Mins", "3 Hours")
        c2.metric("Total Marks", "100 Marks", "65 Questions")
        c3.metric("Core ME Share", "~72 Marks", "Highest weight")
        c4.metric("Aptitude + Math", "28 Marks", "Never skip")

        st.markdown("""
        | Parameter | Detail |
        | :--- | :--- |
        | **Exam Mode** | Computer-based Test (CBT) |
        | **Total Questions** | 65 (10 General Aptitude + 55 Technical & Math) |
        | **Question Types** | Multiple Choice (MCQ), Multiple Select (MSQ), Numerical Answer Type (NAT) |
        | **Section Split** | General Aptitude (15 marks) + Engg Mathematics (~13 marks) + Core Mechanical (~72 marks) |
        | **Negative Marking** | −1/3 for 1-mark MCQs, −2/3 for 2-mark MCQs; **Zero negative marking** on MSQ & NAT |
        """)

        st.markdown("---")
        st.subheader("2. High-Yield Subject Weightage & Priority Matrix")
        
        st.markdown("""
        | Subject | Typical Weightage | Priority Level | Strategic Action |
        | :--- | :--- | :--- | :--- |
        | **General Aptitude** | 15 Marks (Fixed) | 🔴 Never Skip | Daily 15-min practice habit; easiest scoring section |
        | **Engineering Mathematics** | 13–15 Marks | 🔴 Core | Linear Algebra, Calculus, Differential Eq, Vector Calculus |
        | **Manufacturing & Material Science** | 14–16 Marks | 🔴 Core | High weightage in GATE; Machining, Welding, Casting, Metrology |
        | **Thermodynamics & Applications** | 10–12 Marks | 🔴 Core | 1st/2nd Law, Availability, Rankine/Brayton cycles, Psychrometry |
        | **Fluid Mechanics & Hydraulics** | 8–10 Marks | 🔴 Core | Bernoulli, Boundary layer, Navier-Stokes, Pipe flow |
        | **Strength of Materials (SOM)** | 8–10 Marks | 🔴 Core | Mohr's circle, Deflection of beams, Thin/Thick cylinders, Euler buckling |
        | **Theory of Machines & Vibrations** | 8–10 Marks | 🔴 Core | Single DOF vibration, Gear trains, Mechanisms, Flywheels |
        | **Heat Transfer** | 6–8 Marks | 🟠 Important | Conduction critical radius, Radiation shape factors, NTU method |
        | **Industrial Engineering** | 5–7 Marks | 🟠 Important | LPP Simplex, PERT/CPM, Inventory EOQ, Forecasting |
        | **Machine Design** | 4–6 Marks | 🟠 Important | Fatigue Soderberg/Goodman, Brake design, Bearing life |
        | **IC Engines & RAC** | 3–5 Marks | 🟡 Supplementary | Air-standard cycles, Refrigeration COP, VCRS components |
        """)

    # -------------------------------------------------------------
    # TAB 2: TOPPER STRATEGY PROFILES
    # -------------------------------------------------------------
    with tab2:
        st.subheader("👥 Composite Strategy Profiles (Case Studies)")
        st.caption("Archetypes synthesized from consistent AIR < 50 toppers and top coaching methodologies.")

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            st.markdown("""
            <div style="border: 1px solid #38bdf8; border-radius: 10px; padding: 16px; height: 100%;">
                <h4 style="color: #38bdf8; margin-top: 0;">🚀 Profile A: "Fundamentals First"</h4>
                <p style="font-size: 13px; color: #94a3b8;"><em>AIR &lt; 50 Archetype</em></p>
                <ul style="font-size: 13px; padding-left: 18px;">
                    <li>Spent the first 4–6 months building <strong>first-principles clarity</strong> before touching PYQs.</li>
                    <li>Maintained a single consolidated <strong>Formula Notebook</strong> (under 40 pages).</li>
                    <li>Solved 15 years of GATE PYQs twice: once untimed for intuition, once timed for speed.</li>
                    <li>Tracked every calculation slip in a <strong>Mistake Log</strong> reviewed weekly.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_p2:
            st.markdown("""
            <div style="border: 1px solid #10b981; border-radius: 10px; padding: 16px; height: 100%;">
                <h4 style="color: #10b981; margin-top: 0;">⏱️ Profile B: "Consistency Compounder"</h4>
                <p style="font-size: 13px; color: #94a3b8;"><em>Sustainable 4-Year Discipline</em></p>
                <ul style="font-size: 13px; padding-left: 18px;">
                    <li>Studied 4–5 focused hours daily without breaking the streak for 3+ years.</li>
                    <li>Strict weekly rotation: 3 Core subjects + 1 Supplementary + 1 Weekly Mock.</li>
                    <li>Treated General Aptitude as a non-negotiable 15-min daily habit.</li>
                    <li>Balanced college semester GPA with GATE syllabus overlap.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_p3:
            st.markdown("""
            <div style="border: 1px solid #f59e0b; border-radius: 10px; padding: 16px; height: 100%;">
                <h4 style="color: #f59e0b; margin-top: 0;">📊 Profile C: "Analytics-Driven Prep"</h4>
                <p style="font-size: 13px; color: #94a3b8;"><em>Data-Heavy Error Minimizer</em></p>
                <ul style="font-size: 13px; padding-left: 18px;">
                    <li>Logged every study session with subject, duration, and confidence score.</li>
                    <li>Reviewed weekly hours-vs-target to eliminate weak subject gaps.</li>
                    <li>Attempted a full mock test every 10–14 days from Month 8 onward.</li>
                    <li>Dedicated 2 hours after every mock purely to root-cause error analysis.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: 4-YEAR ROADMAP SKELETON
    # -------------------------------------------------------------
    with tab3:
        st.subheader("🗺️ 4-Year GATE Strategy Blueprint (2026–2030)")
        
        st.markdown("""
        | Phase & Year | Focus & Curriculum | Target Milestones |
        | :--- | :--- | :--- |
        | **Year 1 (Foundation)**<br>*(2026–2027)* | Engg Math (Linear Algebra, Calculus), Physics, Basic Electrical, Programming, Graphics, Workshop | Strong conceptual grounding, college GPA > 8.5, mental math fluency |
        | **Year 2 (Core Building)**<br>*(2027–2028)* | SOM, Fluid Mechanics, Thermodynamics, Theory of Machines, Material Science | Standard textbook derivations, concept clarity, 1st round of chapter notes |
        | **Year 3 (Integration & PYQs)**<br>*(2028–2029)* | Heat Transfer, Machine Design, Manufacturing, Industrial Engg, PYQs (2000–2028) | Complete full GATE syllabus, subject-wise test series, formula consolidation |
        | **Year 4 (Rank Push & Mocks)**<br>*(2029–2030)* | Full-length Mock Tests (30+ tests), Error Log elimination, Speed drills, Final 60-day revision | Consistent 80+ marks in national mocks, AIR < 100 on exam day |
        """)

    # -------------------------------------------------------------
    # TAB 4: STUDY TACTICS & EV CALCULATOR
    # -------------------------------------------------------------
    with tab4:
        st.subheader("⚡ Quick-Reference Study Tactics")
        st.markdown("""
        - **Spaced Repetition Beats Linear Re-Reading**: Review formula sheets at spaced intervals (1 Day $\\rightarrow$ 3 Days $\\rightarrow$ 7 Days $\\rightarrow$ 21 Days).
        - **NAT (Numerical Answer Type) Precision**: Dedicate 10 minutes daily purely to fast, clean arithmetic without virtual calculator blunders.
        - **Active Recall with JARVIS**: Ask JARVIS conceptual questions and test yourself before viewing the step-by-step solution.
        """)

        st.markdown("---")
        st.subheader("🧮 Negative Marking Expected Value (EV) Calculator")
        st.caption("Calculate whether guessing an uncertain MCQ is mathematically profitable (+EV).")

        calc_col1, calc_col2 = st.columns(2)
        with calc_col1:
            q_marks = st.radio("Question Marks", [1.0, 2.0], horizontal=True)
            eliminated_options = st.slider("Options Eliminated with 100% Certainty", 0, 3, 2)
            
        with calc_col2:
            remaining_options = 4 - eliminated_options
            prob_correct = 1.0 / remaining_options
            prob_wrong = 1.0 - prob_correct
            neg_mark = (1.0 / 3.0) * q_marks

            ev = (prob_correct * q_marks) - (prob_wrong * neg_mark)

            if ev > 0:
                st.success(f"📈 **Expected Value: +{ev:.3f} marks** (Profitable to guess!)")
                st.caption(f"Random guess chance: {prob_correct*100:.1f}%. Since you eliminated {eliminated_options} options, guessing has positive statistical expected return.")
            else:
                st.error(f"📉 **Expected Value: {ev:.3f} marks** (Do NOT guess purely at random!)")
                st.caption("Without eliminating options, blind guessing on 4 options produces EV = 0.00.")

    # -------------------------------------------------------------
    # TAB 5: OFFICIAL SYLLABUS
    # -------------------------------------------------------------
    with tab5:
        st.subheader("📚 GATE Mechanical Engineering Syllabus Sections")
        st.markdown("""
        - **Section 1: Engineering Mathematics**: Linear Algebra, Calculus, Differential Equations, Complex Variables, Probability & Statistics, Numerical Methods.
        - **Section 2: Applied Mechanics & Design**: Engineering Mechanics, Strength of Materials, Theory of Machines, Vibrations, Machine Design.
        - **Section 3: Fluid Mechanics & Thermal Sciences**: Fluid Mechanics, Heat Transfer, Thermodynamics, Applications (Power Engineering, IC Engines, Refrigeration & AC, Turbomachinery).
        - **Section 4: Materials, Manufacturing & Industrial Engineering**: Engineering Materials, Casting, Forming, Joining Processes, Machining, Metrology, Computer Integrated Manufacturing, Production Planning & Control, Operations Research.
        - **Section 5: General Aptitude**: Verbal Aptitude, Quantitative Aptitude, Spatial Aptitude, Analytical Aptitude.
        """)
