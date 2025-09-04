"""Command-line interface for the transcriber application."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import AppConfig, load_config, validate_supported_format
from .io_utils import with_temp_workspace
from .logging_setup import setup_logging
from .media import ensure_mp3
from .splitting import split_into_chunks
from .transcribe import transcribe_chunks

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="transcriber",
        description="Transcribe audio or video files using WhisperX (GPU-accelerated) or OpenAI's Whisper API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # WhisperX (GPU-accelerated, default)
  python -m transcriber.cli audio.mp3
  python -m transcriber.cli video.mp4 --format srt --enable-alignment --enable-diarization
  python -m transcriber.cli large_file.wav --whisperx-model large-v3 --whisperx-batch-size 32
  
  # OpenAI API (legacy)
  python -m transcriber.cli audio.mp3 --backend openai --concurrency 2
  python -m transcriber.cli interview.m4a --backend openai --language en --format vtt
  
  # PCM files
  python -m transcriber.cli raw_audio.pcm --pcm-sample-rate 48000 --pcm-channels 1

Environment Variables:
  # Backend selection
  TRANSCRIPTION_BACKEND     Backend to use: "whisperx" or "openai" (default: whisperx)
  
  # OpenAI settings (when using openai backend)
  OPENAI_API_KEY            OpenAI API key (required for openai backend)
  OPENAI_MODEL              Model to use (default: gpt-4o-mini-transcribe)
  OPENAI_FALLBACK_MODEL     Fallback model (default: whisper-1)
  
  # WhisperX settings (when using whisperx backend)
  WHISPERX_MODEL            WhisperX model (default: large-v3)
  WHISPERX_DEVICE           Device: "cuda", "cpu", "auto" (default: auto)
  WHISPERX_COMPUTE_TYPE     Compute type: "int8", "float16", etc. (default: auto)
  WHISPERX_BATCH_SIZE       Batch size for inference (default: 16)
  ENABLE_ALIGNMENT          Enable word-level alignment (default: true)
  ENABLE_DIARIZATION        Enable speaker diarization (default: false)
  HF_TOKEN                  Hugging Face token (required for diarization)
  
  # Audio processing
  DEFAULT_BITRATE           Default audio bitrate (default: 128k)
  DEFAULT_MAX_CHUNK_MB      Default max chunk size (default: 24)
  DEFAULT_MIN_SILENCE_MS    Default min silence duration (default: 400)
  DEFAULT_SILENCE_THRESHOLD Default silence threshold (default: -40)
  DEFAULT_CONCURRENCY       Default concurrency level (default: 1, OpenAI only)
  
PCM File Support:
  Use --pcm-* options to specify parameters for raw PCM files.
  Common formats: s16le (16-bit signed LE), s24le (24-bit signed LE)

For more information, see the README.md file.
        """
    )
    
    # Positional arguments
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to audio or video file to transcribe"
    )
    
    # Output options
    parser.add_argument(
        "--format",
        choices=["txt", "srt", "vtt"],
        default="txt",
        help="Output format (default: txt)"
    )
    
    # Audio processing options
    parser.add_argument(
        "--bitrate",
        type=str,
        default=None,
        help="Audio bitrate for conversion (e.g., 128k, 192k)"
    )
    
    parser.add_argument(
        "--max-chunk-mb",
        type=int,
        default=None,
        help="Maximum chunk size in MB (default: 24)"
    )
    
    parser.add_argument(
        "--min-silence-ms",
        type=int,
        default=None,
        help="Minimum silence duration in milliseconds (default: 400)"
    )
    
    parser.add_argument(
        "--silence-threshold",
        type=int,
        default=None,
        help="Silence threshold in dB (default: -40)"
    )
    
    # PCM file options
    parser.add_argument(
        "--pcm-sample-rate",
        type=int,
        default=44100,
        help="Sample rate for PCM files in Hz (default: 44100)"
    )
    
    parser.add_argument(
        "--pcm-channels",
        type=int,
        default=2,
        help="Number of channels for PCM files (default: 2)"
    )
    
    parser.add_argument(
        "--pcm-bit-depth",
        type=int,
        choices=[8, 16, 24, 32],
        default=16,
        help="Bit depth for PCM files (default: 16)"
    )
    
    parser.add_argument(
        "--pcm-format",
        type=str,
        choices=["s8", "s16le", "s16be", "s24le", "s24be", "s32le", "s32be", "u8", "u16le", "u16be"],
        default="s16le",
        help="PCM format (default: s16le - signed 16-bit little-endian)"
    )
    
    # Backend selection
    parser.add_argument(
        "--backend",
        type=str,
        choices=["whisperx", "openai"],
        default=None,
        help="Transcription backend to use (default: whisperx)"
    )
    
    # Common options
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language hint for transcription (e.g., en, es, fr)"
    )
    
    # OpenAI API options (legacy)
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="OpenAI model to use (default: gpt-4o-mini-transcribe)"
    )
    
    parser.add_argument(
        "--fallback-model",
        type=str,
        default=None,
        help="Fallback model if primary model fails (default: whisper-1)"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Number of concurrent API calls for OpenAI backend (default: 1)"
    )
    
    # WhisperX options
    parser.add_argument(
        "--whisperx-model",
        type=str,
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        default=None,
        help="WhisperX model to use (default: large-v3)"
    )
    
    parser.add_argument(
        "--whisperx-device",
        type=str,
        choices=["cuda", "cpu", "auto"],
        default=None,
        help="Device for WhisperX inference (default: auto)"
    )
    
    parser.add_argument(
        "--whisperx-compute-type",
        type=str,
        choices=["int8", "int16", "float16", "float32", "auto"],
        default=None,
        help="Compute type for WhisperX (default: auto)"
    )
    
    parser.add_argument(
        "--whisperx-batch-size",
        type=int,
        default=None,
        help="Batch size for WhisperX inference (default: 16)"
    )
    
    parser.add_argument(
        "--enable-alignment",
        action="store_true",
        help="Enable word-level alignment (WhisperX only)"
    )
    
    parser.add_argument(
        "--enable-diarization",
        action="store_true",
        help="Enable speaker diarization (WhisperX only, requires HF token)"
    )
    
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face token for speaker diarization models"
    )
    
    # Logging options
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main() -> None:
    """Main entry point for the CLI application."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging early
    setup_logging(verbose=args.verbose)
    
    try:
        # Load configuration
        config = load_config(args)
        
        # Validate input file format
        if not validate_supported_format(config.input_path):
            logger.error(f"Unsupported file format: {config.input_path.suffix}")
            sys.exit(2)
        
        logger.info(f"Starting transcription of: {config.input_path}")
        logger.info(f"Output format: {config.output_format}")
        
        # Process the file using temporary workspace
        with with_temp_workspace() as workspace:
            # Convert to MP3 if needed
            mp3_path = ensure_mp3(
                input_path=config.input_path,
                bitrate=config.bitrate,
                workspace=workspace,
                max_chunk_mb=config.max_chunk_mb,
                pcm_config=config.pcm_config
            )
            
            # Split into chunks
            chunks = split_into_chunks(
                mp3_path=mp3_path,
                max_chunk_mb=config.max_chunk_mb,
                min_silence_ms=config.min_silence_ms,
                silence_threshold_db=config.silence_threshold_db,
                workspace=workspace,
                bitrate=config.bitrate
            )
            
            # Transcribe chunks and generate output
            output_path = transcribe_chunks(
                chunks=chunks,
                output_format=config.output_format,
                language=config.language,
                output_basename=config.output_basename,
                input_dir=config.input_dir,
                backend=config.backend,
                # OpenAI settings
                api_key=config.openai_api_key,
                model=config.model,
                fallback_model=config.fallback_model,
                concurrency=config.concurrency,
                # WhisperX settings
                whisperx_model=config.whisperx_model,
                whisperx_device=config.whisperx_device,
                whisperx_compute_type=config.whisperx_compute_type,
                whisperx_batch_size=config.whisperx_batch_size,
                enable_alignment=config.enable_alignment,
                enable_diarization=config.enable_diarization,
                hf_token=config.hf_token
            )
        
        print(f"Transcription completed successfully: {output_path}")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(2)
    
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(2)
    
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        sys.exit(2)
    
    except Exception as e:
        # Check if this is an API-related error
        if "rate limit" in str(e).lower() or "api" in str(e).lower():
            logger.error(f"API error: {e}")
            sys.exit(4)
        elif "conversion" in str(e).lower() or "ffmpeg" in str(e).lower():
            logger.error(f"Media processing error: {e}")
            sys.exit(3)
        else:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            sys.exit(5)


if __name__ == "__main__":
    main()
