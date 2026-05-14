#!/usr/bin/env python3
"""
Video Transcription Tool
Extracts transcripts from video files in various languages (Urdu, English, etc.)
Uses faster-whisper for efficient, accurate multilingual speech-to-text.
"""

import argparse
import os
import sys
import subprocess
import json
import re
import requests
from pathlib import Path
from datetime import timedelta

# Fix for OpenMP duplicate library error on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Error: faster-whisper not installed. Run: pip install faster-whisper")
    sys.exit(1)


def is_youtube_url(url: str) -> bool:
    """Check if string is a YouTube URL."""
    if not url:
        return False
    youtube_patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?',
        r'^https?://(?:www\.)?youtube\.com/shorts/',
        r'^https?://youtu\.be/',
        r'^https?://(?:www\.)?youtube\.com/embed/',
    ]
    import re
    return any(re.match(pattern, url.strip(), re.IGNORECASE) for pattern in youtube_patterns)


def download_youtube_video(url: str, output_dir: str, progress_callback=None) -> str:
    """
    Download a YouTube video using yt-dlp.
    Returns path to downloaded video file.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")

    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s_%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    if progress_callback:
        progress_callback("downloading", 5, f"Downloading YouTube video...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info)

    # Handle case where extension might differ
    if not os.path.exists(video_path) and info.get('ext') != 'mp4':
        alt_path = video_path.rsplit('.', 1)[0] + '.mp4'
        if os.path.exists(alt_path):
            video_path = alt_path

    if progress_callback:
        progress_callback("downloading", 10, f"Download complete: {os.path.basename(video_path)}")

    return video_path


def extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio from video using ffmpeg."""
    if os.path.exists(audio_path):
        os.remove(audio_path)

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",                # no video
        "-acodec", "pcm_s16le",  # PCM 16-bit little-endian
        "-ar", "16000",       # 16kHz (Whisper optimal)
        "-ac", "1",           # mono
        "-y",                 # overwrite
        audio_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT/VTT timestamp format."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Convert seconds to VTT timestamp format."""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


def write_txt(segments, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg.text.strip() + "\n")


