"""Google Gemini provider — real API integration with graceful fallback.

Supports:
- Text generation via ``google-generativeai`` (legacy REST API)
- Live bidirectional audio via ``google-genai`` (Live API / WebSocket)
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from providers.base import (
    LiveAudioProvider,
    LiveTurnResult,
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


def _get_genai_new():  # noqa: ANN202
    """Lazy-import google-genai (new SDK with Live API) if available."""
    try:
        from google import genai  # type: ignore[import]
        return genai
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# Live API session helper
# ---------------------------------------------------------------------------

@dataclass
class _LiveResponse:
    """Accumulated result of receiving from one Live session turn."""
    input_transcription: str = ''
    response_text: str = ''
    response_audio: bytes = field(default_factory=bytes)
    turn_complete: bool = False


async def _run_live_turn_async(
    api_key: str,
    model: str,
    system_prompt: str,
    audio_bytes: bytes,
    audio_mime_type: str,
) -> _LiveResponse:
    """Open a Gemini Live session, send one audio turn, and return the result."""
    from google import genai  # type: ignore[import]
    from google.genai import types  # type: ignore[import]

    client = genai.Client(api_key=api_key)

    config = types.LiveConnectConfig(
        response_modalities=['AUDIO', 'TEXT'],
        system_instruction=system_prompt,
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )

    result = _LiveResponse()

    async with client.aio.live.connect(model=model, config=config) as session:
        # Send candidate audio as a single real-time media chunk.
        await session.send(
            input=types.LiveClientRealtimeInput(
                media_chunks=[types.Blob(data=audio_bytes, mime_type=audio_mime_type)],
            ),
        )
        # Signal end of user turn so the model knows to respond.
        await session.send(input=types.LiveClientRealtimeInput(media_chunks=[]), end_of_turn=True)

        async for response in session.receive():
            sc = response.server_content
            if sc is None:
                continue
            # Collect input (candidate) transcription.
            if sc.input_transcription and sc.input_transcription.text:
                result.input_transcription += sc.input_transcription.text
            # Collect model turn (AI response) text.
            if sc.model_turn:
                for part in sc.model_turn.parts:
                    if part.text:
                        result.response_text += part.text
                    if getattr(part, 'inline_data', None):
                        result.response_audio += part.inline_data.data
            if sc.turn_complete:
                result.turn_complete = True
                break

    return result


class GeminiProvider(TextGenerationProvider, LiveAudioProvider, TranscriptionProvider, MultimodalEvaluationProvider):
    def __init__(self, api_key: str, model: str, live_model: str = 'gemini-2.0-flash-live-001') -> None:
        self.api_key = api_key
        self.model = model
        self.live_model = live_model

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
        return bool(self.api_key and _get_genai_new() is not None)

    def run_live_turn(
        self,
        audio_bytes: bytes,
        system_prompt: str,
        audio_mime_type: str = 'audio/webm',
    ) -> Optional[LiveTurnResult]:
        """Run one audio turn through the Gemini Live API (synchronous wrapper).

        Returns a ``LiveTurnResult`` on success, or ``None`` when the Live API
        package is unavailable or the call fails.
        """
        if not self.api_key or _get_genai_new() is None:
            return None
        if not audio_bytes:
            return None

        try:
            loop = asyncio.new_event_loop()
            try:
                raw = loop.run_until_complete(
                    _run_live_turn_async(
                        api_key=self.api_key,
                        model=self.live_model,
                        system_prompt=system_prompt,
                        audio_bytes=audio_bytes,
                        audio_mime_type=audio_mime_type,
                    )
                )
            finally:
                loop.close()

            return LiveTurnResult(
                input_transcription=raw.input_transcription.strip(),
                response_text=raw.response_text.strip(),
                response_audio=raw.response_audio,
                turn_complete=raw.turn_complete,
            )
        except Exception:
            logger.exception('Gemini Live API turn failed')
            return None

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        # Gemini does not yet offer a separate transcription endpoint.
        # When using the non-Live audio path with Gemini, transcription is
        # unavailable — use the Live API path (supports_live_audio) instead.
        if audio_bytes:
            logger.warning(
                'GeminiProvider.transcribe_audio() called but Gemini has no standalone '
                'transcription endpoint. Audio will NOT be transcribed. '
                'Set INTERVIEW_PROVIDER=openai for Whisper-based transcription, or '
                'ensure GEMINI_API_KEY is set so the Live API path is used.'
            )
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
