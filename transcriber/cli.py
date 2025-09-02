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
        description="Transcribe audio or video files using OpenAI's Whisper API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m transcriber.cli audio.mp3
  python -m transcriber.cli video.mp4 --format srt --verbose
  python -m transcriber.cli large_file.wav --max-chunk-mb 20 --concurrency 2
  python -m transcriber.cli interview.m4a --language en --format vtt

Environment Variables:
  OPENAI_API_KEY            OpenAI API key (required)
  OPENAI_MODEL              Model to use (default: whisper-1)
  DEFAULT_BITRATE           Default audio bitrate (default: 128k)
  DEFAULT_MAX_CHUNK_MB      Default max chunk size (default: 24)
  DEFAULT_MIN_SILENCE_MS    Default min silence duration (default: 400)
  DEFAULT_SILENCE_THRESHOLD Default silence threshold (default: -40)
  DEFAULT_CONCURRENCY       Default concurrency level (default: 1)

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
    
    # API options
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language hint for transcription (e.g., en, es, fr)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="OpenAI model to use (default: whisper-1)"
    )
    
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Number of concurrent API calls (default: 1)"
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
                max_chunk_mb=config.max_chunk_mb
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
                model=config.model,
                concurrency=config.concurrency,
                output_basename=config.output_basename,
                input_dir=config.input_dir,
                api_key=config.openai_api_key
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
