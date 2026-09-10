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
from transcriber import (
    transcribe_audio_stream,
    answer_video_question,
    generate_video_summary,
    STT_MODEL_VERSION,
    CHAT_MODEL_VERSION,
)

app = FastAPI(title="AI 자막뽑기 - YouTube STT & Assistant API")

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


@app.get("/api/config")
async def get_config():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {
        "has_env_key": has_key,
        "stt_model": STT_MODEL_VERSION,
        "chat_model": CHAT_MODEL_VERSION,
    }


@app.post("/api/estimate")
async def handle_estimate(req: EstimateRequest):
    """1단계: 유튜브 영상 메타데이터 분석 및 Google AI Studio 요금 견적 계산"""
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
    """2단계: 사용자가 견적 승인 후 고음질 오디오 다운로드 및 Gemini 3.5 Transcribe 실행"""
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다.")

    try:
        # 1. 오디오 다운로드
        audio_info = download_audio(req.url, output_dir=str(DOWNLOADS_DIR))
        client = genai.Client(api_key=effective_api_key)

        # 2. Gemini 3.5 Transcribe STT
        chunks = []
        for chunk in transcribe_audio_stream(
            client=client,
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            enable_diarization=True,
            enable_timestamps=True,
        ):
            chunks.append(chunk)

        full_transcript = "".join(chunks)

        # 3. Gemini 3.8 Flash 기반 요약
        summary_result = generate_video_summary(client, full_transcript)

        audio_filename = Path(audio_info["file_path"]).name

        cost_estimate = calculate_video_cost(audio_info["duration"])

        return {
            "id": audio_info.get("id", ""),
            "title": audio_info["title"],
            "channel": audio_info["channel"],
            "duration": audio_info["duration"],
            "thumbnail": audio_info["thumbnail"],
            "audio_url": f"/api/audio/{audio_filename}",
            "transcript": full_transcript,
            "summary": summary_result["summary"],
            "cost_estimate": cost_estimate,
            "stt_engine": STT_MODEL_VERSION,
            "summary_engine": summary_result["model_version"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전사 처리 중 오류: {str(e)}")


@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    """3단계: Gemini 3.8 Flash 기반 영상 대본 Q&A 질문 답변"""
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다.")

    try:
        client = genai.Client(api_key=effective_api_key)
        result = answer_video_question(client, req.transcript, req.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 오류: {str(e)}")


@app.get("/api/audio/{filename}")
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
