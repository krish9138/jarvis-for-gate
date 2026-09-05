import streamlit as st
import pandas as pd
from database.queries import save_mock_test, get_all_mock_tests, delete_mock_test, get_all_subjects

def render_mock_tests_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0;">📝 Mock Test Tracker & Performance Analytics</h2>
            <p style="color: #64748b; font-size: 14px; margin: 4px 0 16px 0;">
                Log your full-length mock tests, analyze score trends, and target high-yield weak areas for AIR &lt; 100.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_log = st.tabs(["📊 Performance History", "➕ Log New Mock Test"])

    mock_tests = get_all_mock_tests()

    # -------------------------------------------------------------
    # TAB 1: OVERVIEW & HISTORY
    # -------------------------------------------------------------
    with tab_overview:
        if not mock_tests:
            st.info("No mock tests logged yet. Head over to **Log New Mock Test** to record your first score!")
        else:
            # Summary Metrics
            scores = [t["score"] for t in mock_tests]
            avg_score = sum(scores) / len(scores)
            max_score_logged = max(scores)
            latest_test = mock_tests[0]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Mocks Taken", len(mock_tests))
            m2.metric("Latest Score", f"{latest_test['score']:.1f} / {latest_test['max_score']:.0f}")
            m3.metric("Average Score", f"{avg_score:.1f}")
            m4.metric("Personal Best", f"{max_score_logged:.1f} / 100")

            st.markdown("---")
            st.subheader("📈 Mock Test Score Progression")

            # Chart
            df_chart = pd.DataFrame(mock_tests[::-1]) # chronological order
            st.line_chart(df_chart.set_index("test_name")["score"])

            # Table of tests
            st.markdown("### 📋 Logged Tests")
            for t in mock_tests:
                with st.container():
                    c_info, c_del = st.columns([0.85, 0.15])
                    with c_info:
                        pct = (t["score"] / t["max_score"]) * 100 if t["max_score"] > 0 else 0
                        badge_color = "#10b981" if pct >= 75 else "#f59e0b" if pct >= 55 else "#ef4444"
                        st.markdown(f"#### {t['test_name']} — <span style='color: {badge_color}; font-weight: bold;'>{t['score']:.1f} / {t['max_score']:.0f} ({pct:.1f}%)</span>", unsafe_allow_html=True)
                        st.caption(f"🗓️ Date: {t['taken_at'][:16]} &nbsp;|&nbsp; 📝 Notes: {t['notes'] or 'None'}")
                    with c_del:
                        if st.button("🗑️ Delete", key=f"del_mock_{t['id']}", help="Delete test"):
                            delete_mock_test(t["id"])
                            st.rerun()
                st.markdown("<hr style='margin: 8px 0; border-color: #334155;'/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # TAB 2: LOG TEST
    # -------------------------------------------------------------
    with tab_log:
        st.subheader("➕ Record a Completed Mock Test")

        with st.form("mock_test_form"):
            t_name = st.text_input("Test Name / Series:", placeholder="e.g. Made Easy All-India Mock 01 / GateForum Subject Test")
            
            c1, c2 = st.columns(2)
            with c1:
                t_score = st.number_input("Your Score:", min_value=-33.0, max_value=100.0, value=65.0, step=0.5)
            with c2:
                t_max = st.number_input("Maximum Score:", min_value=10.0, max_value=100.0, value=100.0, step=5.0)

            t_notes = st.text_area("Post-Mortem & Error Analysis Notes:", placeholder="e.g. Silly calculation mistake on Euler column Q8; forgot radius vs diameter in Lame's equation.")

            submitted = st.form_submit_button("💾 Save Mock Test Record")
            if submitted:
                if not t_name.strip():
                    st.error("Please enter a test name.")
                else:
                    if save_mock_test(test_name=t_name, score=t_score, max_score=t_max, notes=t_notes):
                        st.success(f"Recorded '{t_name}' ({t_score}/{t_max})!")
                        st.rerun()
                    else:
                        st.error("Failed to save mock test.")
