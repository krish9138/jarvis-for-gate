"""
views/mastery_view.py
---------------------
Concept Mastery & Prerequisite Dependency Engine for GATE JARVIS 4.0.
Visualizes multi-signal cognitive progression across 8 tiers and proactively alerts
on prerequisite deficiencies before advancing into complex mechanical domains.
"""

import streamlit as st
import pandas as pd
from database.queries import (
    get_all_concept_mastery_states,
    get_all_subjects
)
from services.mastery_service import (
    seed_foundational_concept_graph,
    evaluate_prerequisite_safety,
    MASTERY_STAGES,
    STAGE_DETAILS
)

def render_mastery_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">🧠 Concept Mastery & Prerequisite Graph</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Multi-signal cognitive engine. Rather than binary 'completed/pending' flags, JARVIS evaluates concept comprehension, numerical accuracy, PYQ performance, retention decay, and prerequisite dependencies.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Ensure seeds
    seed_foundational_concept_graph()

    tab_overview, tab_prereqs, tab_drill = st.tabs([
        "📊 Multi-Signal Mastery Matrix",
        "🔗 Prerequisite Graph & Safety Alerts",
        "🎯 8-Stage Cognitive Progression"
    ])

    concepts = get_all_concept_mastery_states()

    # -------------------------------------------------------------
    # TAB 1: MULTI-SIGNAL MASTERY MATRIX
    # -------------------------------------------------------------
    with tab_overview:
        if not concepts:
            st.info("Initializing concept tree...")
            st.rerun()

        # Aggregate metrics
        avg_composite = round(sum(c["composite_mastery"] for c in concepts) / max(1, len(concepts)), 1)
        exam_ready_count = sum(1 for c in concepts if c["state_enum"] in ["PYQ_MASTERED", "REVISION_STABLE", "EXAM_READY"])
        weak_count = sum(1 for c in concepts if c["composite_mastery"] < 50.0)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Mastery Index", f"{avg_composite}%")
        m2.metric("Tracked Concepts", len(concepts))
        m3.metric("GATE Exam Ready", f"{exam_ready_count} concepts")
        m4.metric("Intervention Needed", f"{weak_count} concepts", delta=f"-{weak_count}" if weak_count>0 else None, delta_color="inverse")

        st.markdown("<hr style='margin: 14px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

        # Subject Filter
        subjects = get_all_subjects()
        s_names = ["(All Subjects)"] + [s["name"] for s in subjects]
        sel_subj = st.selectbox("Filter by Subject:", s_names, index=0)

        filtered = concepts if sel_subj == "(All Subjects)" else [c for c in concepts if c["subject_name"] == sel_subj]

        st.markdown(f"#### Tracked Concepts ({len(filtered)})")
        for c in filtered:
            stage_info = STAGE_DETAILS.get(c["state_enum"], {"icon": "⚪", "label": c["state_enum"]})
            score = c["composite_mastery"]

            # Color badge
            badge_color = "#10b981" if score >= 75 else ("#f59e0b" if score >= 50 else "#ef4444")

            with st.expander(f"{stage_info['icon']} **{c['concept_name']}** — {score}% ({stage_info['label']})"):
                col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
                col_kpi1.metric("Concept Comprehension", f"{c['concept_score']}%")
                col_kpi2.metric("Numerical NAT Score", f"{c['numerical_score']}%")
                col_kpi3.metric("PYQ Mastery", f"{c['pyq_score']}%")
                col_kpi4.metric("Retention Memory", f"{c['retention_pct']}%")
                col_kpi5.metric("Mistakes Logged", f"{c['mistake_freq']} errors")

                st.progress(min(1.0, max(0.0, score / 100.0)))

                # Check prerequisite safety
                safety = evaluate_prerequisite_safety(c["concept_id"])
                if not safety["safe"]:
                    st.warning(safety["message"])
                else:
                    st.caption("✅ All prerequisite foundations satisfied.")

    # -------------------------------------------------------------
    # TAB 2: PREREQUISITE GRAPH & SAFETY ALERTS
    # -------------------------------------------------------------
    with tab_prereqs:
        st.markdown("### 🔗 Prerequisite Dependency Safety Checker")
        st.markdown("""
            Attempting advanced topics like *Entropy*, *Vapour Power Cycles*, or *Vibrations* without mastering foundational laws leads to recurring exam blunders.
            Select any topic to perform an automated prerequisite audit:
        """)

        c_options = {c["concept_name"]: c["concept_id"] for c in concepts}
        selected_name = st.selectbox("Select Target Topic to Audit:", list(c_options.keys()))
        selected_id = c_options[selected_name]

        safety_report = evaluate_prerequisite_safety(selected_id)

        if safety_report["safe"]:
            st.success(f"### ✅ Clear to Advance!\n{safety_report['message']}")
        else:
            st.error(f"### ⚠️ JARVIS Prerequisite Warning!\n{safety_report['message']}")
            st.markdown("#### Recommended Actions:")
            for wp in safety_report["weak_prerequisites"]:
                st.markdown(f"- 📘 **Revise Prerequisite**: `{wp['concept_name']}` (Current mastery: `{wp['mastery_level']}%`). Target $\\ge 60\\%$ before attempting complex applications.")

        st.markdown("---")
        st.markdown("#### 🗺️ Core Mechanical Engineering Dependency Graph")
        
        graph_view_mode = st.radio(
            "Graph View Mode:",
            ["✨ Interactive Visual Map", "📊 Mermaid Flowchart"],
            horizontal=True
        )

        if graph_view_mode == "📊 Mermaid Flowchart":
            st.markdown("""
```mermaid
graph TD
    EM_Calc["Calculus: Partial Derivatives & Maxima"] --> EM_ODE["Ordinary Differential Equations"]
    EM_ODE --> VIB_1["SDOF Free Vibrations"]
    VIB_1 --> VIB_2["Damped & Forced Vibrations & Transmissibility"]

    SOM_Hooke["Stress-Strain & Hooke's Law"] --> SOM_Thin["Thin Cylinders & Pressure Vessels"]
    SOM_SFD["Shear Force & Bending Moment Diagrams"] --> SOM_Defl["Deflection of Beams & Superposition"]

    FM_Stat["Fluid Statics & Buoyancy"] --> FM_Bern["Bernoulli Equation & Conservation"]
    FM_Pipe["Laminar & Turbulent Pipe Flow"] --> FM_BL["Boundary Layer Theory & Drag"]

    TH_1st["First Law & Energy Balance"] --> TH_2nd["Second Law & Heat Engines"]
    TH_2nd --> TH_Entropy["Entropy, T-s Diagrams & Availability"]
    TH_Entropy --> TH_Rankine["Vapour Power Cycles (Rankine)"]
    TH_1st --> TH_Gas["Gas Power Cycles (Otto/Diesel/Brayton)"]

    style TH_Entropy fill:#1e1b4b,stroke:#38bdf8,stroke-width:2px;
    style VIB_2 fill:#1e1b4b,stroke:#38bdf8,stroke-width:2px;
```
            """)
        else:
            # Interactive Visual Dependency Matrix with styled cards and live mastery
            concept_map = {c["concept_id"]: c for c in concepts}
            
            dependency_clusters = [
                {
                    "domain": "Thermodynamics & Power Systems",
                    "color": "#f59e0b",
                    "nodes": [
                        ("TH_1st", "First Law & Energy Balance", ["TH_2nd", "TH_Gas"]),
                        ("TH_2nd", "Second Law & Heat Engines", ["TH_Entropy"]),
                        ("TH_Entropy", "Entropy, T-s Diagrams & Availability", ["TH_Rankine"]),
                        ("TH_Rankine", "Vapour Power Cycles (Rankine)", []),
                        ("TH_Gas", "Gas Power Cycles (Otto/Diesel/Brayton)", [])
                    ]
                },
                {
                    "domain": "Strength of Materials (SOM)",
                    "color": "#38bdf8",
                    "nodes": [
                        ("SOM_Hooke", "Stress-Strain & Hooke's Law", ["SOM_Thin"]),
                        ("SOM_Thin", "Thin Cylinders & Pressure Vessels", []),
                        ("SOM_SFD", "Shear Force & Bending Moment Diagrams", ["SOM_Defl"]),
                        ("SOM_Defl", "Deflection of Beams & Superposition", [])
                    ]
                },
                {
                    "domain": "Fluid Mechanics",
                    "color": "#06b6d4",
                    "nodes": [
                        ("FM_Stat", "Fluid Statics & Buoyancy", ["FM_Bern"]),
                        ("FM_Bern", "Bernoulli Equation & Conservation", []),
                        ("FM_Pipe", "Laminar & Turbulent Pipe Flow", ["FM_BL"]),
                        ("FM_BL", "Boundary Layer Theory & Drag", [])
                    ]
                },
                {
                    "domain": "Engineering Mechanics & Vibrations",
                    "color": "#a855f7",
                    "nodes": [
                        ("EM_Calc", "Calculus: Partial Derivatives & Maxima", ["EM_ODE"]),
                        ("EM_ODE", "Ordinary Differential Equations", ["VIB_1"]),
                        ("VIB_1", "SDOF Free Vibrations", ["VIB_2"]),
                        ("VIB_2", "Damped & Forced Vibrations & Transmissibility", [])
                    ]
                }
            ]

            for cluster in dependency_clusters:
                st.markdown(f"""
                    <div style="margin-top: 14px; margin-bottom: 8px; font-weight: 700; color: {cluster['color']}; font-size: 14px;">
                        📌 {cluster['domain']}
                    </div>
                """, unsafe_allow_html=True)
                
                cols = st.columns(len(cluster["nodes"]))
                for i, (cid, cname, downstream) in enumerate(cluster["nodes"]):
                    c_data = concept_map.get(cid, {})
                    m_score = c_data.get("composite_mastery", 0.0)
                    state = c_data.get("cognitive_state", "NOT_STARTED")
                    
                    badge_color = "#10b981" if m_score >= 75 else ("#f59e0b" if m_score >= 50 else "#64748b")
                    downstream_str = ", ".join(downstream) if downstream else "End Goal (Exam Ready)"
                    
                    with cols[i]:
                        st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 10px; min-height: 130px; display: flex; flex-direction: column; justify-content: space-between;">
                                <div>
                                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">{cid}</div>
                                    <div style="font-size: 12px; font-weight: 700; color: #f8fafc; margin-top: 2px;">{cname}</div>
                                </div>
                                <div style="margin-top: 8px;">
                                    <div style="font-size: 11px; color: {badge_color}; font-weight: 800;">
                                        ● {int(m_score)}% ({state})
                                    </div>
                                    <div style="font-size: 10px; color: #64748b; margin-top: 2px;">
                                        Unlocks: <b>{downstream_str}</b>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 3: 8-STAGE COGNITIVE PROGRESSION
    # -------------------------------------------------------------
    with tab_drill:
        st.markdown("### 🏆 8-Tier Cognitive Mastery Pathway")
        st.caption("GATE JARVIS 4.0 classifies every topic into one of eight distinct states:")

        for code, label, icon, min_s in MASTERY_STAGES:
            st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid var(--border); border-radius: 8px; padding: 12px 18px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 20px;">{icon}</span>
                        <div>
                            <strong style="color: var(--accent);">{label}</strong>
                            <div style="font-size: 12px; color: var(--muted);">{code}</div>
                        </div>
                    </div>
                    <span style="font-weight: 700; color: #38bdf8; font-size: 14px;">Min Composite: {min_s}%</span>
                </div>
            """, unsafe_allow_html=True)
