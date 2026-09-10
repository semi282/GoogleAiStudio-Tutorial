import os
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

CURRENT_DIR = Path(__file__).resolve().parent
CSV_FILE_PATH = CURRENT_DIR / "transcripts.csv"

CSV_HEADERS = [
    "url",
    "video_id",
    "title",
    "channel",
    "duration",
    "transcript",
    "summary",
    "created_at",
]


def extract_video_id(url: str) -> str:
    """유튜브 URL에서 video_id를 정규식으로 추출합니다."""
    if not url:
        return ""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/embed\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url.strip()


def init_csv_file():
    """CSV 파일이 없으면 헤더와 함께 초기화합니다."""
    if not CSV_FILE_PATH.exists():
        with open(CSV_FILE_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def get_cached_transcript(url: str) -> Optional[Dict[str, Any]]:
    """입력된 URL 또는 video_id가 CSV에 이미 존재하는지 조회하여 캐시된 데이터를 반환합니다."""
    init_csv_file()
    target_id = extract_video_id(url)

    if not CSV_FILE_PATH.exists():
        return None

    try:
        with open(CSV_FILE_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_url = row.get("url", "").strip()
                row_id = row.get("video_id", "").strip()
                if (target_id and row_id == target_id) or (url.strip() and row_url == url.strip()):
                    try:
                        duration_int = int(row.get("duration", 0))
                    except ValueError:
                        duration_int = 0

                    return {
                        "id": row_id or target_id,
                        "url": row_url,
                        "title": row.get("title", ""),
                        "channel": row.get("channel", ""),
                        "duration": duration_int,
                        "transcript": row.get("transcript", ""),
                        "summary": row.get("summary", ""),
                        "created_at": row.get("created_at", ""),
                        "is_cached": True,
                    }
    except Exception as e:
        print(f"[CSV Cache Error] {e}")

    return None


def save_transcript_to_csv(data: Dict[str, Any]) -> bool:
    """새로운 전사 결과를 CSV 파일에 추가(저장)합니다. 기존 항목이 있다면 최신 정보로 업데이트합니다."""
    init_csv_file()
    video_id = data.get("id") or extract_video_id(data.get("url", ""))
    url = data.get("url", "")
    title = data.get("title", "")
    channel = data.get("channel", "")
    duration = str(data.get("duration", 0))
    transcript = data.get("transcript", "")
    summary = data.get("summary", "")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows: List[Dict[str, str]] = []
    found = False

    try:
        with open(CSV_FILE_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if (video_id and r.get("video_id") == video_id) or (url and r.get("url") == url):
                    # 기존 데이터 업데이트
                    r["url"] = url
                    r["video_id"] = video_id
                    r["title"] = title
                    r["channel"] = channel
                    r["duration"] = duration
                    r["transcript"] = transcript
                    r["summary"] = summary
                    r["created_at"] = created_at
                    found = True
                rows.append(r)

        if not found:
            rows.append({
                "url": url,
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "duration": duration,
                "transcript": transcript,
                "summary": summary,
                "created_at": created_at,
            })

        with open(CSV_FILE_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

        return True
    except Exception as e:
        print(f"[CSV Save Error] {e}")
        return False


def get_all_cached_history() -> List[Dict[str, Any]]:
    """저장된 모든 전사 히스토리 목록을 반환합니다."""
    init_csv_file()
    history = []
    try:
        with open(CSV_FILE_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    duration_int = int(row.get("duration", 0))
                except ValueError:
                    duration_int = 0
                history.append({
                    "id": row.get("video_id", ""),
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                    "channel": row.get("channel", ""),
                    "duration": duration_int,
                    "transcript": row.get("transcript", ""),
                    "summary": row.get("summary", ""),
                    "created_at": row.get("created_at", ""),
                })
        history.reverse()  # 최신순 정렬
    except Exception as e:
        print(f"[CSV History Read Error] {e}")
    return history
