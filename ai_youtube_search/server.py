import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from google import genai

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from cost_calc import calculate_video_cost
from downloader import get_video_info, download_audio
from db import get_cached_transcript, save_transcript_to_csv, get_all_cached_history
from transcriber import (
    transcribe_audio_stream,
    answer_video_question,
    generate_video_summary,
    STT_MODEL_VERSION,
    CHAT_MODEL_VERSION,
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="자막뽑기 AI - YouTube STT & Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = CURRENT_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)


class EstimateRequest(BaseModel):
    url: str


class TranscribeRequest(BaseModel):
    url: str
    api_key: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    transcript: str
    api_key: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = CURRENT_DIR / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.get("/style.css")
async def serve_style():
    return FileResponse(CURRENT_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(CURRENT_DIR / "app.js", media_type="application/javascript")


@app.get("/app.ts")
async def serve_ts():
    return FileResponse(CURRENT_DIR / "app.ts", media_type="text/plain")


@app.get("/api/config")
async def get_config():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "has_env_key": has_key,
        "stt_model": STT_MODEL_VERSION,
        "chat_model": CHAT_MODEL_VERSION,
    }


@app.get("/api/history")
async def get_history():
    """CSV에 저장된 전체 전사 히스토리 목록을 반환합니다."""
    return get_all_cached_history()


@app.post("/api/estimate")
async def handle_estimate(req: EstimateRequest):
    """유튜브 영상 메타데이터 분석 및 Google AI Studio 요금 견적 계산"""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해 주세요.")

    try:
        info = get_video_info(req.url.strip())
        cost_data = calculate_video_cost(info["duration"])
        return {
            "video_info": info,
            "cost_estimate": cost_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 정보 조회 실패: {str(e)}")


@app.post("/api/transcribe")
async def handle_transcribe(req: TranscribeRequest):
    """유튜브 전사 요청: 1) CSV 캐시 확인 -> 2) 없으면 다운로드 및 Gemini 전사 후 CSV 저장"""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해 주세요.")

    cached = get_cached_transcript(req.url.strip())
    if cached and cached.get("transcript"):
        cost_estimate = calculate_video_cost(cached["duration"])
        video_url = ""
        audio_url = ""
        vid_id = cached.get("id", "")
        if vid_id:
            for ext in [".mp4", ".webm", ".mkv"]:
                cand = DOWNLOADS_DIR / f"{vid_id}{ext}"
                if cand.exists():
                    video_url = f"/api/video/{cand.name}"
                    break
            for ext in [".m4a", ".mp3", ".webm", ".opus", ".mp4"]:
                cand = DOWNLOADS_DIR / f"{vid_id}{ext}"
                if cand.exists():
                    audio_url = f"/api/audio/{cand.name}"
                    break

        return {
            "id": cached["id"],
            "url": cached["url"],
            "title": cached["title"],
            "channel": cached["channel"],
            "duration": cached["duration"],
            "thumbnail": f"https://img.youtube.com/vi/{cached['id']}/hqdefault.jpg" if cached["id"] else "",
            "video_url": video_url,
            "audio_url": audio_url,
            "transcript": cached["transcript"],
            "summary": cached["summary"],
            "cost_estimate": cost_estimate,
            "is_cached": True,
            "stt_engine": STT_MODEL_VERSION,
            "summary_engine": CHAT_MODEL_VERSION,
        }

    # 2. 신규 영상인 경우: Gemini API 키 확인 후 추출 시작
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다.")

    try:
        # 비디오 및 오디오 다운로드
        media_info = download_audio(req.url, output_dir=str(DOWNLOADS_DIR))
        client = genai.Client(api_key=effective_api_key)

        # Gemini STT (화자 분리 & [MM:SS] 타임스탬프)
        chunks = []
        for chunk in transcribe_audio_stream(
            client=client,
            audio_path=media_info["file_path"],
            mime_type=media_info["mime_type"],
            enable_diarization=True,
            enable_timestamps=True,
        ):
            chunks.append(chunk)

        full_transcript = "".join(chunks)

        # Gemini 요약 생성
        summary_result = generate_video_summary(client, full_transcript)
        cost_estimate = calculate_video_cost(media_info["duration"])

        # CSV 파일에 저장
        save_transcript_to_csv({
            "id": media_info.get("id", ""),
            "url": req.url.strip(),
            "title": media_info["title"],
            "channel": media_info["channel"],
            "duration": media_info["duration"],
            "transcript": full_transcript,
            "summary": summary_result["summary"],
        })

        media_filename = Path(media_info["file_path"]).name
        is_video = media_filename.lower().endswith(('.mp4', '.webm', '.mkv'))

        return {
            "id": media_info.get("id", ""),
            "url": req.url.strip(),
            "title": media_info["title"],
            "channel": media_info["channel"],
            "duration": media_info["duration"],
            "thumbnail": media_info["thumbnail"],
            "video_url": f"/api/video/{media_filename}" if is_video else "",
            "audio_url": f"/api/audio/{media_filename}",
            "transcript": full_transcript,
            "summary": summary_result["summary"],
            "cost_estimate": cost_estimate,
            "is_cached": False,
            "stt_engine": STT_MODEL_VERSION,
            "summary_engine": summary_result["model_version"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전사 처리 중 오류: {str(e)}")


@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    """Gemini 3.8 Flash 기반 영상 대본 Q&A 질문 답변"""
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다.")

    try:
        client = genai.Client(api_key=effective_api_key)
        result = answer_video_question(client, req.transcript, req.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 오류: {str(e)}")


@app.api_route("/api/video/{filename}", methods=["GET", "HEAD"])
async def get_video(filename: str):
    file_path = DOWNLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="비디오 파일을 찾을 수 없습니다.")
    ext = file_path.suffix.lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
    }
    return FileResponse(file_path, media_type=mime_map.get(ext, "video/mp4"))


@app.api_route("/api/audio/{filename}", methods=["GET", "HEAD"])
async def get_audio(filename: str):
    file_path = DOWNLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")
    ext = file_path.suffix.lower()
    mime_map = {
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".webm": "audio/webm",
        ".opus": "audio/ogg",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }
    return FileResponse(file_path, media_type=mime_map.get(ext, "audio/mp4"))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
