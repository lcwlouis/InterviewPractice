"""Tests for schemas — model instantiation and validation."""

import unittest

from models.schemas import (
    AnswerStyle,
    CandidateProfile,
    CompetencyTag,
    CountryPreset,
    InterviewerTone,
    InterviewPhase,
    InterviewSettings,
    SessionState,
    InterviewMode,
    InterviewType,
)


class SchemaTests(unittest.TestCase):
    def test_interview_settings_defaults(self):
        settings = InterviewSettings()
        self.assertEqual(settings.interview_type, InterviewType.BEHAVIOURAL)
        self.assertEqual(settings.mode, InterviewMode.FULL_MOCK)
        self.assertEqual(settings.answer_style, AnswerStyle.STAR)
        self.assertEqual(settings.interviewer_tone, InterviewerTone.NEUTRAL)
        self.assertEqual(settings.country_preset, CountryPreset.US)
        self.assertFalse(settings.panel_mode)

    def test_session_state_has_phase(self):
        state = SessionState(mode=InterviewMode.FULL_MOCK, interview_type=InterviewType.TECHNICAL)
        self.assertEqual(state.phase, InterviewPhase.OPENING)
        self.assertEqual(state.elapsed_seconds, 0.0)

    def test_candidate_profile_has_target_company(self):
        profile = CandidateProfile(name='Test', target_company='Acme Corp')
        self.assertEqual(profile.target_company, 'Acme Corp')

    def test_competency_tags_count(self):
        self.assertEqual(len(CompetencyTag), 12)

    def test_interview_phase_values(self):
        phases = [p.value for p in InterviewPhase]
        self.assertIn('opening', phases)
        self.assertIn('warmup', phases)
        self.assertIn('main', phases)
        self.assertIn('wrap_up', phases)


if __name__ == '__main__':
    unittest.main()
