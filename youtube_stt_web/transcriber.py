import os
from typing import Generator, Dict, Any, Optional
from google import genai
from google.genai import types


def transcribe_audio(
    client: genai.Client,
    audio_path: str,
    mime_type: str = "audio/mp4",
    model_name: str = "gemini-3.6-flash",
    enable_diarization: bool = True,
    enable_timestamps: bool = True,
) -> Generator[str, None, None]:
    """오디오 파일을 Gemini 모델에 전달하여 한국어/영어/다국어 텍스트 트랜스크립트를 스트리밍 방식으로 생성합니다."""
    file_size = os.path.getsize(audio_path)
    file_size_mb = file_size / (1024 * 1024)

    # 20MB 이하: In-memory bytes 직접 전달 / 20MB 초과: Google File API 업로드
    uploaded_file = None
    if file_size_mb < 20:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
    else:
        uploaded_file = client.files.upload(file=audio_path, mime_type=mime_type)
        audio_part = uploaded_file

    # gemini-3.5-transcribe 전용 설정
    if "transcribe" in model_name:
        generate_content_config = types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(
                word_timestamp=enable_timestamps,
                diarization=enable_diarization,
            ),
        )
        contents = [
            types.Content(
                role="user",
                parts=[audio_part],
            )
        ]
    else:
        # gemini-3.6-flash 등 범용 멀티모달 모델: 한국어, 영어, 혼합 발화 완벽 전사 프롬프트
        generate_content_config = types.GenerateContentConfig(
            temperature=0.1,
        )
        instruction = (
            "You are a professional audio transcription expert. Transcribe the given audio completely and accurately.\n"
            "- Multilingual Support: English, Korean, or any other spoken language must be transcribed verbatim in the spoken language. Do NOT translate.\n"
            "- Completeness: Transcribe all spoken words from the very beginning to the end. Do NOT omit or summarize any dialogue."
        )
        if enable_diarization:
            instruction += "\n- Diarization: Distinguish different speakers (e.g. [Speaker 1], [Speaker 2] or recognized names) whenever the speaker changes."
        if enable_timestamps:
            instruction += "\n- Timestamps: Provide timestamp ranges in [MM:SS - MM:SS] format for each speech segment."

        instruction += "\n\nFormat the output cleanly line-by-line."

        contents = [
            types.Content(
                role="user",
                parts=[audio_part, types.Part.from_text(text=instruction)],
            )
        ]

    try:
        for chunk in client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                yield chunk.text
            elif chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "audio_transcription") and part.audio_transcription and hasattr(part.audio_transcription, "text"):
                        yield part.audio_transcription.text
    finally:
        # File API로 업로드한 임시 파일이 있다면 정리
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass


def summarize_transcript(
    client: genai.Client,
    transcript: str,
    model_name: str = "gemini-3.6-flash",
) -> str:
    """전사된 텍스트 대본을 기반으로 한국어로 핵심 요약을 생성합니다."""
    prompt = f"""다음은 영상 오디오에서 추출한 트랜스크립트 대본(영어, 한국어 또는 다국어)입니다.
원문 언어에 상관없이, 영상의 핵심 내용과 맥락을 이해하기 쉽게 한국어로 3~5개의 깔끔한 불릿 포인트로 요약해 주세요.

[대본 내용]:
{transcript[:30000]}
"""
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return response.text or "요약을 생성할 수 없습니다."
