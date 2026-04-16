"""Recording service — audio/video capture, transcription, and playback.

Implements Suggestion 3 (Audio Recording & Transcription Pipeline) and
Suggestion 7 (Video Recording & Body Language Analysis).

Audio flow:
  - Browser mic capture via Streamlit's st.audio_input() or WebRTC
  - Audio bytes → transcription_provider.transcribe_audio()
  - TTS response → st.audio() playback

Video flow:
  - WebRTC webcam capture via streamlit-webrtc
  - Save video clips per question
  - Send to multimodal provider for body language analysis
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from providers.base import MultimodalEvaluationProvider, TextGenerationProvider, TranscriptionProvider, TTSProvider

logger = logging.getLogger(__name__)

VIDEO_DIR = Path(tempfile.gettempdir()) / 'interview_practice' / 'video'
AUDIO_DIR = Path(tempfile.gettempdir()) / 'interview_practice' / 'audio'


@dataclass
class RecordingArtifact:
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stopped_at: Optional[datetime] = None
    transcription: str = ''


class RecordingService:
    """Manages audio/video recording, transcription, and TTS playback."""

    def __init__(
        self,
        transcription_provider: Optional[TranscriptionProvider] = None,
        tts_provider: Optional[TTSProvider] = None,
        multimodal_provider: Optional[MultimodalEvaluationProvider] = None,
    ) -> None:
        self.transcription_provider = transcription_provider
        self.tts_provider = tts_provider
        self.multimodal_provider = multimodal_provider
        self.current: Optional[RecordingArtifact] = None
        self._recordings: list[RecordingArtifact] = []

        # Ensure directories exist
        VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def start(self, question_id: str = '') -> RecordingArtifact:
        """Start a new recording session for a question."""
        artifact = RecordingArtifact(
            audio_path=str(AUDIO_DIR / f'{question_id}_{datetime.now(timezone.utc).strftime("%H%M%S")}.webm'),
            video_path=str(VIDEO_DIR / f'{question_id}_{datetime.now(timezone.utc).strftime("%H%M%S")}.webm'),
        )
        self.current = artifact
        return artifact

    def stop(self) -> Optional[RecordingArtifact]:
        """Stop current recording."""
        if self.current:
            self.current.stopped_at = datetime.now(timezone.utc)
            self._recordings.append(self.current)
        result = self.current
        self.current = None
        return result

    # ── Audio ────────────────────────────────────────────────────────

    def save_audio(self, audio_bytes: bytes, question_id: str = '') -> str:
        """Save raw audio bytes to disk and return the file path."""
        filename = f'{question_id}_{datetime.now(timezone.utc).strftime("%H%M%S")}.webm'
        path = AUDIO_DIR / filename
        path.write_bytes(audio_bytes)
        if self.current:
            self.current.audio_path = str(path)
        return str(path)

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes using the transcription provider."""
        if not self.transcription_provider or not audio_bytes:
            return ''
        try:
            text = self.transcription_provider.transcribe_audio(audio_bytes)
            if self.current:
                self.current.transcription = text
            return text
        except Exception:
            logger.exception('Transcription failed')
            return ''

    def synthesize_speech(self, text: str, speaker: str = '') -> bytes:
        """Convert text to speech using TTS provider."""
        if not self.tts_provider:
            return b''
        try:
            result = self.tts_provider.synthesize_speech(text, speaker=speaker)
            if result and len(result) <= 100:
                logger.warning(
                    'TTS synthesis returned very short output (%d bytes) — '
                    'likely fell back to raw text bytes. Check TTS provider configuration.',
                    len(result),
                )
            return result
        except Exception:
            logger.exception('TTS synthesis failed')
            return b''

    # ── Video ────────────────────────────────────────────────────────

    def save_video_frame(self, frame_bytes: bytes, question_id: str = '') -> str:
        """Save a video frame/clip to disk."""
        filename = f'{question_id}_{datetime.now(timezone.utc).strftime("%H%M%S")}.webm'
        path = VIDEO_DIR / filename
        path.write_bytes(frame_bytes)
        if self.current:
            self.current.video_path = str(path)
        return str(path)

    def analyze_video(self, video_path: str, transcript: str = '') -> dict:
        """Send video to multimodal provider for body language analysis."""
        if not self.multimodal_provider:
            return {'error': 'No multimodal provider configured'}
        try:
            return self.multimodal_provider.evaluate_recording(
                transcript=transcript, video_path=video_path,
            )
        except Exception:
            logger.exception('Video analysis failed')
            return {'error': 'Video analysis failed'}

    @property
    def recordings(self) -> list[RecordingArtifact]:
        return list(self._recordings)
