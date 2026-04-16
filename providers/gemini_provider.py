"""Google Gemini provider — real API integration with graceful fallback.

Supports:
- Text generation via ``google-generativeai`` (legacy REST API)
- Audio transcription via ``google-generativeai`` content API (audio→text)
- Live bidirectional audio via ``google-genai`` (Live API / WebSocket)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
import threading
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


def _run_async_in_thread(coro):
    """Run an async coroutine safely, even when a loop is already running.

    Streamlit runs its own asyncio event loop. Calling
    ``asyncio.new_event_loop().run_until_complete(...)`` from within it
    can cause conflicts. This helper spins up a *dedicated thread* with
    its own event loop to avoid those issues.
    """
    result = [None]
    exception = [None]

    def _target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result[0] = loop.run_until_complete(coro)
        except Exception as exc:
            exception[0] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout=60)  # 60-second timeout

    if exception[0] is not None:
        raise exception[0]
    if thread.is_alive():
        raise TimeoutError('Gemini Live API call timed out after 60 seconds')
    return result[0]


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
        """Run one audio turn through the Gemini Live API.

        Uses a dedicated thread with its own event loop to avoid
        conflicting with Streamlit's running asyncio loop.

        Returns a ``LiveTurnResult`` on success, or ``None`` when the Live API
        package is unavailable or the call fails.
        """
        if not self.api_key or _get_genai_new() is None:
            return None
        if not audio_bytes:
            return None

        try:
            raw = _run_async_in_thread(
                _run_live_turn_async(
                    api_key=self.api_key,
                    model=self.live_model,
                    system_prompt=system_prompt,
                    audio_bytes=audio_bytes,
                    audio_mime_type=audio_mime_type,
                )
            )

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
        """Transcribe audio using Gemini's content API (upload audio as inline data).

        Gemini models accept audio as part of multimodal content, so we send
        the audio with a transcription prompt to get text back.
        """
        if not audio_bytes:
            return ''

        genai = self._configure()
        if genai is None:
            logger.warning(
                'GeminiProvider.transcribe_audio() — google-generativeai not available '
                'or API key missing. Cannot transcribe.'
            )
            return ''

        try:
            model = genai.GenerativeModel(self.model)

            # Write audio to temp file, then upload
            tmp = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
            try:
                tmp.write(audio_bytes)
                tmp.flush()
                tmp.close()

                # Upload the audio file
                audio_file = genai.upload_file(tmp.name, mime_type='audio/webm')

                response = model.generate_content(
                    [
                        audio_file,
                        'Transcribe this audio exactly as spoken. '
                        'Return ONLY the transcription text, nothing else. '
                        'If you cannot understand the audio, return an empty string.',
                    ],
                )
                text = (response.text or '').strip()
                # Clean up the uploaded file
                try:
                    audio_file.delete()
                except Exception:
                    pass
                return text
            finally:
                os.unlink(tmp.name)
        except Exception:
            logger.exception('Gemini audio transcription via content API failed')
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
