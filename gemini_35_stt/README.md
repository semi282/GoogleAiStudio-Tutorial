# Gemini 3.5 Transcribe STT (Speech-to-Text) 코드 라인별(Line-by-Line) 완벽 해설

이 문서는 `gemini_35_stt_example.py` 코드의 각 라인이 어떤 역할을 수행하는지 상세하게 설명합니다.  
본 코드는 Google GenAI SDK와 Gemini 전용 전사(Transcription) 모델을 활용하여 음성 파일(`.wav`)을 텍스트로 고품질 변환하는 예제입니다.

---

## 1. 의존성 및 모듈 임포트 (1~8행)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
3: 
4: import base64
5: import os
6: from google import genai
7: from google.genai import types
```

- **1~2행**: 실행 전 필요한 구글 공식 GenAI SDK(`google-genai`) 설치 안내 주석입니다.
- **4행 (`import base64`)**: 바이너리 데이터 인코딩/디코딩용 표준 모듈입니다.
- **5행 (`import os`)**: 시스템 환경 변수(`GEMINI_API_KEY`)를 가져오거나 파일의 존재 여부(`os.path.exists`)를 확인할 때 사용합니다.
- **6~7행 (`from google import genai`, `from google.genai import types`)**: Gemini 2.x/3.x 모델과 상호작용하기 위한 최신 클라이언트 라이브러리 및 데이터 타입 클래스들을 임포트합니다.

---

## 2. 함수 선언 및 클라이언트 인증 초기화 (10~13행)

```python
10: def generate():
11:     client = genai.Client(
12:         api_key=os.environ.get("GEMINI_API_KEY"),
13:     )
```

- **10행**: 음성 인식(STT) 전 과정을 수행하는 `generate()` 메인 함수를 선언합니다.
- **11~13행**: `genai.Client` 객체를 생성합니다. 시스템 환경 변수 `GEMINI_API_KEY`에 저장된 API 키를 자동으로 로드하여 구글 클라우드 서버와의 인증을 마칩니다.

---

## 3. 오디오 파일 유효성 검사 및 로드 (15~24행)

```python
15:     # 입력으로 사용할 오디오 파일 경로
16:     audio_path = "output_new.wav"
17:     if not os.path.exists(audio_path) and os.path.exists("gemini_tts_news.wav"):
18:         print(f"'{audio_path}' 파일이 없어 폴더 내의 'gemini_tts_news.wav' 파일을 입력으로 사용합니다.\n")
19:         audio_path = "gemini_tts_news.wav"
20:     elif not os.path.exists(audio_path):
21:         raise FileNotFoundError(f"오디오 파일 '{audio_path}'을(를) 찾을 수 없습니다. 파일명을 확인해 주세요.")
22: 
23:     with open(audio_path, "rb") as f:
24:         audio_bytes = f.read()
```

- **16행**: 변환할 대상 오디오 파일명(`output_new.wav`)을 지정합니다.
- **17~21행 (예외 방어 및 자동 대체)**:
  - 지정한 `output_new.wav` 파일이 로컬에 없더라도 앞서 TTS 예제에서 생성했던 `gemini_tts_news.wav`가 존재한다면 이를 자동으로 찾아 대체 입력으로 사용하도록 유연하게 처리합니다.
  - 두 파일 모두 존재하지 않을 경우 `FileNotFoundError`를 발생시켜 사용자에게 명확한 에러를 안내합니다.
- **23~24행**: 유효한 오디오 파일을 바이너리 읽기 모드(`"rb"`)로 열어 메모리에 순수 바이트 데이터(`audio_bytes`)로 읽어들입니다.

---

## 4. STT 전용 모델 및 멀티모달 오디오 입력 구성 (26~37행)

```python
26:     model = "gemini-3.5-transcribe"
27:     contents = [
28:         types.Content(
29:             role="user",
30:             parts=[
31:                 types.Part.from_bytes(
32:                     data=audio_bytes,
33:                     mime_type="audio/wav",
34:                 ),
35:             ],
36:         ),
37:     ]
```

- **26행**: 음성 인식 및 전사에 특화된 구글의 차세대 전사 모델인 `"gemini-3.5-transcribe"`를 모델명으로 지정합니다.
- **27~30행**: 사용자(`role="user"`)가 모델에 전달할 프롬프트 콘텐츠 구조를 정의합니다.
- **31~35행 (`types.Part.from_bytes`)**:
  - 메모리에 읽어온 오디오 바이트 데이터(`audio_bytes`)를 MIME 타입(`"audio/wav"`)과 함께 전달합니다.
  - 별도의 텍스트 명령 없이 오디오 파트만 전송해도 전사 전용 모델이 자동으로 발화를 감지하여 텍스트로 풀어냅니다.

---

## 5. 고급 전사 옵션 설정 (38~43행)

```python
38:     generate_content_config = types.GenerateContentConfig(
39:         audio_transcription_config=types.AudioTranscriptionConfig(
40:             word_timestamp=True,
41:             diarization=True,
42:         ),
43:     )
```

- **38~39행**: 모델 생성 옵션을 담는 `GenerateContentConfig` 내에 `AudioTranscriptionConfig` 객체를 정의합니다.
- **40행 (`word_timestamp=True`)**: 단순 텍스트 변환뿐만 아니라, 각 단어가 발화된 정확한 시간(초 단위 타임스탬프) 정보를 함께 추출하도록 요청합니다.
- **41행 (`diarization=True`)**: 화자 분리(Diarization) 기능입니다. 발화자가 여러 명일 경우 화자 1(Speaker 1), 화자 2(Speaker 2) 등으로 구분하여 인식하도록 활성화합니다.

---

## 6. 실시간 스트리밍 출력 및 메인 실행부 (45~54행)

```python
45:     for chunk in client.models.generate_content_stream(
46:         model=model,
47:         contents=contents,
48:         config=generate_content_config,
49:     ):
50:         if text := chunk.text:
51:             print(text, end="")
52: 
53: if __name__ == "__main__":
54:     generate()
```

- **45~49행**: `client.models.generate_content_stream()`을 호출하여 모델이 음성을 인식하는 대로 실시간 텍스트 청크를 스트리밍 방식으로 수신합니다.
- **50~51행 (Walrus 연산자 `:=`)**: 수신된 청크에 텍스트 데이터(`chunk.text`)가 포함되어 있으면 줄바꿈 없이(`end=""`) 콘솔에 즉시 출력하여 실시간 자막처럼 보여줍니다.
- **53~54행**: 파이썬 파일이 직접 실행되었을 때 엔트리포인트로 동작하여 `generate()` 함수를 실행합니다.
