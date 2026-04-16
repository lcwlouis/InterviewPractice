from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class InterviewType(str, Enum):
    BEHAVIOURAL = 'behavioural'
    TECHNICAL = 'technical'
    HYBRID = 'hybrid'


class InterviewMode(str, Enum):
    FULL_MOCK = 'full_mock'
    QUICK_FIRE = 'quick_fire'
    ONLY_FOLLOW_UPS = 'only_follow_ups'
    FINAL_ROUND_PANEL = 'final_round_panel'
    ANSWER_COACHING = 'answer_coaching'


class InterviewerRole(str, Enum):
    HR = 'hr'
    TECHNICAL = 'technical'
    SENIOR_LEADERSHIP = 'senior_leadership'


class CompetencyTag(str, Enum):
    LEADERSHIP = 'leadership'
    CONFLICT_RESOLUTION = 'conflict_resolution'
    OWNERSHIP = 'ownership'
    TECHNICAL_DEPTH = 'technical_depth'
    PROBLEM_SOLVING = 'problem_solving'
    COLLABORATION = 'collaboration'
    STAKEHOLDER_MANAGEMENT = 'stakeholder_management'
    MOTIVATION = 'motivation'
    ADAPTABILITY = 'adaptability'
    LEARNING_MINDSET = 'learning_mindset'
    COMMUNICATION_CLARITY = 'communication_clarity'
    BUSINESS_AWARENESS = 'business_awareness'


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


class CompanyContext(BaseModel):
    company_information: str = ''
    job_description: str = ''
    company_values: str = ''


class PanelMember(BaseModel):
    name: str
    role_type: InterviewerRole
    title: str = ''
    notes: str = ''


class Question(BaseModel):
    id: str
    text: str
    interview_type: InterviewType
    seniority: str
    role_family: str
    competencies: List[CompetencyTag]
    difficulty: int = Field(default=2, ge=1, le=5)
    interviewer_type: InterviewerRole


class QuestionPlan(BaseModel):
    question: Question
    rationale: str
    target_competencies: List[CompetencyTag]
    follow_up_of_question_id: Optional[str] = None


class AnswerAnalysis(BaseModel):
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
    category_scores: Dict[str, float]
    weighted_total: float
    reasoning: Dict[str, str]


class GapAnalysis(BaseModel):
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
    what_worked: List[str]
    what_was_weak: List[str]
    what_was_missing: List[str]
    likely_interviewer_inference: List[str]
    immediate_improvements: List[str]
    stronger_answer_outline: Optional[str] = None
    retry_prompt: Optional[str] = None


class QuestionEvaluation(BaseModel):
    question_id: str
    answer_analysis: AnswerAnalysis
    rubric_score: RubricScore
    gap_analysis: GapAnalysis
    coaching_feedback: CoachingFeedback


class TranscriptTurn(BaseModel):
    speaker: str
    role: str
    text: str
    timestamp: datetime
    question_id: Optional[str] = None


class SessionState(BaseModel):
    mode: InterviewMode
    interview_type: InterviewType
    asked_question_ids: List[str] = Field(default_factory=list)
    competency_coverage: Dict[CompetencyTag, int] = Field(default_factory=dict)
    resume_areas_covered: List[str] = Field(default_factory=list)
    gaps_not_yet_tested: List[CompetencyTag] = Field(default_factory=list)
    time_budget_minutes: int = 20


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
