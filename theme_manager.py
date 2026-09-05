"""
theme_manager.py
-----------------
Drop-in multi-theme color-scheme switcher for the GATE JARVIS Streamlit app.
"""

import streamlit as st

THEMES = {
    "Midnight Aerospace": {
        "primary": "#38bdf8",
        "background": "#0f172a",
        "surface": "#1e293b",
        "border": "#334155",
        "text": "#e2e8f0",
        "muted": "#94a3b8",
        "accent": "#f59e0b",
    },
    "Slate Emerald": {
        "primary": "#10b981",
        "background": "#0f1a17",
        "surface": "#16241f",
        "border": "#26382f",
        "text": "#e6f4ef",
        "muted": "#8fb3a4",
        "accent": "#34d399",
    },
    "Sunset Amber": {
        "primary": "#f97316",
        "background": "#1c1410",
        "surface": "#2a1f17",
        "border": "#3d2d1f",
        "text": "#fdecdd",
        "muted": "#c9a486",
        "accent": "#fbbf24",
    },
    "Clean Light": {
        "primary": "#2563eb",
        "background": "#f8fafc",
        "surface": "#ffffff",
        "border": "#e2e8f0",
        "text": "#0f172a",
        "muted": "#64748b",
        "accent": "#0ea5e9",
    },
}

DEFAULT_THEME = "Midnight Aerospace"


def _current_theme_name() -> str:
    return st.session_state.get("theme_name", DEFAULT_THEME)


def render_theme_switcher():
    """Renders a selectbox that lets the user change the color scheme live."""
    st.markdown("##### 🎨 Color Theme")
    choice = st.selectbox(
        "Theme",
        options=list(THEMES.keys()),
        index=list(THEMES.keys()).index(_current_theme_name()),
        label_visibility="collapsed",
    )
    if choice != _current_theme_name():
        st.session_state["theme_name"] = choice
        st.rerun()


def inject_active_theme_css():
    """Injects CSS variables + base styling for the currently active theme.
    Call this on every page load, before any other st.markdown/CSS."""
    theme = THEMES[_current_theme_name()]

    st.markdown(
        f"""
        <style>
        :root {{
            --primary: {theme['primary']};
            --background: {theme['background']};
            --surface: {theme['surface']};
            --border: {theme['border']};
            --text: {theme['text']};
            --muted: {theme['muted']};
            --accent: {theme['accent']};
        }}

        .stApp {{
            background-color: var(--background) !important;
            color: var(--text) !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
        }}

        div[data-testid="stMetricValue"] {{
            font-size: 26px !important;
            font-weight: 700 !important;
            color: var(--text) !important;
        }}

        .stCard, div[data-testid="stForm"], div[data-testid="stExpander"] {{
            background-color: var(--surface) !important;
            border-radius: 10px;
            border: 1px solid var(--border) !important;
        }}

        h1, h2, h3, h4, h5, h6, p, span, label, div {{
            color: var(--text);
        }}

        .stButton>button {{
            background-color: var(--primary) !important;
            color: var(--background) !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        .stButton>button:hover {{
            background-color: var(--accent) !important;
        }}

        .sidebar-header {{
            text-align: center;
            padding: 10px 0;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
