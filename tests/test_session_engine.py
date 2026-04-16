"""Tests for the interview session engine — phases, opening, wrapup."""

import unittest

from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from interview_engine.question_bank import QuestionBank
from interview_engine.session import InterviewSessionEngine
from models.schemas import InterviewMode, InterviewPhase, InterviewType, SessionState


class SessionEngineTests(unittest.TestCase):
    def _make_engine(self) -> tuple[InterviewSessionEngine, SessionState]:
        planner = InterviewPlanner(QuestionBank())
        evaluator = EvaluationPipeline()
        engine = InterviewSessionEngine(planner, evaluator)
        state = SessionState(
            mode=InterviewMode.FULL_MOCK,
            interview_type=InterviewType.BEHAVIOURAL,
        )
        return engine, state

    def test_opening_advances_to_warmup(self):
        engine, state = self._make_engine()
        msg = engine.get_opening(state)
        self.assertIn('Thank you', msg)
        self.assertEqual(state.phase, InterviewPhase.WARMUP)

    def test_warmup_question_returned(self):
        engine, state = self._make_engine()
        engine.get_opening(state)
        prompt = engine.next_prompt(state)
        self.assertIsNotNone(prompt)
        self.assertIn('Interviewer', prompt)

    def test_wrapup_message(self):
        engine, state = self._make_engine()
        msg = engine.get_wrapup(state)
        self.assertIn('concludes', msg)
        self.assertEqual(state.phase, InterviewPhase.WRAP_UP)

    def test_transcript_records_opening(self):
        engine, state = self._make_engine()
        engine.get_opening(state)
        self.assertEqual(len(engine.transcript), 1)
        self.assertEqual(engine.transcript[0].phase, InterviewPhase.OPENING)

    def test_submit_answer_adds_to_transcript(self):
        engine, state = self._make_engine()
        engine.get_opening(state)
        engine.next_prompt(state)
        qid = state.asked_question_ids[-1]
        engine.submit_answer(qid, 'My answer here.', state)
        candidate_turns = [t for t in engine.transcript if t.role == 'candidate']
        self.assertEqual(len(candidate_turns), 1)


class PlannerPhaseTests(unittest.TestCase):
    def test_advance_phase_order(self):
        planner = InterviewPlanner(QuestionBank())
        state = SessionState(
            mode=InterviewMode.FULL_MOCK,
            interview_type=InterviewType.BEHAVIOURAL,
        )
        self.assertEqual(state.phase, InterviewPhase.OPENING)
        planner.advance_phase(state)
        self.assertEqual(state.phase, InterviewPhase.WARMUP)
        planner.advance_phase(state)
        self.assertEqual(state.phase, InterviewPhase.MAIN)

    def test_difficulty_increases_on_high_score(self):
        planner = InterviewPlanner(QuestionBank())
        self.assertEqual(planner._difficulty_target(9.0), 5)
        self.assertEqual(planner._difficulty_target(3.0), 2)
        self.assertEqual(planner._difficulty_target(None), 3)


if __name__ == '__main__':
    unittest.main()
