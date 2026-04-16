"""Interview page — live session with audio-in/audio-out, video recording,
auto-submit on silence, LLM follow-ups, and TTS playback.

Implements the end-to-end flow:
  Browser mic → Whisper transcription → LLM question/follow-up →
  Edge TTS audio-out → st.audio() playback

When WebRTC video is enabled, frames are recorded for body language analysis.
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from interview_engine.question_bank import QuestionBank
from interview_engine.session import InterviewSessionEngine
from models.schemas import (
    CompetencyTag,
    InterviewMode,
    InterviewPhase,
    InterviewSettings,
    SessionState,
)
from services.provider_registry import build_provider_bundle
from services.recording import RecordingService


def _ensure_providers():
    """Build provider bundle once per session."""
    if st.session_state.provider_bundle is None:
        settings = get_settings()
        st.session_state.provider_bundle = build_provider_bundle(settings)
    return st.session_state.provider_bundle


def _ensure_recording_service():
    """Build recording service once per session."""
    if st.session_state.recording_service is None:
        bundle = _ensure_providers()
        st.session_state.recording_service = RecordingService(
            transcription_provider=bundle.transcription_provider,
            tts_provider=bundle.tts_provider,
            multimodal_provider=bundle.multimodal_provider,
        )
    return st.session_state.recording_service


def _play_tts(text: str, speaker: str = 'Interviewer') -> None:
    """Synthesize and play TTS audio for interviewer speech."""
    rec = _ensure_recording_service()
    audio_bytes = rec.synthesize_speech(text, speaker=speaker)
    if audio_bytes and len(audio_bytes) > 100:
        st.audio(audio_bytes, format='audio/mp3', autoplay=True)


def _handle_audio_input(state: SessionState, engine: InterviewSessionEngine) -> str | None:
    """Handle audio input from browser mic, transcribe, and return text."""
    audio_data = st.audio_input(
        '🎤 Speak your answer',
        key='audio_input',
    )
    if audio_data:
        rec = _ensure_recording_service()
        audio_bytes = audio_data.getvalue()
        # Save audio
        qid = state.asked_question_ids[-1] if state.asked_question_ids else 'unknown'
        rec.save_audio(audio_bytes, question_id=qid)
        # Transcribe
        with st.spinner('Transcribing...'):
            transcription = rec.transcribe(audio_bytes)
        if transcription:
            st.success(f'Transcribed: {transcription[:100]}...' if len(transcription) > 100 else f'Transcribed: {transcription}')
            return transcription
        else:
            st.warning('Could not transcribe audio. Please type your answer or try again.')
    return None


def _handle_video_setup() -> None:
    """Set up WebRTC video recording if enabled."""
    if not st.session_state.get('enable_video', False):
        return
    try:
        from streamlit_webrtc import webrtc_streamer, WebRtcMode
        webrtc_streamer(
            key='video_recorder',
            mode=WebRtcMode.SENDONLY,
            media_stream_constraints={'video': True, 'audio': False},
            desired_playing_state=st.session_state.interview_started,
        )
        st.caption('📹 Video recording active — will be analyzed for body language after session.')
    except ImportError:
        st.info('Install streamlit-webrtc for video recording: `pip install streamlit-webrtc`')
    except Exception:
        st.info('WebRTC video unavailable in this environment.')


def render() -> None:
    st.header('🎙️ Interview Session')

    isettings: InterviewSettings = st.session_state.interview_settings
    enable_audio = st.session_state.get('enable_audio', True)
    auto_submit = st.session_state.get('auto_submit', True)

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

    # ── Video setup ──
    _handle_video_setup()

    # ── Start interview ──
    if not st.session_state.interview_started:
        if st.button('▶️ Start Interview', type='primary'):
            bundle = _ensure_providers()
            session_state = SessionState(
                mode=isettings.mode,
                interview_type=isettings.interview_type,
                time_budget_minutes=isettings.time_budget_minutes,
                answer_style=isettings.answer_style,
                interviewer_tone=isettings.interviewer_tone,
                country_preset=isettings.country_preset,
            )
            planner = InterviewPlanner(QuestionBank())
            evaluator = EvaluationPipeline(text_provider=bundle.text_provider)
            engine = InterviewSessionEngine(
                planner, evaluator,
                text_provider=bundle.text_provider,
            )

            # Opening
            opening = engine.get_opening(session_state)
            st.session_state.session_state = session_state
            st.session_state.engine = engine
            st.session_state.interview_started = True
            st.session_state.start_time = time.time()
            st.session_state.current_prompt = opening
            st.session_state.session_id = str(uuid.uuid4())[:8]

            # Start recording
            rec = _ensure_recording_service()
            rec.start(question_id='opening')

            st.rerun()
        return

    engine: InterviewSessionEngine = st.session_state.engine
    state = st.session_state.session_state

    # ── Current question / prompt ──
    st.info(st.session_state.current_prompt or 'No active question.')

    # Play TTS for current prompt
    if st.session_state.current_prompt and enable_audio:
        _play_tts(st.session_state.current_prompt)

    # ── Controls ──
    col_next, col_end = st.columns(2)

    if col_next.button('Next Question'):
        prompt = engine.next_prompt(state)
        if prompt:
            st.session_state.current_prompt = prompt
        else:
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

    if col_end.button('End Interview'):
        wrapup = engine.get_wrapup(state)
        st.session_state.current_prompt = wrapup
        st.session_state.interview_started = False
        # Stop recording
        rec = _ensure_recording_service()
        rec.stop()
        # Save session
        _save_session()
        st.rerun()

    # ── Answer input: audio or text ──
    st.subheader('Your Answer')

    answer = None
    if enable_audio:
        st.markdown('**Option 1: Speak your answer** (audio will be transcribed automatically)')
        transcription = _handle_audio_input(state, engine)
        if transcription:
            answer = transcription
            if auto_submit and answer and state.asked_question_ids:
                # Auto-submit on audio transcription completion
                _submit_answer(engine, state, answer, isettings)
                # Generate follow-up
                _handle_follow_up(engine, state, answer)
                st.rerun()

        st.markdown('**Option 2: Type your answer**')

    answer_text = st.text_area('Type your answer here', height=150, key='candidate_answer')

    col_submit, col_follow = st.columns(2)
    if col_submit.button('Submit Answer') and (answer_text or answer) and state.asked_question_ids:
        final_answer = answer or answer_text
        _submit_answer(engine, state, final_answer, isettings)
        # Generate follow-up
        _handle_follow_up(engine, state, final_answer)
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


def _submit_answer(engine, state, answer, isettings):
    """Submit answer, run evaluation, and show feedback."""
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


def _handle_follow_up(engine, state, answer):
    """Generate and display LLM follow-up question."""
    follow_up = engine.generate_follow_up_prompt(answer, state)
    if follow_up:
        st.session_state.current_prompt = follow_up


def _save_session():
    """Persist session to SQLite."""
    try:
        from storage.session_store import SessionStore
        store = SessionStore()
        engine = st.session_state.engine
        state = st.session_state.session_state
        if engine and state:
            evaluations = st.session_state.evaluations
            pipeline = EvaluationPipeline()
            competency_map = state.competency_coverage if state else {}
            report = pipeline.build_session_report(evaluations, competency_map, {})
            store.save_session(
                session_id=st.session_state.session_id or 'unknown',
                state=state,
                transcript=engine.transcript,
                evaluations=evaluations,
                report=report,
            )
            # Save per-competency scores for spaced repetition
            comp_scores = {}
            for ev in evaluations:
                comp_scores[ev.question_id] = ev.rubric_score.weighted_total
            store.save_competency_scores(st.session_state.session_id or 'unknown', comp_scores)
            store.close()
    except Exception:
        pass  # Don't break the UI if persistence fails
