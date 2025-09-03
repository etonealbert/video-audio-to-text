"""Configuration management for the transcriber application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .types import OutputFormat, PCMConfig


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from environment and CLI arguments."""
    
    # Input/output
    input_path: Path
    output_format: OutputFormat
    input_dir: Path
    output_basename: str
    
    # Audio processing
    bitrate: str
    max_chunk_mb: int
    min_silence_ms: int
    silence_threshold_db: int
    
    # API settings
    openai_api_key: str
    model: str
    language: str | None
    concurrency: int
    
    # Logging
    verbose: bool
    
    # PCM file configuration
    pcm_config: PCMConfig


def load_config(args: Any) -> AppConfig:
    """Load configuration from .env file and CLI arguments."""
    # Load .env file if it exists
    load_dotenv()
    
    # Process input path
    input_path = Path(args.input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Determine output paths
    input_dir = input_path.parent
    output_basename = input_path.stem
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be set in .env file or environment")
    
    return AppConfig(
        # Input/output
        input_path=input_path,
        output_format=args.format,
        input_dir=input_dir,
        output_basename=output_basename,
        
        # Audio processing - CLI args override env vars
        bitrate=args.bitrate or os.getenv("DEFAULT_BITRATE", "128k"),
        max_chunk_mb=args.max_chunk_mb or int(os.getenv("DEFAULT_MAX_CHUNK_MB", "24")),
        min_silence_ms=args.min_silence_ms or int(os.getenv("DEFAULT_MIN_SILENCE_MS", "400")),
        silence_threshold_db=args.silence_threshold or int(os.getenv("DEFAULT_SILENCE_THRESHOLD", "-40")),
        
        # API settings
        openai_api_key=api_key,
        model=args.model or os.getenv("OPENAI_MODEL", "whisper-1"),
        language=args.language,
        concurrency=args.concurrency or int(os.getenv("DEFAULT_CONCURRENCY", "1")),
        
        # Logging
        verbose=args.verbose,
        
        # PCM configuration
        pcm_config=PCMConfig(
            sample_rate=args.pcm_sample_rate,
            channels=args.pcm_channels,
            bit_depth=args.pcm_bit_depth,
            format=args.pcm_format
        ),
    )


def validate_supported_format(file_path: Path) -> bool:
    """Check if the file format is supported."""
    supported_extensions = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".pcm"}
    return file_path.suffix.lower() in supported_extensions
