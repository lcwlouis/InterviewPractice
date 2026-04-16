"""Tests for new functionality — suggestions 1-7, 13, 14."""

import difflib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from interview_engine.question_bank import QuestionBank
from interview_engine.session import InterviewSessionEngine
from models.schemas import (
    AnswerStyle,
    CompetencyTag,
    CountryPreset,
    InterviewMode,
    InterviewPhase,
    InterviewSettings,
    InterviewType,
    SessionState,
)
from research.service import ResearchService
from services.recording import RecordingService
from storage.session_store import SessionStore


class QuestionBankYAMLTests(unittest.TestCase):
    """Suggestion 4: Question bank loads from YAML and has 100+ questions."""

    def test_yaml_loads_100_plus_questions(self):
        bank = QuestionBank()
        self.assertGreaterEqual(len(bank.questions), 100,
                                f'Expected 100+ questions, got {len(bank.questions)}')

    def test_all_competencies_covered(self):
        bank = QuestionBank()
        covered = set()
        for q in bank.questions:
            covered.update(q.competencies)
        for comp in CompetencyTag:
            self.assertIn(comp, covered, f'Competency {comp.value} not covered in question bank')

    def test_all_difficulties_present(self):
        bank = QuestionBank()
        difficulties = {q.difficulty for q in bank.questions}
        for d in [1, 2, 3, 4, 5]:
            self.assertIn(d, difficulties, f'Difficulty {d} not present in question bank')

    def test_has_warmup_questions(self):
        bank = QuestionBank()
        warmups = bank.get_warmup_questions()
        self.assertGreaterEqual(len(warmups), 3)

    def test_fallback_to_builtin_if_no_yaml(self):
        # Use a nonexistent path
        bank = QuestionBank(yaml_path=Path('/nonexistent/questions.yaml'))
        self.assertGreater(len(bank.questions), 0)

    def test_multiple_interview_types(self):
        bank = QuestionBank()
        types = {q.interview_type for q in bank.questions}
        self.assertIn(InterviewType.BEHAVIOURAL, types)
        self.assertIn(InterviewType.TECHNICAL, types)
        self.assertIn(InterviewType.HYBRID, types)


class LLMFollowUpTests(unittest.TestCase):
    """Suggestion 1: LLM-powered follow-up questions."""

    def test_follow_up_with_mock_provider(self):
        mock_provider = MagicMock()
        mock_provider.generate_text.return_value = 'Can you elaborate on the specific metrics you used to measure success?'

        bank = QuestionBank()
        planner = InterviewPlanner(bank)
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator, text_provider=mock_provider, max_follow_ups=2)

        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)

        follow_up = engine.generate_follow_up_prompt('I led a team project.', state)
        self.assertIsNotNone(follow_up)
        self.assertIn('elaborate', follow_up)
        mock_provider.generate_text.assert_called_once()

    def test_follow_up_respects_max_count(self):
        mock_provider = MagicMock()
        mock_provider.generate_text.return_value = 'Tell me more.'

        bank = QuestionBank()
        planner = InterviewPlanner(bank)
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator, text_provider=mock_provider, max_follow_ups=1)

        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)

        # First follow-up should work
        result1 = engine.generate_follow_up_prompt('Answer 1', state)
        self.assertIsNotNone(result1)

        # Second should be None (max reached)
        result2 = engine.generate_follow_up_prompt('Answer 2', state)
        self.assertIsNone(result2)

    def test_follow_up_without_provider_returns_none(self):
        bank = QuestionBank()
        planner = InterviewPlanner(bank)
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator, text_provider=None)

        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        result = engine.generate_follow_up_prompt('I did something.', state)
        self.assertIsNone(result)


