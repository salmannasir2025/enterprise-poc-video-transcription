# Video Transcription Tool

this is enterprise level proof of concept model, and its working, lincese MIT allowed, but for any commercial activity need permission from me.

Extract transcripts from video files in **Urdu**, **English**, and 90+ other languages using OpenAI Whisper (via `faster-whisper`).

**Now with a Streamlit GUI and YouTube support!** 🎬🌐

## Setup

1. Install ffmpeg (required for audio extraction):
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage (GUI - Recommended)

Launch the browser-based GUI with one command:

```bash
./launch_gui.sh
# or on Windows:
python -m streamlit run app.py
```

The GUI provides:
- **File picker** — select video via path or upload
- **Output directory selector** — choose where to save
- **Format checkboxes** — TXT, SRT, VTT, JSON, **Markdown**
- **Model dropdown** — all Whisper model sizes
- **Language input** — auto-detect or specify (ur, en, hi...)
- **Real-time progress bar** — track transcription progress
- **Download buttons** — get your files instantly

## Usage (CLI)

```bash
# Basic usage (auto-detects language, saves txt + srt)
python transcribe.py "video.mp4"

# Transcribe a YouTube video directly
python transcribe.py "https://youtube.com/watch?v=..." -o ./output

# Specify language explicitly (e.g., Urdu)
python transcribe.py "video.mp4" -l ur --verbose

# English with best accuracy
python transcribe.py "video.mp4" -l en --model large-v3 -v

# Custom output formats (now includes Markdown!)
python transcribe.py "video.mp4" -f txt md json srt

# All options
python transcribe.py "video.mp4" -o ./output --model large-v3 -l ur --device cpu --compute int8 -f srt vtt -v
```

## Output Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| Plain Text | `.txt` | Clean transcript, one sentence per line |
| Subtitles | `.srt` | Standard subtitle format with timestamps |
| WebVTT | `.vtt` | HTML5 video captions format |
| JSON | `.json` | Full data with timestamps and confidence scores |
| **Markdown** | `.md` | Formatted transcript with timestamps as headings |

## Options
**OR YouTube URL** 
| Flag | Description |
|------|-------------|
| `video` | Path to input video |
| `-o, --output` | Output directory (default: `transcripts/`) |
| `--model` | Model size: `tiny` → `large-v3`. Larger = more accurate, slower. |
| `-l, --language` | Language code: `ur` (Urdu), `en` (English), `hi` (Hindi). Auto-detected if omitted. |
| `--device` | `cpu`, `cuda`, or `auto` |
| `--compute` | `float16`, `int8`, `int8_float16`, or `auto` |
| `-f, --formats` | Output formats: `txt`, `srt`, `vtt`, `json`, `md` |
| `-v, --verbose` | Show progress |

## Model Recommendations

| Scenario | Model |
|-----------|-------|
| Quick tests / CPU only | `base` or `small` |
| Balanced quality/speed | `medium` |
| Best accuracy | `large-v3` |
| English-only, fast | `base.en` or `small.en` |

## Transcribe All Videos in a Folder

```bash
for f in *.mp4; do python transcribe.py "$f" -v; done
```

## ⚖️ Open-Source Disclaimer & Educational Boundary

This repository is open-sourced under the terms of the standard **MIT License**. It is a technical Proof of Concept (PoC) engineered strictly for educational research, study accessibility, and sandbox testing.

* **Operational Immunity:** This software is provided "as is", without warranty of any kind. ABT PLUS LLC (Automated Business Technologies) assumes zero liability or operational tracing responsibility for how third-party individuals deploy, configure, or utilize this script.
* **Third-Party Terms:** Users bear sole individual responsibility for ensuring that the video links, assets, and media components processed through this open-source local pipeline conform to target platform policies and content distribution frameworks.
