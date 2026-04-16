"""Interview planner — deliberate question selection with competency coverage,
difficulty adaptation, phase awareness, and panel turn-taking logic.
"""

from __future__ import annotations

from collections import Counter

from interview_engine.question_bank import QuestionBank
from models.schemas import (
    CompetencyTag,
    InterviewerRole,
    InterviewPhase,
    Question,
    QuestionPlan,
    SessionState,
)


# Which competency areas each interviewer role should focus on.
ROLE_COMPETENCY_FOCUS: dict[InterviewerRole, set[CompetencyTag]] = {
    InterviewerRole.HR: {
        CompetencyTag.MOTIVATION, CompetencyTag.COLLABORATION,
        CompetencyTag.CONFLICT_RESOLUTION, CompetencyTag.ADAPTABILITY,
        CompetencyTag.COMMUNICATION_CLARITY,
    },
    InterviewerRole.TECHNICAL: {
        CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING,
        CompetencyTag.LEARNING_MINDSET,
    },
    InterviewerRole.SENIOR_LEADERSHIP: {
        CompetencyTag.OWNERSHIP, CompetencyTag.STAKEHOLDER_MANAGEMENT,
        CompetencyTag.BUSINESS_AWARENESS, CompetencyTag.LEADERSHIP,
    },
}


class InterviewPlanner:
    def __init__(self, question_bank: QuestionBank) -> None:
        self.question_bank = question_bank

    # ── internal helpers ──────────────────────────────────────────────

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

    # ── public API ────────────────────────────────────────────────────

    def select_next_question(
        self,
        state: SessionState,
        recent_score: float | None = None,
    ) -> QuestionPlan | None:
        """Pick the next question based on phase, competency gaps and difficulty."""
        phase = state.phase

        # Warm-up: return first unused warm-up question
        if phase == InterviewPhase.WARMUP:
            warmups = self.question_bank.get_warmup_questions()
            for q in warmups:
                if q.id not in state.asked_question_ids:
                    return QuestionPlan(
                        question=q,
                        rationale='Warm-up question to ease into the interview.',
                        target_competencies=q.competencies,
                    )
            # Fall through to main if no warm-ups left
            state.phase = InterviewPhase.MAIN

        # Candidate-questions phase: return closing question
        if phase == InterviewPhase.CANDIDATE_QUESTIONS:
            closing = self.question_bank.get_closing_question()
            if closing and closing.id not in state.asked_question_ids:
                return QuestionPlan(
                    question=closing,
                    rationale='Closing: candidate asks questions.',
                    target_competencies=closing.competencies,
                )
            return None

        # Main / follow-up phase
        preferred = self._least_covered(state)
        difficulty_target = self._difficulty_target(recent_score)
        candidates = [
            q for q in self.question_bank.filter_questions(
                state.interview_type, difficulty_target, phase=InterviewPhase.MAIN,
            )
            if q.id not in state.asked_question_ids
        ]

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

    def advance_phase(self, state: SessionState) -> InterviewPhase:
        """Advance to the next interview phase (Full Mock flow)."""
        order = [
            InterviewPhase.OPENING,
            InterviewPhase.WARMUP,
            InterviewPhase.MAIN,
            InterviewPhase.FOLLOW_UP,
            InterviewPhase.CANDIDATE_QUESTIONS,
            InterviewPhase.WRAP_UP,
        ]
        try:
            idx = order.index(state.phase)
        except ValueError:
            idx = len(order) - 1
        next_idx = min(idx + 1, len(order) - 1)
        state.phase = order[next_idx]
        return state.phase
