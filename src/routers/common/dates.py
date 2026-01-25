"""日付関連ユーティリティ

責務: 月・週の計算、パース、フォーマット
"""
from datetime import datetime, date, timedelta

from fastapi import HTTPException


# === 月関連ユーティリティ ===

def get_current_month() -> str:
    """現在の年月をYYYY-MM形式で取得"""
    return datetime.now().strftime("%Y-%m")


def parse_month(month_str: str) -> str:
    """年月文字列を検証してYYYY-MM形式で返す"""
    try:
        parsed = datetime.strptime(month_str, "%Y-%m")
        return parsed.strftime("%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")


def get_prev_next_month(year_month: str) -> tuple[str, str]:
    """前月・翌月を計算"""
    dt = datetime.strptime(year_month, "%Y-%m")
    year, month = dt.year, dt.month

    # 前月
    if month == 1:
        prev_month = f"{year - 1}-12"
    else:
        prev_month = f"{year}-{month - 1:02d}"

    # 翌月
    if month == 12:
        next_month = f"{year + 1}-01"
    else:
        next_month = f"{year}-{month + 1:02d}"

    return prev_month, next_month


# === 週関連ユーティリティ ===

WEEKDAY_NAMES = ["月", "火", "水", "木", "金", "土", "日"]


def get_week_dates(target_date: date = None) -> list[date]:
    """指定日を含む週（月〜日）の日付リストを返す"""
    if target_date is None:
        target_date = date.today()

    # 月曜日を週の開始とする（weekday: 月=0, 日=6）
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)

    return [monday + timedelta(days=i) for i in range(7)]


def get_prev_next_week(target_date: date) -> tuple[date, date]:
    """前週・翌週の基準日（月曜日）を返す"""
    days_since_monday = target_date.weekday()
    this_monday = target_date - timedelta(days=days_since_monday)

    prev_monday = this_monday - timedelta(days=7)
    next_monday = this_monday + timedelta(days=7)

    return prev_monday, next_monday


def get_week_range_str(dates: list[date]) -> str:
    """週の範囲を文字列で返す（例: 1/13(月) - 1/19(日)）"""
    if not dates:
        return ""
    start = dates[0]
    end = dates[-1]
    start_wd = WEEKDAY_NAMES[start.weekday()]
    end_wd = WEEKDAY_NAMES[end.weekday()]
    return f"{start.month}/{start.day}({start_wd}) - {end.month}/{end.day}({end_wd})"


def parse_week_date(date_str: str) -> date:
    """日付文字列をdateに変換（YYYY-MM-DD形式）"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
