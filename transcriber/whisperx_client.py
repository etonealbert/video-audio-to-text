"""WhisperX client with GPU acceleration, word-level alignment, and speaker diarization."""

from __future__ import annotations

import logging
import tempfile
import torch
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    import whisperx
    import gc
    HAS_WHISPERX = True
except ImportError:
    HAS_WHISPERX = False
    logger.warning("WhisperX not available. Install with: pip install whisperx")


class WhisperXError(Exception):
    """Exception raised for WhisperX-related errors."""
    pass


class WhisperXClient:
    """WhisperX client with GPU acceleration and advanced features."""
    
    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
        language: Optional[str] = None,
        enable_alignment: bool = True,
        enable_diarization: bool = False,
        hf_token: Optional[str] = None,
        batch_size: int = 16
    ):
        """Initialize the WhisperX client.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large, large-v2, large-v3)
            device: Device to use ("cuda", "cpu", or "auto")
            compute_type: Compute type ("int8", "int16", "float16", "float32", or "auto")
            language: Language code for transcription (e.g., "en", "es", "fr")
            enable_alignment: Whether to enable word-level alignment
            enable_diarization: Whether to enable speaker diarization
            hf_token: Hugging Face token for speaker diarization models
            batch_size: Batch size for inference
        """
        if not HAS_WHISPERX:
            raise WhisperXError("WhisperX is not installed. Please install with: pip install whisperx")
        
        self.model_name = model_name
        self.language = language
        self.enable_alignment = enable_alignment
        self.enable_diarization = enable_diarization
        self.hf_token = hf_token
        self.batch_size = batch_size
        
        # Auto-detect optimal device and compute type
        self.device = self._get_device(device)
        self.compute_type = self._get_compute_type(compute_type)
        
        # Initialize models (lazy loading)
        self._transcription_model = None
        self._alignment_model = None
        self._diarization_pipeline = None
        
        logger.info(f"WhisperX client initialized: model={model_name}, device={self.device}, compute_type={self.compute_type}")
    
    def _get_device(self, device: str) -> str:
        """Determine the optimal device to use."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                logger.warning("CUDA not available, falling back to CPU")
                return "cpu"
        return device
    
    def _get_compute_type(self, compute_type: str) -> str:
        """Determine the optimal compute type."""
        if compute_type == "auto":
            if self.device == "cuda":
                # Use float16 for GPU for better performance
                return "float16"
            else:
                # Use int8 for CPU for efficiency
                return "int8"
        return compute_type
    
    def _load_transcription_model(self):
        """Load the transcription model."""
        if self._transcription_model is None:
            logger.info(f"Loading transcription model: {self.model_name}")
            self._transcription_model = whisperx.load_model(
                self.model_name, 
                self.device,
                compute_type=self.compute_type,
                language=self.language
            )
    
    def _load_alignment_model(self, language: str):
        """Load the alignment model for the specified language."""
        if self.enable_alignment and self._alignment_model is None:
            logger.info(f"Loading alignment model for language: {language}")
            self._alignment_model, self._alignment_metadata = whisperx.load_align_model(
                language_code=language, 
                device=self.device
            )
    
    def _load_diarization_pipeline(self):
        """Load the speaker diarization pipeline."""
        if self.enable_diarization and self._diarization_pipeline is None:
            if not self.hf_token:
                raise WhisperXError("Hugging Face token required for speaker diarization")
            
            logger.info("Loading speaker diarization pipeline")
            self._diarization_pipeline = whisperx.DiarizationPipeline(
                use_auth_token=self.hf_token, 
                device=self.device
            )
    
    def transcribe_file(
        self,
        file_path: Path,
        language: Optional[str] = None,
        response_format: str = "verbose_json",
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Transcribe an audio file with WhisperX.
        
        Args:
            file_path: Path to the audio file
            language: Optional language hint (e.g., "en", "es", "fr")
            response_format: Response format ("text", "json", "verbose_json")
            max_retries: Maximum number of retry attempts (for compatibility)
            
        Returns:
            Transcription response compatible with OpenAI API format
            
        Raises:
            WhisperXError: If transcription fails
            FileNotFoundError: If audio file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            # Load transcription model
            self._load_transcription_model()
            
            # Use provided language or fallback to instance language
            target_language = language or self.language
            
            logger.info(f"Transcribing {file_path.name} with WhisperX")
            
            # Load and transcribe audio
            audio = whisperx.load_audio(str(file_path))
            result = self._transcription_model.transcribe(
                audio, 
                batch_size=self.batch_size,
                language=target_language
            )
            
            # Detect language if not specified
            detected_language = result.get("language", target_language or "en")
            
            # Perform alignment if enabled
            if self.enable_alignment:
                try:
                    self._load_alignment_model(detected_language)
                    result = whisperx.align(
                        result["segments"], 
                        self._alignment_model, 
                        self._alignment_metadata, 
                        audio, 
                        self.device, 
                        return_char_alignments=False
                    )
                except Exception as e:
                    logger.warning(f"Alignment failed: {e}. Continuing without alignment.")
            
            # Perform diarization if enabled
            if self.enable_diarization:
                try:
                    self._load_diarization_pipeline()
                    diarization_result = self._diarization_pipeline(audio)
                    result = whisperx.assign_word_speakers(diarization_result, result)
                except Exception as e:
                    logger.warning(f"Diarization failed: {e}. Continuing without speaker labels.")
            
            # Format response according to requested format
            return self._format_response(result, response_format, detected_language)
            
        except Exception as e:
            # Clean up GPU memory on error
            self._cleanup_gpu_memory()
            raise WhisperXError(f"Transcription failed: {e}")
    
    def transcribe_batch(
        self,
        file_paths: List[Path],
        language: Optional[str] = None,
        response_format: str = "verbose_json"
    ) -> List[Dict[str, Any]]:
        """Transcribe multiple audio files in batch for better efficiency.
        
        Args:
            file_paths: List of paths to audio files
            language: Optional language hint
            response_format: Response format
            
        Returns:
            List of transcription responses
        """
        results = []
        
        try:
            # Load model once for all files
            self._load_transcription_model()
            
            for file_path in file_paths:
                if not file_path.exists():
                    logger.warning(f"File not found, skipping: {file_path}")
                    continue
                
                result = self.transcribe_file(
                    file_path=file_path,
                    language=language,
                    response_format=response_format
                )
                results.append(result)
                
                # Periodic GPU memory cleanup
                if len(results) % 10 == 0:
                    self._cleanup_gpu_memory()
        
        except Exception as e:
            self._cleanup_gpu_memory()
            raise WhisperXError(f"Batch transcription failed: {e}")
        
        return results
    
    def _format_response(self, result: Dict[str, Any], response_format: str, language: str) -> Dict[str, Any]:
        """Format the WhisperX result to match OpenAI API format."""
        if response_format == "text":
            # Extract just the text
            segments = result.get("segments", [])
            text = " ".join(seg.get("text", "").strip() for seg in segments).strip()
            return {"text": text}
        
        elif response_format == "json":
            # Basic JSON format
            segments = result.get("segments", [])
            text = " ".join(seg.get("text", "").strip() for seg in segments).strip()
            return {
                "text": text,
                "language": language
            }
        
        else:  # verbose_json (default)
            # Full format with segments and timing
            segments = []
            for seg in result.get("segments", []):
                segment_data = {
                    "id": seg.get("id", 0),
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "text": seg.get("text", "").strip(),
                    "no_speech_prob": seg.get("no_speech_prob", 0.0),
                }
                
                # Add word-level data if available (from alignment)
                if "words" in seg:
                    segment_data["words"] = []
                    for word in seg["words"]:
                        word_data = {
                            "word": word.get("word", ""),
                            "start": word.get("start", 0.0),
                            "end": word.get("end", 0.0),
                            "probability": word.get("score", 0.0)
                        }
                        # Add speaker information if available
                        if "speaker" in word:
                            word_data["speaker"] = word["speaker"]
                        segment_data["words"].append(word_data)
                
                # Add speaker information if available (from diarization)
                if "speaker" in seg:
                    segment_data["speaker"] = seg["speaker"]
                
                segments.append(segment_data)
            
            full_text = " ".join(seg.get("text", "").strip() for seg in result.get("segments", [])).strip()
            
            return {
                "text": full_text,
                "language": language,
                "duration": result.get("duration", 0.0),
                "segments": segments
            }
    
    def _cleanup_gpu_memory(self):
        """Clean up GPU memory to prevent OOM errors."""
        if self.device == "cuda":
            torch.cuda.empty_cache()
            gc.collect()
    
    def cleanup(self):
        """Clean up models and free GPU memory."""
        logger.info("Cleaning up WhisperX models")
        
        # Delete models
        if self._transcription_model is not None:
            del self._transcription_model
            self._transcription_model = None
        
        if self._alignment_model is not None:
            del self._alignment_model
            self._alignment_model = None
        
        if self._diarization_pipeline is not None:
            del self._diarization_pipeline
            self._diarization_pipeline = None
        
        # Clean up GPU memory
        self._cleanup_gpu_memory()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass


def create_whisperx_client(
    model_name: str = "large-v3",
    device: str = "auto", 
    compute_type: str = "auto",
    language: Optional[str] = None,
    enable_alignment: bool = True,
    enable_diarization: bool = False,
    hf_token: Optional[str] = None,
    batch_size: int = 16
) -> WhisperXClient:
    """Factory function to create a WhisperX client.
    
    Args:
        model_name: Whisper model to use
        device: Device to use ("cuda", "cpu", or "auto")
        compute_type: Compute type ("int8", "int16", "float16", "float32", or "auto")
        language: Language code for transcription
        enable_alignment: Whether to enable word-level alignment
        enable_diarization: Whether to enable speaker diarization
        hf_token: Hugging Face token for diarization models
        batch_size: Batch size for inference
        
    Returns:
        Configured WhisperX client
    """
    return WhisperXClient(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        language=language,
        enable_alignment=enable_alignment,
        enable_diarization=enable_diarization,
        hf_token=hf_token,
        batch_size=batch_size
    )
