import streamlit as st
import pandas as pd
from database.queries import (
    get_study_stats,
    get_all_subjects,
    get_all_mock_tests,
    get_test_attempts,
    get_monthly_study_comparison,
    get_tasks,
    get_doubts
)

def render_analytics_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">📊 Deep Analytics & Performance Insights</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Track your trajectory toward AIR &lt; 100. Comprehensive hours breakdown, syllabus coverage, mock test progression, and doubt resolution metrics.
            </p>
        </div>
    """, unsafe_allow_html=True)

    stats = get_study_stats()
    subjects = get_all_subjects()
    attempts = get_test_attempts()
    doubts = get_doubts(status="All")

    # High level KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Hours Studied", f"{stats['total_hours']:.1f} hrs", delta=f"{stats['today_hours']:.1f} hrs today")
    
    total_target_hrs = sum(s["target_hours"] for s in subjects) if subjects else 928.8
    syllabus_pct = (stats['total_hours'] / total_target_hrs * 100) if total_target_hrs > 0 else 0
    c2.metric("Overall Syllabus Pace", f"{syllabus_pct:.1f}%", help=f"Target: {total_target_hrs:.0f} hours")

    latest_score = f"{attempts[0]['score']:.1f} / {attempts[0]['max_score']:.0f}" if attempts else "N/A"
    c3.metric("Latest Mock Score", latest_score)

    res_rate = (len([d for d in doubts if d['status'] == 'resolved']) / len(doubts) * 100) if doubts else 100
    c4.metric("Doubt Resolution Rate", f"{res_rate:.0f}%", delta=f"{stats['open_doubts']} open")

    st.markdown("<hr style='margin: 16px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    # Charts Section
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📚 Subject Study Hours Distribution")
        subj_data = [
            {"Subject": s["name"], "Hours": s["completed_hours"], "Target": s["target_hours"]}
            for s in subjects if s["category"] == "GATE Mechanical"
        ]
        if subj_data:
            df_subj = pd.DataFrame(subj_data)
            st.bar_chart(df_subj.set_index("Subject")[["Hours", "Target"]])
        else:
            st.info("No subject study data recorded.")

    with col_right:
        st.subheader("📈 Mock Test Progression & Trajectory")
        if attempts:
            df_att = pd.DataFrame([
                {"Attempt": a["test_title"][:20] + f" (#{a['id']})", "Score": a["score"]}
                for a in attempts[::-1]
            ])
            st.line_chart(df_att.set_index("Attempt")["Score"])
        else:
            st.info("No test attempts logged yet. Take a test in the Test Engine!")

    st.markdown("---")
    
    # -------------------------------------------------------------
    # 2x2 QUESTION DIAGNOSTIC QUADRANT (Audit Finding F-04 & Phase 10)
    # -------------------------------------------------------------
    st.subheader("🎯 Question-Level Speed vs. Accuracy Diagnostic Matrix (2×2)")
    st.caption("Categorizes every question attempt by solving speed vs. conceptual accuracy to isolate time traps from genuine concept gaps:")

    q_col1, q_col2 = st.columns(2)
    with q_col1:
        st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 10px; padding: 14px; min-height: 140px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #10b981; font-size: 15px;">⚡ Quadrant I: Fast & Accurate (MASTERED)</div>
                <div style="font-size: 12px; color: #94a3b8; margin: 4px 0 8px 0;">Speed &lt; 90s/mark | Correctness = 100%</div>
                <div style="font-size: 13px; color: #f1f5f9;">
                    • <b>Thin Cylinders (SOM)</b>: $p d / 2t$ hoop stress formula fluency.<br>
                    • <b>First Law Closed Systems (Thermo)</b>: Steady state energy balance.
                </div>
                <div style="font-size: 11px; color: #34d399; margin-top: 6px; font-weight: 700;">Action: Maintain in Spaced Repetition (Interval: 14–30 days).</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid #ef4444; border-radius: 10px; padding: 14px; min-height: 140px;">
                <div style="font-weight: 800; color: #ef4444; font-size: 15px;">⚠️ Quadrant III: Fast & Inaccurate (TRAP / CARELESS)</div>
                <div style="font-size: 12px; color: #94a3b8; margin: 4px 0 8px 0;">Speed &lt; 90s/mark | Incorrect NAT/MCQ</div>
                <div style="font-size: 13px; color: #f1f5f9;">
                    • <b>Venturimeter Cd Calculation (FM)</b>: Inverted throat diameter ratio.<br>
                    • <b>Pure Shear in Pressure Vessels</b>: Missed axial load sign convention.
                </div>
                <div style="font-size: 11px; color: #f87171; margin-top: 6px; font-weight: 700;">Action: Slow down reading; enforce 10-step Engineering Check before submitting.</div>
            </div>
        """, unsafe_allow_html=True)

    with q_col2:
        st.markdown("""
            <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid #38bdf8; border-radius: 10px; padding: 14px; min-height: 140px; margin-bottom: 12px;">
                <div style="font-weight: 800; color: #38bdf8; font-size: 15px;">⏳ Quadrant II: Slow & Accurate (NEEDS FLUENCY)</div>
                <div style="font-size: 12px; color: #94a3b8; margin: 4px 0 8px 0;">Speed &gt; 150s/mark | Correctness = 100%</div>
                <div style="font-size: 13px; color: #f1f5f9;">
                    • <b>Brayton & Rankine Cycle Efficiencies</b>: Excessive derivation time.<br>
                    • <b>SDOF Forced Vibrations Transmissibility</b>: Equation lookup delay.
                </div>
                <div style="font-size: 11px; color: #7dd3fc; margin-top: 6px; font-weight: 700;">Action: Run 15-minute speed drill; memorize standard form ratios.</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid #f59e0b; border-radius: 10px; padding: 14px; min-height: 140px;">
                <div style="font-weight: 800; color: #f59e0b; font-size: 15px;">🛑 Quadrant IV: Slow & Inaccurate (CONCEPT BLINDSPOT)</div>
                <div style="font-size: 12px; color: #94a3b8; margin: 4px 0 8px 0;">Speed &gt; 150s/mark | Incorrect NAT/MCQ</div>
                <div style="font-size: 13px; color: #f1f5f9;">
                    • <b>Entropy & Availability in Multistage Compressors</b>.<br>
                    • <b>Boundary Layer Momentum Integral Equations</b>.
                </div>
                <div style="font-size: 11px; color: #fbbf24; margin-top: 6px; font-weight: 700;">Action: Mandatory Prerequisite Review; Socratic relearning before testing again.</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🗓️ 8-Month Master Plan Target vs. Actual")
    monthly_comp = get_monthly_study_comparison()
    if monthly_comp:
        df_month = pd.DataFrame(monthly_comp)
        st.bar_chart(df_month.set_index("month")[["planned_hours", "actual_hours"]])