def write_srt(segments, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            f.write(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n\n")


def write_vtt(segments, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = format_timestamp_vtt(seg.start)
            end = format_timestamp_vtt(seg.end)
            f.write(f"{start} --> {end}\n{seg.text.strip()}\n\n")


def write_json(segments, info, output_path: str) -> None:
    data = {
        "language": info.language,
        "language_probability": info.language_probability,
        "segments": [
            {
                "id": i,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "confidence": float(getattr(seg, 'avg_logprob', 0.0) or 0.0),
            }
            for i, seg in enumerate(segments)
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_md(segments, info, output_path: str) -> None:
    """Write transcript as Markdown with timestamps as headings."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcript\n\n")
        f.write(f"**Language:** {info.language}  \n")
        f.write(f"**Confidence:** {info.language_probability:.1%}\n\n")
        f.write("---\n\n")
        for seg in segments:
            start = format_timestamp(seg.start)
            end = format_timestamp(seg.end)
            f.write(f"## {start} → {end}\n\n")
            f.write(f"{seg.text.strip()}\n\n")


def search_youtube_videos(query: str, max_results: int = 10) -> list:
    """Search YouTube videos by title and return results."""
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Search for videos
            search_url = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_url, download=False)
            
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    if entry.get('title') and entry.get('url'):
                        results.append({
                            'title': entry['title'],
                            'url': entry['url'],
                            'duration': entry.get('duration', 0),
                            'uploader': entry.get('uploader', 'Unknown'),
                            'thumbnail': entry.get('thumbnail', ''),
                            'view_count': entry.get('view_count', 0),
                            'id': entry.get('id', ''),
                        })
            
            return results
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []


def is_facebook_url(url: str) -> bool:
    """Check if string is a Facebook URL."""
    if not url:
        return False
    facebook_patterns = [
        r'^https?://(?:www\.)?facebook\.com/',
        r'^https?://(?:www\.)?fb\.watch/',
        r'^https?://(?:www\.)?m\.facebook\.com/',
    ]
    return any(re.match(pattern, url.strip(), re.IGNORECASE) for pattern in facebook_patterns)


def download_facebook_video(url: str, output_dir: str, progress_callback=None) -> str:
    """Download a Facebook video using requests and yt-dlp."""
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")
    
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': not progress_callback,
        'no_warnings': True,
    }
    
    if progress_callback:
        ydl_opts['progress_hooks'] = [lambda d: progress_callback("downloading", d.get('percent', 0), f"Downloading: {d.get('filename', 'video')}")]
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            # Find the downloaded file
            for file in os.listdir(output_dir):
                if info['title'] in file:
                    return os.path.join(output_dir, file)
            return None
        except Exception as e:
            raise Exception(f"Failed to download Facebook video: {e}")


def get_video_info(url: str) -> dict:
    """Get video information without downloading."""
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0),
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
            }
        except Exception as e:
            raise Exception(f"Failed to get video info: {e}")


def transcribe(
    video_path: str,
    output_dir: str = "transcripts",
    model_size: str = "base",
    language: str = None,
    device: str = "auto",
    compute_type: str = "auto",
    formats: list = None,
    verbose: bool = False,
    progress_callback=None,
) -> dict:
    """
    Transcribe a video file and save outputs. Also accepts YouTube URLs.

    Args:
        video_path: Path to input video OR YouTube URL.
        output_dir: Directory to save transcript files.
        model_size: Whisper model size (tiny, base, small, medium, large-v3).
        language: Language code (e.g., 'ur', 'en'). Auto-detected if None.
        device: 'cpu', 'cuda', or 'auto'.
        compute_type: 'float16', 'int8', 'int8_float16', or 'auto'.
        formats: List of output formats ['txt', 'srt', 'vtt', 'json', 'md'].
        verbose: Print progress.
        progress_callback: Optional callback function(step, progress_pct, message).

    Returns:
        Dict with 'language', 'language_probability', 'segments', 'output_files', 'downloaded_video'.
    """
    if formats is None:
        formats = ["txt", "srt"]

    downloaded_video = None

    # Check if input is an online URL
    if is_youtube_url(video_path):
        video_path = download_youtube_video(video_path, output_dir, progress_callback)
        downloaded_video = video_path
    elif is_facebook_url(video_path):
        video_path = download_facebook_video(video_path, output_dir, progress_callback)
        downloaded_video = video_path
    else:
        video_path = os.path.abspath(video_path)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(video_path).stem

    # Extract audio to temp WAV
    audio_path = os.path.join(output_dir, f"{base_name}_temp.wav")
    if progress_callback:
        progress_callback("extracting", 10, f"Extracting audio from: {Path(video_path).name}")
    if verbose:
        print(f"Extracting audio from: {Path(video_path).name}")
    extract_audio(video_path, audio_path)

    # Load model
    if progress_callback:
        progress_callback("loading", 20, f"Loading Whisper model: {model_size}")
    if verbose:
        print(f"Loading Whisper model: {model_size} (device={device}, compute={compute_type})")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # Transcribe
    if progress_callback:
        progress_callback("transcribing", 30, "Transcribing... (this may take a while)")
    if verbose:
        print("Transcribing... (this may take a while)")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        best_of=5,
        condition_on_previous_text=True,
    )

    # Materialize segments with progress
    collected_segments = []
    for i, seg in enumerate(segments):
        collected_segments.append(seg)
        if progress_callback and i % 5 == 0:
            pct = min(30 + int((i / 100) * 60), 90)
            progress_callback("transcribing", pct, f"Transcribing segment {i+1}...")
    segments = collected_segments

    if progress_callback:
        progress_callback("transcribing", 90, f"Transcription complete: {len(segments)} segments")

    if progress_callback:
        progress_callback("saving", 95, f"Detected language: {info.language} ({info.language_probability:.1%} confidence)")
    if verbose:
        detected = info.language
        prob = info.language_probability
        print(f"Detected language: {detected} (confidence: {prob:.2%})")
        print(f"Segments found: {len(segments)}")

    # Write outputs
    output_files = []
    for fmt in formats:
        out_path = os.path.join(output_dir, f"{base_name}.{fmt}")
        if fmt == "txt":
            write_txt(segments, out_path)
        elif fmt == "srt":
            write_srt(segments, out_path)
        elif fmt == "vtt":
            write_vtt(segments, out_path)
        elif fmt == "json":
            write_json(segments, info, out_path)
        elif fmt == "md":
            write_md(segments, info, out_path)
        output_files.append(out_path)
        if verbose:
            print(f"Saved: {out_path}")

    # Cleanup temp audio
    os.remove(audio_path)
    if progress_callback:
        progress_callback("done", 100, "Done!")
    if verbose:
        print("Done.")

    return {
        "language": info.language,
        "language_probability": info.language_probability,
        "segments": [
            {
                "id": i,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            }
            for i, seg in enumerate(segments)
        ],
        "output_files": output_files,
        "downloaded_video": downloaded_video,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe videos to text using faster-whisper. Supports Urdu, English, and 90+ languages. Also supports YouTube URLs."
    )
    parser.add_argument("video", help="Path to video file OR YouTube URL (e.g., https://youtube.com/watch?v=...)")
    parser.add_argument("-o", "--output", default="transcripts", help="Output directory")
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo"],
        help="Whisper model size. Use 'base' for speed, 'large-v3' for accuracy.",
    )
    parser.add_argument("-l", "--language", default=None, help="Language code (e.g., ur, en, hi). Auto-detected if omitted.")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Compute device")
    parser.add_argument("--compute", default="auto", choices=["auto", "float16", "int8", "int8_float16"], help="Compute type")
    parser.add_argument("-f", "--formats", nargs="+", default=["txt", "srt"], choices=["txt", "srt", "vtt", "json", "md"], help="Output formats")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    transcribe(
        video_path=args.video,
        output_dir=args.output,
        model_size=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute,
        formats=args.formats,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
