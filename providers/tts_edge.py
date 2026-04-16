from typing import Optional

from providers.base import TTSProvider


class EdgeTTSProvider(TTSProvider):
    def synthesize_speech(self, text: str, speaker: Optional[str] = None) -> bytes:
        payload = f'{speaker}: {text}' if speaker else text
        return payload.encode('utf-8')
