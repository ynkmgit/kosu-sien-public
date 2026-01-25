"""実績サービス

責務: 工数実績のデータ操作のみ
"""
from datetime import date
from database import get_db


class WorkLogService:
    """工数実績関連のデータ操作"""

    @staticmethod
    def get_all(
        user_id: int = None,
        task_id: int = None,
        project_id: int = None,
        issue_id: int = None,
        start_date: date = None,
        end_date: date = None
    ) -> list[dict]:
        """実績一覧を取得"""
        with get_db() as conn:
            conditions = []
            params = []

            if user_id:
                conditions.append("wl.user_id = ?")
                params.append(user_id)

            if task_id:
                conditions.append("wl.task_id = ?")
                params.append(task_id)

            if project_id:
                conditions.append("p.id = ?")
                params.append(project_id)

            if issue_id:
                conditions.append("i.id = ?")
                params.append(issue_id)

            if start_date:
                conditions.append("wl.work_date >= ?")
                params.append(start_date.isoformat())

            if end_date:
                conditions.append("wl.work_date <= ?")
                params.append(end_date.isoformat())

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            rows = conn.execute(
                f"""SELECT wl.*,
                           t.cd as task_cd, t.name as task_name,
                           i.id as issue_id, i.cd as issue_cd, i.name as issue_name,
                           p.id as project_id, p.cd as project_cd, p.name as project_name,
                           u.cd as user_cd, u.name as user_name
                    FROM work_log wl
                    JOIN task t ON wl.task_id = t.id
                    JOIN issue i ON t.issue_id = i.id
                    JOIN project p ON i.project_id = p.id
                    JOIN user u ON wl.user_id = u.id
                    {where}
                    ORDER BY wl.work_date DESC, p.cd, i.cd, t.cd""",
                params
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(work_log_id: int) -> dict | None:
        """実績をIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT wl.*,
                          t.cd as task_cd, t.name as task_name,
                          i.id as issue_id, i.cd as issue_cd, i.name as issue_name,
                          p.id as project_id, p.cd as project_cd, p.name as project_name,
                          u.cd as user_cd, u.name as user_name
                   FROM work_log wl
                   JOIN task t ON wl.task_id = t.id
                   JOIN issue i ON t.issue_id = i.id
                   JOIN project p ON i.project_id = p.id
                   JOIN user u ON wl.user_id = u.id
                   WHERE wl.id = ?""",
                (work_log_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def upsert(task_id: int, user_id: int, work_date: date, hours: float) -> dict | None:
        """実績を追加/更新"""
        if hours < 0:
            raise ValueError("時間は0以上で入力してください")

        if hours > 0 and (hours * 4) % 1 != 0:
            raise ValueError("時間は0.25刻みで入力してください")

        with get_db() as conn:
            # 担当割当の確認
            assignee = conn.execute(
                "SELECT id FROM task_assignee WHERE task_id = ? AND user_id = ?",
                (task_id, user_id)
            ).fetchone()
            if not assignee:
                raise ValueError("この作業の担当ではありません")

            # 既存レコード確認
            existing = conn.execute(
                "SELECT id FROM work_log WHERE task_id = ? AND user_id = ? AND work_date = ?",
                (task_id, user_id, work_date.isoformat())
            ).fetchone()

            if hours == 0:
                if existing:
                    conn.execute("DELETE FROM work_log WHERE id = ?", (existing['id'],))
                return None
            elif existing:
                conn.execute(
                    "UPDATE work_log SET hours = ? WHERE id = ?",
                    (hours, existing['id'])
                )
                work_log_id = existing['id']
            else:
                cur = conn.execute(
                    "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, ?, ?)",
                    (task_id, user_id, work_date.isoformat(), hours)
                )
                work_log_id = cur.lastrowid

        return WorkLogService.get_by_id(work_log_id)

    @staticmethod
    def delete(work_log_id: int) -> bool:
        """実績削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM work_log WHERE id = ?", (work_log_id,))
        return cur.rowcount > 0

    @staticmethod
    def get_daily_total(user_id: int, work_date: date) -> float:
        """指定日の合計時間を取得"""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(hours), 0) FROM work_log WHERE user_id = ? AND work_date = ?",
                (user_id, work_date.isoformat())
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def get_monthly_total(user_id: int = None, year_month: str = None) -> float:
        """月次合計時間を取得"""
        with get_db() as conn:
            conditions = []
            params = []

            if year_month:
                conditions.append("strftime('%Y-%m', work_date) = ?")
                params.append(year_month)

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            result = conn.execute(
                f"SELECT COALESCE(SUM(hours), 0) FROM work_log {where}",
                params
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def get_assignee_rows(user_ids: list[int] = None, project_ids: list[int] = None, issue_ids: list[int] = None) -> list[dict]:
        """担当割当から行データを取得"""
        with get_db() as conn:
            query = """
                SELECT
                    ta.id as assignee_id,
                    ta.task_id,
                    ta.user_id,
                    t.cd as task_cd,
                    t.name as task_name,
                    t.progress_rate,
                    i.id as issue_id,
                    i.cd as issue_cd,
                    i.name as issue_name,
                    p.id as project_id,
                    p.cd as project_cd,
                    p.name as project_name,
                    u.cd as user_cd,
                    u.name as user_name
                FROM task_assignee ta
                JOIN task t ON ta.task_id = t.id
                JOIN issue i ON t.issue_id = i.id
                JOIN project p ON i.project_id = p.id
                JOIN user u ON ta.user_id = u.id
                WHERE (u.is_active = 1 OR u.is_active IS NULL)
            """
            params = []

            if user_ids:
                placeholders = ",".join("?" * len(user_ids))
                query += f" AND ta.user_id IN ({placeholders})"
                params.extend(user_ids)

            if project_ids:
                placeholders = ",".join("?" * len(project_ids))
                query += f" AND p.id IN ({placeholders})"
                params.extend(project_ids)

            if issue_ids:
                placeholders = ",".join("?" * len(issue_ids))
                query += f" AND i.id IN ({placeholders})"
                params.extend(issue_ids)

            query += " ORDER BY p.cd, i.cd, t.cd, u.cd"

            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_work_logs_for_dates(dates: list[date], user_ids: list[int] = None, project_ids: list[int] = None, issue_ids: list[int] = None) -> dict:
        """指定日付リストの実績データを取得

        Returns:
            {(task_id, user_id, work_date): {'id': id, 'hours': hours}}
        """
        if not dates:
            return {}

        with get_db() as conn:
            start_date = dates[0].isoformat()
            end_date = dates[-1].isoformat()

            query = """
                SELECT wl.id, wl.task_id, wl.user_id, wl.work_date, wl.hours
                FROM work_log wl
                JOIN task t ON wl.task_id = t.id
                JOIN issue i ON t.issue_id = i.id
                JOIN project p ON i.project_id = p.id
                WHERE wl.work_date >= ? AND wl.work_date <= ?
            """
            params = [start_date, end_date]

            if user_ids:
                placeholders = ",".join("?" * len(user_ids))
                query += f" AND wl.user_id IN ({placeholders})"
                params.extend(user_ids)

            if project_ids:
                placeholders = ",".join("?" * len(project_ids))
                query += f" AND p.id IN ({placeholders})"
                params.extend(project_ids)

            if issue_ids:
                placeholders = ",".join("?" * len(issue_ids))
                query += f" AND i.id IN ({placeholders})"
                params.extend(issue_ids)

            rows = conn.execute(query, params).fetchall()

        return {
            (r['task_id'], r['user_id'], r['work_date']): {'id': r['id'], 'hours': r['hours']}
            for r in rows
        }

    @staticmethod
    def get_user_daily_logs(user_id: int, target_date: date) -> list[dict]:
        """指定ユーザーの指定日の実績を取得（業務終了報告用）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT
                    wl.hours,
                    t.name as task_name,
                    t.progress_rate,
                    i.cd as issue_cd,
                    i.name as issue_name,
                    p.cd as project_cd,
                    p.name as project_name
                FROM work_log wl
                JOIN task t ON wl.task_id = t.id
                JOIN issue i ON t.issue_id = i.id
                JOIN project p ON i.project_id = p.id
                WHERE wl.user_id = ? AND wl.work_date = ?
                ORDER BY p.cd, i.cd, t.name""",
                (user_id, target_date.isoformat())
            ).fetchall()
        return [dict(r) for r in rows]
