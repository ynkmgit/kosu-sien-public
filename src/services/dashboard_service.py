"""ダッシュボードサービス

責務: ダッシュボード表示用のデータ操作のみ
"""
from datetime import date
from database import get_db


class DashboardService:
    """ダッシュボード関連のデータ操作"""

    @staticmethod
    def get_today_hours(target_date: date = None) -> float:
        """指定日の全体合計工数を取得"""
        if target_date is None:
            target_date = date.today()

        with get_db() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(hours), 0) as total FROM work_log WHERE work_date = ?",
                (target_date.isoformat(),)
            ).fetchone()
        return result['total'] if result else 0

    @staticmethod
    def get_monthly_stats(year_month: str) -> dict:
        """月次の予実統計を取得

        Returns:
            {'planned': float, 'actual': float}
        """
        with get_db() as conn:
            result = conn.execute("""
                SELECT
                    COALESCE(SUM(ma.planned_hours), 0) as planned,
                    COALESCE((
                        SELECT SUM(wl.hours) FROM work_log wl
                        WHERE strftime('%Y-%m', wl.work_date) = ?
                    ), 0) as actual
                FROM monthly_assignment ma
                WHERE ma.year_month = ?
            """, (year_month, year_month)).fetchone()

        return {
            'planned': result['planned'] if result else 0,
            'actual': result['actual'] if result else 0,
        }

    @staticmethod
    def get_counts() -> dict:
        """プロジェクト数・有効ユーザー数を取得

        Returns:
            {'project_count': int, 'user_count': int}
        """
        with get_db() as conn:
            project_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM project"
            ).fetchone()['cnt']

            user_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM user WHERE is_active = 1"
            ).fetchone()['cnt']

        return {
            'project_count': project_count,
            'user_count': user_count,
        }
