"""Intelligent audio splitting with silence detection for API-safe chunks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pydub import AudioSegment
from pydub.silence import detect_silence

from .io_utils import get_file_size, safe_filename
from .media import estimate_mp3_duration_for_size
from .types import Chunk, WorkspaceProtocol

logger = logging.getLogger(__name__)


def split_into_chunks(
    mp3_path: Path,
    max_chunk_mb: int,
    min_silence_ms: int,
    silence_threshold_db: int,
    workspace: WorkspaceProtocol,
    bitrate: str = "128k"
) -> List[Chunk]:
    """Split MP3 file into API-safe chunks using intelligent silence detection.
    
    Args:
        mp3_path: Path to the MP3 file to split
        max_chunk_mb: Maximum chunk size in megabytes
        min_silence_ms: Minimum silence duration in milliseconds
        silence_threshold_db: Silence threshold in dB (negative value)
        workspace: Temporary workspace for chunk files
        bitrate: Bitrate of the MP3 file for size estimation
        
    Returns:
        List of Chunk objects representing the split audio segments
        
    Raises:
        FileNotFoundError: If input MP3 file doesn't exist
        ValueError: If audio file is empty or invalid
    """
    if not mp3_path.exists():
        raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
    
    # Check if file is small enough to process as single chunk
    file_size_mb = get_file_size(mp3_path) / (1024 * 1024)
    if file_size_mb <= max_chunk_mb:
        logger.info(f"File size ({file_size_mb:.1f}MB) is within limit, using single chunk")
        return [Chunk(
            path=mp3_path,
            index=0,
            start_ms=0,
            end_ms=int(AudioSegment.from_mp3(mp3_path).duration_seconds * 1000),
            size_bytes=int(file_size_mb * 1024 * 1024)
        )]
    
    logger.info(f"Splitting large file ({file_size_mb:.1f}MB) into chunks...")
    
    # Load audio file
    try:
        audio = AudioSegment.from_mp3(mp3_path)
    except Exception as e:
        raise ValueError(f"Failed to load MP3 file {mp3_path}: {e}")
    
    if len(audio) == 0:
        raise ValueError(f"Audio file is empty: {mp3_path}")
    
    duration_ms = len(audio)
    logger.info(f"Audio duration: {duration_ms / 1000:.1f} seconds")
    
    # Calculate target chunk duration based on size limit
    target_chunk_duration_s = estimate_mp3_duration_for_size(max_chunk_mb * 0.95, bitrate)  # 5% buffer
    target_chunk_duration_ms = int(target_chunk_duration_s * 1000)
    
    logger.info(f"Target chunk duration: {target_chunk_duration_s:.1f} seconds")
    
    # Find optimal split points using silence detection
    split_points = _find_split_points(
        audio=audio,
        target_duration_ms=target_chunk_duration_ms,
        min_silence_ms=min_silence_ms,
        silence_threshold_db=silence_threshold_db
    )
    
    # Ensure we start at 0 and end at total duration
    if split_points[0] != 0:
        split_points.insert(0, 0)
    if split_points[-1] != duration_ms:
        split_points.append(duration_ms)
    
    logger.info(f"Found {len(split_points) - 1} chunks with split points at: {split_points}")
    
    # Create chunks
    chunks: List[Chunk] = []
    for i in range(len(split_points) - 1):
        start_ms = split_points[i]
        end_ms = split_points[i + 1]
        
        # Extract audio segment
        segment = audio[start_ms:end_ms]
        
        # Create chunk file
        chunk_filename = safe_filename(f"chunk_{i:03d}.mp3")
        chunk_path = workspace.get_temp_path(chunk_filename)
        
        # Export segment to file
        segment.export(chunk_path, format="mp3", bitrate=bitrate)
        
        # Verify chunk size
        chunk_size = get_file_size(chunk_path)
        chunk_size_mb = chunk_size / (1024 * 1024)
        
        if chunk_size_mb > max_chunk_mb:
            logger.warning(
                f"Chunk {i} is oversized ({chunk_size_mb:.1f}MB), "
                f"may need smaller target duration"
            )
        
        chunks.append(Chunk(
            path=chunk_path,
            index=i,
            start_ms=start_ms,
            end_ms=end_ms,
            size_bytes=chunk_size
        ))
        
        logger.info(
            f"Created chunk {i}: {start_ms/1000:.1f}s-{end_ms/1000:.1f}s "
            f"({chunk_size_mb:.1f}MB)"
        )
    
    return chunks


def _find_split_points(
    audio: AudioSegment,
    target_duration_ms: int,
    min_silence_ms: int,
    silence_threshold_db: int,
    search_window_ms: int = 30000  # 30 seconds
) -> List[int]:
    """Find optimal split points using silence detection.
    
    Args:
        audio: AudioSegment to analyze
        target_duration_ms: Target duration for each chunk in milliseconds
        min_silence_ms: Minimum silence duration to consider
        silence_threshold_db: Silence threshold in dB
        search_window_ms: Window around target point to search for silence
        
    Returns:
        List of split points in milliseconds
    """
    duration_ms = len(audio)
    split_points = [0]  # Always start at 0
    
    current_pos = 0
    
    while current_pos + target_duration_ms < duration_ms:
        # Calculate target split point
        target_split = current_pos + target_duration_ms
        
        # Define search window around target point
        search_start = max(current_pos, target_split - search_window_ms // 2)
        search_end = min(duration_ms, target_split + search_window_ms // 2)
        
        # Find silence in the search window
        search_segment = audio[search_start:search_end]
        
        silence_ranges = detect_silence(
            search_segment,
            min_silence_len=min_silence_ms,
            silence_thresh=silence_threshold_db
        )
        
        if silence_ranges:
            # Find silence closest to target point
            target_offset = target_split - search_start
            best_silence = min(
                silence_ranges,
                key=lambda s: abs((s[0] + s[1]) // 2 - target_offset)
            )
            
            # Use middle of silence range as split point
            silence_middle = (best_silence[0] + best_silence[1]) // 2
            actual_split = search_start + silence_middle
            
            logger.info(
                f"Found silence at {actual_split/1000:.1f}s "
                f"(target was {target_split/1000:.1f}s)"
            )
        else:
            # No suitable silence found, use target point as fallback
            actual_split = target_split
            logger.warning(
                f"No silence found near {target_split/1000:.1f}s, "
                f"using hard split"
            )
        
        split_points.append(actual_split)
        current_pos = actual_split
    
    return split_points


def _validate_chunks(chunks: List[Chunk], max_chunk_mb: int) -> None:
    """Validate that all chunks are within size limits.
    
    Args:
        chunks: List of chunks to validate
        max_chunk_mb: Maximum allowed chunk size in MB
        
    Raises:
        ValueError: If any chunk exceeds the size limit
    """
    for chunk in chunks:
        chunk_size_mb = chunk.size_bytes / (1024 * 1024)
        if chunk_size_mb > max_chunk_mb:
            raise ValueError(
                f"Chunk {chunk.index} exceeds size limit: "
                f"{chunk_size_mb:.1f}MB > {max_chunk_mb}MB"
            )
