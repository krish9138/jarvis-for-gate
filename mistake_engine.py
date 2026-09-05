"""
mistake_engine.py
------------------
Standalone Mistake Book / Error Intelligence module for GATE JARVIS.
Can be run directly with:
    streamlit run mistake_engine.py
or imported in app.py:
    from mistake_engine import render_mistake_engine_view
"""

import sys
from pathlib import Path

# Ensure root dir is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from views.mistake_view import (
    render_mistake_engine_view,
    log_mistake,
    get_mistakes,
    get_category_counts,
    MISTAKE_CATEGORIES,
    CATEGORY_ICONS,
    CATEGORY_DESCRIPTIONS
)
from database.connection import init_db

if __name__ == "__main__":
    st.set_page_config(
        page_title="GATE JARVIS - Mistake Engine",
        page_icon="❌",
        layout="wide"
    )
    init_db()
    render_mistake_engine_view()
