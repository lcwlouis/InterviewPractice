"""Deliberate question bank organised by interview type, seniority,
role family, competency, difficulty, and interviewer type.

The original design requires intentional question selection, not random
generation.  Every question is tagged with the competencies it tests.

Loads questions from ``data/questions.yaml`` when the file is present,
falling back to a minimal built-in set so tests still work without YAML.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from models.schemas import (
    CompetencyTag,
    InterviewPhase,
    InterviewType,
    InterviewerRole,
    Question,
)

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
_QUESTIONS_YAML = _DATA_DIR / 'questions.yaml'


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML, returning empty dict on failure."""
    try:
        import yaml
    except ImportError:
        logger.warning('pyyaml not installed — using built-in fallback questions.')
        return {}
    if not path.exists():
        return {}
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _parse_question(raw: dict[str, Any]) -> Question:
    """Convert a raw YAML dict into a Question model instance."""
    competencies = [CompetencyTag(c) for c in raw.get('competencies', [])]
    phase_str = raw.get('phase', 'main')
    return Question(
        id=raw['id'],
        text=raw['text'],
        interview_type=InterviewType(raw['interview_type']),
        seniority=raw.get('seniority', 'any'),
        role_family=raw.get('role_family', 'general'),
        competencies=competencies,
        difficulty=raw.get('difficulty', 3),
        interviewer_type=InterviewerRole(raw['interviewer_type']),
        phase=InterviewPhase(phase_str),
    )


def _load_questions_from_yaml(path: Path = _QUESTIONS_YAML) -> list[Question]:
    """Load the full question bank from YAML."""
    data = _load_yaml(path)
    if not data:
        return []
    questions: list[Question] = []
    for _section, items in data.items():
        if isinstance(items, list):
            for raw in items:
                try:
                    questions.append(_parse_question(raw))
                except Exception:
                    logger.warning('Skipping malformed question: %s', raw.get('id', '?'))
    return questions


# Minimal built-in fallback so unit tests work without YAML
_BUILTIN_FALLBACK: list[Question] = [
    Question(
        id='w1',
        text='Walk me through your background and what brings you here today.',
        interview_type=InterviewType.BEHAVIOURAL, seniority='any', role_family='general',
        competencies=[CompetencyTag.COMMUNICATION_CLARITY, CompetencyTag.MOTIVATION],
        difficulty=1, interviewer_type=InterviewerRole.HR, phase=InterviewPhase.WARMUP,
    ),
    Question(
        id='w2',
        text='What about this role or company excites you the most?',
        interview_type=InterviewType.BEHAVIOURAL, seniority='any', role_family='general',
        competencies=[CompetencyTag.MOTIVATION, CompetencyTag.BUSINESS_AWARENESS],
        difficulty=1, interviewer_type=InterviewerRole.HR, phase=InterviewPhase.WARMUP,
    ),
    Question(
        id='b1',
        text='Tell me about a time you resolved a conflict on your team.',
        interview_type=InterviewType.BEHAVIOURAL, seniority='mid', role_family='general',
        competencies=[CompetencyTag.CONFLICT_RESOLUTION, CompetencyTag.COLLABORATION],
        difficulty=2, interviewer_type=InterviewerRole.HR,
    ),
    Question(
        id='t1',
        text='Walk me through a system you designed and key tradeoffs.',
        interview_type=InterviewType.TECHNICAL, seniority='senior', role_family='engineering',
        competencies=[CompetencyTag.TECHNICAL_DEPTH, CompetencyTag.PROBLEM_SOLVING],
        difficulty=4, interviewer_type=InterviewerRole.TECHNICAL,
    ),
    Question(
        id='h1',
        text='How do you balance speed versus reliability under stakeholder pressure?',
        interview_type=InterviewType.HYBRID, seniority='senior', role_family='engineering',
        competencies=[CompetencyTag.BUSINESS_AWARENESS, CompetencyTag.STAKEHOLDER_MANAGEMENT],
        difficulty=4, interviewer_type=InterviewerRole.SENIOR_LEADERSHIP,
    ),
    Question(
        id='cq1',
        text='Do you have any questions for us?',
        interview_type=InterviewType.BEHAVIOURAL, seniority='any', role_family='general',
        competencies=[CompetencyTag.BUSINESS_AWARENESS, CompetencyTag.MOTIVATION],
        difficulty=1, interviewer_type=InterviewerRole.HR,
        phase=InterviewPhase.CANDIDATE_QUESTIONS,
    ),
]


class QuestionBank:
    def __init__(self, yaml_path: Path | None = None) -> None:
        loaded = _load_questions_from_yaml(yaml_path or _QUESTIONS_YAML)
        self.questions: list[Question] = loaded if loaded else list(_BUILTIN_FALLBACK)
        logger.info('Question bank loaded: %d questions', len(self.questions))

    def filter_questions(
        self,
        interview_type: InterviewType,
        max_difficulty: int = 5,
        phase: InterviewPhase | None = None,
    ) -> list[Question]:
        results = []
        for q in self.questions:
            type_match = q.interview_type in {interview_type, InterviewType.HYBRID}
            diff_match = q.difficulty <= max_difficulty
            phase_match = phase is None or q.phase == phase
            if type_match and diff_match and phase_match:
                results.append(q)
        return results

    def get_warmup_questions(self) -> list[Question]:
        return [q for q in self.questions if q.phase == InterviewPhase.WARMUP]

    def get_closing_question(self) -> Question | None:
        for q in self.questions:
            if q.phase == InterviewPhase.CANDIDATE_QUESTIONS:
                return q
        return None
