# Gemini 3.1 Flash TTS (Text-to-Speech) 코드 라인별(Line-by-Line) 완벽 해설

이 문서는 `gemini_31_tts_example.py` 코드의 각 라인이 어떤 역할을 수행하는지 상세하게 설명합니다.  
본 코드는 Google GenAI SDK를 활용하여 텍스트 대본(감정/상황 지시문 포함)을 오디오 음성 파일(`.wav`)로 합성하는 예제입니다.

---

## 1. 의존성 및 모듈 임포트 (1~9행)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
3: 
4: import mimetypes
5: import os
6: import re
7: import struct
8: from google import genai
9: from google.genai import types
```

- **1~2행**: 실행 전 필요한 공식 구글 GenAI 라이브러리(`google-genai`) 설치 안내 주석입니다.
- **4행 (`import mimetypes`)**: MIME 타입(예: `audio/wav`)을 기반으로 파일 확장자(`.wav`)를 추론할 때 사용합니다.
- **5행 (`import os`)**: 시스템 환경 변수(`GEMINI_API_KEY`)를 읽어오기 위해 사용합니다.
- **6행 (`import re`)**: 정규표현식 모듈입니다 (확장 파싱 로직용).
- **7행 (`import struct`)**: 파이썬의 원시 바이너리 바이트 데이터를 C 언어 스타일의 구조체(바이너리 바이트 열)로 패킹(`pack`)하기 위한 모듈입니다. 표준 WAV 파일의 44바이트 헤더를 생성할 때 핵심적으로 사용됩니다.
- **8~9행 (`from google import genai`, `from google.genai import types`)**: 구글의 최신 통합 Gemini SDK 클라이언트와 설정/콘텐츠 타입 객체들을 임포트합니다.

---

## 2. 바이너리 파일 저장 함수 (14~18행)

```python
14: def save_binary_file(file_name, data):
15:     f = open(file_name, "wb")
16:     f.write(data)
17:     f.close()
18:     print(f"File saved to to: {file_name}")
```

- **14행**: 파일 경로(`file_name`)와 바이너리 데이터(`data`)를 전달받는 함수를 정의합니다.
- **15~17행**: 쓰기 바이너리 모드(`"wb"`)로 파일을 열어 오디오 바이트 데이터를 디스크에 기록하고 파일을 닫습니다.
- **18행**: 파일 저장이 완료되었음을 알리는 콘솔 메시지를 출력합니다.

---

## 3. 음성 생성 메인 함수 `generate()` 및 클라이언트 초기화 (21~24행)

```python
21: def generate():
22:     client = genai.Client(
23:         api_key=os.environ.get("GEMINI_API_KEY"),
24:     )
```

- **21행**: TTS 음성을 요청하고 생성하는 메인 로직 함수입니다.
- **22~24행**: `genai.Client` 인스턴스를 생성합니다. 시스템 환경 변수에 등록된 `GEMINI_API_KEY` 값을 읽어와 인증을 수행합니다.

---

## 4. 모델 및 프롬프트 대본 구성 (26~51행)

```python
26:     model = "gemini-3.1-flash-tts-preview"
27:     contents = [
28:         types.Content(
29:             role="user",
30:             parts=[
31:                 types.Part.from_text(text="""## Scene:
32:  A professional tech news studio, fast-paced and exciting breaking news announcement.
33: 
34: ## Sample Context:
35: The anchor has just received breaking news about Google's latest AI release and is eager to share the unexpected pricing details with the audience.
36: 
37: ## Transcript:
38: [breaking news] 테크 뉴스 긴급 속보입니다. 
39: 
40: [excited] 구글이 마침내 차세대 인공지능 모델, '제미나이 4.0 프로(Gemini 4.0 Pro)'를 전격 공개했습니다! 
41: 
42: [confident] 복합 추론 능력과 코딩 성능이 압도적으로 향상되었는데요. 놀라운 건 성능뿐만이 아닙니다. 
43: 
44: [gasp] [whispering] 가격이… 상상을 초월할 정도로 저렴합니다! [pause] 
45: 
46: [excited] 기존 프로 모델 대비 토큰당 비용이 무려 90% 이상 파격 인하되어, 사실상 플래시 모델 수준의 가격으로 출시되었습니다. 
47: 
48: [chuckle] 업계에서는 \"이 가격이면 다른 모델을 쓸 이유가 없다\"는 반응까지 쏟아지고 있는데요. [confident] AI 개발 시장에 또 한 번 거대한 지각변동이 일어날 것으로 보입니다!"""),
49:             ],
50:         ),
51:     ]
```

- **26행**: 사용할 TTS 전용 모델(`gemini-3.1-flash-tts-preview`)을 지정합니다.
- **27~30행**: 모델에 전달할 `user` 역할의 콘텐츠를 리스트 형태로 구성합니다.
- **31~36행**:
  - `## Scene:` 음성이 발화되는 배경 공간의 분위기를 설정합니다 (전문 테크 뉴스 스튜디오).
  - `## Sample Context:` 말하는 화자(앵커)의 심리적 맥락과 의도를 지시합니다.
