import os
import yt_dlp
from typing import Dict, Any


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
    """유튜브 영상에서 고음질 오디오 스트림(m4a/webm)을 다운로드합니다."""
    os.makedirs(output_dir, exist_ok=True)
    out_tmpl = os.path.join(output_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            for ext in [".m4a", ".webm", ".opus", ".mp3", ".wav"]:
                candidate = base + ext
                if os.path.exists(candidate):
                    filename = candidate
                    break

        ext = os.path.splitext(filename)[1].lower()
        mime_map = {
            ".m4a": "audio/mp4",
            ".mp4": "audio/mp4",
            ".webm": "audio/webm",
            ".opus": "audio/ogg",
            ".ogg": "audio/ogg",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
        }
        mime_type = mime_map.get(ext, "audio/mp4")

        return {
            "id": info.get("id", ""),
            "file_path": filename,
            "title": info.get("title", "Unknown Title"),
            "channel": info.get("uploader") or info.get("channel", "Unknown Channel"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", ""),
            "mime_type": mime_type,
        }
