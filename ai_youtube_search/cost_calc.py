from typing import Dict, Any


USD_TO_KRW = 1400.0  # 기준 환율 (1 USD = 1,400 KRW)
AUDIO_INPUT_PER_SEC_USD = 0.00002  # 초당 $0.00002 (시간당 약 $0.072)
TEXT_OUTPUT_PER_M_TOKENS_USD = 0.60  # 100만 출력 토큰당 $0.60
AVG_SPEECH_TOKENS_PER_SEC = 3.0  # 음성 1초당 평균 생성 텍스트 토큰 수 (약 3 토큰)


def format_duration(seconds: int) -> str:
    """초 단위 시간을 'X시간 Y분 Z초' 또는 'Y분 Z초' 형태로 포맷팅합니다."""
    if seconds <= 0:
        return "0초"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    rem_seconds = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}시간")
    if minutes > 0:
        parts.append(f"{minutes}분")
    if rem_seconds > 0 or not parts:
        parts.append(f"{rem_seconds}초")
    return " ".join(parts)


def calculate_video_cost(duration_seconds: int) -> Dict[str, Any]:
    """영상 길이를 기반으로 Google AI Studio 기준 예상 사용 요금(USD 및 KRW)을 산출합니다."""
    sec = max(1, int(duration_seconds))

    # 1. 오디오 입력 비용 계산
    audio_cost_usd = sec * AUDIO_INPUT_PER_SEC_USD

    # 2. 텍스트 자막 출력 비용 계산 (예상)
    estimated_tokens = int(sec * AVG_SPEECH_TOKENS_PER_SEC)
    text_cost_usd = (estimated_tokens / 1_000_000.0) * TEXT_OUTPUT_PER_M_TOKENS_USD

    # 3. 총합
    total_cost_usd = audio_cost_usd + text_cost_usd
    total_cost_krw = total_cost_usd * USD_TO_KRW

    return {
        "duration_seconds": sec,
        "duration_formatted": format_duration(sec),
        "estimated_tokens": estimated_tokens,
        "audio_cost_usd": round(audio_cost_usd, 6),
        "text_cost_usd": round(text_cost_usd, 6),
        "total_cost_usd": round(total_cost_usd, 4),
        "total_cost_usd_formatted": f"${total_cost_usd:.4f}",
        "total_cost_krw": round(total_cost_krw, 1),
        "total_cost_krw_formatted": f"약 {round(total_cost_krw, 1):,.1f}원",
        "exchange_rate": USD_TO_KRW,
        "is_free_tier_eligible": True,
        "free_tier_notice": "Google AI Studio 기본 무료 티어(Free Tier, 일 1,500회 한도) 이용 시 실제 청구 금액은 0원(무료)입니다.",
    }
