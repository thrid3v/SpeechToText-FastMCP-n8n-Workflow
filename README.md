# 🎙️ MCP Audio Server

A **Model Context Protocol (MCP)** server that gives AI agents the ability to process audio files — transcribe speech to text, detect spoken languages, and extract audio metadata. Built with [OpenAI Whisper](https://github.com/openai/whisper) and served over **Streamable HTTP** transport for seamless integration with any MCP-compatible client.

---

## ✨ Features

| Tool | Description |
|---|---|
| **`speech_to_text`** | Transcribes spoken dialogue from an audio file into structured text using Whisper |
| **`detect_audio_language`** | Analyzes the first 30 seconds of audio to predict the primary spoken language with a confidence score |
| **`get_audio_metadata`** | Extracts technical specs — duration, bitrate, sample rate, channels, format, and file size via `ffprobe` |

### Highlights

- 🧠 **Thread-safe model caching** — Whisper models are loaded once and reused across requests
- 🔒 **Strict input validation** — All inputs are validated with Pydantic (file existence, extension support, model size)
- 📡 **Streamable HTTP transport** — stateless HTTP transport accessible by any MCP client over the network
- 🎛️ **Multiple Whisper models** — Choose from `tiny`, `base`, `small`, `medium`, or `large` depending on accuracy/speed tradeoff
- 🎵 **Wide format support** — `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.mp4`, `.aac`

---

## 📁 Project Structure

```
mcp-audio-server/
├── server.py              # MCP server entry point — registers tools, runs Streamable HTTP transport
├── audio_processor.py     # Core processing logic — transcription, language detection, metadata
├── models.py              # Pydantic models — request validation & standardized response format
├── requirements.txt       # Python dependencies
├── speech-text-MCP.json   # Pre-built n8n workflow for AI agent integration
└── tests/
    └── test_models.py     # Unit tests for input validation and response serialization
```

---

## 🛠️ Prerequisites

- **Python 3.10+**
- **ffmpeg** (required for audio metadata extraction and Whisper audio loading)
  - Windows: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`
- **GPU (optional)** — Whisper will use CUDA if available, otherwise falls back to CPU

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/mcp-audio-server.git
cd mcp-audio-server
```

### 2. Create a virtual environment and install dependencies

Using `uv` (recommended):

```bash
uv venv
uv pip install -r requirements.txt
```

Or with standard `pip`:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Start the server

```bash
python server.py
```

The server starts on **`http://127.0.0.1:8000`** with the following endpoint:

| Endpoint | Purpose |
|---|---|
| `http://127.0.0.1:8000/mcp` | Streamable HTTP endpoint for MCP clients |

---

## 🧪 Testing

### MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is the easiest way to test the server interactively:

```bash
npx @modelcontextprotocol/inspector
```

1. Open the Inspector UI in your browser
2. Set **Transport Type** → `Streamable HTTP`
3. Set **URL** → `http://127.0.0.1:8000/mcp`
4. Click **Connect**
5. Select any tool and provide an absolute path to an audio file

### Unit Tests

```bash
pytest tests/ -v
```

---

## 🔌 Integration

### n8n Workflow

A pre-built [n8n](https://n8n.io) workflow is included in [`speech-text-MCP.json`](speech-text-MCP.json). It sets up a complete AI agent pipeline:

```
Chat Trigger → AI Agent → Google Gemini LLM
                  ↕              ↕
            MCP Client     Buffer Memory
        (this server)
```

**To import:**
1. Start n8n (`npx n8n`)
2. Go to **Workflows** → **Import from File**
3. Select `speech-text-MCP.json`
4. Configure your Google Gemini API credentials in the **Google Gemini Chat Model** node
5. Ensure this MCP server is running on `http://127.0.0.1:8000`
6. Activate the workflow and start chatting — the AI agent can now transcribe audio, detect languages, and extract metadata on demand

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "audio-server": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

### Any MCP Client

Connect to `http://127.0.0.1:8000/mcp` using any MCP-compatible client that supports Streamable HTTP. The server exposes three tools that are automatically discoverable through the MCP protocol.

---

## 📖 API Reference

### `speech_to_text`

Transcribes audio to text using OpenAI Whisper.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `audio_path` | `string` | *required* | Absolute path to the audio file |
| `model_size` | `string` | `"base"` | Whisper model variant: `tiny`, `base`, `small`, `medium`, `large` |

**Response:**
```json
{
  "status": "success",
  "data": {
    "text": "The transcribed text content...",
    "language": "en"
  }
}
```

---

### `detect_audio_language`

Identifies the spoken language from the first 30 seconds of audio.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `audio_path` | `string` | *required* | Absolute path to the audio file |

**Response:**
```json
{
  "status": "success",
  "data": {
    "detected_language": "en",
    "confidence_score": 0.9847
  }
}
```

---

### `get_audio_metadata`

Extracts technical metadata using `ffprobe`.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `audio_path` | `string` | *required* | Absolute path to the audio file |

**Response:**
```json
{
  "status": "success",
  "data": {
    "format_name": "mp3",
    "duration_seconds": 245.67,
    "size_bytes": 3932160,
    "bit_rate": "128000",
    "sample_rate": "44100",
    "channels": 2
  }
}
```

---

### Error Response

All tools return a standardized error format on failure:

```json
{
  "status": "error",
  "message": "Validation failed: The path '/bad/path.mp3' does not exist on this machine."
}
```

---

## ⚙️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Client                          │
│         (Claude, n8n, Inspector, etc.)                  │
└──────────────────────┬──────────────────────────────────┘
                       │ Streamable HTTP
                       ▼
┌──────────────────────────────────────────────────────────┐
│  server.py — FastMCP Server                              │
│  ┌────────────────┬──────────────────┬────────────────┐  │
│  │ speech_to_text │ detect_language   │ get_metadata   │  │
│  └───────┬────────┴────────┬─────────┴───────┬────────┘  │
│          │                 │                 │            │
│          ▼                 ▼                 ▼            │
│  ┌───────────────────────────────────────────────────┐   │
│  │  models.py — Pydantic Validation Layer            │   │
│  │  (AudioPathMixin, TranscriptionRequest, etc.)     │   │
│  └───────────────────────┬───────────────────────────┘   │
│                          ▼                               │
│  ┌───────────────────────────────────────────────────┐   │
│  │  audio_processor.py — Processing Engine           │   │
│  │  ┌─────────────┐  ┌───────────┐  ┌────────────┐  │   │
│  │  │   Whisper    │  │  Whisper   │  │  ffprobe   │  │   │
│  │  │ transcribe() │  │ detect()  │  │  metadata  │  │   │
│  │  └─────────────┘  └───────────┘  └────────────┘  │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 📝 License

This project is open source. See [LICENSE](LICENSE) for details.
