"""History page — session persistence, replay, and spaced repetition.

Implements Suggestion 6 UI: browse past sessions, view transcripts,
see competency trends, and identify weak areas for practice.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.session_store import SessionStore


def render() -> None:
    st.header('📜 Session History')

    try:
        store = SessionStore()
    except Exception:
        st.error('Could not connect to session database.')
        return

    sessions = store.list_sessions()

    if not sessions:
        st.info('No past sessions found. Complete an interview to see history here.')
        store.close()
        return

    # ── Session list ──
    st.subheader('Past Sessions')
    for sess in sessions:
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.write(f"**{sess['id']}**")
        col2.write(f"Started: {sess['started_at'][:19]}")
        if col3.button('View', key=f"view_{sess['id']}"):
            st.session_state['viewing_session'] = sess['id']

    # ── Session detail ──
    viewing = st.session_state.get('viewing_session')
    if viewing:
        st.divider()
        st.subheader(f'Session: {viewing}')

        # Transcript replay
        with st.expander('📜 Transcript', expanded=True):
            transcript = store.load_transcript(viewing)
            if transcript:
                for turn in transcript:
                    ts = turn.timestamp.strftime('%H:%M:%S')
                    if turn.role == 'candidate':
                        st.markdown(f'`{ts}` **You:** {turn.text}')
                    else:
                        st.markdown(f'`{ts}` **{turn.speaker}:** {turn.text}')
            else:
                st.write('No transcript found.')

        # Evaluations
        with st.expander('📊 Evaluations', expanded=False):
            evaluations = store.load_evaluations(viewing)
            if evaluations:
                for ev in evaluations:
                    st.write(f'**{ev.question_id}**: Score {ev.rubric_score.weighted_total:.1f}/10')
                    st.caption(f'Strengths: {", ".join(ev.coaching_feedback.what_worked) or "—"}')
                    st.caption(f'Weaknesses: {", ".join(ev.coaching_feedback.what_was_weak) or "—"}')
            else:
                st.write('No evaluations found.')

        # Report
        report = store.load_report(viewing)
        if report:
            with st.expander('📋 Session Report', expanded=False):
                st.write(f'**Summary:** {report.overall_summary}')
                if report.top_3_actions:
                    st.write('**Top 3 Actions:**')
                    for action in report.top_3_actions:
                        st.write(f'- {action}')

    # ── Spaced Repetition / Weak Areas ──
    st.divider()
    st.subheader('🎯 Areas for Practice (Spaced Repetition)')
    weak = store.get_weak_competencies(threshold=6.0)
    if weak:
        st.warning('These competencies need more practice:')
        for comp in weak:
            trend = store.get_competency_trend(comp, limit=5)
            scores = [t['score'] for t in trend]
            avg = sum(scores) / len(scores) if scores else 0
            st.write(f'- **{comp}**: avg score {avg:.1f}/10 ({len(scores)} data points)')
    else:
        st.success('No weak competencies detected! Keep practicing to maintain your skills.')

    store.close()
