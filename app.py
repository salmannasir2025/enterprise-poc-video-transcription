#!/usr/bin/env python3
"""
Video Transcription GUI
Streamlit-based web interface for transcribing videos using faster-whisper.
"""

import os
import sys
import shutil
from pathlib import Path

# Fix for OpenMP duplicate library error on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st

# Page config
st.set_page_config(
    page_title="Video Transcription",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Check for faster-whisper
try:
    from transcribe import transcribe, write_txt, write_srt, write_vtt, write_json, write_md, is_youtube_url, is_facebook_url
except ImportError as e:
    st.error(f"Error importing transcription module: {e}")
    st.info("Please install dependencies: `pip install -r requirements.txt`")
    st.stop()


def get_folder_dialog(initial_dir: str = None) -> str:
    """Open a native folder picker dialog using tkinter (lazy-loaded)."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring dialog to front
    folder = filedialog.askdirectory(initialdir=initial_dir or str(Path.home()))
    root.destroy()
    return folder


def find_video_files(directory: str) -> list:
    """Find all video files in a directory."""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.3gp', '.flv', '.wmv', '.mpg', '.mpeg'}
    video_files = []
    dir_path = Path(directory)
    if dir_path.exists() and dir_path.is_dir():
        for file in dir_path.iterdir():
            if file.is_file() and file.suffix.lower() in video_extensions:
                video_files.append(str(file))
    return sorted(video_files)


def main():
    if os.path.exists("logo.png"):
        st.image("logo.png", width=300)
    st.title("🎬 Video Transcription Tool")
    st.markdown("Extract transcripts from videos in **Urdu**, **English**, and 90+ other languages.")
    st.markdown("🌐 **Now with YouTube support!** Just paste a YouTube URL and get your transcript.")
    st.markdown("---")

    # Check ffmpeg
    import subprocess
    ffmpeg_available = subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0
    if not ffmpeg_available:
        st.error("⚠️ **ffmpeg not found**. Please install it:")
        st.code("brew install ffmpeg  # macOS\nsudo apt install ffmpeg  # Ubuntu/Debian")
        st.stop()
    
    # Check yt-dlp (for YouTube support)
    try:
        import yt_dlp
    except ImportError:
        yt_dlp = None

    # --- Input Section ---
    st.subheader("1. Select Video Source")
    
    # Input method tabs
    input_method = st.radio(
        "Choose input method:",
        options=["Local File", "Online Video URL", "Upload File", "Batch Mode", "Search & Download"],
        horizontal=True,
        index=0,
    )
    
    video_path = None
    temp_video_path = None
    is_online_url = False
    
    if input_method == "Local File":
        if not yt_dlp:
            st.warning("⚠️ **yt-dlp not installed**. YouTube support requires it. Run: `pip install yt-dlp`")
        video_path = st.text_input(
            "Video file path",
            placeholder="/path/to/your/video.mp4",
            help="Enter the full path to your video file on disk",
        )
    elif input_method == "Online Video URL":
        video_path = st.text_input(
            "Video URL",
            placeholder="https://youtube.com/... or https://facebook.com/...",
            help="Paste a YouTube or Facebook video URL",
        )
        
        is_youtube = False
        is_facebook = False
        
        if video_path:
            if is_youtube_url(video_path):
                is_online_url = True
                is_youtube = True
                st.success("✅ Valid YouTube URL detected")
            elif is_facebook_url(video_path):
                is_online_url = True
                is_facebook = True
                st.success("✅ Valid Facebook URL detected")
            else:
                st.warning("⚠️ Doesn't look like a valid YouTube or Facebook URL")
                
        if is_online_url:
            st.markdown("---")
            st.markdown("**Optional: Download Video**")
            st.markdown("You can download the video to your Videos folder without transcribing it.")
            
            if st.button("⬇️ Download Video Only", type="secondary"):
                import datetime
                
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                download_dir = Path.home() / "Videos" / date_str
                download_dir.mkdir(parents=True, exist_ok=True)
                
                with st.spinner(f"Downloading video to {download_dir}..."):
                    try:
                        if is_youtube:
                            from transcribe import download_youtube_video
                            downloaded_path = download_youtube_video(video_path, str(download_dir))
                        else:
                            from transcribe import download_facebook_video
                            downloaded_path = download_facebook_video(video_path, str(download_dir))
                        
                        if downloaded_path:
                            st.success(f"✅ Video downloaded successfully to:\n`{downloaded_path}`")
                            st.balloons()
                        else:
                            st.error("❌ Failed to download video.")
                    except Exception as e:
                        st.error(f"❌ Error downloading video: {e}")
                        
    elif input_method == "Batch Mode":
        st.markdown("**Select a folder containing video files:**")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            batch_folder = st.text_input(
                "Folder path",
                placeholder="/path/to/your/video/folder",
                help="Enter the path to a folder containing video files",
            )
        
        with col2:
            st.markdown("&nbsp;")
            if st.button("📁 Browse...", use_container_width=True, type="secondary"):
                try:
                    selected_folder = get_folder_dialog(initial_dir=batch_folder or str(Path.home()))
                    if selected_folder:
                        batch_folder = selected_folder
                        st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ Folder picker not available: {e}")
                    st.info("Please type the path manually in the text field.")
        
        # Find and display video files
        video_files = []
        if batch_folder:
            video_files = find_video_files(batch_folder)
            if video_files:
                st.success(f"Found {len(video_files)} video file(s)")
                with st.expander("📋 Video files to process", expanded=True):
                    for i, video_file in enumerate(video_files, 1):
                        st.write(f"{i}. {Path(video_file).name}")
            else:
                st.warning("No video files found in the selected folder")
        
        video_path = video_files  # Store list of videos for batch processing
    
    elif input_method == "Search & Download":
        st.markdown("**Search for videos or paste a URL:**")
        
        # Search input
        search_query = st.text_input(
            "Search videos or paste URL",
            placeholder="Enter video title or YouTube/Facebook URL",
            help="Search YouTube by title or paste direct video URLs",
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            max_results = st.slider(
                "Max search results",
                min_value=5,
                max_value=20,
                value=10,
                help="Maximum number of search results to show"
            )
        
        with col2:
            if st.button("🔍 Search", type="primary", use_container_width=True):
                if search_query:
                    with st.spinner("Searching..."):
                        try:
                            if is_youtube_url(search_query):
                                # Direct YouTube URL
                                video_info = get_video_info(search_query)
                                search_results = [video_info] if video_info else []
                            elif is_facebook_url(search_query):
                                # Direct Facebook URL
                                video_info = get_video_info(search_query)
                                search_results = [video_info] if video_info else []
                            else:
                                # Search by title
                                from transcribe import search_youtube_videos
                                search_results = search_youtube_videos(search_query, max_results)
                            
                            st.session_state.search_results = search_results
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Search failed: {e}")
        
        # Display search results
        if 'search_results' in st.session_state and st.session_state.search_results:
            search_results = st.session_state.search_results
            
            if search_results:
                st.success(f"Found {len(search_results)} video(s)")
                
                # Video selection
                selected_videos = []
                for i, video in enumerate(search_results):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        selected = st.checkbox(
                            f"Select",
                            key=f"select_video_{i}",
                            value=True,
                        )
                        if selected:
                            selected_videos.append(video)
                    
                    with col2:
                        # Display video info
                        if video.get('thumbnail'):
                            st.image(video['thumbnail'], width=120)
                        
                        st.markdown(f"**{video.get('title', 'Unknown Title')}**")
                        
                        # Video metadata
                        metadata_cols = st.columns(3)
                        with metadata_cols[0]:
                            if video.get('duration'):
                                minutes = int(video['duration'] // 60)
                                seconds = int(video['duration'] % 60)
                                st.metric("Duration", f"{minutes}:{seconds:02d}")
                        with metadata_cols[1]:
                            st.metric("Uploader", video.get('uploader', 'Unknown'))
                        with metadata_cols[2]:
                            if video.get('view_count'):
                                views = video['view_count']
                                st.metric("Views", f"{views:,}" if views else "N/A")
                        
                        st.markdown("---")
                
                # Download and transcribe button
                if selected_videos:
                    st.markdown(f"**{len(selected_videos)} video(s) selected**")
                    if st.button("⬇️ Download & Transcribe", type="primary", use_container_width=True):
                        # Download selected videos
                        temp_dir = Path("temp_downloads")
                        temp_dir.mkdir(exist_ok=True)
                        
                        downloaded_videos = []
                        for video in selected_videos:
                            try:
                                with st.spinner(f"Downloading {video['title']}..."):
                                    if 'youtube.com' in video['url'] or 'youtu.be' in video['url']:
                                        from transcribe import download_youtube_video
                                        downloaded_path = download_youtube_video(
                                            video['url'], 
                                            str(temp_dir),
                                            progress_callback=lambda step, pct, msg: None
                                        )
                                    else:
                                        from transcribe import download_facebook_video
                                        downloaded_path = download_facebook_video(
                                            video['url'],
                                            str(temp_dir),
                                            progress_callback=lambda step, pct, msg: None
                                        )
                                    
                                    if downloaded_path:
                                        downloaded_videos.append(downloaded_path)
                                        st.success(f"✅ Downloaded: {video['title']}")
                            except Exception as e:
                                st.error(f"❌ Failed to download {video['title']}: {e}")
                        
                        # Set video_path for transcription
                        video_path = downloaded_videos
            else:
                st.warning("No videos found. Try different search terms.")
        
        # Clear results button
        if 'search_results' in st.session_state:
            if st.button("🗑️ Clear Results", use_container_width=True):
                del st.session_state.search_results
                st.rerun()
    else:  # Upload File
        uploaded_file = st.file_uploader(
            "Upload a video file (limited to 200MB by Streamlit)",
            type=["mp4", "mov", "avi", "mkv", "webm", "m4v", "3gp"],
        )
        if uploaded_file is not None:
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_video_path = temp_dir / uploaded_file.name
            with open(temp_video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            video_path = str(temp_video_path)
            st.success(f"Uploaded: {uploaded_file.name}")

    st.markdown("---")

    # --- Output Settings ---
    st.subheader("2. Output Settings")
    
    # Get project output directory as default
    project_dir = Path(__file__).parent
    default_output = str(project_dir / "output")
    
    # Initialize session state for output directory
    if "output_dir" not in st.session_state:
        st.session_state.output_dir = default_output
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        output_dir = st.text_input(
            "Output directory",
            value=st.session_state.output_dir,
            help="Where to save the transcript files",
        )
        # Update session state when text input changes
        st.session_state.output_dir = output_dir
    
    with col2:
        st.markdown("&nbsp;")
        if st.button("📁 Browse...", use_container_width=True, type="secondary"):
            try:
                selected_folder = get_folder_dialog(initial_dir=st.session_state.output_dir)
                if selected_folder:
                    st.session_state.output_dir = selected_folder
                    st.rerun()
            except Exception as e:
                st.warning(f"⚠️ Folder picker not available: {e}")
                st.info("Please type the path manually in the text field.")

    # Format selection
    st.markdown("**Output formats:**")
    cols = st.columns(5)
    formats = []
    format_options = [
        ("txt", "Plain Text"),
        ("srt", "Subtitles (SRT)"),
        ("vtt", "WebVTT"),
        ("json", "JSON"),
        ("md", "Markdown"),
    ]
    for i, (fmt, label) in enumerate(format_options):
        with cols[i]:
            if st.checkbox(label, value=(fmt in ["txt", "srt"]), key=f"fmt_{fmt}"):
                formats.append(fmt)

    st.markdown("---")

    # --- Model Settings ---
    st.subheader("3. Model Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        model_size = st.selectbox(
            "Model size",
            options=["tiny", "tiny.en", "base", "base.en", "small", "small.en", 
                     "medium", "medium.en", "large-v1", "large-v2", "large-v3", "large-v3-turbo"],
            index=2,  # base as default
            help="Larger models = more accurate but slower. Use .en variants for English-only.",
        )
    
    with col2:
        language = st.text_input(
            "Language code (optional)",
            placeholder="ur, en, hi, etc. (leave empty for auto-detect)",
            help="Examples: ur (Urdu), en (English), hi (Hindi). Leave empty to auto-detect.",
        )
        if language.strip() == "":
            language = None

    # Advanced options
    with st.expander("Advanced settings"):
        device = st.selectbox(
            "Compute device",
            options=["auto", "cpu", "cuda"],
            index=0,
            help="Use 'cuda' for NVIDIA GPU if available",
        )
        compute_type = st.selectbox(
            "Compute type",
            options=["auto", "float16", "int8", "int8_float16"],
            index=0,
            help="int8 is faster on CPU, float16 for GPU",
        )

    st.markdown("---")

    # --- Transcribe Button ---
    st.subheader("4. Transcribe")
    
    if not video_path:
        st.info("⬆️ Please provide a video source above")
        st.stop()
    
    # Validate input - skip file existence check for online URLs
    if input_method not in ["Batch Mode", "Search & Download"]:
        if not is_online_url and not os.path.exists(video_path):
            st.error("❌ Video file not found. Please check the path.")
            st.stop()
    if input_method == "Batch Mode":
        # Batch mode validation
        if not video_path:  # video_path is a list in batch mode
            st.error("❌ Please select a folder with video files.")
            st.stop()
        if not isinstance(video_path, list):
            st.error("❌ Invalid video files list.")
            st.stop()
    elif input_method == "Search & Download":
        # Search & Download mode validation
        if not video_path:  # video_path is a list in search mode
            st.error("❌ Please search and select videos to download.")
            st.stop()
        if not isinstance(video_path, list):
            st.error("❌ Invalid video selection.")
            st.stop()

    if not formats:
        st.warning("⚠️ Please select at least one output format")
        st.stop()

    # Progress tracking
    progress_bar = st.progress(0, text="Ready")
    status_text = st.empty()
    
    def progress_callback(step, pct, message):
        progress_bar.progress(pct / 100, text=f"{step.title()}: {message}")
        status_text.info(f"**{step.title()}** — {message}")

    # Transcribe button
    if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
        try:
            if input_method == "Batch Mode":
                # Batch processing
                batch_results = []
                total_videos = len(video_path)
                
                for idx, current_video in enumerate(video_path, 1):
                    # Check if already transcribed
                    video_name = Path(current_video).stem
                    already_transcribed = False
                    for fmt in formats:
                        output_file = Path(output_dir) / f"{video_name}.{fmt}"
                        if output_file.exists():
                            already_transcribed = True
                            break
                    
                    if already_transcribed:
                        st.info(f"⏭️ Skipping {Path(current_video).name} (already transcribed)")
                        continue
                    
                    # Update progress for overall batch
                    overall_pct = int(((idx - 1) / total_videos) * 100)
                    progress_bar.progress(overall_pct / 100, text=f"Processing video {idx}/{total_videos}")
                    status_text.info(f"**Video {idx}/{total_videos}** — Processing: {Path(current_video).name}")
                    
                    # Transcribe current video
                    with st.spinner(f"Transcribing {Path(current_video).name}..."):
                        result = transcribe(
                            video_path=current_video,
                            output_dir=output_dir,
                            model_size=model_size,
                            language=language,
                            device=device,
                            compute_type=compute_type,
                            formats=formats,
                            verbose=False,
                            progress_callback=lambda step, pct, msg: None,  # Disable individual progress for batch
                        )
                        batch_results.append(result)
                
                # Final success state
                progress_bar.progress(100, text="Batch Complete!")
                status_text.success(f"✅ Batch transcription complete! Processed {len(batch_results)} video(s)")
                
                # Show batch results
                st.markdown("---")
                st.subheader("📊 Batch Results")
                
                for i, result in enumerate(batch_results, 1):
                    with st.expander(f"📹 {Path(result['video_path']).name}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Language", result["language"].upper())
                        with col2:
                            st.metric("Confidence", f"{result['language_probability']:.1%}")
                        with col3:
                            st.metric("Segments", len(result["segments"]))
                        
                        # Download files for this video
                        st.markdown("**📥 Download Files:**")
                        for file_path in result["output_files"]:
                            file = Path(file_path)
                            if file.exists():
                                with open(file, "rb") as f:
                                    data = f.read()
                                st.download_button(
                                    label=f"⬇️ {file.name}",
                                    data=data,
                                    file_name=file.name,
                                    mime="text/plain" if file.suffix in [".txt", ".md", ".srt", ".vtt"] else "application/json",
                                    use_container_width=True,
                                )
            elif input_method == "Search & Download":
                # Search & Download processing
                with st.spinner("Processing downloaded videos..."):
                    batch_results = []
                    total_videos = len(video_path)
                    
                    for idx, current_video in enumerate(video_path, 1):
                        # Check if already transcribed
                        video_name = Path(current_video).stem
                        already_transcribed = False
                        for fmt in formats:
                            output_file = Path(output_dir) / f"{video_name}.{fmt}"
                            if output_file.exists():
                                already_transcribed = True
                                break
                        
                        if already_transcribed:
                            st.info(f"⏭️ Skipping {Path(current_video).name} (already transcribed)")
                            continue
                        
                        # Update progress for overall batch
                        overall_pct = int(((idx - 1) / total_videos) * 100)
                        progress_bar.progress(overall_pct / 100, text=f"Processing video {idx}/{total_videos}")
                        status_text.info(f"**Video {idx}/{total_videos}** — Processing: {Path(current_video).name}")
                        
                        # Transcribe current video
                        result = transcribe(
                            video_path=current_video,
                            output_dir=output_dir,
                            model_size=model_size,
                            language=language,
                            device=device,
                            compute_type=compute_type,
                            formats=formats,
                            verbose=False,
                            progress_callback=lambda step, pct, msg: None,  # Disable individual progress for batch
                        )
                        batch_results.append(result)
                
                # Final success state
                progress_bar.progress(100, text="Batch Complete!")
                status_text.success(f"✅ Batch transcription complete! Processed {len(batch_results)} video(s)")
                
                # Show batch results
                st.markdown("---")
                st.subheader("📊 Batch Results")
                
                for i, result in enumerate(batch_results, 1):
                    with st.expander(f"📹 {Path(result['video_path']).name}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Language", result["language"].upper())
                        with col2:
                            st.metric("Confidence", f"{result['language_probability']:.1%}")
                        with col3:
                            st.metric("Segments", len(result["segments"]))
                        
                        # Download files for this video
                        st.markdown("**📥 Download Files:**")
                        for file_path in result["output_files"]:
                            file = Path(file_path)
                            if file.exists():
                                with open(file, "rb") as f:
                                    data = f.read()
                                st.download_button(
                                    label=f"⬇️ {file.name}",
                                    data=data,
                                    file_name=file.name,
                                    mime="text/plain" if file.suffix in [".txt", ".md", ".srt", ".vtt"] else "application/json",
                                    use_container_width=True,
                                )
            else:
                # Single video processing (existing logic)
                with st.spinner("Processing..."):
                    result = transcribe(
                        video_path=video_path,
                        output_dir=output_dir,
                        model_size=model_size,
                        language=language,
                        device=device,
                        compute_type=compute_type,
                        formats=formats,
                        verbose=False,
                        progress_callback=progress_callback,
                    )
                
                # Success state
                progress_bar.progress(100, text="Complete!")
                status_text.success("✅ Transcription complete!")
                
                # Results
                st.markdown("---")
                st.subheader("📊 Results")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Detected Language", result["language"].upper())
                with col2:
                    st.metric("Confidence", f"{result['language_probability']:.1%}")
                with col3:
                    st.metric("Segments", len(result["segments"]))
                
                # Download files
                st.markdown("### 📥 Download Files")
                
                for file_path in result["output_files"]:
                    file = Path(file_path)
                    if file.exists():
                        with open(file, "rb") as f:
                            data = f.read()
                        st.download_button(
                            label=f"⬇️ {file.name}",
                            data=data,
                            file_name=file.name,
                            mime="text/plain" if file.suffix in [".txt", ".md", ".srt", ".vtt"] else "application/json",
                            use_container_width=True,
                        )
                
                # Show preview
                with st.expander("👁️ Preview Transcript"):
                    for seg in result["segments"][:10]:
                        start = f"{int(seg['start'] // 60):02d}:{int(seg['start'] % 60):02d}"
                        st.markdown(f"**{start}** — {seg['text']}")
                    if len(result["segments"]) > 10:
                        st.markdown(f"... and {len(result['segments']) - 10} more segments")

                # Show downloaded video info if from YouTube
                if result.get("downloaded_video"):
                    st.info(f"📹 Downloaded video saved to: {result['downloaded_video']}")

        except FileNotFoundError as e:
            st.error(f"❌ Video file not found: {e}")
        except Exception as e:
            st.error(f"❌ Error during transcription: {e}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            # Cleanup temp files
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            # Cleanup downloaded videos from Search & Download mode
            if input_method == "Search & Download":
                temp_dir = Path("temp_downloads")
                if temp_dir.exists():
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        print(f"Warning: Could not clean up temp directory: {e}")

    # Footer
    st.markdown("---")
    st.caption("Powered by [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Built with Streamlit")


if __name__ == "__main__":
    main()
