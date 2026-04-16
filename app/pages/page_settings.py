"""Settings page — provider config, audio modes, environment variables."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from services.provider_registry import build_provider_bundle


def render() -> None:
    st.header('⚙️ Settings & Providers')
    settings = get_settings()
    providers = build_provider_bundle(settings)

    st.subheader('Active Provider')
    st.write({
        'provider': settings.interview_provider,
        'model': settings.openai_model if settings.interview_provider == 'openai' else settings.gemini_model,
        'live_audio_supported': providers.live_audio_provider.supports_live_audio(),
        'web_research_enabled': settings.enable_web_research,
        'search_api_configured': bool(settings.search_api_key),
        'default_country': settings.default_country_preset,
    })

    st.subheader('Audio Modes')
    st.markdown('''
The interview session supports three audio modes:

1. **Live audio conversation** — Mic input → Whisper transcription → LLM response → Edge TTS playback.
   This is the default mode when audio is enabled. Answers are automatically submitted
   after silence detection (when auto-submit is on).

2. **Audio-in → text-out** — Mic capture → Whisper transcription → text response displayed.
   Use this when you prefer to read the interviewer's questions.

3. **Full multimodal** — Audio + video recording → body language analysis via GPT-4o/Gemini Vision.
   Enable video recording in Setup to activate webcam capture. Video clips are analyzed
   at the end of the session for body language, confidence, and presence observations.
    ''')

    st.subheader('Environment Variables')
    st.code(
        '# Provider\n'
        'INTERVIEW_PROVIDER=openai          # openai | gemini\n'
        'OPENAI_API_KEY=sk-...              # OpenAI API key\n'
        'OPENAI_MODEL=gpt-4.1-mini         # Model for text generation\n'
        'GEMINI_API_KEY=...                 # Google Gemini API key\n'
        'GEMINI_MODEL=gemini-2.5-pro        # Model for text generation\n'
        '\n'
        '# Search / Research\n'
        'SEARCH_API_KEY=tvly-...            # Tavily API key for web research\n'
        'ENABLE_WEB_RESEARCH=false          # Enable interviewer web research\n'
        '\n'
        '# Defaults\n'
        'DEFAULT_COUNTRY_PRESET=SG          # US | UK | CA | AU | DE | JP | IN | SG\n'
        'APP_LOG_LEVEL=INFO                 # DEBUG | INFO | WARNING | ERROR',
        language='bash',
    )
