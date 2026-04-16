from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RecordingArtifact:
    audio_path: Optional[str]
    video_path: Optional[str]
    started_at: datetime
    stopped_at: Optional[datetime] = None


class RecordingService:
    def __init__(self) -> None:
        self.current: Optional[RecordingArtifact] = None

    def start(self) -> RecordingArtifact:
        self.current = RecordingArtifact(audio_path=None, video_path=None, started_at=datetime.now(timezone.utc))
        return self.current

    def stop(self) -> Optional[RecordingArtifact]:
        if self.current:
            self.current.stopped_at = datetime.now(timezone.utc)
        return self.current
