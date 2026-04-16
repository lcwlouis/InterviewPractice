"""Tests for question bank — coverage, filtering, phases."""

import unittest

from interview_engine.question_bank import QuestionBank
from models.schemas import InterviewPhase, InterviewType


class QuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.bank = QuestionBank()

    def test_has_warmup_questions(self):
        warmups = self.bank.get_warmup_questions()
        self.assertGreaterEqual(len(warmups), 1)
        for q in warmups:
            self.assertEqual(q.phase, InterviewPhase.WARMUP)

    def test_has_closing_question(self):
        closing = self.bank.get_closing_question()
        self.assertIsNotNone(closing)
        self.assertEqual(closing.phase, InterviewPhase.CANDIDATE_QUESTIONS)

    def test_filter_by_type_and_phase(self):
        main_tech = self.bank.filter_questions(InterviewType.TECHNICAL, phase=InterviewPhase.MAIN)
        self.assertGreaterEqual(len(main_tech), 3)
        for q in main_tech:
            self.assertEqual(q.phase, InterviewPhase.MAIN)

    def test_filter_respects_max_difficulty(self):
        easy = self.bank.filter_questions(InterviewType.BEHAVIOURAL, max_difficulty=2)
        for q in easy:
            self.assertLessEqual(q.difficulty, 2)

    def test_all_questions_have_competencies(self):
        for q in self.bank.questions:
            self.assertGreaterEqual(len(q.competencies), 1,
                                    f'Question {q.id} has no competencies')

    def test_minimum_question_count(self):
        self.assertGreaterEqual(len(self.bank.questions), 20)


if __name__ == '__main__':
    unittest.main()
