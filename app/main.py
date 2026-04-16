"""InterviewPractice — Streamlit multi-page app entry point.

Refactored to use Streamlit's native pages/ directory structure
(Suggestion 14). This file handles global configuration and shared state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings  # noqa: E402
from backend.logging import configure_logging  # noqa: E402
from models.schemas import (  # noqa: E402
    CandidateProfile,
    CompanyContext,
    InterviewSettings,
    CountryPreset,
)


def _init_state() -> None:
    """Initialise Streamlit session state with defaults, restoring persisted setup data."""
    settings = get_settings()
    # Map config default_country_preset to enum
    try:
        default_country = CountryPreset(settings.default_country_preset)
    except ValueError:
        default_country = CountryPreset.SINGAPORE

    defaults = {
        'candidate_profile': CandidateProfile(),
        'company_context': CompanyContext(),
        'panel_members': [],
        'evaluations': [],
        'interview_settings': InterviewSettings(country_preset=default_country),
        'session_state': None,
        'engine': None,
        'current_prompt': None,
        'interview_started': False,
        'start_time': None,
        'session_id': None,
        'recording_service': None,
        'provider_bundle': None,
        'retry_answers': {},  # question_id -> list of retry texts
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Restore persisted setup data on first load
    if '_setup_restored' not in st.session_state:
        st.session_state['_setup_restored'] = True
        try:
            from storage.session_store import SessionStore
            store = SessionStore()
            saved = store.load_setup_data()
            store.close()
            if 'candidate_profile' in saved:
                st.session_state['candidate_profile'] = saved['candidate_profile']
            if 'company_context' in saved:
                st.session_state['company_context'] = saved['company_context']
            if 'interview_settings' in saved:
                st.session_state['interview_settings'] = saved['interview_settings']
            if 'panel_members' in saved:
                st.session_state['panel_members'] = saved['panel_members']
        except Exception:
            pass  # First run or DB not available yet


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)

    st.set_page_config(
        page_title='InterviewPractice',
        page_icon='🎙️',
        layout='wide',
    )
    _init_state()

    st.sidebar.title('InterviewPractice')
    st.sidebar.caption('AI-powered mock interview with structured critique')

    # Navigation using native multi-page structure
    pages = {
        '📝 Setup': 'pages/1_Setup.py',
        '🎙️ Interview': 'pages/2_Interview.py',
        '📊 Feedback': 'pages/3_Feedback.py',
        '📜 History': 'pages/4_History.py',
        '⚙️ Settings': 'pages/5_Settings.py',
    }

    page = st.sidebar.radio('Navigation', list(pages.keys()), label_visibility='collapsed')

    # Import and run selected page
    if page == '📝 Setup':
        from pages.page_setup import render
    elif page == '🎙️ Interview':
        from pages.page_interview import render
    elif page == '📊 Feedback':
        from pages.page_feedback import render
    elif page == '📜 History':
        from pages.page_history import render
    else:
        from pages.page_settings import render

    render()


if __name__ == '__main__':
    main()
