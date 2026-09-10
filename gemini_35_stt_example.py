# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    # 입력으로 사용할 오디오 파일 경로
    audio_path = "output_new.wav"
    if not os.path.exists(audio_path) and os.path.exists("gemini_tts_news.wav"):
        print(f"'{audio_path}' 파일이 없어 폴더 내의 'gemini_tts_news.wav' 파일을 입력으로 사용합니다.\n")
        audio_path = "gemini_tts_news.wav"
    elif not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일 '{audio_path}'을(를) 찾을 수 없습니다. 파일명을 확인해 주세요.")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    model = "gemini-3.5-transcribe"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav",
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")

if __name__ == "__main__":
    generate()