class ResearchServiceTests(unittest.TestCase):
    """Suggestion 2: Web research integration (Tavily)."""

    def test_disabled_returns_empty(self):
        svc = ResearchService(enabled=False)
        results = svc.search('John Smith')
        self.assertEqual(results, [])

    def test_enabled_without_api_key_returns_empty(self):
        svc = ResearchService(enabled=True, api_key='')
        results = svc.search('John Smith')
        self.assertEqual(results, [])

    def test_research_subject_fallback(self):
        svc = ResearchService(enabled=False)
        result = svc.research_subject('Unknown Person')
        self.assertLess(result.confidence, 0.4)
        self.assertEqual(result.likely_background, 'Fallback to archetypal behavior')


class RecordingServiceTests(unittest.TestCase):
    """Suggestion 3 & 7: Audio/video recording service."""

    def test_start_stop_recording(self):
        svc = RecordingService()
        artifact = svc.start(question_id='test_q1')
        self.assertIsNotNone(artifact)
        self.assertIsNotNone(artifact.started_at)

        stopped = svc.stop()
        self.assertIsNotNone(stopped)
        self.assertIsNotNone(stopped.stopped_at)

    def test_save_audio(self):
        svc = RecordingService()
        svc.start(question_id='test_audio')
        path = svc.save_audio(b'fake audio data', question_id='test_audio')
        self.assertTrue(os.path.exists(path))
        os.unlink(path)

    def test_transcribe_without_provider(self):
        svc = RecordingService(transcription_provider=None)
        result = svc.transcribe(b'audio data')
        self.assertEqual(result, '')

    def test_transcribe_with_mock_provider(self):
        mock_transcription = MagicMock()
        mock_transcription.transcribe_audio.return_value = 'Hello world'
        svc = RecordingService(transcription_provider=mock_transcription)
        result = svc.transcribe(b'audio data')
        self.assertEqual(result, 'Hello world')

    def test_synthesize_without_provider(self):
        svc = RecordingService(tts_provider=None)
        result = svc.synthesize_speech('Hello')
        self.assertEqual(result, b'')

    def test_analyze_video_without_provider(self):
        svc = RecordingService(multimodal_provider=None)
        result = svc.analyze_video('/tmp/test.webm')
        self.assertIn('error', result)


class LLMEvaluationTests(unittest.TestCase):
    """Suggestion 5: LLM-enhanced evaluation with fallback."""

    def test_heuristic_fallback_when_no_provider(self):
        pipeline = EvaluationPipeline(text_provider=None)
        result = pipeline.evaluate_answer('q1', 'I led a team to build a new API system.', InterviewType.BEHAVIOURAL)
        self.assertIsNotNone(result)
        self.assertGreater(result.rubric_score.weighted_total, 0)

    def test_llm_enhanced_with_mock_provider(self):
        mock_provider = MagicMock()
        # Return valid JSON for decomposition
        mock_provider.generate_text.return_value = json.dumps({
            'question_id': 'q1',
            'claimed_context': 'Led team at startup',
            'goal_or_task': 'Build new API',
            'actions_taken': 'Designed architecture, implemented caching',
            'technical_details': 'Used Redis for caching, PostgreSQL',
            'result_outcome': 'Reduced latency by 50%',
            'learning_reflection': 'Learned about trade-offs',
            'emotional_interpersonal_signals': 'Collaborated with team',
            'missing_evidence': [],
            'transcript_evidence': ['Led team at startup', 'Reduced latency by 50%'],
        })

        pipeline = EvaluationPipeline(text_provider=mock_provider)
        analysis = pipeline.decompose_answer('q1', 'I led a team to build a new API system.')
        self.assertEqual(analysis.claimed_context, 'Led team at startup')

    def test_llm_fallback_on_bad_json(self):
        mock_provider = MagicMock()
        mock_provider.generate_text.return_value = 'This is not valid JSON at all'

        pipeline = EvaluationPipeline(text_provider=mock_provider)
        analysis = pipeline.decompose_answer('q1', 'I led a team to build a new API system.')
        # Should fall back to heuristic
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.question_id, 'q1')


