# To run this code you need to install the following dependencies:
# pip install google-genai

import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types


# 변경사항이 발생했습니다

def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3.1-flash-tts-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""## Scene:
 A professional tech news studio, fast-paced and exciting breaking news announcement.

## Sample Context:
The anchor has just received breaking news about Google's latest AI release and is eager to share the unexpected pricing details with the audience.

## Transcript:
[breaking news] 테크 뉴스 긴급 속보입니다. 

[excited] 구글이 마침내 차세대 인공지능 모델, '제미나이 4.0 프로(Gemini 4.0 Pro)'를 전격 공개했습니다! 

[confident] 복합 추론 능력과 코딩 성능이 압도적으로 향상되었는데요. 놀라운 건 성능뿐만이 아닙니다. 

[gasp] [whispering] 가격이… 상상을 초월할 정도로 저렴합니다! [pause] 

[excited] 기존 프로 모델 대비 토큰당 비용이 무려 90% 이상 파격 인하되어, 사실상 플래시 모델 수준의 가격으로 출시되었습니다. 

[chuckle] 업계에서는 \"이 가격이면 다른 모델을 쓸 이유가 없다\"는 반응까지 쏟아지고 있는데요. [confident] AI 개발 시장에 또 한 번 거대한 지각변동이 일어날 것으로 보입니다!"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Achird"
                )
            )
        ),
    )

    audio_chunks = []
    mime_type = None

    print("Generating audio stream from Gemini...")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.parts is None:
            continue
        
        part = chunk.parts[0]
        if part.inline_data and part.inline_data.data:
            audio_chunks.append(part.inline_data.data)
            if not mime_type and part.inline_data.mime_type:
                mime_type = part.inline_data.mime_type
        elif chunk.text:
            print(chunk.text, end="", flush=True)

    if audio_chunks:
        all_audio_data = b"".join(audio_chunks)
        file_name = "gemini_tts_news"
        file_extension = mimetypes.guess_extension(mime_type) if mime_type else None
        
        if file_extension is None:
            file_extension = ".wav"
            data_buffer = convert_to_wav(all_audio_data, mime_type or "audio/L16;rate=24000")
        else:
            data_buffer = all_audio_data
            
        output_file = f"{file_name}{file_extension}"
        save_binary_file(output_file, data_buffer)
        print(f"Done! Audio successfully saved to: {output_file}")
    else:
        print("No audio data received.")

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"] or 16
    sample_rate = parameters["rate"] or 24000
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    generate()


