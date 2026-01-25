"""月次アサインサービス

責務: 月次アサインのデータ操作のみ
"""
from datetime import datetime
from database import get_db


class MonthlyAssignmentService:
    """月次アサイン関連のデータ操作"""

    @staticmethod
    def get_assignments_for_month(year_month: str) -> dict:
        """指定月の全アサインを取得

        Returns:
            {(user_id, project_id): {'id': id, 'hours': planned_hours}}
        """
        with get_db() as conn:
            rows = conn.execute(
                """SELECT id, user_id, project_id, planned_hours
                   FROM monthly_assignment
                   WHERE year_month = ?""",
                (year_month,)
            ).fetchall()
        return {(r['user_id'], r['project_id']): {'id': r['id'], 'hours': r['planned_hours']} for r in rows}

    @staticmethod
    def get_actuals_for_month(year_month: str) -> dict:
        """指定月の実績を取得（ユーザー×プロジェクト）

        Returns:
            {(user_id, project_id): actual_hours}
        """
        # year_monthは"YYYY-MM"形式なので、work_dateの開始日と終了日を計算
        start_date = f"{year_month}-01"
        dt = datetime.strptime(year_month, "%Y-%m")
        if dt.month == 12:
            end_date = f"{dt.year + 1}-01-01"
        else:
            end_date = f"{dt.year}-{dt.month + 1:02d}-01"

        with get_db() as conn:
            rows = conn.execute(
                """SELECT w.user_id, i.project_id, COALESCE(SUM(w.hours), 0) as total
                   FROM work_log w
                   JOIN task t ON w.task_id = t.id
                   JOIN issue i ON t.issue_id = i.id
                   WHERE w.work_date >= ? AND w.work_date < ?
                   GROUP BY w.user_id, i.project_id""",
                (start_date, end_date)
            ).fetchall()
        return {(r['user_id'], r['project_id']): r['total'] for r in rows}

    @staticmethod
    def get_user_with_status(user_id: int) -> dict | None:
        """ユーザーの存在確認と有効状態を取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, is_active FROM user WHERE id = ?",
                (user_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_project(project_id: int) -> dict | None:
        """プロジェクトの存在確認"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM project WHERE id = ?",
                (project_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_assignment(user_id: int, project_id: int, year_month: str) -> dict | None:
        """既存のアサインを確認"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT id FROM monthly_assignment
                   WHERE user_id = ? AND project_id = ? AND year_month = ?""",
                (user_id, project_id, year_month)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_id(assignment_id: int) -> dict | None:
        """アサインをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM monthly_assignment WHERE id = ?",
                (assignment_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def upsert(user_id: int, project_id: int, year_month: str, planned_hours: float) -> int | None:
        """アサイン追加/更新

        Returns:
            assignment_id if created/updated, None if deleted
        """
        if planned_hours < 0:
            raise ValueError("工数は0以上で入力してください")

        with get_db() as conn:
            existing = conn.execute(
                """SELECT id FROM monthly_assignment
                   WHERE user_id = ? AND project_id = ? AND year_month = ?""",
                (user_id, project_id, year_month)
            ).fetchone()

            if planned_hours == 0:
                if existing:
                    conn.execute("DELETE FROM monthly_assignment WHERE id = ?", (existing['id'],))
                return None
            elif existing:
                conn.execute(
                    "UPDATE monthly_assignment SET planned_hours = ? WHERE id = ?",
                    (planned_hours, existing['id'])
                )
                return existing['id']
            else:
                cur = conn.execute(
                    """INSERT INTO monthly_assignment (user_id, project_id, year_month, planned_hours)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, project_id, year_month, planned_hours)
                )
                return cur.lastrowid

    @staticmethod
    def delete(assignment_id: int) -> bool:
        """アサイン削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM monthly_assignment WHERE id = ?", (assignment_id,))
        return cur.rowcount > 0
