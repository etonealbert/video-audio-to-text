"""Audio and video transcription tool using OpenAI's Whisper API.

This package provides a command-line tool for transcribing audio and video files
to text, with support for various output formats including plain text, SRT, and VTT.

Main features:
- Supports multiple audio/video formats (MP3, MP4, WAV, M4A, etc.)
- Intelligent chunking with silence detection for large files
- Retry logic with exponential backoff for API reliability
- Multiple output formats (txt, srt, vtt)
- Configurable via environment variables and CLI arguments
"""

__version__ = "1.0.0"
__author__ = "Transcriber"
__description__ = "Audio and video transcription tool using OpenAI Whisper API"

from .cli import main
from .config import AppConfig, load_config
from .types import Chunk, TranscriptionResult, MediaInfo, OutputFormat

__all__ = [
    "main",
    "AppConfig",
    "load_config", 
    "Chunk",
    "TranscriptionResult",
    "MediaInfo",
    "OutputFormat",
]
