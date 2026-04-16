"""Interview session engine — orchestrates phases, transcript, and evaluation."""

from __future__ import annotations

from datetime import datetime, timezone

from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from models.schemas import (
    InterviewPhase,
    QuestionEvaluation,
    SessionState,
    TranscriptTurn,
)


# Pre-defined opening / closing messages per phase.
_PHASE_MESSAGES = {
    InterviewPhase.OPENING: (
        'Thank you for joining us today. We are looking forward to learning '
        'more about your experience. This session will include a few warm-up '
        'questions followed by the main interview. Ready?'
    ),
    InterviewPhase.WRAP_UP: (
        'That concludes our questions. Thank you for your time — we appreciate '
        'the thoughtful answers. We will be in touch soon.'
    ),
}


class InterviewSessionEngine:
    def __init__(self, planner: InterviewPlanner, evaluator: EvaluationPipeline) -> None:
        self.planner = planner
        self.evaluator = evaluator
        self.transcript: list[TranscriptTurn] = []

    # ── helpers ────────────────────────────────────────────────────────

    def _append_turn(
        self,
        speaker: str,
        role: str,
        text: str,
        question_id: str | None = None,
        phase: InterviewPhase = InterviewPhase.MAIN,
    ) -> None:
        self.transcript.append(
            TranscriptTurn(
                speaker=speaker,
                role=role,
                text=text,
                timestamp=datetime.now(timezone.utc),
                question_id=question_id,
                phase=phase,
            )
        )

    # ── public API ────────────────────────────────────────────────────

    def get_opening(self, state: SessionState) -> str:
        """Return opening remarks and advance phase to WARMUP."""
        msg = _PHASE_MESSAGES[InterviewPhase.OPENING]
        self._append_turn('Interviewer', 'system', msg, phase=InterviewPhase.OPENING)
        self.planner.advance_phase(state)  # OPENING -> WARMUP
        return msg

    def get_wrapup(self, state: SessionState) -> str:
        """Return wrap-up remarks."""
        msg = _PHASE_MESSAGES[InterviewPhase.WRAP_UP]
        self._append_turn('Interviewer', 'system', msg, phase=InterviewPhase.WRAP_UP)
        state.phase = InterviewPhase.WRAP_UP
        return msg

    def next_prompt(self, state: SessionState, recent_score: float | None = None) -> str | None:
        """Select next question, add to transcript, return formatted prompt."""
        plan = self.planner.select_next_question(state, recent_score=recent_score)
        if not plan:
            return None

        self.planner.register_question(state, plan.question)
        speaker = f'{plan.question.interviewer_type.value.upper()} Interviewer'
        self._append_turn(
            speaker=speaker,
            role=plan.question.interviewer_type.value,
            text=plan.question.text,
            question_id=plan.question.id,
            phase=state.phase,
        )
        return f'[{speaker}]: {plan.question.text}'

    def submit_answer(self, question_id: str, candidate_answer: str, state: SessionState) -> QuestionEvaluation:
        """Record candidate answer and run evaluation pipeline."""
        self._append_turn(
            speaker='Candidate',
            role='candidate',
            text=candidate_answer,
            question_id=question_id,
            phase=state.phase,
        )
        return self.evaluator.evaluate_answer(question_id, candidate_answer, state.interview_type)
