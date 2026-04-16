from dataclasses import dataclass

from backend.config import Settings
from providers.base import TextGenerationProvider, TTSProvider
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.tts_edge import EdgeTTSProvider


@dataclass
class ProviderBundle:
    text_provider: TextGenerationProvider
    transcription_provider: object
    live_audio_provider: object
    multimodal_provider: object
    tts_provider: TTSProvider


def build_provider_bundle(settings: Settings) -> ProviderBundle:
    if settings.interview_provider.lower() == 'gemini':
        provider = GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    else:
        provider = OpenAIProvider(settings.openai_api_key, settings.openai_model)

    return ProviderBundle(
        text_provider=provider,
        transcription_provider=provider,
        live_audio_provider=provider,
        multimodal_provider=provider,
        tts_provider=EdgeTTSProvider(),
    )
