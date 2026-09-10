import os
from typing import Generator, Dict, Any, Optional
from google import genai
from google.genai import types

STT_MODEL_NAME = "gemini-3.5-transcribe"
STT_MODEL_VERSION = "Gemini 3.5 Transcribe (v1.0)"

CHAT_MODEL_NAME = "gemini-3.8-flash"
CHAT_MODEL_VERSION = "Gemini 3.8 Flash (v1.0)"


def transcribe_audio_stream(
    client: genai.Client,
    audio_path: str,
    mime_type: str = "audio/mp4",
    enable_diarization: bool = True,
    enable_timestamps: bool = True,
) -> Generator[str, None, None]:
    """오디오 파일을 분석하여 화자 분리 및 [MM:SS] 형식의 정밀 타임스탬프가 포함된 트랜스크립트를 생성합니다."""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

    uploaded_file = None
    if file_size_mb < 20:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    else:
        uploaded_file = client.files.upload(file=audio_path, mime_type=mime_type)
        audio_part = uploaded_file

    prompt = """다음 오디오를 정밀하게 분석하여 화자 분리(Diarization)와 함께 시간대별 타임스탬프를 포함하여 한국어/영어 대사를 전사해 주세요.
[규칙]:
1. 반드시 각 문장이나 발화가 시작하는 시점에 [MM:SS] 형식(예: [00:05] 화자 1: 대사 내용)으로 타임스탬프를 붙여주세요.
2. 모든 대화, 영어 및 한국어 발화를 누락 없이 정확하게 작성하세요.
3. [MM:SS] 화자 N: 대사 내용 형식 외에 불필요한 서두나 결말 텍스트는 출력하지 마세요."""

    contents = [
        types.Content(
            role="user",
            parts=[audio_part, types.Part.from_text(text=prompt)],
        )
    ]

    try:
        for chunk in client.models.generate_content_stream(
            model="gemini-3.6-flash",
            contents=contents,
        ):
            if chunk.text:
                yield chunk.text
    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


def answer_video_question(
    client: genai.Client,
    transcript: str,
    question: str,
) -> Dict[str, str]:
    """gemini-3.8-flash 모델을 사용하여 영상 트랜스크립트 기반으로 사용자의 질문에 답변합니다."""
    prompt = f"""당신은 유튜브 영상의 전체 자막(트랜스크립트)을 완벽하게 숙지한 전문 AI 영상 어시스턴트입니다.
제공된 대본 내용을 철저히 바탕으로 시청자의 질문에 자연스럽고 친절한 한국어로 답변해 주세요.

[규칙]:
1. 대본에 언급된 사실만을 근거로 정확하게 답변하세요.
2. 대본에 명시되지 않은 내용이라면 상상하여 지어내지 말고, "대본에 해당 내용이 언급되지 않았습니다"라고 정직하게 안내하세요.
3. 중요한 대사나 시점이 있다면 타임스탬프나 등장인물 이름을 함께 언급해 주면 좋습니다.

[영상 자막 대본]:
{transcript[:35000]}

[시청자 질문]:
{question}
"""
    response = client.models.generate_content(
        model=CHAT_MODEL_NAME,
        contents=prompt,
    )

    return {
        "answer": response.text or "답변을 생성할 수 없습니다.",
        "model_name": CHAT_MODEL_NAME,
        "model_version": CHAT_MODEL_VERSION,
    }


def generate_video_summary(
    client: genai.Client,
    transcript: str,
) -> Dict[str, str]:
    """gemini-3.8-flash 모델을 사용하여 영상의 3~5줄 핵심 요약을 생성합니다."""
    prompt = f"""다음은 유튜브 영상에서 추출한 자막 대본입니다.
이 영상의 핵심 주제와 주요 대화/내용을 3~5개의 깔끔한 불릿 포인트로 한국어로 요약해 주세요.

[자막 대본]:
{transcript[:30000]}
"""
    response = client.models.generate_content(
        model=CHAT_MODEL_NAME,
        contents=prompt,
    )

    return {
        "summary": response.text or "요약을 생성할 수 없습니다.",
        "model_name": CHAT_MODEL_NAME,
        "model_version": CHAT_MODEL_VERSION,
    }
