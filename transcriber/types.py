"""Type definitions for the transcriber application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol


@dataclass(frozen=True)
class Chunk:
    """Represents an audio chunk for transcription."""
    
    path: Path
    index: int
    start_ms: int
    end_ms: int
    size_bytes: int


@dataclass(frozen=True)
class TranscriptionSegment:
    """Represents a timestamped transcription segment."""
    
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    """Result from transcribing a single chunk."""
    
    chunk_index: int
    text: str
    segments: list[TranscriptionSegment] | None = None


@dataclass(frozen=True)
class MediaInfo:
    """Information about a media file."""
    
    duration_seconds: float
    sample_rate: int
    channels: int
    bitrate: int | None
    format: str
    size_bytes: int


OutputFormat = Literal["txt", "srt", "vtt"]


class WorkspaceProtocol(Protocol):
    """Protocol for temporary workspace management."""
    
    def get_temp_path(self, filename: str) -> Path:
        """Get a temporary file path within the workspace."""
        ...
    
    def cleanup(self) -> None:
        """Clean up the workspace."""
        ...
