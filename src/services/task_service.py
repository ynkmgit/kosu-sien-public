"""作業サービス

責務: 作業のデータ操作のみ
"""
import sqlite3

from database import get_db
from exceptions import DuplicateCodeError


class TaskService:
    """作業関連のデータ操作"""

    @staticmethod
    def get_all(issue_id: int = None, project_id: int = None, sort: str = "cd", order: str = "asc", q: str = "") -> list[dict]:
        """作業一覧を取得"""
        allowed_sorts = {"cd", "name"}
        if sort not in allowed_sorts:
            sort = "cd"
        order_dir = "DESC" if order.lower() == "desc" else "ASC"

        with get_db() as conn:
            conditions = []
            params = []

            if issue_id:
                conditions.append("t.issue_id = ?")
                params.append(issue_id)

            if project_id:
                conditions.append("i.project_id = ?")
                params.append(project_id)

            if q:
                like = f"%{q}%"
                conditions.append("(t.cd LIKE ? OR t.name LIKE ?)")
                params.extend([like, like])

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            rows = conn.execute(
                f"""SELECT t.*, i.cd as issue_cd, i.name as issue_name,
                           p.id as project_id, p.cd as project_cd, p.name as project_name
                    FROM task t
                    JOIN issue i ON t.issue_id = i.id
                    JOIN project p ON i.project_id = p.id
                    {where}
                    ORDER BY t.{sort} {order_dir}""",
                params
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(task_id: int) -> dict | None:
        """作業をIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT t.*, i.cd as issue_cd, i.name as issue_name,
                          p.id as project_id, p.cd as project_cd, p.name as project_name
                   FROM task t
                   JOIN issue i ON t.issue_id = i.id
                   JOIN project p ON i.project_id = p.id
                   WHERE t.id = ?""",
                (task_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(issue_id: int, cd: str, name: str, estimate_hours: float = None, status: str = "open") -> dict:
        """作業作成"""
        with get_db() as conn:
            try:
                cur = conn.execute(
                    """INSERT INTO task (cd, issue_id, name, estimate_hours, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (cd, issue_id, name, estimate_hours, status)
                )
            except sqlite3.IntegrityError:
                raise DuplicateCodeError(f"作業CD '{cd}' はこの案件内で既に使用されています")
            row = conn.execute(
                """SELECT t.*, i.cd as issue_cd, i.name as issue_name,
                          p.id as project_id, p.cd as project_cd, p.name as project_name
                   FROM task t
                   JOIN issue i ON t.issue_id = i.id
                   JOIN project p ON i.project_id = p.id
                   WHERE t.id = ?""",
                (cur.lastrowid,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def update(task_id: int, cd: str, name: str, estimate_hours: float = None, status: str = None) -> dict | None:
        """作業更新"""
        with get_db() as conn:
            try:
                if status is not None:
                    cur = conn.execute(
                        """UPDATE task SET cd = ?, name = ?, estimate_hours = ?, status = ?
                           WHERE id = ?""",
                        (cd, name, estimate_hours, status, task_id)
                    )
                else:
                    cur = conn.execute(
                        """UPDATE task SET cd = ?, name = ?, estimate_hours = ?
                           WHERE id = ?""",
                        (cd, name, estimate_hours, task_id)
                    )
            except sqlite3.IntegrityError:
                raise DuplicateCodeError(f"作業CD '{cd}' はこの案件内で既に使用されています")
            if cur.rowcount == 0:
                return None
            row = conn.execute(
                """SELECT t.*, i.cd as issue_cd, i.name as issue_name,
                          p.id as project_id, p.cd as project_cd, p.name as project_name
                   FROM task t
                   JOIN issue i ON t.issue_id = i.id
                   JOIN project p ON i.project_id = p.id
                   WHERE t.id = ?""",
                (task_id,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def update_status(task_id: int, status: str) -> bool:
        """ステータスのみ更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE task SET status = ? WHERE id = ?",
                (status, task_id)
            )
        return cur.rowcount > 0

    @staticmethod
    def delete(task_id: int) -> bool:
        """作業削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
        return cur.rowcount > 0

    @staticmethod
    def get_assignees(task_id: int) -> list[dict]:
        """作業の担当者一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT u.id, u.cd, u.name
                   FROM task_assignee ta
                   JOIN user u ON ta.user_id = u.id
                   WHERE ta.task_id = ?""",
                (task_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id_with_actuals(task_id: int) -> dict | None:
        """作業をIDで実績付きで取得"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT t.*,
                          COALESCE(SUM(w.hours), 0) as actual_hours
                   FROM task t
                   LEFT JOIN work_log w ON t.id = w.task_id
                   WHERE t.id = ?
                   GROUP BY t.id""",
                (task_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_all_with_actuals(issue_id: int) -> list[dict]:
        """作業一覧を実績付きで取得（作業管理ページ用）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT t.*,
                          COALESCE(SUM(w.hours), 0) as actual_hours
                   FROM task t
                   LEFT JOIN work_log w ON t.id = w.task_id
                   WHERE t.issue_id = ?
                   GROUP BY t.id
                   ORDER BY t.cd ASC""",
                (issue_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_issue_totals(issue_id: int) -> dict:
        """案件の集計値を取得（顧客見積はissue_estimate_itemから）"""
        with get_db() as conn:
            # 社内計画と実績
            row = conn.execute(
                """SELECT
                       COALESCE(SUM(t.estimate_hours), 0) as internal_plan_total,
                       COALESCE(SUM(w.hours), 0) as actual_total
                   FROM task t
                   LEFT JOIN work_log w ON t.id = w.task_id
                   WHERE t.issue_id = ?""",
                (issue_id,)
            ).fetchone()
            # 顧客見積（issue_estimate_itemから）
            client_row = conn.execute(
                "SELECT COALESCE(SUM(hours), 0) as total FROM issue_estimate_item WHERE issue_id = ?",
                (issue_id,)
            ).fetchone()
        result = dict(row) if row else {"internal_plan_total": 0, "actual_total": 0}
        result["client_estimate_total"] = client_row["total"] if client_row else 0
        return result

    @staticmethod
    def update_estimate(task_id: int, estimate_hours: float = None) -> bool:
        """社内計画のみ更新（インライン編集用）"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE task SET estimate_hours = ? WHERE id = ?",
                (estimate_hours, task_id)
            )
        return cur.rowcount > 0
