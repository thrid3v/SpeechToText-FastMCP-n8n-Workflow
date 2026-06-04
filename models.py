import os
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

# Supported audio extensions
VALID_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.mp4', '.aac'}

class AudioPathMixin(BaseModel):
    """Reusable mixin for validating local system files."""
    audio_path: str = Field(..., description="The absolute path to the local audio file.")

    @field_validator("audio_path")
    @classmethod
    def validate_local_file(cls, value: str) -> str:
        # 1. Check for empty strings or whitespace
        cleaned_path = value.strip()
        if not cleaned_path:
            raise ValueError("Audio path cannot be empty or whitespace.")
        
        # 2. Check physical existence
        if not os.path.exists(cleaned_path):
            raise FileNotFoundError(f"The path '{cleaned_path}' does not exist on this machine.")
        
        # 3. Verify it's a file, not a directory
        if not os.path.isfile(cleaned_path):
            raise ValueError(f"The path '{cleaned_path}' points to a directory, not a valid file.")
        
        # 4. Check file extension support
        _, ext = os.path.splitext(cleaned_path.lower())
        if ext not in VALID_EXTENSIONS:
            raise ValueError(f"Unsupported file extension '{ext}'. Must be one of: {list(VALID_EXTENSIONS)}")
            
        return cleaned_path

# --- Tool Input Models ---

class TranscriptionRequest(AudioPathMixin):
    model_size: Literal["tiny", "base", "small", "medium", "large"] = Field(
        default="base", 
        description="The size of the Whisper model to utilize for speech processing."
    )

class LanguageDetectionRequest(AudioPathMixin):
    pass

class MetadataRequest(AudioPathMixin):
    pass

# --- Standardized Output Model ---

class MCPResult(BaseModel):
    """Standardized wrapper for all tool responses."""
    status: Literal["success", "error"]
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Serializes the response payload uniformly for MCP consumption."""
        return self.model_dump_json(exclude_none=True)