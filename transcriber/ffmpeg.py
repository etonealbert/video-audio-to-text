"""FFmpeg utilities for media file operations."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .types import MediaInfo

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Exception raised for FFmpeg-related errors."""
    pass


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system PATH.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    return shutil.which("ffmpeg") is not None


def ensure_ffmpeg_available() -> None:
    """Ensure FFmpeg is available, raise exception if not.
    
    Raises:
        FFmpegError: If FFmpeg is not found in PATH
    """
    if not check_ffmpeg_available():
        raise FFmpegError(
            "FFmpeg not found in PATH. Please install FFmpeg:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
            "  Windows: winget install ffmpeg or download from https://ffmpeg.org/"
        )


def validate_media_file(file_path: Path) -> None:
    """Validate that a media file appears to be in a supported format.
    
    Args:
        file_path: Path to the media file
        
    Raises:
        FFmpegError: If file appears to be corrupted or unsupported
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Media file not found: {file_path}")
    
    # Check file size
    if file_path.stat().st_size == 0:
        raise FFmpegError(f"Media file is empty: {file_path}")
    
    # For MP4 files, check for basic file structure
    if file_path.suffix.lower() in {".mp4", ".m4a", ".m4v"}:
        try:
            with open(file_path, "rb") as f:
                header = f.read(64)
                
            # MP4 files should start with an ftyp box or have recognizable structure
            # Look for common MP4 signatures
            if not any(signature in header for signature in [
                b"ftyp",  # File type box
                b"moov",  # Movie box
                b"mdat",  # Media data box
                b"mp4",   # MP4 brand
                b"isom",  # ISO base media
                b"M4A ",  # M4A brand
                b"M4V ",  # M4V brand
            ]):
                raise FFmpegError(
                    f"File does not appear to be a valid MP4: {file_path}\n"
                    f"The file might be:\n"
                    f"  - Corrupted or incomplete\n"
                    f"  - Encrypted or password-protected\n"
                    f"  - A different file type with wrong extension\n"
                    f"Try re-downloading or re-creating the file."
                )
        except OSError as e:
            raise FFmpegError(f"Cannot read media file {file_path}: {e}")


def probe_media_file(file_path: Path) -> MediaInfo:
    """Probe media file to extract metadata.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        MediaInfo object with file metadata
        
    Raises:
        FFmpegError: If probing fails
    """
    ensure_ffmpeg_available()
    
    # Validate file before attempting to probe
    validate_media_file(file_path)
    
    try:
        # Use ffprobe to get detailed media information
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        probe_data = json.loads(result.stdout)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown ffprobe error"
        
        # Provide more helpful error messages for common issues
        if "moov atom not found" in error_msg or "Invalid data found when processing input" in error_msg:
            raise FFmpegError(
                f"Media file appears to be corrupted or incomplete: {file_path}\n"
                f"Common causes:\n"
                f"  - File was not fully downloaded or copied\n"
                f"  - File is encrypted or password-protected\n"
                f"  - Recording was interrupted or failed\n"
                f"  - File format is not actually MP4 despite the extension\n"
                f"FFprobe error: {error_msg}"
            )
        elif "Permission denied" in error_msg:
            raise FFmpegError(
                f"Permission denied accessing media file: {file_path}\n"
                f"Try: chmod 644 \"{file_path}\""
            )
        else:
            raise FFmpegError(f"Failed to probe media file {file_path}: {error_msg}")
    except subprocess.TimeoutExpired:
        raise FFmpegError(f"Timeout while probing media file {file_path}")
    except json.JSONDecodeError as e:
        raise FFmpegError(f"Failed to parse ffprobe output for {file_path}: {e}")
    
    # Extract format information
    format_info = probe_data.get("format", {})
    duration = float(format_info.get("duration", 0))
    size_bytes = int(format_info.get("size", 0))
    format_name = format_info.get("format_name", "unknown")
    
    # Find first audio stream
    audio_stream = None
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break
    
    if not audio_stream:
        raise FFmpegError(f"No audio stream found in {file_path}")
    
    # Extract audio stream information
    sample_rate = int(audio_stream.get("sample_rate", 0))
    channels = int(audio_stream.get("channels", 0))
    
    # Bitrate might be in the stream or format
    bitrate = None
    if "bit_rate" in audio_stream:
        bitrate = int(audio_stream["bit_rate"])
    elif "bit_rate" in format_info:
        bitrate = int(format_info["bit_rate"])
    
    return MediaInfo(
        duration_seconds=duration,
        sample_rate=sample_rate,
        channels=channels,
        bitrate=bitrate,
        format=format_name,
        size_bytes=size_bytes
    )


def extract_audio_to_mp3(
    input_path: Path,
    output_path: Path,
    bitrate: str = "128k",
    sample_rate: int = 44100
) -> None:
    """Extract audio from media file and convert to MP3.
    
    Args:
        input_path: Path to input media file
        output_path: Path for output MP3 file
        bitrate: Audio bitrate (e.g., "128k", "192k")
        sample_rate: Target sample rate in Hz
        
    Raises:
        FFmpegError: If conversion fails
    """
    ensure_ffmpeg_available()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",  # No video
            "-acodec", "libmp3lame",  # MP3 codec
            "-ab", bitrate,  # Audio bitrate
            "-ar", str(sample_rate),  # Sample rate
            "-ac", "2",  # Stereo
            "-y",  # Overwrite output file
            str(output_path)
        ]
        
        logger.info(f"Converting {input_path} to MP3...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=3600  # 1 hour timeout for large files
        )
        
        logger.info(f"Successfully converted to {output_path}")
        
    except subprocess.CalledProcessError as e:
        raise FFmpegError(f"Failed to convert {input_path} to MP3: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise FFmpegError(f"Timeout while converting {input_path} to MP3")


def estimate_mp3_size(duration_seconds: float, bitrate_str: str) -> int:
    """Estimate the size of an MP3 file in bytes.
    
    Args:
        duration_seconds: Duration of audio in seconds
        bitrate_str: Bitrate string (e.g., "128k", "192k")
        
    Returns:
        Estimated file size in bytes
    """
    # Parse bitrate string (e.g., "128k" -> 128000)
    bitrate_str = bitrate_str.lower()
    if bitrate_str.endswith("k"):
        bitrate_bps = int(bitrate_str[:-1]) * 1000
    elif bitrate_str.endswith("m"):
        bitrate_bps = int(bitrate_str[:-1]) * 1000000
    else:
        bitrate_bps = int(bitrate_str)
    
    # Calculate file size: (bitrate in bits/sec * duration in sec) / 8 bits/byte
    estimated_bytes = int((bitrate_bps * duration_seconds) / 8)
    
    # Add small overhead for MP3 metadata/headers (~2%)
    return int(estimated_bytes * 1.02)
