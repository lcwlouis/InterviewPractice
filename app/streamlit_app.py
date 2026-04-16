"""InterviewPractice — Streamlit application entry point.

UI is organised into four sidebar pages instead of many tabs:
1. Setup         — Resume upload, candidate profile, company context, panel
2. Interview     — Session controls, live transcript, answer submission
3. Feedback      — Per-question evaluations and full session report
4. Settings      — Provider config and audio mode display
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings  # noqa: E402
from backend.logging import configure_logging  # noqa: E402
from evaluation.pipeline import EvaluationPipeline  # noqa: E402
from ingestion.resume_parser import extract_resume_text, parse_resume_to_profile  # noqa: E402
from interview_engine.planner import InterviewPlanner  # noqa: E402
from interview_engine.question_bank import QuestionBank  # noqa: E402
from interview_engine.session import InterviewSessionEngine  # noqa: E402
from models.schemas import (  # noqa: E402
    AnswerStyle,
    CandidateProfile,
    CompanyContext,
    CompetencyTag,
    CountryPreset,
    InterviewerTone,
    InterviewMode,
    InterviewPhase,
    InterviewSettings,
    InterviewType,
    PanelMember,
    SessionState,
)
from research.service import ResearchService  # noqa: E402
from services.provider_registry import build_provider_bundle  # noqa: E402
from storage.local_store import save_report_json, save_report_markdown  # noqa: E402


# ── session state defaults ────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        'candidate_profile': CandidateProfile(),
        'company_context': CompanyContext(),
        'panel_members': [],
        'evaluations': [],
        'interview_settings': InterviewSettings(),
        'session_state': None,
        'engine': None,
        'current_prompt': None,
        'interview_started': False,
        'start_time': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ── page: Setup ───────────────────────────────────────────────────────────

def _page_setup() -> None:
    st.header('📝 Interview Setup')

    # ── Resume upload ──
    with st.expander('Resume Upload', expanded=True):
        uploaded = st.file_uploader('Upload resume (PDF or DOCX)', type=['pdf', 'docx'])
        if uploaded and st.button('Parse Resume'):
            suffix = Path(uploaded.name).suffix if uploaded.name else '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as fh:
                fh.write(uploaded.getbuffer())
                temp_path = fh.name
            parsed = parse_resume_to_profile(extract_resume_text(temp_path))
            st.session_state.candidate_profile = parsed
            st.success('Resume parsed — review below.')

    # ── Candidate profile ──
    with st.expander('Candidate Profile', expanded=False):
        profile: CandidateProfile = st.session_state.candidate_profile
        profile.name = st.text_input('Name', value=profile.name)
        profile.summary = st.text_area('Summary', value=profile.summary, height=80)
        profile.target_role = st.text_input('Target role', value=profile.target_role)
        profile.target_company = st.text_input('Target company', value=profile.target_company)
        profile.additional_background = st.text_area(
            'Additional background / achievements / projects', value=profile.additional_background, height=100,
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
            for idx, m in enumerate(st.session_state.panel_members):
                st.write(f'**{m.name}** — {m.role_type} ({m.title})')
            if st.button('Clear panel'):
                st.session_state.panel_members = []
                st.rerun()

        settings = get_settings()
        if st.toggle('Enable interviewer web research', value=settings.enable_web_research):
            research = ResearchService(enabled=True)
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
        st.session_state.interview_settings = isettings


# ── page: Interview ───────────────────────────────────────────────────────

def _page_interview() -> None:
    st.header('🎙️ Interview Session')

    isettings: InterviewSettings = st.session_state.interview_settings

    # ── Status bar ──
    col_phase, col_timer, col_mode = st.columns(3)
    state: SessionState | None = st.session_state.session_state
    if state:
        col_phase.metric('Phase', state.phase.value)
        elapsed = time.time() - (st.session_state.start_time or time.time())
        remaining = max(0, state.time_budget_minutes * 60 - elapsed)
        col_timer.metric('Time left', f'{int(remaining // 60)}:{int(remaining % 60):02d}')
    else:
        col_phase.metric('Phase', '—')
        col_timer.metric('Time left', f'{isettings.time_budget_minutes}:00')
    col_mode.metric('Mode', isettings.mode.value)

    # ── Start interview ──
    if not st.session_state.interview_started:
        if st.button('▶️ Start Interview', type='primary'):
            session_state = SessionState(
                mode=isettings.mode,
                interview_type=isettings.interview_type,
                time_budget_minutes=isettings.time_budget_minutes,
                answer_style=isettings.answer_style,
                interviewer_tone=isettings.interviewer_tone,
                country_preset=isettings.country_preset,
            )
            planner = InterviewPlanner(QuestionBank())
            evaluator = EvaluationPipeline()
            engine = InterviewSessionEngine(planner, evaluator)

            # Opening
            opening = engine.get_opening(session_state)
            st.session_state.session_state = session_state
            st.session_state.engine = engine
            st.session_state.interview_started = True
            st.session_state.start_time = time.time()
            st.session_state.current_prompt = opening
            st.rerun()
        return

    engine: InterviewSessionEngine = st.session_state.engine
    state = st.session_state.session_state

    # ── Current question / prompt ──
    st.info(st.session_state.current_prompt or 'No active question.')

    # ── Next question button ──
    if st.button('Next Question'):
        prompt = engine.next_prompt(state)
        if prompt:
            st.session_state.current_prompt = prompt
        else:
            # No more questions — move to candidate questions / wrap-up
            if state.phase not in (InterviewPhase.CANDIDATE_QUESTIONS, InterviewPhase.WRAP_UP):
                state.phase = InterviewPhase.CANDIDATE_QUESTIONS
                prompt = engine.next_prompt(state)
                if prompt:
                    st.session_state.current_prompt = prompt
                else:
                    wrapup = engine.get_wrapup(state)
                    st.session_state.current_prompt = wrapup
            else:
                wrapup = engine.get_wrapup(state)
                st.session_state.current_prompt = wrapup
        st.rerun()

    # ── Answer input ──
    answer = st.text_area('Your answer', height=150, key='candidate_answer')
    col_submit, col_coaching = st.columns(2)

    if col_submit.button('Submit Answer') and answer and state.asked_question_ids:
        qid = state.asked_question_ids[-1]
        evaluation = engine.submit_answer(qid, answer, state)
        st.session_state.evaluations.append(evaluation)

        if isettings.mode == InterviewMode.ANSWER_COACHING:
            st.subheader('💡 Coaching Feedback')
            cf = evaluation.coaching_feedback
            st.markdown(f'**What worked:** {", ".join(cf.what_worked) or "—"}')
            st.markdown(f'**Weak areas:** {", ".join(cf.what_was_weak) or "—"}')
            st.markdown(f'**Missing:** {", ".join(cf.what_was_missing) or "—"}')
            if cf.stronger_answer_outline:
                st.markdown(f'**Stronger outline:** {cf.stronger_answer_outline}')
            if cf.retry_prompt:
                st.info(f'🔄 {cf.retry_prompt}')
        else:
            st.success(f'Scored: {evaluation.rubric_score.weighted_total:.1f}/10')

    if col_coaching.button('End Interview'):
        wrapup = engine.get_wrapup(state)
        st.session_state.current_prompt = wrapup
        st.session_state.interview_started = False
        st.rerun()

    # ── Competency progress ──
    if state.competency_coverage:
        st.subheader('Competency Coverage')
        for comp in CompetencyTag:
            count = state.competency_coverage.get(comp, 0)
            st.progress(min(count / 3, 1.0), text=f'{comp.value}: {count}')

    # ── Live transcript ──
    st.subheader('📜 Live Transcript')
    for turn in engine.transcript:
        ts = turn.timestamp.strftime('%H:%M:%S')
        if turn.role == 'candidate':
            st.markdown(f'`{ts}` **You:** {turn.text}')
        else:
            st.markdown(f'`{ts}` **{turn.speaker}:** {turn.text}')


# ── page: Feedback ────────────────────────────────────────────────────────

def _page_feedback() -> None:
    st.header('📊 Feedback & Report')
    evaluations = st.session_state.evaluations

    if not evaluations:
        st.info('No evaluations yet — run an interview first.')
        return

    pipeline = EvaluationPipeline()

    # Per-question breakdown
    with st.expander('Question-by-Question Breakdown', expanded=True):
        for evaluation in evaluations:
            st.subheader(f'Question: {evaluation.question_id}')
            col1, col2 = st.columns(2)
            col1.metric('Score', f'{evaluation.rubric_score.weighted_total:.1f}')
            col2.write(f'**Evidence:** {evaluation.answer_analysis.transcript_evidence[:2]}')

            st.markdown(pipeline.to_human_critique(evaluation))
            with st.expander('Raw JSON analysis'):
                st.json(json.loads(pipeline.to_structured_json(evaluation)))
            st.divider()

    # Full session report
    with st.expander('Full Session Report', expanded=False):
        state = st.session_state.session_state
        competency_map = state.competency_coverage if state else {}
        report = pipeline.build_session_report(evaluations, competency_map, interviewer_feedback={})
        st.json(report.model_dump(mode='json'))

        col_json, col_md = st.columns(2)
        if col_json.button('Export JSON'):
            save_report_json(report, '/tmp/interview_report.json')
            st.success('Saved to /tmp/interview_report.json')
        if col_md.button('Export Markdown'):
            save_report_markdown(report, '/tmp/interview_report.md')
            st.success('Saved to /tmp/interview_report.md')


# ── page: Settings ────────────────────────────────────────────────────────

def _page_settings() -> None:
    st.header('⚙️ Settings & Providers')
    settings = get_settings()
    providers = build_provider_bundle(settings)

    st.subheader('Active Provider')
    st.write({
        'provider': settings.interview_provider,
        'model': settings.openai_model if settings.interview_provider == 'openai' else settings.gemini_model,
        'live_audio_supported': providers.live_audio_provider.supports_live_audio(),
    })

    st.subheader('Audio Modes')
    st.markdown('''
1. **Live audio conversation** — if provider supports realtime/live API
2. **Audio-in → text-out** — transcribe audio, generate text response
3. **Audio-in → text-out → TTS** — add Edge TTS speech synthesis fallback
    ''')

    st.subheader('Environment Variables')
    st.code(
        'INTERVIEW_PROVIDER=openai\n'
        'OPENAI_API_KEY=sk-...\n'
        'OPENAI_MODEL=gpt-4.1-mini\n'
        'GEMINI_API_KEY=...\n'
        'GEMINI_MODEL=gemini-2.5-pro\n'
        'APP_LOG_LEVEL=INFO\n'
        'ENABLE_WEB_RESEARCH=false\n'
        'DEFAULT_COUNTRY_PRESET=US',
        language='bash',
    )


# ── main ──────────────────────────────────────────────────────────────────

PAGES = {
    '📝 Setup': _page_setup,
    '🎙️ Interview': _page_interview,
    '📊 Feedback': _page_feedback,
    '⚙️ Settings': _page_settings,
}


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)

    st.set_page_config(page_title='InterviewPractice', layout='wide')
    _init_state()

    st.sidebar.title('InterviewPractice')
    st.sidebar.caption('AI-powered mock interview with structured critique')
    page = st.sidebar.radio('Navigation', list(PAGES.keys()), label_visibility='collapsed')
    PAGES[page]()


if __name__ == '__main__':
    main()
