"""作業月次計画サービス

責務: 作業×担当者×月ごとの予定工数（山積工数）のデータ操作
"""
from database import get_db


class TaskMonthlyPlanService:
    """作業月次計画関連のデータ操作"""

    @staticmethod
    def get_plans_for_months(months: list[str]) -> dict:
        """指定月リストの全計画を一括取得

        Returns:
            {(task_id, user_id, year_month): planned_hours}
        """
        if not months:
            return {}
        with get_db() as conn:
            placeholders = ",".join("?" * len(months))
            rows = conn.execute(
                f"""SELECT task_id, user_id, year_month, planned_hours
                    FROM task_monthly_plan
                    WHERE year_month IN ({placeholders})""",
                months
            ).fetchall()
        return {
            (r['task_id'], r['user_id'], r['year_month']): r['planned_hours']
            for r in rows
        }

    @staticmethod
    def get_plan_totals() -> dict:
        """全月の山積工数合計をタスク×ユーザー単位で取得

        Returns:
            {(task_id, user_id): total_planned_hours}
        """
        with get_db() as conn:
            rows = conn.execute(
                """SELECT task_id, user_id, SUM(planned_hours) AS total
                   FROM task_monthly_plan
                   GROUP BY task_id, user_id"""
            ).fetchall()
        return {
            (r['task_id'], r['user_id']): r['total']
            for r in rows
        }

    @staticmethod
    def upsert(task_id: int, user_id: int, year_month: str, planned_hours: float) -> int | None:
        """計画追加/更新

        0→DELETE, >0→INSERT/UPDATE

        Returns:
            plan_id if created/updated, None if deleted
        """
        if planned_hours < 0:
            raise ValueError("工数は0以上で入力してください")

        with get_db() as conn:
            existing = conn.execute(
                """SELECT id FROM task_monthly_plan
                   WHERE task_id = ? AND user_id = ? AND year_month = ?""",
                (task_id, user_id, year_month)
            ).fetchone()

            if planned_hours == 0:
                if existing:
                    conn.execute("DELETE FROM task_monthly_plan WHERE id = ?", (existing['id'],))
                return None
            elif existing:
                conn.execute(
                    "UPDATE task_monthly_plan SET planned_hours = ? WHERE id = ?",
                    (planned_hours, existing['id'])
                )
                return existing['id']
            else:
                cur = conn.execute(
                    """INSERT INTO task_monthly_plan (task_id, user_id, year_month, planned_hours)
                       VALUES (?, ?, ?, ?)""",
                    (task_id, user_id, year_month, planned_hours)
                )
                return cur.lastrowid