- **37~48행**: `## Transcript:` 실제 읽을 대본입니다. `[breaking news]`, `[excited]`, `[whispering]`, `[pause]` 등 오디오 제어 태그를 함께 전달하여 톤과 감정을 조절합니다.

---

## 5. 생성 파라미터 및 음성(Voice) 설정 (52~64행)

```python
52:     generate_content_config = types.GenerateContentConfig(
53:         temperature=1,
54:         response_modalities=[
55:             "audio",
56:         ],
57:         speech_config=types.SpeechConfig(
58:             voice_config=types.VoiceConfig(
59:                 prebuilt_voice_config=types.PrebuiltVoiceConfig(
60:                     voice_name="Achird"
61:                 )
62:             )
63:         ),
64:     )
```

- **52~53행**: `GenerateContentConfig`를 설정합니다. `temperature=1`은 발화 표현의 자연스러운 다양성을 부여합니다.
- **54~56행 (`response_modalities=["audio"]`)**: 모델의 응답 결과물을 텍스트가 아닌 **오디오(Audio)** 형태로 출력하도록 지정하는 가장 중요한 핵심 설정입니다.
- **57~63행**: 발화에 사용할 구글의 사전 제작 음성(`prebuilt_voice_config`)을 지정합니다. 여기서는 차분하면서도 명확한 톤의 `"Achird"` 보이스를 선택했습니다.

---

## 6. 스트리밍 수신 및 오디오 청크 결합 (66~85행)

```python
66:     audio_chunks = []
67:     mime_type = None
68: 
69:     print("Generating audio stream from Gemini...")
70:     for chunk in client.models.generate_content_stream(
71:         model=model,
72:         contents=contents,
73:         config=generate_content_config,
74:     ):
75:         if chunk.parts is None:
76:             continue
77:         
78:         part = chunk.parts[0]
79:         if part.inline_data and part.inline_data.data:
80:             audio_chunks.append(part.inline_data.data)
81:             if not mime_type and part.inline_data.mime_type:
82:                 mime_type = part.inline_data.mime_type
83:         elif chunk.text:
84:             print(chunk.text, end="", flush=True)
```

- **66~67행**: 스트리밍으로 전달되는 오디오 바이트 조각들을 모으기 위한 리스트(`audio_chunks`)와 수신된 MIME 타입을 담을 변수를 선언합니다.
- **70~74행**: `client.models.generate_content_stream()`을 호출하여 서버로부터 실시간 스트리밍으로 데이터를 청크 단위로 받아옵니다.
- **75~76행**: 청크 내 파트가 비어있는 예외 상황을 방어합니다.
- **78~82행**: 청크에 포함된 인라인 바이너리 데이터(`part.inline_data.data`)를 순서대로 `audio_chunks` 리스트에 누적하고, MIME 타입(`audio/L16;rate=24000` 등)을 기록합니다.
- **83~84행**: 오디오 외에 텍스트 응답이 함께 수신될 경우 콘솔에 즉시 출력합니다.

---

## 7. 단일 WAV 파일 변환 및 저장 (86~102행)

