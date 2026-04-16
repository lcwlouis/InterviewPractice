import unittest

from interview_engine.planner import InterviewPlanner
from interview_engine.question_bank import QuestionBank
from models.schemas import InterviewMode, InterviewType, SessionState


class PlannerTests(unittest.TestCase):
    def test_planner_avoids_duplicate_questions(self):
        planner = InterviewPlanner(QuestionBank())
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.TECHNICAL)

        first = planner.select_next_question(state)
        self.assertIsNotNone(first)
        planner.register_question(state, first.question)

        second = planner.select_next_question(state)
        if second:
            self.assertNotEqual(first.question.id, second.question.id)

    def test_register_updates_coverage(self):
        planner = InterviewPlanner(QuestionBank())
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.BEHAVIOURAL)

        plan = planner.select_next_question(state)
        self.assertIsNotNone(plan)
        planner.register_question(state, plan.question)

        self.assertGreaterEqual(len(state.competency_coverage), 1)


if __name__ == '__main__':
    unittest.main()
