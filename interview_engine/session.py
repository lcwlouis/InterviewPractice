from datetime import datetime

from evaluation.pipeline import EvaluationPipeline
from interview_engine.planner import InterviewPlanner
from models.schemas import QuestionEvaluation, SessionState, TranscriptTurn


class InterviewSessionEngine:
    def __init__(self, planner: InterviewPlanner, evaluator: EvaluationPipeline) -> None:
        self.planner = planner
        self.evaluator = evaluator
        self.transcript: list[TranscriptTurn] = []

    def next_prompt(self, state: SessionState, recent_score: float | None = None) -> str | None:
        plan = self.planner.select_next_question(state, recent_score=recent_score)
        if not plan:
            return None

        self.planner.register_question(state, plan.question)
        self.transcript.append(
            TranscriptTurn(
                speaker=f'{plan.question.interviewer_type.value.upper()} Interviewer',
                role=plan.question.interviewer_type.value,
                text=plan.question.text,
                timestamp=datetime.utcnow(),
                question_id=plan.question.id,
            )
        )
        return f'[{plan.question.interviewer_type.value.upper()} Interviewer]: {plan.question.text}'

    def submit_answer(self, question_id: str, candidate_answer: str, state: SessionState) -> QuestionEvaluation:
        self.transcript.append(
            TranscriptTurn(
                speaker='Candidate',
                role='candidate',
                text=candidate_answer,
                timestamp=datetime.utcnow(),
                question_id=question_id,
            )
        )
        return self.evaluator.evaluate_answer(question_id, candidate_answer, state.interview_type)