class SessionStoreTests(unittest.TestCase):
    """Suggestion 6: Session persistence."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.sqlite3')
        self.store = SessionStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_save_and_list_sessions(self):
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        self.store.save_session('test-001', state, [], [])
        sessions = self.store.list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['id'], 'test-001')

    def test_load_session_state(self):
        state = SessionState(
            mode=InterviewMode.FULL_MOCK,
            interview_type=InterviewType.TECHNICAL,
            time_budget_minutes=30,
        )
        self.store.save_session('test-002', state, [], [])
        loaded = self.store.load_session_state('test-002')
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.interview_type, InterviewType.TECHNICAL)
        self.assertEqual(loaded.time_budget_minutes, 30)

    def test_save_competency_scores_and_get_weak(self):
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        self.store.save_session('test-003', state, [], [])
        self.store.save_competency_scores('test-003', {
            'leadership': 3.0,
            'technical_depth': 8.0,
            'communication_clarity': 4.0,
        })
        weak = self.store.get_weak_competencies(threshold=6.0)
        self.assertIn('leadership', weak)
        self.assertIn('communication_clarity', weak)
        self.assertNotIn('technical_depth', weak)

    def test_competency_trend(self):
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        self.store.save_session('test-004', state, [], [])
        self.store.save_competency_scores('test-004', {'leadership': 5.0})
        trend = self.store.get_competency_trend('leadership')
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0]['score'], 5.0)

    def test_nonexistent_session(self):
        loaded = self.store.load_session_state('nonexistent')
        self.assertIsNone(loaded)


class DiffHighlightingTests(unittest.TestCase):
    """Suggestion 13: Answer retry with diff highlighting."""

    def test_inline_diff_shows_changes(self):
        original = 'I led a team project at my company'
        retry = 'I led a cross-functional team of 8 engineers at my company to redesign the API'

        sm = difflib.SequenceMatcher(None, original.split(), retry.split())
        parts = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                parts.append(' '.join(original.split()[i1:i2]))
            elif tag == 'replace':
                parts.append(f'~~{" ".join(original.split()[i1:i2])}~~')
                parts.append(f'**{" ".join(retry.split()[j1:j2])}**')
            elif tag == 'delete':
                parts.append(f'~~{" ".join(original.split()[i1:i2])}~~')
            elif tag == 'insert':
                parts.append(f'**{" ".join(retry.split()[j1:j2])}**')
        diff_text = ' '.join(parts)

        # Should contain both strikethrough (deletions) and bold (additions)
        self.assertIn('**', diff_text)
        self.assertIn('~~', diff_text)

    def test_identical_text_produces_no_diff(self):
        text = 'I led a team project'
        sm = difflib.SequenceMatcher(None, text.split(), text.split())
        opcodes = sm.get_opcodes()
        # All opcodes should be 'equal'
        for tag, _, _, _, _ in opcodes:
            self.assertEqual(tag, 'equal')


class DefaultSingaporeTests(unittest.TestCase):
    """Default location should be Singapore."""

    def test_interview_settings_default_sg(self):
        settings = InterviewSettings()
        self.assertEqual(settings.country_preset, CountryPreset.SINGAPORE)

    def test_session_state_default_sg(self):
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        self.assertEqual(state.country_preset, CountryPreset.SINGAPORE)


class EngineWithProvidersTests(unittest.TestCase):
    """Test engine initialization with providers (suggestions 1, 5)."""

    def test_engine_accepts_text_provider(self):
        mock_provider = MagicMock()
        bank = QuestionBank()
        planner = InterviewPlanner(bank)
        evaluator = EvaluationPipeline(text_provider=mock_provider)
        engine = InterviewSessionEngine(planner, evaluator, text_provider=mock_provider)
        self.assertIsNotNone(engine.text_provider)

    def test_engine_works_without_providers(self):
        bank = QuestionBank()
        planner = InterviewPlanner(bank)
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator)
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)
        opening = engine.get_opening(state)
        self.assertIsNotNone(opening)
        self.assertEqual(state.phase, InterviewPhase.WARMUP)


if __name__ == '__main__':
    unittest.main()
