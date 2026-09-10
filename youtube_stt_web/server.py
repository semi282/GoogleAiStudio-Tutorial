import os
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from google import genai

# 현재 스크립트 디렉터리를 모듈 탐색 경로에 추가
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from downloader import get_video_info, download_audio
from transcriber import transcribe_audio, summarize_transcript

app = FastAPI(title="YouTube Audio & Gemini STT Web Service")

DOWNLOADS_DIR = CURRENT_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)


class TranscribeRequest(BaseModel):
    url: str
    api_key: Optional[str] = None
    model: str = "gemini-3.6-flash"
    enable_diarization: bool = True
    enable_timestamps: bool = True
    enable_summary: bool = True


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = CURRENT_DIR / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.get("/api/config")
async def get_config():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {"has_env_key": has_key}


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


@app.post("/api/transcribe")
async def handle_transcribe(req: TranscribeRequest):
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다. 입력창에 API 키를 입력해 주세요.")

    try:
        # 1. 유튜브 메타데이터 & 오디오 다운로드
        audio_info = download_audio(req.url, output_dir=str(DOWNLOADS_DIR))
        client = genai.Client(api_key=effective_api_key)

        # 2. Gemini STT 전사
        chunks = []
        for chunk in transcribe_audio(
            client=client,
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            model_name=req.model,
            enable_diarization=req.enable_diarization,
            enable_timestamps=req.enable_timestamps,
        ):
            chunks.append(chunk)

        full_transcript = "".join(chunks)

        # 3. 요약 (선택)
        summary_text = ""
        if req.enable_summary and full_transcript.strip():
            try:
                summary_text = summarize_transcript(client, full_transcript)
            except Exception as e:
                summary_text = f"요약 생성 중 오류 발생: {e}"

        audio_filename = Path(audio_info["file_path"]).name

        return {
            "id": audio_info.get("id", ""),
            "title": audio_info["title"],
            "channel": audio_info["channel"],
            "duration": audio_info["duration"],
            "thumbnail": audio_info["thumbnail"],
            "audio_url": f"/api/audio/{audio_filename}",
            "transcript": full_transcript,
            "summary": summary_text,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ChatRequest(BaseModel):
    question: str
    transcript: str
    api_key: Optional[str] = None
    model: str = "gemini-3.6-flash"


@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    effective_api_key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY")
    if not effective_api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key가 필요합니다.")

    try:
        client = genai.Client(api_key=effective_api_key)
        prompt = f"""당신은 제공된 유튜브 영상 트랜스크립트(대본)를 기반으로 시청자의 질문에 친절하고 정확하게 답변하는 전문 AI 어시스턴트입니다.
대본에 언급된 내용을 바탕으로 자연스러운 한국어로 명쾌하게 답변해 주세요.
만약 대본에 없는 내용이라면 상상해서 지어내지 말고 "대본에 해당 내용이 언급되지 않았습니다"라고 솔직하게 안내해 주세요.

[영상 대본]:
{req.transcript[:35000]}

[시청자 질문]:
{req.question}
"""
        response = client.models.generate_content(
            model=req.model,
            contents=prompt,
        )
        return {"answer": response.text or "답변을 생성할 수 없습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
