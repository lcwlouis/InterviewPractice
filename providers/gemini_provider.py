from __future__ import annotations

from typing import Optional

from providers.base import LiveAudioProvider, MultimodalEvaluationProvider, TextGenerationProvider, TranscriptionProvider


class GeminiProvider(TextGenerationProvider, LiveAudioProvider, TranscriptionProvider, MultimodalEvaluationProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            return 'Gemini API key not configured. Safe fallback response.'
        return f'[Gemini:{self.model}] {prompt[:300]}'

    def supports_live_audio(self) -> bool:
        return bool(self.api_key)

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ''
        return 'Transcription placeholder from Gemini provider.'

    def evaluate_recording(self, transcript: str, video_path: Optional[str] = None) -> dict:
        return {
            'provider': 'gemini',
            'model': self.model,
            'transcript_length': len(transcript),
            'video_analyzed': bool(video_path),
            'note': 'TODO: integrate Gemini multimodal evaluation API.'
        }
