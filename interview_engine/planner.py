from collections import Counter

from interview_engine.question_bank import QuestionBank
from models.schemas import CompetencyTag, Question, QuestionPlan, SessionState


class InterviewPlanner:
    def __init__(self, question_bank: QuestionBank) -> None:
        self.question_bank = question_bank

    def _least_covered(self, state: SessionState) -> CompetencyTag | None:
        counter = Counter(state.competency_coverage)
        for competency in CompetencyTag:
            counter.setdefault(competency, 0)
        if not counter:
            return None
        return min(counter, key=counter.get)

    def _difficulty_target(self, recent_score: float | None) -> int:
        if recent_score is None:
            return 3
        if recent_score >= 8:
            return 5
        if recent_score <= 4:
            return 2
        return 3

    def select_next_question(self, state: SessionState, recent_score: float | None = None) -> QuestionPlan | None:
        preferred = self._least_covered(state)
        difficulty_target = self._difficulty_target(recent_score)
        candidates = [q for q in self.question_bank.filter_questions(state.interview_type, difficulty_target) if q.id not in state.asked_question_ids]

        if preferred:
            prioritized = [q for q in candidates if preferred in q.competencies]
            if prioritized:
                candidates = prioritized

        if not candidates:
            return None

        question = candidates[0]
        return QuestionPlan(
            question=question,
            rationale=f'Target competency coverage: {", ".join(c.value for c in question.competencies)}',
            target_competencies=question.competencies,
        )

    def register_question(self, state: SessionState, question: Question) -> None:
        state.asked_question_ids.append(question.id)
        for competency in question.competencies:
            state.competency_coverage[competency] = state.competency_coverage.get(competency, 0) + 1
