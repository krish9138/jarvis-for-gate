"""
views/mistake_view.py
---------------------
Mistake Book & Error Intelligence View for GATE JARVIS.
Tracks errors, categorizes cognitive / technical root causes, and visualizes 30-day analytics.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st
import config
from database.connection import get_db_connection

# Comprehensive 11-Category Error Taxonomy for GATE Mechanical
MISTAKE_CATEGORIES = [
    "Concept Error",
    "Formula Error",
    "Calculation Error",
    "Unit Error",
    "Sign Error",
    "Reading Error",
    "Silly Mistake",
    "Time Pressure",
    "Wrong Assumption",
    "Question Misinterpretation",
    "Guessing Error",
    # Legacy fallbacks for backward compatibility
    "Concept",
    "Formula",
    "Calculation",
    "Unit",
    "Reading",
    "Time-management",
    "Guessing",
]

CORE_11_CATEGORIES = [
    "Concept Error",
    "Formula Error",
    "Calculation Error",
    "Unit Error",
    "Sign Error",
    "Reading Error",
    "Silly Mistake",
    "Time Pressure",
    "Wrong Assumption",
    "Question Misinterpretation",
    "Guessing Error",
]

CATEGORY_ICONS = {
    "Concept Error": "🧠",
    "Formula Error": "📐",
    "Calculation Error": "🔢",
    "Unit Error": "⚖️",
    "Sign Error": "➕",
    "Reading Error": "📖",
    "Silly Mistake": "🤦",
    "Time Pressure": "⏳",
    "Wrong Assumption": "🌫️",
    "Question Misinterpretation": "🎯",
    "Guessing Error": "🎲",
    # Legacy fallbacks
    "Concept": "🧠",
    "Formula": "📐",
    "Calculation": "🔢",
    "Unit": "⚖️",
    "Reading": "📖",
    "Time-management": "⏳",
    "Guessing": "🎲",
}

CATEGORY_DESCRIPTIONS = {
    "Concept Error": "Misunderstood core physics, mechanical principle, thermodynamic boundary, or equilibrium condition.",
    "Formula Error": "Understood the concept, but selected, recalled, or misderived an incorrect governing formula.",
    "Calculation Error": "Correct equations and parameters, but committed arithmetic, algebraic, or calculator entry blunder.",
    "Unit Error": "Forgot unit conversions (e.g. MPa to Pa, mm to m, rpm to rad/s, Celsius to Kelvin, bar to N/m²).",
    "Sign Error": "Inverted sign convention (e.g. tensile vs compressive, heat absorbed vs rejected, clockwise vs counterclockwise).",
    "Reading Error": "Overlooked vital question parameters (e.g. 'radius' vs 'diameter', 'gauge' vs 'absolute', 'per unit length').",
    "Silly Mistake": "Selected the wrong option in haste or mistyped numerical input into the NAT box despite correct solution.",
    "Time Pressure": "Rushed through derivation or skipped essential sanity check due to running out of exam countdown time.",
    "Wrong Assumption": "Applied formulas outside validity domain (e.g. ideal gas for steam, thin cylinder equation for thick cylinder).",
    "Question Misinterpretation": "Answered a different parameter than requested (e.g. calculated stress when strain energy was asked).",
    "Guessing Error": "Gambled on MCQ/MSQ option without rigorous engineering derivation.",
    # Legacy fallbacks
    "Concept": "Misunderstood core physics, mechanical principle, or boundary condition.",
    "Formula": "Understood the concept, but selected or recalled an incorrect formula.",
    "Calculation": "Correct formula and numbers, but made an arithmetic/algebra error.",
    "Unit": "Forgot conversion (e.g. MPa to Pa, mm to m, rpm to rad/s) or wrong units.",
    "Reading": "Misread given parameters, overlooked keywords (e.g. 'radius' vs 'diameter').",
    "Time-management": "Rushed due to time pressure or skipped essential checking steps.",
    "Guessing": "Solved without solid derivation or guessed an option in test.",
}


def _get_subjects():
    """Fetches subject list from database with fallback."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM subjects ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return [(r["id"], r["name"]) for r in rows]
    except Exception:
        pass
    fallback = [
        "Engineering Mathematics", "Strength of Materials", "Thermodynamics",
        "Fluid Mechanics", "Theory of Machines", "Machine Design",
        "Heat Transfer", "Manufacturing Engineering", "Industrial Engineering",
        "Engineering Mechanics", "General Aptitude",
    ]
    return [(None, name) for name in fallback]


