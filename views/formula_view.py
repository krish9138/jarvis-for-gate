import streamlit as st
from database.queries import get_chunks_for_retrieval, get_all_subjects
from services.rag_service import query_knowledge_base

def render_formula_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">📄 Formula Bank & Quick Revision Sheet</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Instant mathematical reference, governing equations, SI units, and sign conventions for GATE Mechanical Engineering.
            </p>
        </div>
    """, unsafe_allow_html=True)

    search_term = st.text_input("🔍 Search Formulas & Key Relations:", placeholder="e.g. Bernoulli, Lame, Euler, Hoop stress, Mohr, Strain...")

    # High-Yield Formula Cards
    core_formulas = [
        {
            "subject": "Strength of Materials",
            "topic": "Thin Cylinders (Internal Pressure $p$)",
            "equations": [
                "Hoop / Circumferential Stress: $\\sigma_c = \\frac{p d}{2t} = \\frac{p r}{t}$ (Tensile)",
                "Longitudinal Stress: $\\sigma_L = \\frac{p d}{4t} = \\frac{p r}{2t} = \\frac{\\sigma_c}{2}$",
                "Max In-Plane Shear Stress: $\\tau_{max, in-plane} = \\frac{\\sigma_c - \\sigma_L}{2} = \\frac{pd}{8t}$",
                "Absolute Max Shear Stress: $\\tau_{max, abs} = \\frac{\\sigma_c - 0}{2} = \\frac{pd}{4t}$",
                "Volumetric Strain: $\\epsilon_v = \\frac{pd}{4tE}(5 - 4\\mu)$",
                "Pure Shear Condition ($p$ + Axial Load $F$): $F = 3\\pi p r^2$"
            ]
        },
        {
            "subject": "Strength of Materials",
            "topic": "Thick Cylinders (Lame's Equations)",
            "equations": [
                "Radial Stress at radius $r$: $\\sigma_r = \\frac{B}{r^2} - A$ (Compressive: $\\sigma_r(R_i)=p_i$, $\\sigma_r(R_o)=p_o$)",
                "Circumferential / Hoop Stress: $\\sigma_c = \\frac{B}{r^2} + A$ (Max at inner radius $r=R_i$)",
                "Max Shear Stress at any radius $r$: $\\tau_{max} = \\frac{\\sigma_c + \\sigma_r}{2} = \\frac{B}{r^2}$",
                "Longitudinal Stress: $\\sigma_L = \\frac{p_i R_i^2 - p_o R_o^2}{R_o^2 - R_i^2} = \\text{Constant}$"
            ]
        },
        {
            "subject": "Strength of Materials",
            "topic": "Columns & Struts (Euler Buckling Load)",
            "equations": [
                "Euler Critical Load: $P_{cr} = \\frac{\\pi^2 E I_{min}}{L_e^2}$",
                "Both Ends Hinged: $L_e = L \\implies P_{cr} = \\frac{\\pi^2 EI}{L^2}$",
                "Both Ends Fixed: $L_e = 0.5L \\implies P_{cr} = \\frac{4\\pi^2 EI}{L^2}$",
                "One Fixed, One Free: $L_e = 2L \\implies P_{cr} = \\frac{\\pi^2 EI}{4L^2}$",
                "One Fixed, One Hinged: $L_e = \\frac{L}{\\sqrt{2}} \\implies P_{cr} = \\frac{2\\pi^2 EI}{L^2}$",
                "Slenderness Ratio: $\\lambda = \\frac{L_e}{k}$, where $k = \\sqrt{I/A}$"
            ]
        },
        {
            "subject": "Fluid Mechanics",
            "topic": "Fluid Dynamics & Bernoulli's Equation",
            "equations": [
                "Euler Equation along Streamline: $\\frac{dp}{\\rho} + v dv + g dz = 0$",
                "Bernoulli Equation (Head Form): $\\frac{P}{\\rho g} + \\frac{v^2}{2g} + z = H = \\text{Constant}$",
                "Venturimeter Discharge: $Q = C_d \\frac{a_1 a_2}{\\sqrt{a_1^2 - a_2^2}} \\sqrt{2g \\Delta h}$",
                "Pitot Tube Velocity: $v = \\sqrt{\\frac{2(P_{stag} - P_{stat})}{\\rho}} = \\sqrt{2gh}$",
                "Torricelli Law: $v = \\sqrt{2gh}$",
                "Validity Conditions: Steady, Incompressible, Frictionless (Inviscid), along a Streamline"
            ]
        },
        {
            "subject": "Thermodynamics",
            "topic": "1st & 2nd Laws of Thermodynamics",
            "equations": [
                "Closed System 1st Law (Process): $\\delta Q = dU + \\delta W$",
                "Quasi-Static Boundary Work: $W = \\int P dV$",
                "Ideal Gas Internal Energy: $\\Delta U = m C_v \\Delta T$",
                "Enthalpy: $H = U + PV \\implies \\Delta H = m C_p \\Delta T$",
                "Carnot Efficiency: $\\eta_{th} = 1 - \\frac{T_L}{T_H}$",
                "Clausius Inequality: $\\oint \\frac{\\delta Q}{T} \\le 0$"
            ]
        }
    ]

    filtered_formulas = core_formulas
    if search_term.strip():
        term = search_term.lower()
        filtered_formulas = [
            f for f in core_formulas 
            if term in f["topic"].lower() or term in f["subject"].lower() or any(term in eq.lower() for eq in f["equations"])
        ]

    for item in filtered_formulas:
        with st.expander(f"📌 {item['subject']} — {item['topic']}", expanded=True):
            for eq in item["equations"]:
                st.markdown(f"- {eq}")
