from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from backend.logging import configure_logging
from evaluation.pipeline import EvaluationPipeline
from ingestion.resume_parser import extract_resume_text, parse_resume_to_profile
from interview_engine.planner import InterviewPlanner
from interview_engine.question_bank import QuestionBank
from interview_engine.session import InterviewSessionEngine
from models.schemas import CandidateProfile, CompanyContext, InterviewMode, InterviewType, PanelMember, SessionState
from research.service import ResearchService
from services.provider_registry import build_provider_bundle


def _init_state() -> None:
    if 'candidate_profile' not in st.session_state:
        st.session_state.candidate_profile = CandidateProfile()
    if 'company_context' not in st.session_state:
        st.session_state.company_context = CompanyContext()
    if 'panel_members' not in st.session_state:
        st.session_state.panel_members = []
    if 'evaluations' not in st.session_state:
        st.session_state.evaluations = []


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    providers = build_provider_bundle(settings)

    st.set_page_config(page_title='InterviewPractice', layout='wide')
    st.title('InterviewPractice MVP')
    st.caption('AI-powered interview simulation with structured critique pipeline')

    _init_state()

    tabs = st.tabs([
        'Setup',
        'Candidate Profile',
        'Company Context',
        'Panel Configuration',
        'Interview Session',
        'Live Transcript',
        'Final Feedback',
        'Settings / Providers',
    ])

    with tabs[0]:
        uploaded = st.file_uploader('Upload resume (PDF or DOCX)', type=['pdf', 'docx'])
        if uploaded and st.button('Parse Resume'):
            suffix = Path(uploaded.name).suffix if uploaded.name else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
                file.write(uploaded.getbuffer())
                temp_path = file.name
            parsed = parse_resume_to_profile(extract_resume_text(temp_path))
            st.session_state.candidate_profile = parsed
            st.success('Resume parsed. Review extracted profile in Candidate Profile tab.')

    with tabs[1]:
        profile: CandidateProfile = st.session_state.candidate_profile
        profile.name = st.text_input('Name', value=profile.name)
        profile.summary = st.text_area('Summary', value=profile.summary)
        profile.additional_background = st.text_area('Additional background', value=profile.additional_background)
        profile.target_role = st.text_input('Target role', value=profile.target_role)
        profile.skills = [s.strip() for s in st.text_area('Skills (comma-separated)', value=','.join(profile.skills)).split(',') if s.strip()]
        st.session_state.candidate_profile = profile

    with tabs[2]:
        context: CompanyContext = st.session_state.company_context
        context.company_information = st.text_area('Company information', value=context.company_information)
        context.job_description = st.text_area('Job description', value=context.job_description)
        context.company_values = st.text_area('What this company values', value=context.company_values)
        st.session_state.company_context = context

    with tabs[3]:
        with st.form('panel_form'):
            name = st.text_input('Interviewer name')
            role = st.selectbox('Role type', ['hr', 'technical', 'senior_leadership'])
            title = st.text_input('Title')
            notes = st.text_area('Optional notes')
            submitted = st.form_submit_button('Add panel member')
            if submitted and name:
                st.session_state.panel_members.append(PanelMember(name=name, role_type=role, title=title, notes=notes))

        st.write(st.session_state.panel_members)

        if st.toggle('Enable optional interviewer research', value=settings.enable_web_research):
            research = ResearchService(enabled=True)
            for member in st.session_state.panel_members:
                st.write({member.name: research.research_subject(member.name).__dict__})

    with tabs[4]:
        interview_type = st.selectbox('Interview type', list(InterviewType), format_func=lambda x: x.value)
        mode = st.selectbox('Interview mode', list(InterviewMode), format_func=lambda x: x.value)
        time_budget = st.selectbox('Time budget (minutes)', [10, 20, 30, 45, 60])

        state = SessionState(mode=mode, interview_type=interview_type, time_budget_minutes=time_budget)
        planner = InterviewPlanner(QuestionBank())
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator)

        if st.button('Ask next question'):
            st.session_state.current_prompt = engine.next_prompt(state)
            st.session_state.engine = engine
            st.session_state.state = state

        st.info(st.session_state.get('current_prompt', 'No question asked yet.'))
        answer = st.text_area('Candidate answer')

        if st.button('Evaluate answer') and answer and st.session_state.get('engine') and st.session_state.get('state'):
            current_engine: InterviewSessionEngine = st.session_state.engine
            current_state: SessionState = st.session_state.state
            qid = current_state.asked_question_ids[-1]
            evaluation = current_engine.submit_answer(qid, answer, current_state)
            st.session_state.evaluations.append(evaluation)
            st.json(json.loads(evaluator.to_structured_json(evaluation)))
            st.markdown(evaluator.to_human_critique(evaluation))

    with tabs[5]:
        engine = st.session_state.get('engine')
        if not engine:
            st.write('Transcript will appear once session starts.')
        else:
            for turn in engine.transcript:
                st.write(f'[{turn.timestamp.isoformat()}] {turn.speaker}: {turn.text}')

    with tabs[6]:
        evaluations = st.session_state.evaluations
        if evaluations:
            pipeline = EvaluationPipeline()
            current_state = st.session_state.get('state')
            competency_map = current_state.competency_coverage if current_state else {}
            report = pipeline.build_session_report(evaluations, competency_map, interviewer_feedback={})
            st.json(report.model_dump(mode='json'))
        else:
            st.write('No feedback yet. Run an interview first.')

    with tabs[7]:
        st.write(
            {
                'provider': settings.interview_provider,
                'model': settings.openai_model if settings.interview_provider == 'openai' else settings.gemini_model,
                'live_audio_supported': providers.live_audio_provider.supports_live_audio(),
                'audio_modes': [
                    'Live audio conversation mode (if provider supports)',
                    'Audio-in -> text-out',
                    'Audio-in -> text-out -> TTS output (Edge fallback)',
                ],
            }
        )


if __name__ == '__main__':
    main()