def log_mistake(question_text: str, user_answer: str, correct_answer: str, mistake_category: str, subject_id=None, source: str = "manual"):
    """Inserts a new mistake record into SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO mistake_log
           (question_text, user_answer, correct_answer, mistake_category, subject_id, source)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (question_text, user_answer, correct_answer, mistake_category, subject_id, source),
    )
    conn.commit()
    mistake_id = cursor.lastrowid
    conn.close()
    return mistake_id


def get_mistakes(days: int = 30, subject_id=None, category=None):
    """Fetches mistakes filtered by timeframe, subject, and category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    query = """
        SELECT m.*, COALESCE(s.name, 'General') as subject_name
        FROM mistake_log m
        LEFT JOIN subjects s ON m.subject_id = s.id
        WHERE m.created_at >= ?
    """
    params = [cutoff]
    if subject_id is not None:
        query += " AND m.subject_id = ?"
        params.append(subject_id)
    if category is not None and category != "(all)":
        query += " AND m.mistake_category = ?"
        params.append(category)
    query += " ORDER BY m.created_at DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_category_counts(days: int = 30):
    """Returns {category: count} dictionary for the last N days."""
    mistakes = get_mistakes(days=days)
    counts = {cat: 0 for cat in MISTAKE_CATEGORIES}
    SYNONYM_MAP = {
        "Concept": "Concept Error",
        "Concept Error": "Concept",
        "Formula": "Formula Error",
        "Formula Error": "Formula",
        "Calculation": "Calculation Error",
        "Calculation Error": "Calculation",
        "Unit": "Unit Error",
        "Unit Error": "Unit",
        "Reading": "Reading Error",
        "Reading Error": "Reading",
        "Time-management": "Time Pressure",
        "Time Pressure": "Time-management",
        "Guessing": "Guessing Error",
        "Guessing Error": "Guessing",
    }
    for m in mistakes:
        cat = m["mistake_category"]
        if cat in counts:
            counts[cat] += 1
        syn = SYNONYM_MAP.get(cat)
        if syn and syn in counts:
            counts[syn] += 1
    return counts


