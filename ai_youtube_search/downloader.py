import os
import yt_dlp
from typing import Dict, Any

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = None


def get_video_info(url: str) -> Dict[str, Any]:
    """유튜브 영상의 메타데이터(ID, 제목, 채널명, 재생 시간, 썸네일 등)를 초고속으로 조회합니다 (다운로드 없음)."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id", ""),
            "title": info.get("title", "Unknown Title"),
            "channel": info.get("uploader") or info.get("channel", "Unknown Channel"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "description": info.get("description", ""),
        }


def download_audio(url: str, output_dir: str = "downloads") -> Dict[str, Any]:
    """유튜브 영상에서 비디오+오디오 통합 MP4 또는 고음질 오디오를 다운로드합니다."""
    os.makedirs(output_dir, exist_ok=True)
    out_tmpl = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[ext=mp4]/best",
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    if FFMPEG_EXE:
        ydl_opts["ffmpeg_location"] = FFMPEG_EXE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception:
        # Fallback to audio-only if video download fails
        ydl_opts_audio = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": out_tmpl,
            "quiet": True,
            "no_warnings": True,
        }
        if FFMPEG_EXE:
            ydl_opts_audio["ffmpeg_location"] = FFMPEG_EXE
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        base, _ = os.path.splitext(filename)
        for ext in [".mp4", ".m4a", ".webm", ".opus", ".mp3", ".wav"]:
            candidate = base + ext
            if os.path.exists(candidate):
                filename = candidate
                break

    ext = os.path.splitext(filename)[1].lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".m4a": "audio/mp4",
        ".opus": "audio/ogg",
        ".ogg": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }
    mime_type = mime_map.get(ext, "video/mp4" if ext == ".mp4" else "audio/mp4")

    return {
        "id": info.get("id", ""),
        "file_path": filename,
        "title": info.get("title", "Unknown Title"),
        "channel": info.get("uploader") or info.get("channel", "Unknown Channel"),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "mime_type": mime_type,
    }
