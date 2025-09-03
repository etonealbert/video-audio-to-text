"""Main transcription orchestration with chunk processing and output generation."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from tqdm import tqdm

from .openai_client import OpenAITranscriptionClient, create_transcription_client
from .types import Chunk, OutputFormat, TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


def transcribe_chunks(
    chunks: List[Chunk],
    output_format: OutputFormat,
    language: str | None,
    model: str,
    fallback_model: str,
    concurrency: int,
    output_basename: str,
    input_dir: Path,
    api_key: str
) -> Path:
    """Transcribe audio chunks and generate output file.
    
    Args:
        chunks: List of audio chunks to transcribe
        output_format: Output format ("txt", "srt", "vtt")
        language: Optional language hint
        model: Primary OpenAI model to use
        fallback_model: Fallback OpenAI model if primary fails
        concurrency: Number of concurrent API calls
        output_basename: Base name for output file
        input_dir: Directory to write output file
        api_key: OpenAI API key
        
    Returns:
        Path to the generated output file
        
    Raises:
        ValueError: If chunks are empty or invalid output format
        TranscriptionError: If transcription fails
    """
    if not chunks:
        raise ValueError("No chunks provided for transcription")
    
    if output_format not in {"txt", "srt", "vtt"}:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    logger.info(f"Starting transcription of {len(chunks)} chunks with concurrency {concurrency}")
    
    if concurrency > 1:
        logger.warning(
            f"Using concurrency {concurrency} > 1. Monitor API rate limits. "
            f"Consider using concurrency=1 to avoid quota issues."
        )
    
    # Create OpenAI client
    client = create_transcription_client(api_key=api_key, model=model, fallback_model=fallback_model)
    
    # Determine response format based on output needs
    api_response_format = "verbose_json" if output_format in {"srt", "vtt"} else "text"
    
    # Transcribe chunks
    results = _transcribe_chunks_concurrent(
        chunks=chunks,
        client=client,
        language=language,
        response_format=api_response_format,
        concurrency=concurrency
    )
    
    # Generate output file
    output_path = _generate_output_file(
        results=results,
        output_format=output_format,
        output_basename=output_basename,
        input_dir=input_dir
    )
    
    logger.info(f"Transcription completed successfully: {output_path}")
    return output_path


def _transcribe_chunks_concurrent(
    chunks: List[Chunk],
    client: OpenAITranscriptionClient,
    language: str | None,
    response_format: str,
    concurrency: int
) -> List[TranscriptionResult]:
    """Transcribe chunks concurrently while preserving order.
    
    Args:
        chunks: List of chunks to transcribe
        client: OpenAI transcription client
        language: Optional language hint
        response_format: API response format
        concurrency: Number of concurrent workers
        
    Returns:
        List of transcription results in order
    """
    results: List[TranscriptionResult | None] = [None] * len(chunks)
    
    def transcribe_single_chunk(chunk: Chunk) -> TranscriptionResult:
        """Transcribe a single chunk."""
        try:
            response = client.transcribe_file(
                file_path=chunk.path,
                language=language,
                response_format=response_format
            )
            
            # Extract text and segments based on response format
            if response_format == "text":
                text = response["text"]
                segments = None
            else:
                # verbose_json format
                text = response.get("text", "")
                segments = _parse_segments(response.get("segments", []), chunk.start_ms)
            
            return TranscriptionResult(
                chunk_index=chunk.index,
                text=text,
                segments=segments
            )
            
        except Exception as e:
            logger.error(f"Failed to transcribe chunk {chunk.index}: {e}")
            raise
    
    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all tasks
        future_to_chunk = {
            executor.submit(transcribe_single_chunk, chunk): chunk
            for chunk in chunks
        }
        
        # Process results with progress bar
        with tqdm(total=len(chunks), desc="Transcribing chunks") as pbar:
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    results[result.chunk_index] = result
                    pbar.update(1)
                    logger.info(f"Completed chunk {result.chunk_index + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Chunk {chunk.index} failed: {e}")
                    raise
    
    # Verify all results were processed
    if any(result is None for result in results):
        missing_indices = [i for i, result in enumerate(results) if result is None]
        raise RuntimeError(f"Failed to process chunks: {missing_indices}")
    
    return results  # type: ignore


def _parse_segments(segments_data: List[dict], chunk_start_ms: int) -> List[TranscriptionSegment]:
    """Parse segment data from API response and adjust timestamps.
    
    Args:
        segments_data: Raw segment data from API
        chunk_start_ms: Start time of the chunk in milliseconds
        
    Returns:
        List of parsed transcription segments with adjusted timestamps
    """
    segments = []
    for seg_data in segments_data:
        # Adjust timestamps to absolute time
        start = seg_data.get("start", 0) + (chunk_start_ms / 1000)
        end = seg_data.get("end", 0) + (chunk_start_ms / 1000)
        text = seg_data.get("text", "").strip()
        
        if text:  # Only include non-empty segments
            segments.append(TranscriptionSegment(
                start=start,
                end=end,
                text=text
            ))
    
    return segments


def _generate_output_file(
    results: List[TranscriptionResult],
    output_format: OutputFormat,
    output_basename: str,
    input_dir: Path
) -> Path:
    """Generate the final output file from transcription results.
    
    Args:
        results: List of transcription results
        output_format: Output format ("txt", "srt", "vtt")
        output_basename: Base name for output file
        input_dir: Directory to write output file
        
    Returns:
        Path to the generated output file
    """
    if output_format == "txt":
        return _generate_txt_output(results, output_basename, input_dir)
    elif output_format == "srt":
        return _generate_srt_output(results, output_basename, input_dir)
    elif output_format == "vtt":
        return _generate_vtt_output(results, output_basename, input_dir)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def _generate_txt_output(
    results: List[TranscriptionResult],
    output_basename: str,
    input_dir: Path
) -> Path:
    """Generate plain text output file.
    
    Args:
        results: List of transcription results
        output_basename: Base name for output file
        input_dir: Directory to write output file
        
    Returns:
        Path to the generated text file
    """
    output_path = input_dir / f"{output_basename}_transcription.txt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(result.text.strip())
            f.write("\n")
    
    logger.info(f"Generated text output: {output_path}")
    return output_path


def _generate_srt_output(
    results: List[TranscriptionResult],
    output_basename: str,
    input_dir: Path
) -> Path:
    """Generate SRT subtitle output file.
    
    Args:
        results: List of transcription results
        output_basename: Base name for output file
        input_dir: Directory to write output file
        
    Returns:
        Path to the generated SRT file
    """
    output_path = input_dir / f"{output_basename}.srt"
    
    subtitle_index = 1
    
    with open(output_path, "w", encoding="utf-8") as f:
        for result in results:
            if result.segments:
                for segment in result.segments:
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{_format_srt_timestamp(segment.start)} --> {_format_srt_timestamp(segment.end)}\n")
                    f.write(f"{segment.text}\n\n")
                    subtitle_index += 1
    
    logger.info(f"Generated SRT output: {output_path}")
    return output_path


def _generate_vtt_output(
    results: List[TranscriptionResult],
    output_basename: str,
    input_dir: Path
) -> Path:
    """Generate WebVTT output file.
    
    Args:
        results: List of transcription results
        output_basename: Base name for output file
        input_dir: Directory to write output file
        
    Returns:
        Path to the generated VTT file
    """
    output_path = input_dir / f"{output_basename}.vtt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        
        for result in results:
            if result.segments:
                for segment in result.segments:
                    f.write(f"{_format_vtt_timestamp(segment.start)} --> {_format_vtt_timestamp(segment.end)}\n")
                    f.write(f"{segment.text}\n\n")
    
    logger.info(f"Generated VTT output: {output_path}")
    return output_path


def _format_srt_timestamp(seconds: float) -> str:
    """Format timestamp for SRT format (HH:MM:SS,mmm).
    
    Args:
        seconds: Timestamp in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    """Format timestamp for WebVTT format (HH:MM:SS.mmm).
    
    Args:
        seconds: Timestamp in seconds
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
