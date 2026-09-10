# 🎬 YouTube Transcriber & AI Assistant 웹서비스

첨부해주신 유튜브 시청 화면 UI를 기반으로, 유튜브 영상 링크를 입력하면 실제 유튜브 영상 플레이어와 함께 고음질 음성 전사(STT), AI 대본 Q&A, 그리고 대화 히스토리를 제공하는 웹 서비스입니다.

---

## 🌟 주요 기능

1. **YouTube 실제 플레이어 화면 레이아웃 (다크 테마)**:
   - 상단 중앙 검색창을 통해 **유튜브 영상 URL 입력 및 돋보기 검색 실행**
   - 중앙에 실제 유튜브 비디오 플레이어(Iframe)가 자동 연동되어 영상과 오디오를 함께 시청 가능
   - 불필요한 요소(빨간색 X 표시된 구독, 좋아요/싫어요, 공유, 저장, 마이크, 알림, 프로필 등)는 모두 제외하고 깔끔하게 구현
2. **접이식 패널 (Collapsible Drawers)**:
   - **왼쪽 서랍 (대화 리스트)**: 상단 햄버거 메뉴(☰)로 언제든지 접고 펼칠 수 있으며, 분석했던 영상 목록과 대화 기록을 보관 및 로드
   - **오른쪽 패널 (스크립트 & 질문하기)**: 
     - **[📄 스크립트]**: 타임스탬프 및 화자 분리가 포함된 전체 대본 뷰어 (복사 및 TXT 다운로드 지원)
     - **[✨ 질문하기]**: 영상 대본을 기반으로 무엇이든 질문하고 답변받는 Gemini AI 챗봇
     - **[💡 요약]**: 영상 핵심 내용 3줄 요약 리포트
3. **Gemini 3.6 Flash 기반 다국어 고성능 STT**:
   - 한국어, 영어, 혼합 발화까지 누락 없이 높은 정확도로 전사
   - Google AI Studio 무료 티어(Free Tier) 지원

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
