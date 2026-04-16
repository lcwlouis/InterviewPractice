"""Provider registry — builds the correct provider bundle from settings."""

from __future__ import annotations

from dataclasses import dataclass

from backend.config import Settings
from providers.base import (
    LiveAudioProvider,
    MultimodalEvaluationProvider,
    TextGenerationProvider,
    TranscriptionProvider,
    TTSProvider,
)
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.tts_edge import EdgeTTSProvider


@dataclass
class ProviderBundle:
    text_provider: TextGenerationProvider
    transcription_provider: TranscriptionProvider
    live_audio_provider: LiveAudioProvider
    multimodal_provider: MultimodalEvaluationProvider
    tts_provider: TTSProvider


def build_provider_bundle(settings: Settings) -> ProviderBundle:
    if settings.interview_provider.lower() == 'gemini':
        provider = GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.gemini_live_model)
    else:
        provider = OpenAIProvider(settings.openai_api_key, settings.openai_model)

    return ProviderBundle(
        text_provider=provider,
        transcription_provider=provider,
        live_audio_provider=provider,
        multimodal_provider=provider,
        tts_provider=EdgeTTSProvider(),
    )
