import json
import logging
import shutil
import subprocess
import threading
import whisper
from models import TranscriptionRequest, LanguageDetectionRequest, MetadataRequest, MCPResult


def _ffprobe_binary() -> str:
    """Return the installed ffprobe path or raise an informative error."""
    path = shutil.which("ffprobe")
    if path is None:
        raise EnvironmentError(
            "ffprobe is required for metadata extraction but was not found in PATH. "
            "Install ffmpeg or ensure ffprobe is available to the service."
        )
    return path


def _mediainfo(audio_path: str) -> dict:
    """
    Runs ffprobe to extract container/stream metadata.
    Drop-in replacement for pydub.utils.mediainfo — same ffprobe call,
    no dependency on audioop/pydub.
    """
    cmd = [
        _ffprobe_binary(), "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    probe = json.loads(result.stdout)

    fmt = probe.get("format", {})
    # Grab first audio stream for sample_rate / channels
    audio_stream = next(
        (s for s in probe.get("streams", []) if s.get("codec_type") == "audio"),
        None
    )
    return {
        "format_name":  fmt.get("format_name"),
        "duration":     fmt.get("duration", "0"),
        "size":         fmt.get("size", "0"),
        "bit_rate":     fmt.get("bit_rate"),
        "sample_rate":  audio_stream.get("sample_rate") if audio_stream else None,
        "channels":     audio_stream.get("channels", 1) if audio_stream else 1,
    }

logger = logging.getLogger("mcp_audio_server.processor")

class AudioProcessor:
    def __init__(self) -> None:
        # Cache models in memory to avoid redundant disk reloads across tool invocations
        self._model_cache: dict[str, whisper.Whisper] = {}
        self._model_cache_lock = threading.Lock()

    def _get_whisper_model(self, model_size: str) -> whisper.Whisper:
        """Thread-safe access pattern to the cached execution models."""
        with self._model_cache_lock:
            if model_size not in self._model_cache:
                logger.info(f"Model cache miss. Loading Whisper model: '{model_size}'...")
                self._model_cache[model_size] = whisper.load_model(model_size)
                logger.info(f"Whisper model '{model_size}' fully committed to memory.")
            return self._model_cache[model_size]

    def process_transcription(self, request: TranscriptionRequest) -> MCPResult:
        """Transcribes the file down to plain text."""
        try:
            model = self._get_whisper_model(request.model_size)
            logger.info(f"Starting audio transcription for: {request.audio_path}")
            
            result = model.transcribe(request.audio_path)
            
            return MCPResult(
                status="success",
                data={
                    "text": result["text"].strip(),
                    "language": result.get("language", "unknown")
                }
            )
        except Exception as e:
            logger.error(f"Failed transcription routine: {str(e)}", exc_info=True)
            return MCPResult(status="error", message=f"Transcription failed: {str(e)}")

    def process_language_detection(self, request: LanguageDetectionRequest) -> MCPResult:
        """Inspects the initial 30 seconds of audio to evaluate spoken language."""
        try:
            model = self._get_whisper_model("base")
            logger.info(f"Sampling audio headers for language detection: {request.audio_path}")
            
            audio = whisper.load_audio(request.audio_path)
            audio = whisper.pad_or_trim(audio)
            
            mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)
            _, probabilities = model.detect_language(mel)
            detected_lang = max(probabilities, key=probabilities.get)
            
            return MCPResult(
                status="success",
                data={
                    "detected_language": detected_lang,
                    "confidence_score": round(probabilities[detected_lang], 4)
                }
            )
        except Exception as e:
            logger.error(f"Failed language determination routine: {str(e)}", exc_info=True)
            return MCPResult(status="error", message=f"Language detection failed: {str(e)}")

    def process_metadata_extraction(self, request: MetadataRequest) -> MCPResult:
        """Extracts low-level structural formatting parameters from file containers."""
        try:
            logger.info(f"Extracting media container specs for: {request.audio_path}")
            info = _mediainfo(request.audio_path)
            
            extracted_specs = {
                "format_name": info.get("format_name"),
                "duration_seconds": round(float(info.get("duration", 0)), 2),
                "size_bytes": int(info.get("size", 0)),
                "bit_rate": info.get("bit_rate"),
                "sample_rate": info.get("sample_rate"),
                "channels": int(info.get("channels", 1))
            }
            return MCPResult(status="success", data=extracted_specs)
        except Exception as e:
            logger.error(f"Failed metadata validation: {str(e)}", exc_info=True)
            return MCPResult(status="error", message=f"Metadata extraction failed: {str(e)}")