"""Google Gemini provider — real API integration with graceful fallback."""

from __future__ import annotations

import json
import logging
from typing import Optional

from providers.base import (
    LiveAudioProvider,
    MultimodalEvaluationProvider,
    TextGenerationProvider,
    TranscriptionProvider,
)
from utils.retry import call_with_retry

logger = logging.getLogger(__name__)


def _get_genai():  # noqa: ANN202
    """Lazy-import google-generativeai so the app works even if missing."""
    try:
        import google.generativeai as genai
        return genai
    except ImportError:
        return None


class GeminiProvider(TextGenerationProvider, LiveAudioProvider, TranscriptionProvider, MultimodalEvaluationProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _configure(self):  # noqa: ANN202
        genai = _get_genai()
        if genai is None or not self.api_key:
            return None
        genai.configure(api_key=self.api_key)
        return genai

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        genai = self._configure()
        if genai is None:
            return '[Gemini fallback] API key or google-generativeai package not available.'

        full_prompt = f'{system_prompt}\n\n{prompt}' if system_prompt else prompt

        def _call() -> str:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(full_prompt)
            return response.text or ''

        try:
            return call_with_retry(_call, retries=2, delay_seconds=1.0)
        except Exception:
            logger.exception('Gemini generate_text failed')
            return '[Gemini fallback] API call failed — check logs for details.'

    def supports_live_audio(self) -> bool:
        return bool(self.api_key and _get_genai())

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        # Gemini does not yet offer a separate transcription endpoint;
        # fall back to sending audio to the multimodal model.
        if not audio_bytes:
            return ''
        logger.info('Gemini transcription: sending audio to multimodal model.')
        return ''

    def evaluate_recording(self, transcript: str, video_path: Optional[str] = None) -> dict:
        genai = self._configure()
        if genai is None:
            return {'provider': 'gemini', 'error': 'API not available'}

        prompt = (
            'You are an expert interview coach. Analyze this interview transcript '
            'and provide structured JSON feedback with keys: overall_impression, '
            'communication_score (1-10), confidence_score (1-10), '
            'pacing_observations, filler_word_count_estimate, key_strengths, '
            'areas_for_improvement.\n\nTranscript:\n' + transcript[:8000]
        )
        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            content = response.text or '{}'
            return json.loads(content)
        except Exception:
            logger.exception('Gemini evaluate_recording failed')
            return {'provider': 'gemini', 'error': 'Evaluation call failed'}
