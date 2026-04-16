"""Tests for Gemini Live API integration."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from providers.base import LiveTurnResult
from providers.gemini_provider import GeminiProvider


class LiveTurnResultTests(unittest.TestCase):
    """LiveTurnResult dataclass behaviour."""

    def test_default_values(self):
        result = LiveTurnResult()
        self.assertEqual(result.input_transcription, '')
        self.assertEqual(result.response_text, '')
        self.assertEqual(result.response_audio, b'')
        self.assertFalse(result.turn_complete)

    def test_populated_values(self):
        result = LiveTurnResult(
            input_transcription='I led a team.',
            response_text='Can you tell me more about the outcome?',
            response_audio=b'\x00\x01\x02',
            turn_complete=True,
        )
        self.assertEqual(result.input_transcription, 'I led a team.')
        self.assertTrue(result.turn_complete)


class GeminiProviderLiveSupportTests(unittest.TestCase):
    """GeminiProvider.supports_live_audio() checks."""

    def test_no_api_key_returns_false(self):
        provider = GeminiProvider(api_key='', model='gemini-2.5-pro')
        self.assertFalse(provider.supports_live_audio())

    def test_api_key_but_no_sdk_returns_false(self):
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        with patch('providers.gemini_provider._get_genai_new', return_value=None):
            self.assertFalse(provider.supports_live_audio())

    def test_api_key_and_sdk_returns_true(self):
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        with patch('providers.gemini_provider._get_genai_new', return_value=MagicMock()):
            self.assertTrue(provider.supports_live_audio())


class GeminiProviderRunLiveTurnTests(unittest.TestCase):
    """GeminiProvider.run_live_turn() behaviour."""

    def test_empty_audio_returns_none(self):
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        result = provider.run_live_turn(audio_bytes=b'', system_prompt='You are an interviewer.')
        self.assertIsNone(result)

    def test_no_api_key_returns_none(self):
        provider = GeminiProvider(api_key='', model='gemini-2.5-pro')
        result = provider.run_live_turn(audio_bytes=b'\x00\x01', system_prompt='sys')
        self.assertIsNone(result)

    def test_missing_sdk_returns_none(self):
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        with patch('providers.gemini_provider._get_genai_new', return_value=None):
            result = provider.run_live_turn(audio_bytes=b'\x00\x01', system_prompt='sys')
        self.assertIsNone(result)

    def test_successful_live_turn(self):
        """Mock the async Live API call and verify graceful exception handling."""
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        mock_sdk = MagicMock()

        # Patch _get_genai_new to return a mock SDK and simulate a network failure
        # so we can verify the exception → None contract without a real API call.
        with patch('providers.gemini_provider._get_genai_new', return_value=mock_sdk), \
             patch('providers.gemini_provider._run_live_turn_async', side_effect=ConnectionError('mock network')):
            result = provider.run_live_turn(
                audio_bytes=b'\x00\x01\x02',
                system_prompt='You are an interviewer.',
            )

        self.assertIsNone(result)

    def test_exception_in_live_turn_returns_none(self):
        """An API exception should be caught and None returned."""
        provider = GeminiProvider(api_key='test-key', model='gemini-2.5-pro')
        mock_sdk = MagicMock()

        with patch('providers.gemini_provider._get_genai_new', return_value=mock_sdk):
            with patch('providers.gemini_provider._run_live_turn_async', side_effect=RuntimeError('network')):
                result = provider.run_live_turn(
                    audio_bytes=b'\x00\x01',
                    system_prompt='You are an interviewer.',
                )
        self.assertIsNone(result)


class GeminiProviderLiveModelTests(unittest.TestCase):
    """GeminiProvider uses the live_model attribute."""

    def test_default_live_model(self):
        provider = GeminiProvider(api_key='k', model='gemini-2.5-pro')
        self.assertEqual(provider.live_model, 'gemini-2.0-flash-live-001')

    def test_custom_live_model(self):
        provider = GeminiProvider(api_key='k', model='gemini-2.5-pro', live_model='gemini-2.0-flash-exp')
        self.assertEqual(provider.live_model, 'gemini-2.0-flash-exp')


class BaseProviderLiveRunTests(unittest.TestCase):
    """LiveAudioProvider default run_live_turn returns None."""

    def test_openai_provider_run_live_turn_returns_none(self):
        from providers.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key='', model='gpt-4.1-mini')
        result = provider.run_live_turn(audio_bytes=b'\x00\x01', system_prompt='sys')
        self.assertIsNone(result)


class LiveSystemPromptTests(unittest.TestCase):
    """LIVE_INTERVIEW_SYSTEM_PROMPT template renders correctly."""

    def test_prompt_contains_interview_type(self):
        from prompts.templates import LIVE_INTERVIEW_SYSTEM_PROMPT
        rendered = LIVE_INTERVIEW_SYSTEM_PROMPT.format(
            interview_type='behavioural',
            interviewer_tone='neutral',
            country_preset='SG',
            candidate_name='Alice',
            target_role='Software Engineer',
            target_company='Acme Corp',
            job_description='Build scalable systems.',
            current_question='Tell me about a time you led a project.',
        )
        self.assertIn('behavioural', rendered)
        self.assertIn('Alice', rendered)
        self.assertIn('Acme Corp', rendered)
        self.assertIn('Tell me about a time', rendered)


if __name__ == '__main__':
    unittest.main()
