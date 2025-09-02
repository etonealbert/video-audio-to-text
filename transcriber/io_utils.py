"""Input/output utilities for safe path handling and temporary workspace management."""

from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from .types import WorkspaceProtocol

logger = logging.getLogger(__name__)


class TempWorkspace:
    """Manages a temporary workspace for file operations."""
    
    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialize a temporary workspace.
        
        Args:
            base_dir: Base directory for temp files. If None, uses system temp.
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir())
        self.workspace_id = str(uuid.uuid4())[:8]
        self.workspace_path = self.base_dir / f"transcriber_{self.workspace_id}"
        
        # Create workspace directory
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created temporary workspace: {self.workspace_path}")
    
    def get_temp_path(self, filename: str) -> Path:
        """Get a temporary file path within the workspace."""
        return self.workspace_path / filename
    
    def cleanup(self) -> None:
        """Clean up the workspace and all its contents."""
        if self.workspace_path.exists():
            try:
                shutil.rmtree(self.workspace_path)
                logger.info(f"Cleaned up workspace: {self.workspace_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up workspace {self.workspace_path}: {e}")


@contextmanager
def with_temp_workspace(base_dir: Path | None = None) -> Generator[WorkspaceProtocol, None, None]:
    """Context manager for temporary workspace.
    
    Args:
        base_dir: Base directory for temp files. If None, uses system temp.
        
    Yields:
        WorkspaceProtocol: Temporary workspace instance
    """
    workspace = TempWorkspace(base_dir)
    try:
        yield workspace
    finally:
        workspace.cleanup()


def safe_filename(name: str, max_length: int = 255) -> str:
    """Create a filesystem-safe filename.
    
    Args:
        name: Original filename
        max_length: Maximum length for the filename
        
    Returns:
        Safe filename with dangerous characters replaced
    """
    # Replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    safe_name = name
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, "_")
    
    # Truncate if too long, but preserve extension if present
    if len(safe_name) > max_length:
        if "." in safe_name:
            name_part, ext = safe_name.rsplit(".", 1)
            max_name_length = max_length - len(ext) - 1
            safe_name = name_part[:max_name_length] + "." + ext
        else:
            safe_name = safe_name[:max_length]
    
    return safe_name


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return file_path.stat().st_size
