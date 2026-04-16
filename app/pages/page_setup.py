"""Setup page — resume upload, candidate profile, company context, panel config, interview settings."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from ingestion.resume_parser import extract_resume_text, parse_resume_to_profile
from models.schemas import (
    CandidateProfile,
    CompanyContext,
    InterviewSettings,
    InterviewType,
    InterviewMode,
    AnswerStyle,
    InterviewerTone,
    CountryPreset,
    PanelMember,
)
from research.service import ResearchService


def render() -> None:
    st.header('📝 Interview Setup')

    # ── Resume upload ──
    with st.expander('Resume Upload', expanded=True):
        uploaded = st.file_uploader('Upload resume (PDF or DOCX)', type=['pdf', 'docx'])
        if uploaded and st.button('Parse Resume'):
            suffix = Path(uploaded.name).suffix if uploaded.name else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
                fh.write(uploaded.getbuffer())
                temp_path = fh.name
            raw_text = extract_resume_text(temp_path)
            if not raw_text.strip():
                st.error(
                    '❌ Resume text extraction returned nothing. '
                    'Check that `pypdf` (for PDF) or `python-docx` (for DOCX) is installed, '
                    'and that the file is not password-protected or image-only.'
                )
            else:
                parsed = parse_resume_to_profile(raw_text)
                st.session_state.candidate_profile = parsed
                if not parsed.name:
                    st.warning(
                        '⚠️ Resume parsed but no name was detected. '
                        'The parser uses heuristic keyword matching — review and fill in '
                        'the profile fields below.'
                    )
                else:
                    st.success('Resume parsed — review below.')

    # ── Candidate profile ──
    with st.expander('Candidate Profile', expanded=False):
        profile: CandidateProfile = st.session_state.candidate_profile
        profile.name = st.text_input('Name', value=profile.name)
        profile.summary = st.text_area('Summary', value=profile.summary, height=80)
        profile.target_role = st.text_input('Target role', value=profile.target_role)
        profile.target_company = st.text_input('Target company', value=profile.target_company)
        profile.additional_background = st.text_area(
            'Additional background / achievements / projects',
            value=profile.additional_background, height=100,
        )
        profile.skills = [
            s.strip() for s in
            st.text_area('Skills (comma-separated)', value=', '.join(profile.skills)).split(',')
            if s.strip()
        ]
        st.session_state.candidate_profile = profile

    # ── Company context ──
    with st.expander('Company & Job Context', expanded=False):
        ctx: CompanyContext = st.session_state.company_context
        ctx.company_information = st.text_area('Company information', value=ctx.company_information, height=100)
        ctx.job_description = st.text_area('Job description', value=ctx.job_description, height=100)
        ctx.company_values = st.text_area('What this company values', value=ctx.company_values, height=80)
        st.session_state.company_context = ctx

    # ── Panel configuration ──
    with st.expander('Panel Configuration', expanded=False):
        with st.form('panel_form', clear_on_submit=True):
            col1, col2 = st.columns(2)
            name = col1.text_input('Interviewer name')
            role = col2.selectbox('Role type', ['hr', 'technical', 'senior_leadership'])
            title = col1.text_input('Title')
            notes = col2.text_area('Notes', height=68)
            if st.form_submit_button('Add Panel Member') and name:
                st.session_state.panel_members.append(
                    PanelMember(name=name, role_type=role, title=title, notes=notes)
                )
        if st.session_state.panel_members:
            for m in st.session_state.panel_members:
                st.write(f'**{m.name}** — {m.role_type} ({m.title})')
            if st.button('Clear panel'):
                st.session_state.panel_members = []
                st.rerun()

        settings = get_settings()
        if st.toggle('Enable interviewer web research', value=settings.enable_web_research):
            research = ResearchService(enabled=True, api_key=settings.search_api_key)
            for member in st.session_state.panel_members:
                result = research.research_subject(member.name)
                with st.container():
                    st.caption(f'{member.name} — confidence: {result.confidence:.0%}')
                    st.write(result.likely_background)

    # ── Interview settings ──
    with st.expander('Interview Settings', expanded=True):
        isettings: InterviewSettings = st.session_state.interview_settings
        col1, col2 = st.columns(2)
        isettings.interview_type = col1.selectbox(
            'Interview type', list(InterviewType), format_func=lambda x: x.value,
            index=list(InterviewType).index(isettings.interview_type),
        )
        isettings.mode = col2.selectbox(
            'Interview mode', list(InterviewMode), format_func=lambda x: x.value,
            index=list(InterviewMode).index(isettings.mode),
        )
        col3, col4 = st.columns(2)
        isettings.answer_style = col3.selectbox(
            'Expected answer style', list(AnswerStyle), format_func=lambda x: x.value,
            index=list(AnswerStyle).index(isettings.answer_style),
        )
        isettings.interviewer_tone = col4.selectbox(
            'Interviewer tone', list(InterviewerTone), format_func=lambda x: x.value,
            index=list(InterviewerTone).index(isettings.interviewer_tone),
        )
        col5, col6 = st.columns(2)
        isettings.country_preset = col5.selectbox(
            'Country / culture preset', list(CountryPreset), format_func=lambda x: x.value,
            index=list(CountryPreset).index(isettings.country_preset),
        )
        isettings.time_budget_minutes = col6.selectbox(
            'Time budget (minutes)', [10, 20, 30, 45, 60],
            index=[10, 20, 30, 45, 60].index(isettings.time_budget_minutes),
        )
        isettings.panel_mode = st.checkbox('Panel mode', value=isettings.panel_mode)

        # Audio/Video settings
        st.divider()
        st.subheader('🎤 Audio & Video')
        col7, col8 = st.columns(2)
        enable_audio = col7.checkbox('Enable audio input (mic)', value=True, key='enable_audio')
        enable_video = col8.checkbox('Enable video recording (webcam)', value=False, key='enable_video')
        auto_submit = st.checkbox(
            'Auto-submit on silence detection (hands-free mode)',
            value=True, key='auto_submit',
            help='Automatically submits your answer when silence is detected after you stop speaking.',
        )

        st.session_state.interview_settings = isettings
