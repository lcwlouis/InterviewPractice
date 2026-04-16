"""History page — session persistence, replay, and spaced repetition.

Implements Suggestion 6 UI: browse past sessions, view transcripts,
see competency trends, and identify weak areas for practice.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)

from storage.session_store import SessionStore


def render() -> None:
    st.header('📜 Session History')

    try:
        store = SessionStore()
    except Exception:
        logger.exception('Could not connect to session database')
        st.error('Could not connect to session database. Check the app logs.')
        return

    try:
        sessions = store.list_sessions()
    except Exception:
        logger.exception('Failed to list sessions')
        st.error('Failed to load session list from database.')
        store.close()
        return

    if not sessions:
        st.info('No past sessions found. Complete an interview to see history here.')
        store.close()
        return

    # ── Session list ──
    st.subheader('Past Sessions')
    for sess in sessions:
        col1, col2, col3 = st.columns([2, 2, 1])
        session_id = sess.get('id', 'unknown')
        started = sess.get('started_at', '')[:19] if sess.get('started_at') else '—'
        col1.write(f"**{session_id}**")
        col2.write(f"Started: {started}")
        if col3.button('View', key=f"view_{session_id}"):
            st.session_state['viewing_session'] = session_id

    # ── Session detail ──
    viewing = st.session_state.get('viewing_session')
    if viewing:
        st.divider()
        st.subheader(f'Session: {viewing}')

        # Transcript replay
        with st.expander('📜 Transcript', expanded=True):
            try:
                transcript = store.load_transcript(viewing)
                if transcript:
                    for turn in transcript:
                        ts = turn.timestamp.strftime('%H:%M:%S')
                        if turn.role == 'candidate':
                            st.markdown(f'`{ts}` **You:** {turn.text}')
                        else:
                            st.markdown(f'`{ts}` **{turn.speaker}:** {turn.text}')
                else:
                    st.write('No transcript found for this session.')
            except Exception:
                logger.exception('Failed to load transcript for session %s', viewing)
                st.warning('Could not load transcript for this session.')

        # Evaluations
        with st.expander('📊 Evaluations', expanded=False):
            try:
                evaluations = store.load_evaluations(viewing)
                if evaluations:
                    for ev in evaluations:
                        st.write(f'**{ev.question_id}**: Score {ev.rubric_score.weighted_total:.1f}/10')
                        st.caption(f'Strengths: {", ".join(ev.coaching_feedback.what_worked) or "—"}')
                        st.caption(f'Weaknesses: {", ".join(ev.coaching_feedback.what_was_weak) or "—"}')
                else:
                    st.write('No evaluations found for this session.')
            except Exception:
                logger.exception('Failed to load evaluations for session %s', viewing)
                st.warning('Could not load evaluations for this session.')

        # Report
        try:
            report = store.load_report(viewing)
            if report:
                with st.expander('📋 Session Report', expanded=False):
                    st.write(f'**Summary:** {report.overall_summary}')
                    if report.top_3_actions:
                        st.write('**Top 3 Actions:**')
                        for action in report.top_3_actions:
                            st.write(f'- {action}')
        except Exception:
            logger.exception('Failed to load report for session %s', viewing)
            st.warning('Could not load session report.')

    # ── Spaced Repetition / Weak Areas ──
    st.divider()
    st.subheader('🎯 Areas for Practice (Spaced Repetition)')
    try:
        weak = store.get_weak_competencies(threshold=6.0)
        if weak:
            st.warning('These competencies need more practice:')
            for comp in weak:
                try:
                    trend = store.get_competency_trend(comp, limit=5)
                    scores = [t['score'] for t in trend]
                    avg = sum(scores) / len(scores) if scores else 0
                    st.write(f'- **{comp}**: avg score {avg:.1f}/10 ({len(scores)} data points)')
                except Exception:
                    st.write(f'- **{comp}**: (could not load trend data)')
        else:
            st.success('No weak competencies detected! Keep practicing to maintain your skills.')
    except Exception:
        logger.exception('Failed to load competency data')
        st.info('Competency tracking will be available after completing sessions with evaluations.')

    store.close()
