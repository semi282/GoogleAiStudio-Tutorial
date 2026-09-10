# 🎬 YouTube 오디오 다운로드 & Gemini STT 웹서비스

유튜브 영상의 링크를 입력하면 자동으로 고음질 오디오 스트림을 추출하여 다운로드하고, Google의 최신 `gemini-3.5-transcribe` 모델을 통해 화자 분리 및 타임스탬프가 포함된 텍스트 트랜스크립트를 생성해 주는 Streamlit 웹 애플리케이션입니다.

---

## 🌟 주요 기능

1. **YouTube 고음질 오디오 추출**:
   - `yt-dlp`를 활용하여 원본 오디오 스트림(`m4a` / `webm`) 직접 다운로드 (별도의 FFmpeg 설치 없이 동작)
2. **Gemini STT 고품질 텍스트 전사**:
   - `gemini-3.5-transcribe` 특화 모델 연동
   - 화자 분리(Speaker Diarization) 및 단어별/구간별 타임스탬프 지원
   - 20MB 미만 파일은 초고속 In-Memory 바이너리 처리, 대용량 파일은 Google File API 연동
3. **인터랙티브 웹 대시보드 (Streamlit)**:
   - 유튜브 영상 썸네일, 제목, 채널, 재생 시간 메타데이터 미리보기
   - 웹 브라우저 내 오디오 즉시 재생 플레이어
   - 실시간 처리 단계 표시 (영상 정보 조회 ➜ 다운로드 ➜ 전사 ➜ 요약)
   - 전사 대본 텍스트(.txt) 원클릭 다운로드
   - Gemini 기반 **AI 3줄 핵심 요약** 생성

---

## 🚀 실행 방법

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정 (선택)
터미널 환경 변수에 API 키를 설정해 두면 웹 실행 시 자동으로 인식됩니다:
- **PowerShell**:
  ```powershell
  $env:GEMINI_API_KEY="본인의_API_키"
  ```
- **CMD**:
  ```cmd
  set GEMINI_API_KEY=본인의_API_키
  ```
*(또는 웹페이지 사이드바에서 직접 API 키를 입력할 수도 있습니다.)*

### 3. 웹 서비스 실행

두 가지 방식 중 원하는 방식을 실행할 수 있습니다:

#### 옵션 A. 모던 HTML 웹 애플리케이션 (추천, 현재 백그라운드 가동 중)
```bash
python youtube_stt_web/server.py
```
* 브라우저에서 **`http://127.0.0.1:8000`** 접속
* 가볍고 빠르며 반응성이 뛰어난 단일 페이지(SPA) HTML 인터페이스를 제공합니다.

#### 옵션 B. Streamlit 대시보드
```bash
streamlit run youtube_stt_web/app.py
```
* 브라우저에서 **`http://localhost:8501`** 접속

---

## 📁 파일 구조

```text
youtube_stt_web/
├── index.html       # 모던 반응형 웹 프론트엔드 (Tailwind CSS)
├── server.py        # FastAPI 백엔드 서버 (포트 8000)
├── app.py           # Streamlit 대시보드 (포트 8501)
├── downloader.py    # yt-dlp 기반 유튜브 오디오 및 메타데이터 추출기
├── transcriber.py   # Gemini 3.5 Transcribe & AI 요약 엔진
├── requirements.txt # 필수 의존성 목록
└── README.md        # 가이드 문서
```
