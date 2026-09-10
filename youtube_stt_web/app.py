import os
import streamlit as st
from google import genai
from downloader import get_video_info, download_audio
from transcriber import transcribe_audio, summarize_transcript

# 페이지 기본 설정
st.set_page_config(
    page_title="YouTube 오디오 & Gemini STT 웹서비스",
    page_icon="🎙️",
    layout="wide",
)

# 커스텀 스타일 (모던 다크/라이트 톤 & 둥근 카드)
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(120deg, #4285F4, #EA4335, #FBBC05, #34A853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .video-card {
        padding: 1.2rem;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 1.5rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 서비스 설정")
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Google Gemini API Key",
        value=env_api_key,
        type="password",
        help="Google AI Studio에서 발급받은 API 키를 입력하세요.",
    )

    st.markdown("---")
    st.subheader("모델 및 옵션")
    selected_model = st.selectbox(
        "STT 모델 선택",
        options=["gemini-3.6-flash", "gemini-3.5-transcribe"],
        index=0,
        help="gemini-3.6-flash는 영어, 한국어 및 다국어를 완벽하게 전사합니다.",
    )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        enable_diarization = st.checkbox("화자 분리", value=True)
    with col_opt2:
        enable_timestamps = st.checkbox("타임스탬프", value=True)

    enable_summary = st.checkbox("💡 텍스트 요약 생성", value=True)

    st.markdown("---")
    st.caption("Google AI Studio & Gemini 3.5 Transcribe Tutorial")

# 메인 헤더
st.markdown('<div class="main-title">🎬 YouTube Audio & Gemini STT Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">유튜브 영상 URL을 입력하면 고음질 오디오를 다운로드하고, Gemini STT를 통해 텍스트로 자동 변환합니다.</div>', unsafe_allow_html=True)

# URL 입력 필드
youtube_url = st.text_input(
    "유튜브 영상 URL을 입력하세요:",
    placeholder="https://www.youtube.com/watch?v=... 또는 https://youtu.be/...",
)

start_button = st.button("🚀 오디오 추출 및 텍스트 전사 시작", type="primary", use_container_width=True)

# 세션 상태 초기화
if "result_data" not in st.session_state:
    st.session_state.result_data = None

if start_button:
    if not youtube_url.strip():
        st.warning("⚠️ 유튜브 영상 URL을 입력해 주세요.")
    elif not api_key.strip():
        st.error("❌ Gemini API Key가 필요합니다. 사이드바에 API 키를 입력해 주세요.")
    else:
        try:
            client = genai.Client(api_key=api_key.strip())

            # 1단계: 비디오 정보 조회
            with st.status("🔍 유튜브 영상 정보 및 오디오 다운로드 중...", expanded=True) as status:
                st.write("1. 영상 메타데이터 분석 중...")
                info = get_video_info(youtube_url)
                st.write(f"✔ 제목: **{info['title']}** (길이: {info['duration']}초)")

                # 2단계: 오디오 다운로드
                st.write("2. 고음질 오디오 스트림 다운로드 중...")
                audio_info = download_audio(youtube_url, output_dir="downloads")
                st.write(f"✔ 오디오 다운로드 완료: `{os.path.basename(audio_info['file_path'])}`")
                status.update(label="✅ 오디오 다운로드 완료! Gemini STT 전사 시작...", state="running")

                # 3단계: Gemini STT 전사
                st.write(f"3. Gemini (`{selected_model}`) 음성 전사 진행 중...")
                transcript_stream = transcribe_audio(
                    client=client,
                    audio_path=audio_info["file_path"],
                    mime_type=audio_info["mime_type"],
                    model_name=selected_model,
                    enable_diarization=enable_diarization,
                    enable_timestamps=enable_timestamps,
                )

                transcript_chunks = []
                for chunk in transcript_stream:
                    transcript_chunks.append(chunk)

                full_transcript = "".join(transcript_chunks)
                st.write("✔ 텍스트 전사 완료!")

                # 4단계: 요약 생성 (선택 시)
                summary_text = ""
                if enable_summary and full_transcript.strip():
                    st.write("4. AI 3줄 핵심 요약 생성 중...")
                    try:
                        summary_text = summarize_transcript(client, full_transcript)
                        st.write("✔ 요약 완료!")
                    except Exception as sum_e:
                        st.write(f"⚠️ 요약 생성 중 알림: {sum_e}")

                status.update(label="🎉 모든 처리가 완료되었습니다!", state="complete", expanded=False)

            # 결과 세션에 저장
            st.session_state.result_data = {
                "info": info,
                "audio_info": audio_info,
                "transcript": full_transcript,
                "summary": summary_text,
            }

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# 결과 출력 화면
if st.session_state.result_data:
    data = st.session_state.result_data
    info = data["info"]
    audio_info = data["audio_info"]
    transcript = data["transcript"]
    summary = data["summary"]

    st.markdown("---")

    # 영상 정보 및 오디오 플레이어 카드
    col1, col2 = st.columns([1, 2])
    with col1:
        if info.get("thumbnail"):
            st.image(info["thumbnail"], use_container_width=True)
    with col2:
        st.subheader(info.get("title", "영상 제목"))
        st.caption(f"채널: **{info.get('channel')}** | 재생 시간: **{info.get('duration', 0)}초**")
        st.markdown("**🎧 다운로드된 오디오 재생:**")
        if os.path.exists(audio_info["file_path"]):
            with open(audio_info["file_path"], "rb") as af:
                st.audio(af.read(), format=audio_info["mime_type"])

    # 탭 구성: 전사 대본 / 핵심 요약
    tab1, tab2 = st.tabs(["📄 전체 트랜스크립트 (Full Transcript)", "💡 AI 핵심 요약 (Summary)"])

    with tab1:
        st.markdown("#### 추출된 텍스트 대본")
        st.text_area(
            "대본 내용",
            value=transcript,
            height=380,
            label_visibility="collapsed",
        )

        col_dl, col_blank = st.columns([1, 4])
        with col_dl:
            st.download_button(
                label="📥 텍스트 파일(.txt) 다운로드",
                data=transcript,
                file_name=f"{info.get('id', 'transcript')}_transcript.txt",
                mime="text/plain",
                use_container_width=True,
            )

    with tab2:
        if summary:
            st.markdown("#### 📌 AI 핵심 요약 리포트")
            st.info(summary)
        else:
            st.write("생성된 요약이 없습니다. 사이드바에서 '요약 생성' 옵션을 켜고 다시 실행해 보세요.")
