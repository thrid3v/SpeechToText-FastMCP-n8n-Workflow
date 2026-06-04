import pytest
from pathlib import Path
from pydantic import ValidationError

from models import AudioPathMixin, MCPResult


def test_audio_path_validator_rejects_empty_string():
    with pytest.raises(ValidationError):
        AudioPathMixin(audio_path="   ")


def test_audio_path_validator_rejects_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.mp3"
    with pytest.raises(ValidationError):
        AudioPathMixin(audio_path=str(missing))


def test_audio_path_validator_rejects_unsupported_extension(tmp_path: Path):
    unsupported = tmp_path / "audio.txt"
    unsupported.write_text("not audio")
    with pytest.raises(ValidationError):
        AudioPathMixin(audio_path=str(unsupported))


def test_mcp_result_to_json_outputs_status_and_data():
    result = MCPResult(status="success", data={"text": "hello"})
    json_payload = result.to_json()

    assert '"status":"success"' in json_payload
    assert '"text":"hello"' in json_payload
