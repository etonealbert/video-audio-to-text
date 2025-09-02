"""Media file processing for audio extraction and MP3 conversion."""

from __future__ import annotations

import logging
from pathlib import Path

from .ffmpeg import extract_audio_to_mp3, probe_media_file, estimate_mp3_size
from .io_utils import get_file_size, safe_filename
from .types import MediaInfo, WorkspaceProtocol

logger = logging.getLogger(__name__)


def ensure_mp3(
    input_path: Path,
    bitrate: str,
    workspace: WorkspaceProtocol,
    max_chunk_mb: int = 24
) -> Path:
    """Ensure input file is converted to MP3 format if needed.
    
    Args:
        input_path: Path to input media file
        bitrate: Target bitrate for MP3 conversion (e.g., "128k")
        workspace: Temporary workspace for file operations
        max_chunk_mb: Maximum chunk size in MB
        
    Returns:
        Path to MP3 file (either original or converted)
        
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If input file doesn't exist
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Check if file extension is supported
    supported_extensions = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav"}
    file_extension = input_path.suffix.lower()
    
    if file_extension not in supported_extensions:
        raise ValueError(
            f"Unsupported file format: {file_extension}. "
            f"Supported formats: {', '.join(sorted(supported_extensions))}"
        )
    
    # Probe the media file to get information
    logger.info(f"Probing media file: {input_path}")
    media_info = probe_media_file(input_path)
    
    logger.info(
        f"Media info - Duration: {media_info.duration_seconds:.1f}s, "
        f"Format: {media_info.format}, Size: {media_info.size_bytes / (1024*1024):.1f}MB"
    )
    
    # Check if file is already MP3 and within size limits
    if (file_extension == ".mp3" and 
        media_info.size_bytes <= max_chunk_mb * 1024 * 1024 and
        _is_acceptable_mp3_quality(media_info, bitrate)):
        
        logger.info("File is already suitable MP3 format, using original")
        return input_path
    
    # Need to convert to MP3
    safe_name = safe_filename(f"{input_path.stem}.mp3")
    mp3_path = workspace.get_temp_path(safe_name)
    
    logger.info(f"Converting to MP3: {input_path} -> {mp3_path}")
    
    # Parse sample rate from media info or use default
    target_sample_rate = media_info.sample_rate if media_info.sample_rate > 0 else 44100
    
    # Limit sample rate to reasonable values for transcription
    if target_sample_rate > 48000:
        target_sample_rate = 48000
    elif target_sample_rate < 16000:
        target_sample_rate = 16000
    
    extract_audio_to_mp3(
        input_path=input_path,
        output_path=mp3_path,
        bitrate=bitrate,
        sample_rate=target_sample_rate
    )
    
    # Verify the conversion was successful
    if not mp3_path.exists():
        raise RuntimeError(f"MP3 conversion failed: output file not created")
    
    converted_size = get_file_size(mp3_path)
    logger.info(f"Conversion complete. Output size: {converted_size / (1024*1024):.1f}MB")
    
    return mp3_path


def _is_acceptable_mp3_quality(media_info: MediaInfo, target_bitrate: str) -> bool:
    """Check if existing MP3 has acceptable quality for our needs.
    
    Args:
        media_info: Information about the media file
        target_bitrate: Target bitrate string (e.g., "128k")
        
    Returns:
        True if quality is acceptable, False if needs re-encoding
    """
    if not media_info.bitrate:
        # If we can't determine bitrate, assume it needs conversion
        return False
    
    # Parse target bitrate
    target_bitrate_num = _parse_bitrate_string(target_bitrate)
    
    # Accept if existing bitrate is close to or higher than target
    # Allow some tolerance for VBR files
    return media_info.bitrate >= target_bitrate_num * 0.8


def _parse_bitrate_string(bitrate_str: str) -> int:
    """Parse bitrate string to numeric value.
    
    Args:
        bitrate_str: Bitrate string (e.g., "128k", "192k")
        
    Returns:
        Bitrate in bits per second
    """
    bitrate_str = bitrate_str.lower()
    if bitrate_str.endswith("k"):
        return int(bitrate_str[:-1]) * 1000
    elif bitrate_str.endswith("m"):
        return int(bitrate_str[:-1]) * 1000000
    else:
        return int(bitrate_str)


def estimate_mp3_duration_for_size(target_size_mb: float, bitrate: str) -> float:
    """Estimate how many seconds of MP3 audio fit in a target size.
    
    Args:
        target_size_mb: Target size in megabytes
        bitrate: Bitrate string (e.g., "128k")
        
    Returns:
        Duration in seconds that would fit in the target size
    """
    target_bytes = target_size_mb * 1024 * 1024
    bitrate_bps = _parse_bitrate_string(bitrate)
    
    # Calculate duration: (size in bytes * 8 bits/byte) / (bitrate in bits/sec)
    # Add small buffer for metadata overhead
    duration_seconds = (target_bytes * 8 * 0.98) / bitrate_bps
    
    return duration_seconds
