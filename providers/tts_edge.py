"""Microsoft Edge TTS provider — real integration via edge-tts package."""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Optional

from providers.base import TTSProvider

logger = logging.getLogger(__name__)


def _get_edge_tts():  # noqa: ANN202
    try:
        import edge_tts
        return edge_tts
    except ImportError:
        return None


class EdgeTTSProvider(TTSProvider):
    """TTS using Microsoft Edge's free TTS service.

    Falls back to plain UTF-8 encoded text if the edge-tts package
    is not installed.
    """

    DEFAULT_VOICE = 'en-US-AriaNeural'

    def synthesize_speech(self, text: str, speaker: Optional[str] = None) -> bytes:
        edge_tts = _get_edge_tts()
        if edge_tts is None:
            logger.warning(
                'edge-tts package not installed — TTS unavailable, returning raw text bytes. '
                'Install with: pip install edge-tts'
            )
            payload = f'{speaker}: {text}' if speaker else text
            return payload.encode('utf-8')

        voice = self.DEFAULT_VOICE
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._generate(edge_tts, text, voice))
            loop.close()
            if not result:
                logger.warning('Edge TTS synthesis returned empty audio for text: %.80s', text)
            return result
        except Exception:
            logger.exception('Edge TTS synthesis failed — returning raw text bytes as fallback')
            payload = f'{speaker}: {text}' if speaker else text
            return payload.encode('utf-8')

    @staticmethod
    async def _generate(edge_tts, text: str, voice: str) -> bytes:  # noqa: ANN001
        communicate = edge_tts.Communicate(text, voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                buffer.write(chunk['data'])
        return buffer.getvalue()
