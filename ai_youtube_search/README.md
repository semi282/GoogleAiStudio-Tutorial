# 🎬 자막뽑기 AI (Zapok AI) - AI 유튜브 검색기

유튜브 영상 링크를 입력하면 **Google AI Studio 공식 요금표 기준의 예상 비용($ / ₩)을 먼저 확인**한 후,
Google의 음성 전사 특화 모델인 **`Gemini 3.5 Transcribe (v1.0)`**로 정밀 자막을 추출하고,
최신 플래그십 모델인 **`Gemini 3.8 Flash (v1.0)`**로 실시간 Q&A 대화를 나눌 수 있는 프리미엄 웹 서비스입니다.

---

## 🌟 주요 특징

1. **브랜드 컨셉: 자막뽑기 AI (`Zapok AI`)**
   - 유튜브 영상 속 목소리를 1초 만에 텍스트 자막으로 '쏙' 뽑아내는 직관적인 인터페이스.
2. **중간 요금 견적 단계 (Intermediate Cost Estimation)**:
   - 영상을 다운로드하기 전, 영상 길이(초/분)를 기반으로 Google AI Studio 기준 공식 API 요금을 산출합니다.
   - **USD($)와 KRW(₩, 환율 1,400원 기준)**를 동시에 명확하게 안내합니다.
   - **Google AI Studio 무료 티어(일 1,500회 한도)** 이용 시 **0원 (무료)** 안내 뱃지 제공.
   - 사용자가 견적을 확인하고 `[확인하고 자막 뽑기 실행]`을 눌러야 실제 다운로드 및 전사가 진행됩니다.
3. **기능별 모델 분리 및 버전 명시**:
   - **자막 및 타임스탬프 전사**: `Gemini 3.5 Transcribe (v1.0)`
   - **질문하기(Q&A 답변) 및 요약**: `Gemini 3.8 Flash (v1.0)`
4. **접이식 패널 (Collapsible Panels)**:
   - **왼쪽 서랍 (대화 리스트)**: 상단 햄버거 메뉴(☰)로 열고 닫을 수 있으며, 분석했던 이전 영상 목록 보관.
   - **오른쪽 서랍 (스크립트 & 질문하기 & 요약)**: 탭 형태로 구성되어 스크립트 복사, TXT 다운로드, AI 질문 답변 지원.

---

## 🚀 실행 방법

### 1. 웹 서버 실행 (포트 8500)
```bash
python ai_youtube_search/server.py
```

### 2. 브라우저 접속
웹 브라우저를 열고 아래 주소로 접속합니다:
👉 **`http://127.0.0.1:8500`**

---

## 📁 파일 구조

```text
ai_youtube_search/
├── index.html       # 자막뽑기 AI 웹 프론트엔드 (중간 견적 모달 + 다크 테마)
├── server.py        # FastAPI 백엔드 서버 (포트 8500)
├── cost_calc.py     # Google AI Studio 요금 계산 엔진 (USD & KRW)
├── downloader.py    # 유튜브 메타데이터 및 오디오 다운로더
├── transcriber.py   # Gemini 3.5 Transcribe & Gemini 3.8 Flash 엔진
├── requirements.txt # 의존성 목록
└── README.md        # 안내 문서
```
