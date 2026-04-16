"""Interview session engine — orchestrates phases, transcript, evaluation,
and LLM-powered follow-up generation.

Implements Suggestion 1 (LLM follow-ups) and integrates with the
text generation provider for dynamic question generation.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from models.schemas import (
    InterviewPhase,
    QuestionEvaluation,
    SessionState,
    TranscriptTurn,
)
from prompts.templates import FOLLOW_UP_PROMPT, SYSTEM_INTERVIEWER_PROMPT
from providers.base import TextGenerationProvider

logger = logging.getLogger(__name__)


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
    def __init__(
        self,
        planner: InterviewPlanner,
        evaluator: EvaluationPipeline,
        text_provider: Optional[TextGenerationProvider] = None,
        max_follow_ups: int = 2,
    ) -> None:
        self.planner = planner
        self.evaluator = evaluator
        self.text_provider = text_provider
        self.max_follow_ups = max_follow_ups
        self.transcript: list[TranscriptTurn] = []
        self._follow_up_count: int = 0

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

    def _build_system_prompt(self, state: SessionState) -> str:
        """Build the interviewer system prompt from session settings."""
        return SYSTEM_INTERVIEWER_PROMPT.format(
            interview_type=state.interview_type.value,
            interviewer_tone=state.interviewer_tone.value,
            country_preset=state.country_preset.value,
        )

    # ── LLM follow-up generation (Suggestion 1) ─────────────────────

    def _generate_follow_up(self, candidate_answer: str, state: SessionState) -> str | None:
        """Use the LLM to generate a contextual follow-up question."""
        if self.text_provider is None:
            return None
        if self._follow_up_count >= self.max_follow_ups:
            return None

        # Determine interviewer role from context
        interviewer_role = 'HR'
        if state.interview_type.value == 'technical':
            interviewer_role = 'Technical'
        elif state.phase == InterviewPhase.MAIN:
            interviewer_role = 'Senior Leadership'

        prompt = FOLLOW_UP_PROMPT.format(
            candidate_answer=candidate_answer[:2000],
            interviewer_role=interviewer_role,
        )
        system_prompt = self._build_system_prompt(state)

        try:
            follow_up = self.text_provider.generate_text(prompt, system_prompt=system_prompt)
            if follow_up and not follow_up.startswith('[') and len(follow_up.strip()) > 10:
                self._follow_up_count += 1
                return follow_up.strip()
        except Exception:
            logger.exception('Failed to generate LLM follow-up')
        return None

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

    def generate_follow_up_prompt(self, candidate_answer: str, state: SessionState) -> str | None:
        """Generate an LLM follow-up question and add to transcript."""
        follow_up = self._generate_follow_up(candidate_answer, state)
        if follow_up:
            speaker = 'Interviewer (Follow-up)'
            self._append_turn(
                speaker=speaker,
                role='follow_up',
                text=follow_up,
                phase=state.phase,
            )
            state.phase = InterviewPhase.FOLLOW_UP
            return f'[{speaker}]: {follow_up}'
        return None

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
