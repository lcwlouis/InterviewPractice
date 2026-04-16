"""Core Pydantic schemas for InterviewPractice.

All typed intermediate evaluation artifacts live here so the critique
pipeline is explicit and traceable — not a single monolithic LLM call.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# Enums are defined in models.enums; re-exported here for convenience.
from models.enums import (  # noqa: F401
    AnswerStyle,
    CompetencyTag,
    CountryPreset,
    InterviewerRole,
    InterviewerTone,
    InterviewMode,
    InterviewPhase,
    InterviewType,
)


# ---------------------------------------------------------------------------
# Candidate / Company
# ---------------------------------------------------------------------------

class CandidateProfile(BaseModel):
    name: str = ''
    summary: str = ''
    education: List[str] = Field(default_factory=list)
    work_experience: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    leadership: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    additional_background: str = ''
    target_role: str = ''
    target_company: str = ''


class CompanyContext(BaseModel):
    company_information: str = ''
    job_description: str = ''
    company_values: str = ''


# ---------------------------------------------------------------------------
# Panel / Interviewer configuration
# ---------------------------------------------------------------------------

class PanelMember(BaseModel):
    name: str
    role_type: InterviewerRole
    title: str = ''
    notes: str = ''


class InterviewSettings(BaseModel):
    """Per-session interview customisation options from the original design."""
    interview_type: InterviewType = InterviewType.BEHAVIOURAL
    mode: InterviewMode = InterviewMode.FULL_MOCK
    answer_style: AnswerStyle = AnswerStyle.STAR
    interviewer_tone: InterviewerTone = InterviewerTone.NEUTRAL
    country_preset: CountryPreset = CountryPreset.SINGAPORE
    time_budget_minutes: int = 20
    panel_mode: bool = False


# ---------------------------------------------------------------------------
# Question bank & planning
# ---------------------------------------------------------------------------

class Question(BaseModel):
    id: str
    text: str
    interview_type: InterviewType
    seniority: str
    role_family: str
    competencies: List[CompetencyTag]
    difficulty: int = Field(default=2, ge=1, le=5)
    interviewer_type: InterviewerRole
    phase: InterviewPhase = InterviewPhase.MAIN


class QuestionPlan(BaseModel):
    question: Question
    rationale: str
    target_competencies: List[CompetencyTag]
    follow_up_of_question_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Evaluation artifacts (structured pipeline)
# ---------------------------------------------------------------------------

class AnswerAnalysis(BaseModel):
    """Step 1 — Decompose candidate answer into evidence components."""
    question_id: str
    claimed_context: str
    goal_or_task: str
    actions_taken: str
    technical_details: str
    result_outcome: str
    learning_reflection: str
    emotional_interpersonal_signals: str
    missing_evidence: List[str] = Field(default_factory=list)
    transcript_evidence: List[str] = Field(default_factory=list)


class RubricScore(BaseModel):
    """Step 2 — Weighted rubric scores per category."""
    category_scores: Dict[str, float]
    weighted_total: float
    reasoning: Dict[str, str]


class GapAnalysis(BaseModel):
    """Step 3 — Identify what is missing from the answer."""
    weak_ownership: bool = False
    vague_results: bool = False
    no_metrics: bool = False
    insufficient_technical_depth: bool = False
    poor_structure: bool = False
    weak_reflection: bool = False
    ignored_business_impact: bool = False
    did_not_answer_question: bool = False
    notes: List[str] = Field(default_factory=list)


class CoachingFeedback(BaseModel):
    """Steps 4–6 — Evidence-grounded feedback + rewrite + coaching."""
    what_worked: List[str]
    what_was_weak: List[str]
    what_was_missing: List[str]
    likely_interviewer_inference: List[str]
    immediate_improvements: List[str]
    stronger_answer_outline: Optional[str] = None
    retry_prompt: Optional[str] = None


class QuestionEvaluation(BaseModel):
    """Complete per-question evaluation bundle."""
    question_id: str
    answer_analysis: AnswerAnalysis
    rubric_score: RubricScore
    gap_analysis: GapAnalysis
    coaching_feedback: CoachingFeedback


# ---------------------------------------------------------------------------
# Transcript & session state
# ---------------------------------------------------------------------------

class TranscriptTurn(BaseModel):
    speaker: str
    role: str
    text: str
    timestamp: datetime
    question_id: Optional[str] = None
    phase: InterviewPhase = InterviewPhase.MAIN


class SessionState(BaseModel):
    mode: InterviewMode
    interview_type: InterviewType
    phase: InterviewPhase = InterviewPhase.OPENING
    asked_question_ids: List[str] = Field(default_factory=list)
    competency_coverage: Dict[CompetencyTag, int] = Field(default_factory=dict)
    resume_areas_covered: List[str] = Field(default_factory=list)
    gaps_not_yet_tested: List[CompetencyTag] = Field(default_factory=list)
    time_budget_minutes: int = 20
    elapsed_seconds: float = 0.0
    answer_style: AnswerStyle = AnswerStyle.STAR
    interviewer_tone: InterviewerTone = InterviewerTone.NEUTRAL
    country_preset: CountryPreset = CountryPreset.SINGAPORE


# ---------------------------------------------------------------------------
# Session report (final output)
# ---------------------------------------------------------------------------

class SessionReport(BaseModel):
    overall_summary: str
    interview_score_by_category: Dict[str, float]
    interviewer_feedback: Dict[str, str]
    question_breakdown: Dict[str, QuestionEvaluation]
    competency_coverage_map: Dict[CompetencyTag, int]
    best_answer_question_id: Optional[str] = None
    weakest_answer_question_id: Optional[str] = None
    missed_opportunities: List[str] = Field(default_factory=list)
    stronger_rewrites: Dict[str, str] = Field(default_factory=dict)
    communication_observations: List[str] = Field(default_factory=list)
    body_language_observations: List[str] = Field(default_factory=list)
    confidence_presence_observations: List[str] = Field(default_factory=list)
    suggested_drills: List[str] = Field(default_factory=list)
    top_3_actions: List[str] = Field(default_factory=list)
