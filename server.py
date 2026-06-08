import sys
import logging
from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from models import TranscriptionRequest, LanguageDetectionRequest, MetadataRequest, MCPResult
from audio_processor import AudioProcessor

# 1. Explicit Logging Configuration
# Redirecting all logging streams directly to stderr. Standard stdout MUST stay dedicated entirely to the JSON-RPC channel.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("mcp_audio_server.main")

# 2. Server Framework & Controller Initialization
mcp = FastMCP("ModularSpeechToTextServer")
processor = AudioProcessor()

# 3. MCP Unified Interface Enforcements

@mcp.tool()
def speech_to_text(audio_path: str, model_size: str = "base") -> str:
    """
    Converts a local audio file's spoken dialogue directly into structured text.
    
    Args:
        audio_path: The explicit absolute system file path to process.
        model_size: The targeted whisper variant context ('tiny', 'base', 'small', 'medium', 'large').
    """
    try:
        validated_req = TranscriptionRequest(audio_path=audio_path, model_size=model_size)
        result = processor.process_transcription(validated_req)
        return result.to_json()
    except (ValidationError, FileNotFoundError, ValueError) as err:
        logger.warning(f"Inbound input structural validation mismatch: {str(err)}")
        return MCPResult(status="error", message=f"Validation failed: {str(err)}").to_json()

@mcp.tool()
def detect_audio_language(audio_path: str) -> str:
    """
    Analyzes the structural frequencies of audio to predict the primary spoken language dialect.
    
    Args:
        audio_path: The explicit absolute system file path to analyze.
    """
    try:
        validated_req = LanguageDetectionRequest(audio_path=audio_path)
        result = processor.process_language_detection(validated_req)
        return result.to_json()
    except (ValidationError, FileNotFoundError, ValueError) as err:
        logger.warning(f"Inbound input structural validation mismatch: {str(err)}")
        return MCPResult(status="error", message=f"Validation failed: {str(err)}").to_json()
    except Exception as err:
        logger.exception(f"Unexpected error in detect_audio_language: {str(err)}")
        return MCPResult(status="error", message="Internal server error while detecting audio language.").to_json()

@mcp.tool()
def get_audio_metadata(audio_path: str) -> str:
    """
    Extracts binary structural info including length, bit rates, sample speeds and channel metrics.
    
    Args:
        audio_path: The explicit absolute system file path to examine.
    """
    try:
        validated_req = MetadataRequest(audio_path=audio_path)
        result = processor.process_metadata_extraction(validated_req)
        return result.to_json()
    except (ValidationError, FileNotFoundError, ValueError) as err:
        logger.warning(f"Inbound input structural validation mismatch: {str(err)}")
        return MCPResult(status="error", message=f"Validation failed: {str(err)}").to_json()
    except Exception as err:
        logger.exception(f"Unexpected error in get_audio_metadata: {str(err)}")
        return MCPResult(status="error", message="Internal server error while extracting audio metadata.").to_json()

if __name__ == "__main__":
    logger.info("Initializing Modular Speech-to-Text Streamable HTTP Transport Loop...")
    mcp.run(transport="streamable-http")