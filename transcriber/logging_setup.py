"""Logging configuration for the transcriber application."""

import logging
import sys
from typing import TextIO


def setup_logging(verbose: bool = False, stream: TextIO = sys.stderr) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: If True, set log level to INFO; otherwise WARNING
        stream: Output stream for log messages
    """
    level = logging.INFO if verbose else logging.WARNING
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=stream,
        force=True,  # Override any existing configuration
    )
    
    # Reduce noise from external libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