```python
86:     if audio_chunks:
87:         all_audio_data = b"".join(audio_chunks)
88:         file_name = "gemini_tts_news"
89:         file_extension = mimetypes.guess_extension(mime_type) if mime_type else None
90:         
91:         if file_extension is None:
92:             file_extension = ".wav"
93:             data_buffer = convert_to_wav(all_audio_data, mime_type or "audio/L16;rate=24000")
94:         else:
95:             data_buffer = all_audio_data
96:             
97:         output_file = f"{file_name}{file_extension}"
98:         save_binary_file(output_file, data_buffer)
99:         print(f"Done! Audio successfully saved to: {output_file}")
100:     else:
101:         print("No audio data received.")
```

- **86~87행**: 수신된 모든 오디오 바이트 청크들을 `b"".join()`을 통해 단 하나의 연속된 바이너리 바이트열로 합칩니다.
- **88~89행**: 저장할 기본 파일명(`gemini_tts_news`)을 지정하고 확장자를 판별합니다.
- **91~95행**: Gemini TTS가 반환하는 원시 PCM(L16) 데이터는 컨테이너 헤더가 없으므로 `file_extension`이 `None`으로 판별됩니다. 따라서 `convert_to_wav()`를 호출하여 표준 WAV 헤더를 붙인 완성형 WAV 바이너리를 만듭니다.
- **97~99행**: `save_binary_file()`을 호출하여 디스크에 최종 `gemini_tts_news.wav` 단일 파일로 저장합니다.

---

## 8. RIFF WAV 헤더 생성 함수 `convert_to_wav()` (103~141행)

```python
103: def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
...
113:     parameters = parse_audio_mime_type(mime_type)
114:     bits_per_sample = parameters["bits_per_sample"] or 16
115:     sample_rate = parameters["rate"] or 24000
116:     num_channels = 1
117:     data_size = len(audio_data)
118:     bytes_per_sample = bits_per_sample // 8
119:     block_align = num_channels * bytes_per_sample
120:     byte_rate = sample_rate * block_align
121:     chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size
122: 
125:     header = struct.pack(
126:         "<4sI4s4sIHHIIHH4sI",
127:         b"RIFF",          # ChunkID
128:         chunk_size,       # ChunkSize (total file size - 8 bytes)
129:         b"WAVE",          # Format
130:         b"fmt ",          # Subchunk1ID
131:         16,               # Subchunk1Size (16 for PCM)
132:         1,                # AudioFormat (1 for PCM)
133:         num_channels,     # NumChannels (1 = Mono)
134:         sample_rate,      # SampleRate (24000Hz)
135:         byte_rate,        # ByteRate (초당 바이트 수)
136:         block_align,      # BlockAlign (샘플 블록 크기)
137:         bits_per_sample,  # BitsPerSample (16-bit)
138:         b"data",          # Subchunk2ID
139:         data_size         # Subchunk2Size (순수 오디오 데이터 크기)
140:     )
141:     return header + audio_data
```

- **역할**: 미디어 플레이어가 인식할 수 있도록 순수 PCM 음성 데이터 앞에 **44바이트 표준 RIFF WAV 헤더**를 붙여 반환합니다.
- **113~121행**: 오디오 사양(16비트, 24,000Hz, 모노 채널)을 기반으로 전체 청크 크기, 초당 바이트 수(`byte_rate`) 등을 계산합니다.
- **125~140행 (`struct.pack`)**: 리틀 엔디언(`"<"`) 포맷으로 44바이트 헤더 구조체를 바이너리로 압축 생성합니다.
- **141행**: 완성된 헤더와 실제 원시 오디오 바이트(`audio_data`)를 이어붙여 리턴합니다.

---

## 9. MIME 파싱 함수 및 실행 진입점 (143~179행)

```python
143: def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
...
177: if __name__ == "__main__":
178:     generate()
```

- **143~174행**: `audio/L16;rate=24000`와 같은 MIME 문자열을 파싱하여 비트 심도(16)와 샘플링 레이트(24000)를 추출합니다.
- **177~178행**: 스크립트가 직접 실행될 때 `generate()` 함수를 호출하여 전체 TTS 합성 과정을 실행합니다.
