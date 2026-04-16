from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TextGenerationProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError


class LiveAudioProvider(ABC):
    @abstractmethod
    def supports_live_audio(self) -> bool:
        raise NotImplementedError


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
