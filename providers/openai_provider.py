"""OpenAI provider — real API integration with graceful fallback."""

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


def _get_openai():  # noqa: ANN202
    """Lazy-import openai so the app works even if the package is missing."""
    try:
        import openai
        return openai
    except ImportError:
        return None


class OpenAIProvider(TextGenerationProvider, LiveAudioProvider, TranscriptionProvider, MultimodalEvaluationProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def _client(self):  # noqa: ANN202
        openai = _get_openai()
        if openai is None or not self.api_key:
            return None
        return openai.OpenAI(api_key=self.api_key)

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = self._client()
        if client is None:
            return '[OpenAI fallback] API key or openai package not available.'

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})

        def _call() -> str:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content or ''

        try:
            return call_with_retry(_call, retries=2, delay_seconds=1.0)
        except Exception:
            logger.exception('OpenAI generate_text failed')
            return '[OpenAI fallback] API call failed — check logs for details.'

    def supports_live_audio(self) -> bool:
        # OpenAI does not support bidirectional live audio in this integration
        return False

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        client = self._client()
        if client is None or not audio_bytes:
            return ''

        import os
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
        try:
            tmp.write(audio_bytes)
            tmp.flush()
            tmp.close()
            with open(tmp.name, 'rb') as f:
                transcript = client.audio.transcriptions.create(
                    model='whisper-1', file=f,
                )
            return transcript.text
        except Exception:
            logger.exception('OpenAI transcribe_audio failed')
            return ''
        finally:
            os.unlink(tmp.name)

    def evaluate_recording(self, transcript: str, video_path: Optional[str] = None) -> dict:
        client = self._client()
        if client is None:
            return {'provider': 'openai', 'error': 'API not available'}

        prompt = (
            'You are an expert interview coach. Analyze this interview transcript '
            'and provide structured JSON feedback with keys: overall_impression, '
            'communication_score (1-10), confidence_score (1-10), '
            'pacing_observations, filler_word_count_estimate, key_strengths, '
            'areas_for_improvement.\n\nTranscript:\n' + transcript[:8000]
        )
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content or '{}'
            return json.loads(content)
        except Exception:
            logger.exception('OpenAI evaluate_recording failed')
            return {'provider': 'openai', 'error': 'Evaluation call failed'}
