"""Enums for interview configuration options specified in the original design."""

from __future__ import annotations

from enum import Enum


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


class AnswerStyle(str, Enum):
    """Answer style expectations the candidate should target."""
    CONCISE_EXECUTIVE = 'concise_executive'
    STAR = 'star'
    STAR_PLUS = 'star_plus'
    TECHNICAL_DEEP_DIVE = 'technical_deep_dive'
    CPARL = 'context_problem_actions_result_learning'
    LEADERSHIP_ORIENTED = 'leadership_oriented'


class InterviewerTone(str, Enum):
    """Tone / style the interviewer should adopt."""
    FRIENDLY = 'friendly'
    NEUTRAL = 'neutral'
    SHARP = 'sharp'
    HIGH_PRESSURE = 'high_pressure'
    ENCOURAGING = 'encouraging'


class CountryPreset(str, Enum):
    """Regional culture presets that influence interviewer behaviour."""
    US = 'US'
    UK = 'UK'
    CANADA = 'CA'
    AUSTRALIA = 'AU'
    GERMANY = 'DE'
    JAPAN = 'JP'
    INDIA = 'IN'
    SINGAPORE = 'SG'


class InterviewPhase(str, Enum):
    """Phases within a full mock interview flow."""
    OPENING = 'opening'
    WARMUP = 'warmup'
    MAIN = 'main'
    FOLLOW_UP = 'follow_up'
    CANDIDATE_QUESTIONS = 'candidate_questions'
    WRAP_UP = 'wrap_up'
