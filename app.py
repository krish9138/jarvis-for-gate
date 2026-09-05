import sys
from pathlib import Path

# 0. Ensure project root directory is always in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from theme_manager import render_theme_switcher, inject_active_theme_css
import config
from database.connection import init_db
from views import (
    render_dashboard_view,
    render_assistant_view,
    render_doubt_engine_view,
    render_problem_solver_view,
    render_test_engine_view,
    render_study_plan_view,
    render_knowledge_view,
    render_timer_view,
    render_subjects_view,
    render_analytics_view,
    render_formula_view,
    render_resources_view,
    render_settings_view,
    render_mistake_engine_view,
    render_agent_command_view,
    render_case_study_plot_view,
    render_dpp_view,
    render_pyq_view,
    render_mastery_view,
    render_active_recall_view
)

# 1. Page Configuration
st.set_page_config(
    page_title="GATE JARVIS | Mechanical Engineering AI Super-App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Database Initialization & Seed Sync
init_db()

# 3. Dynamic Multi-Theme CSS Injection
inject_active_theme_css()

# 4. Sidebar Navigation
with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <h2 style="margin: 0; color: var(--primary); font-weight: 800; letter-spacing: 1px;">⚙️ GATE JARVIS</h2>
            <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--muted);">Mechanical Engineering (2026–2030)</p>
            <p style="margin: 2px 0 0 0; font-size: 11px; color: var(--accent); font-weight: 700;">TARGET: AIR &lt; 100</p>
        </div>
    """, unsafe_allow_html=True)

    # Multi-Theme Color Switcher
    render_theme_switcher()
    st.markdown("<hr style='margin: 10px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    # Grouped Navigation Structure
    SECTIONS = {
        "🏠 Dashboard": ["🏠 Dashboard"],
        "🤖 JARVIS Agent": ["🎙️ JARVIS Autonomous Agent"],
        "📚 Learning Hub": [
            "💬 AI Study Assistant",
            "❓ Doubt Engine",
            "🧠 Concept Mastery & Prereqs",
            "🔄 Spaced Repetition & Recall"
        ],
        "📝 Practice Lab": [
            "📝 DPP & Practice Lab",
            "📚 PYQ Intelligence Hub",
            "🧮 Problem-Solving Engine",
            "❌ Mistake Book & Error Intel"
        ],
        "📖 Knowledge Base": [
            "📖 Knowledge Base & Notes Intel",
            "📄 Formula Bank",
            "🏆 Strategy & Case Studies"
        ],
        "🧪 GATE Tests": [
            "📝 GATE Test Engine"
        ],
        "📅 Study Planning": [
            "🗓️ Study Plan Dashboard",
            "⏱️ Study Timer",
            "📚 Subjects & Tasks"
        ],
        "🏗️ Engineering Projects": [
            "🏗️ Plot & Property Case Studies"
        ],
        "📊 Analytics": [
            "📊 Analytics & Insights"
        ],
        "⚙️ Settings": [
            "⚙️ Settings & API Keys"
        ]
    }

    if "active_section" not in st.session_state:
        st.session_state["active_section"] = "🏠 Dashboard"

    section_names = list(SECTIONS.keys())
    current_sec_idx = section_names.index(st.session_state["active_section"]) if st.session_state["active_section"] in section_names else 0

    selected_section = st.selectbox(
        "Navigation Hub",
        options=section_names,
        index=current_sec_idx,
        label_visibility="collapsed"
    )
    st.session_state["active_section"] = selected_section

    sub_options = SECTIONS[selected_section]
    if len(sub_options) > 1:
        st.markdown(f"<p style='font-size:11px; text-transform:uppercase; color:var(--muted); margin:8px 0 4px 4px; font-weight:700;'>{selected_section} Modules</p>", unsafe_allow_html=True)
        menu_option = st.radio(
            "Sub Navigation",
            options=sub_options,
            index=0,
            label_visibility="collapsed"
        )
    else:
        menu_option = sub_options[0]

    st.markdown("<hr style='margin: 12px 0; border-color: var(--border);'/>", unsafe_allow_html=True)
    st.caption("🚀 **GATE JARVIS v4.0** (Adaptive Learning OS)")
    st.caption("Mastery Engine • DPP Lab • PYQ Hub • Notes Intel")

# 5. Route to selected view
if menu_option == "🏠 Dashboard":
    render_dashboard_view()
elif menu_option == "🎙️ JARVIS Autonomous Agent":
    render_agent_command_view()
elif menu_option == "🧠 Concept Mastery & Prereqs":
    render_mastery_view()
elif menu_option == "📝 DPP & Practice Lab":
    render_dpp_view()
elif menu_option == "📚 PYQ Intelligence Hub":
    render_pyq_view()
elif menu_option == "🔄 Spaced Repetition & Recall":
    render_active_recall_view()
elif menu_option == "💬 AI Study Assistant":
    render_assistant_view()
elif menu_option == "❓ Doubt Engine":
    render_doubt_engine_view()
elif menu_option == "🧮 Problem-Solving Engine":
    render_problem_solver_view()
elif menu_option in ["📝 GATE Test Engine", "📝 Test Engine"]:
    render_test_engine_view()
elif menu_option == "❌ Mistake Book & Error Intel":
    render_mistake_engine_view()
elif menu_option == "🗓️ Study Plan Dashboard":
    render_study_plan_view()
elif menu_option in ["📖 Knowledge Base & Notes Intel", "📖 Knowledge Base"]:
    render_knowledge_view()
elif menu_option == "⏱️ Study Timer":
    render_timer_view()
elif menu_option == "📚 Subjects & Tasks":
    render_subjects_view()
elif menu_option == "🏗️ Plot & Property Case Studies":
    render_case_study_plot_view()
elif menu_option == "📊 Analytics & Insights":
    render_analytics_view()
elif menu_option == "📄 Formula Bank":
    render_formula_view()
elif menu_option == "🏆 Strategy & Case Studies":
    render_resources_view()
elif menu_option == "⚙️ Settings & API Keys":
    render_settings_view()