def render_mistake_engine_view():
    """Renders the comprehensive Mistake Book UI in Streamlit."""
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(30, 41, 59, 0.7)); 
                    border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 18px 24px; margin-bottom: 20px;">
            <h2 style="margin:0; color: #f87171; display:flex; align-items:center; gap:10px;">
                ❌ Mistake Book & Error Intelligence
            </h2>
            <p style="margin:4px 0 0 0; color: #cbd5e1; font-size:14px;">
                Evolve past repeat errors. Log every wrong question, diagnose the cognitive root cause, and auto-feed data to the Adaptive Learning Engine.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_log, tab_analytics, tab_history = st.tabs([
        "📝 Log New Mistake", 
        "📊 30-Day Error Analytics", 
        "📜 Mistake Archive & Filter"
    ])

    subjects = _get_subjects()
    subject_map = {name: sid for sid, name in subjects}
    subject_labels = ["(General / Cross-Subject)"] + [name for _, name in subjects]

    # --- TAB 1: LOG A MISTAKE ---
    with tab_log:
        col_form, col_guide = st.columns([1.6, 1.0])

        with col_form:
            with st.form("log_mistake_form", clear_on_submit=True):
                st.markdown("#### ✍️ Log Incorrect Question")
                question_text = st.text_area(
                    "Question Statement / Numerical Problem*",
                    placeholder="e.g. A solid cylinder of radius 50 mm is subjected to torque T = 2 kNm...",
                    height=120
                )

                c1, c2 = st.columns(2)
                user_answer = c1.text_input("Your Attempted Answer", placeholder="e.g. 101.8 MPa")
                correct_answer = c2.text_input("Correct Answer / Key", placeholder="e.g. 81.5 MPa")

                c3, c4 = st.columns(2)
                subject_choice = c3.selectbox("Subject", options=subject_labels)
                mistake_category = c4.selectbox(
                    "Root Cause / Mistake Category*",
                    options=CORE_11_CATEGORIES,
                    format_func=lambda c: f"{CATEGORY_ICONS.get(c, '')} {c}"
                )

                source_type = st.selectbox("Source of Question", ["Manual Practice", "Test Engine Simulation", "PYQ Drill", "DPP / Assignment"])

                submitted = st.form_submit_button("💾 Save to Mistake Intelligence Book", use_container_width=True)

            if submitted:
                if not question_text.strip():
                    st.error("⚠️ Please provide the question text before saving.")
                else:
                    subj_id = subject_map.get(subject_choice)
                    m_id = log_mistake(
                        question_text=question_text.strip(),
                        user_answer=user_answer.strip(),
                        correct_answer=correct_answer.strip(),
                        mistake_category=mistake_category,
                        subject_id=subj_id,
                        source=source_type
                    )
                    st.success(f"✅ Mistake #{m_id} successfully logged under **{CATEGORY_ICONS.get(mistake_category, '')} {mistake_category}**!")

        with col_guide:
            st.markdown("#### 🎯 11-Tier Error Taxonomy Guide")
            for cat in CORE_11_CATEGORIES:
                with st.expander(f"{CATEGORY_ICONS.get(cat, '')} **{cat}**", expanded=(cat in ["Calculation Error", "Unit Error"])):
                    st.write(CATEGORY_DESCRIPTIONS.get(cat, ""))

    # --- TAB 2: ANALYTICS ---
    with tab_analytics:
        st.markdown("#### 📈 Longitudinal Error Distribution & Recurrence Patterns")
        timeframe = st.radio(
            "Analysis Window", 
            options=[7, 30, 90, 365], 
            index=1, 
            horizontal=True,
            format_func=lambda d: f"Last {d} Days"
        )

        counts = get_category_counts(days=timeframe)
        core_counts = {cat: counts.get(cat, 0) for cat in CORE_11_CATEGORIES}
        total = sum(core_counts.values())

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Errors Logged", total)
        
        top_cat = max(core_counts, key=core_counts.get) if total > 0 else "None"
        top_val = core_counts[top_cat] if total > 0 else 0
        top_pct = f"{round((top_val / total) * 100, 1)}%" if total > 0 else "0%"
        
        m2.metric("Primary Error Pattern", f"{CATEGORY_ICONS.get(top_cat, '')} {top_cat}")
        m3.metric("Primary Error Count", f"{top_val} ({top_pct})")
        m4.metric("Error Stability Score", f"{max(0, 100 - total * 3)}/100")

        st.markdown("<hr style='margin:15px 0; border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)

        if total == 0:
            st.info("💡 No errors logged in this timeframe yet. Keep practicing and log any incorrect questions!")
        else:
            col_chart, col_insight = st.columns([1.5, 1.0])
            with col_chart:
                st.markdown("**11-Category Error Distribution**")
                st.bar_chart(core_counts)

            with col_insight:
                st.markdown("#### 🧠 JARVIS Pattern Diagnostics & Interventions")
                calc_unit_val = core_counts.get("Calculation Error", 0) + core_counts.get("Unit Error", 0)
                if calc_unit_val >= 3:
                    st.warning(f"🚨 **High-Frequency Execution Errors ({calc_unit_val} blunders):**\nYou understand the concepts, but marks are leaking through arithmetic or unit conversion. \n\n**⚡ Prescribed Intervention:** 20-minute Calculation Accuracy & Unit Conversion Drill.")
                elif top_cat in ["Concept Error", "Wrong Assumption"]:
                    st.error(f"🚨 **Foundational Concept Trap ({top_val} errors):**\nMisunderstanding core physical boundary conditions. Review derivations and First/Second laws before advancing.")
                elif top_cat in ["Reading Error", "Question Misinterpretation"]:
                    st.warning(f"⚠️ **Careless Reading Pattern ({top_val} errors):**\nAlways circle keywords ('radius' vs 'diameter', 'gauge' vs 'absolute') before touching your calculator.")
                elif top_cat == "Time Pressure":
                    st.warning(f"⏳ **Speed Pressure ({top_val} errors):**\nPractice with 2-minute countdown timers per 1-mark question.")
                else:
                    st.info(f"Primary pattern: **{top_val} {top_cat}** errors recorded. Daily spaced repetition recommended.")

            st.markdown("##### Detailed 11-Category Grid")
            g_cols1 = st.columns(6)
            for i, cat in enumerate(CORE_11_CATEGORIES[:6]):
                g_cols1[i].metric(label=f"{CATEGORY_ICONS.get(cat, '')} {cat.replace(' Error', '')}", value=core_counts[cat])
            g_cols2 = st.columns(5)
            for i, cat in enumerate(CORE_11_CATEGORIES[6:]):
                g_cols2[i].metric(label=f"{CATEGORY_ICONS.get(cat, '')} {cat.replace(' Error', '')}", value=core_counts[cat])

    # --- TAB 3: HISTORY & ARCHIVE ---
    with tab_history:
        st.markdown("#### 📜 Search & Review Past Errors")
        f1, f2 = st.columns(2)
        filter_cat = f1.selectbox("Filter by Category", ["(all)"] + CORE_11_CATEGORIES, key="hist_filter_cat")
        filter_days = f2.selectbox("Filter by Time Range", [7, 30, 90, 365, 1000], index=3, format_func=lambda d: f"Past {d} Days", key="hist_filter_days")

        all_mistakes = get_mistakes(days=filter_days, category=filter_cat)

        if not all_mistakes:
            st.info("No mistake records match the selected filters.")
        else:
            st.caption(f"Showing {len(all_mistakes)} recorded mistakes:")
            for m in all_mistakes:
                icon = CATEGORY_ICONS.get(m['mistake_category'], '📌')
                with st.expander(f"{icon} **[{m['mistake_category']}]** {m['subject_name']} — {m['question_text'][:80]}...", expanded=False):
                    st.markdown(f"**📖 Question:**\n{m['question_text']}")
                    c_u, c_c = st.columns(2)
                    c_u.markdown(f"**🔴 Your Answer:** `{m['user_answer'] or 'Not Recorded'}`")
                    c_c.markdown(f"**🟢 Correct Answer:** `{m['correct_answer'] or 'Not Recorded'}`")
                    st.caption(f"📅 Logged: {m['created_at']} | 🏷️ Source: {m['source']} | ID: #{m['id']}")
