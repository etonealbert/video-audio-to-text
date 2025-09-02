"""OpenAI client with retry logic for transcription API calls."""

from __future__ import annotations

import logging
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Exception raised for transcription-related errors."""
    pass


class OpenAITranscriptionClient:
    """OpenAI client with built-in retry logic for transcription."""
    
    def __init__(self, api_key: str, model: str = "whisper-1"):
        """Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for transcription
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def transcribe_file(
        self,
        file_path: Path,
        language: Optional[str] = None,
        response_format: str = "text",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Transcribe an audio file with retry logic.
        
        Args:
            file_path: Path to the audio file
            language: Optional language hint (e.g., "en", "es", "fr")
            response_format: Response format ("text", "json", "verbose_json")
            max_retries: Maximum number of retry attempts
            
        Returns:
            Transcription response from OpenAI API
            
        Raises:
            TranscriptionError: If transcription fails after all retries
            FileNotFoundError: If audio file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Prepare transcription parameters
        params = {
            "model": self.model,
            "response_format": response_format
        }
        
        if language:
            params["language"] = language
        
        # Execute with retry logic
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                logger.info(f"Transcribing {file_path.name} (attempt {attempt + 1})")
                
                with open(file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        file=audio_file,
                        **params
                    )
                
                # Handle different response formats
                if response_format == "text":
                    return {"text": response}
                else:
                    # For JSON formats, the response is already a dict-like object
                    return response.model_dump() if hasattr(response, 'model_dump') else dict(response)
                
            except openai.RateLimitError as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt, base_delay=60)
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Waiting {wait_time:.1f}s before retry: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TranscriptionError(f"Rate limit exceeded after {max_retries} retries: {e}")
            
            except openai.APITimeoutError as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    logger.warning(
                        f"API timeout (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Waiting {wait_time:.1f}s before retry: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TranscriptionError(f"API timeout after {max_retries} retries: {e}")
            
            except openai.APIConnectionError as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    logger.warning(
                        f"API connection error (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Waiting {wait_time:.1f}s before retry: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TranscriptionError(f"API connection failed after {max_retries} retries: {e}")
            
            except openai.InternalServerError as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    logger.warning(
                        f"Internal server error (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Waiting {wait_time:.1f}s before retry: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TranscriptionError(f"Server error after {max_retries} retries: {e}")
            
            except openai.BadRequestError as e:
                # Don't retry on bad request errors (4xx except 429)
                raise TranscriptionError(f"Bad request error: {e}")
            
            except openai.AuthenticationError as e:
                # Don't retry on authentication errors
                raise TranscriptionError(f"Authentication error: {e}")
            
            except openai.PermissionDeniedError as e:
                # Don't retry on permission errors
                raise TranscriptionError(f"Permission denied error: {e}")
            
            except Exception as e:
                if attempt < max_retries:
                    wait_time = self._calculate_backoff_time(attempt)
                    logger.warning(
                        f"Unexpected error (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Waiting {wait_time:.1f}s before retry: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    raise TranscriptionError(f"Unexpected error after {max_retries} retries: {e}")
        
        # This should never be reached, but just in case
        raise TranscriptionError("Transcription failed for unknown reason")
    
    def _calculate_backoff_time(self, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate exponential backoff time with jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            
        Returns:
            Delay time in seconds
        """
        # Exponential backoff: base_delay * 2^attempt
        exponential_delay = base_delay * (2 ** attempt)
        
        # Add jitter (±25% randomness)
        jitter = exponential_delay * 0.25 * (2 * random.random() - 1)
        
        # Cap at 60 seconds
        return min(60.0, exponential_delay + jitter)


def create_transcription_client(api_key: str, model: str = "whisper-1") -> OpenAITranscriptionClient:
    """Factory function to create a transcription client.
    
    Args:
        api_key: OpenAI API key
        model: Model to use for transcription
        
    Returns:
        Configured OpenAI transcription client
    """
    return OpenAITranscriptionClient(api_key=api_key, model=model)
