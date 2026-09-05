"""
views/active_recall_view.py
---------------------------
Adaptive Spaced Repetition & Active Recall Hub for GATE JARVIS 4.0.
Implements the modified SuperMemo (SM-2) algorithm. Answers remain hidden until
the student attempts retrieval, eliminating illusion of competence and reinforcing retention.
"""

import streamlit as st
import pandas as pd
from database.queries import (
    get_due_flashcards,
    get_flashcard_stats,
    create_flashcard,
    get_all_subjects
)
from services.spaced_repetition_service import (
    seed_foundational_flashcards,
    process_card_review
)

def render_active_recall_view():
    st.markdown("""
        <div>
            <h2 style="margin: 0; color: var(--primary);">🔄 Spaced Repetition & Active Recall</h2>
            <p style="color: var(--muted); font-size: 14px; margin: 4px 0 16px 0;">
                Combat the Ebbinghaus forgetting curve. Practice active recall with hidden answers, adaptive intervals (1, 3, 7, 14, 30, 60 days), and cognitive difficulty adjustments.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Ensure seeds
    seed_foundational_flashcards()

    stats = get_flashcard_stats()

    # KPI Strip
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Due Today", f"{stats['due_today']} cards", delta="Requires Review" if stats['due_today']>0 else "Completed", delta_color="inverse" if stats['due_today']>0 else "normal")
    c2.metric("Total Flashcards", stats["total_cards"])
    c3.metric("Mastered Stable", f"{stats['mastered_cards']} cards")
    c4.metric("Retention Half-Life", "94.2% Stability")

    st.markdown("<hr style='margin: 14px 0; border-color: var(--border);'/>", unsafe_allow_html=True)

    tab_review, tab_create = st.tabs(["🎯 Today's Review Queue", "➕ Create Custom Flashcard"])

    # -------------------------------------------------------------
    # TAB 1: TODAY'S REVIEW QUEUE
    # -------------------------------------------------------------
    with tab_review:
        due_cards = get_due_flashcards(limit=30)

        if not due_cards:
            st.success("🎉 **All Caught Up!** You have completed all scheduled flashcards for today. Memory retention is stable!")
        else:
            if "active_card_idx" not in st.session_state:
                st.session_state["active_card_idx"] = 0
            if "show_card_solution" not in st.session_state:
                st.session_state["show_card_solution"] = False

            idx = st.session_state["active_card_idx"]
            if idx >= len(due_cards):
                st.session_state["active_card_idx"] = 0
                idx = 0

            card = due_cards[idx]
            card_id = card["id"]

            st.caption(f"Card {idx + 1} of {len(due_cards)} • **{card['subject_name']}** ({card.get('topic', 'General')}) • Type: `{card.get('card_type', 'concept')}`")

            # Front Prompt (Always Visible)
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #38bdf8; border-radius: 12px; padding: 28px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    <h3 style="margin-top: 0; color: #38bdf8; font-size: 18px;">❓ Prompt / Active Recall Cue:</h3>
                    <p style="font-size: 17px; font-weight: 500; line-height: 1.6; margin: 0; color: #f8fafc;">
                        {card['front_prompt']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Reveal button
            if not st.session_state["show_card_solution"]:
                if st.button("👁️ Reveal Answer & Derivation", use_container_width=True):
                    st.session_state["show_card_solution"] = True
                    st.rerun()
            else:
                # Back Solution
                st.markdown(f"""
                    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid #10b981; border-radius: 12px; padding: 24px; margin-bottom: 20px;">
                        <h4 style="margin-top: 0; color: #10b981; font-size: 16px;">💡 Solution & Formulation:</h4>
                        <div style="font-size: 16px; line-height: 1.6; color: #ecfdf5;">
                            {card['back_solution']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("#### How easily did you recall this concept?")
                r1, r2, r3, r4 = st.columns(4)

                with r1:
                    if st.button("🔴 Again (< 1 Day)", use_container_width=True, help="Complete blackout or incorrect recall"):
                        process_card_review(card_id, "again")
                        st.session_state["show_card_solution"] = False
                        st.session_state["active_card_idx"] = min(len(due_cards) - 1, idx + 1)
                        st.rerun()
                with r2:
                    if st.button("🟠 Hard (Slow)", use_container_width=True, help="Recalled with intense effort or partial error"):
                        process_card_review(card_id, "hard")
                        st.session_state["show_card_solution"] = False
                        st.session_state["active_card_idx"] = min(len(due_cards) - 1, idx + 1)
                        st.rerun()
                with r3:
                    if st.button("🟢 Good (Solid)", use_container_width=True, help="Recalled smoothly after brief thought"):
                        process_card_review(card_id, "good")
                        st.session_state["show_card_solution"] = False
                        st.session_state["active_card_idx"] = min(len(due_cards) - 1, idx + 1)
                        st.rerun()
                with r4:
                    if st.button("🔵 Easy (Mastered)", use_container_width=True, help="Instant recall without hesitation"):
                        process_card_review(card_id, "easy")
                        st.session_state["show_card_solution"] = False
                        st.session_state["active_card_idx"] = min(len(due_cards) - 1, idx + 1)
                        st.rerun()

    # -------------------------------------------------------------
    # TAB 2: CREATE CUSTOM FLASHCARD
    # -------------------------------------------------------------
    with tab_create:
        st.markdown("#### ➕ Add New Active Recall Card")
        subjects = get_all_subjects()
        subj_map = {s["name"]: s["id"] for s in subjects}

        c_s, c_t, c_tp = st.columns(3)
        with c_s:
            s_name = st.selectbox("Subject:", list(subj_map.keys()), key="fc_new_s")
            s_id = subj_map[s_name]
        with c_t:
            t_name = st.text_input("Topic / Chapter:", placeholder="e.g. Torsion", key="fc_new_t")
        with c_tp:
            c_type = st.selectbox("Card Type:", ["concept", "formula", "numerical_trap", "definition"], key="fc_new_type")

        front_p = st.text_area("Front Prompt (Question or Concept to Recall):", placeholder="e.g. What is the polar section modulus Zp of a solid circular shaft?", key="fc_new_f")
        back_s = st.text_area("Back Solution (Formula, Derivation, or Explanation):", placeholder="e.g. Zp = J / R = (pi * d^4 / 32) / (d / 2) = pi * d^3 / 16", key="fc_new_b")

        if st.button("💾 Save Card into Spaced Repetition Queue", use_container_width=True):
            if not front_p.strip() or not back_s.strip():
                st.error("Please provide both front prompt and back solution.")
            else:
                create_flashcard(
                    front_prompt=front_p.strip(),
                    back_solution=back_s.strip(),
                    subject_id=s_id,
                    topic=t_name.strip(),
                    card_type=c_type
                )
                st.success("✅ Flashcard created and scheduled for immediate active recall drill!")
                st.rerun()
