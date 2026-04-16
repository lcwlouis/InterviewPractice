from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


class TextGenerationProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError


@dataclass
class LiveTurnResult:
    """Result of one bidirectional Live API turn."""
    input_transcription: str = ''   # what the candidate said (speech-to-text)
    response_text: str = ''          # AI interviewer's text response
    response_audio: bytes = field(default_factory=bytes)  # AI response audio (PCM/16kHz)
    turn_complete: bool = False


class LiveAudioProvider(ABC):
    @abstractmethod
    def supports_live_audio(self) -> bool:
        raise NotImplementedError

    def run_live_turn(
        self,
        audio_bytes: bytes,
        system_prompt: str,
        audio_mime_type: str = 'audio/webm',
    ) -> Optional[LiveTurnResult]:
        """Run one audio turn through the Live API.

        Returns a ``LiveTurnResult`` on success, or ``None`` when the provider
        does not support Live API (default implementation).  Override in
        providers that have native Live API support.
        """
        return None


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe_audio(self, audio_bytes: bytes) -> str:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    def synthesize_speech(self, text: str, speaker: Optional[str] = None) -> bytes:
        raise NotImplementedError


class MultimodalEvaluationProvider(ABC):
    @abstractmethod
    def evaluate_recording(self, transcript: str, video_path: Optional[str] = None) -> dict:
        raise NotImplementedError
