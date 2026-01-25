"""作業サービス

責務: 作業のデータ操作のみ
"""
from database import get_db


class TaskService:
    """作業関連のデータ操作"""

    @staticmethod
    def get_all(issue_id: int = None, project_id: int = None, sort: str = "cd", order: str = "asc", q: str = "") -> list[dict]:
        """作業一覧を取得"""
        allowed_sorts = {"cd", "name", "description"}
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
                conditions.append("(t.cd LIKE ? OR t.name LIKE ? OR t.description LIKE ?)")
                params.extend([like, like, like])

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
    def create(issue_id: int, cd: str, name: str, description: str = "") -> dict:
        """作業作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO task (cd, issue_id, name, description) VALUES (?, ?, ?, ?)",
                (cd, issue_id, name, description)
            )
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
    def update(task_id: int, cd: str, name: str, description: str = "") -> dict | None:
        """作業更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE task SET cd = ?, name = ?, description = ? WHERE id = ?",
                (cd, name, description, task_id)
            )
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
    def update_progress(task_id: int, progress_rate: int) -> bool:
        """進捗率更新"""
        if progress_rate < 0 or progress_rate > 100:
            raise ValueError("進捗率は0-100の範囲で入力してください")

        with get_db() as conn:
            cur = conn.execute(
                "UPDATE task SET progress_rate = ? WHERE id = ?",
                (progress_rate, task_id)
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
                """SELECT u.id, u.cd, u.name, u.email
                   FROM task_assignee ta
                   JOIN user u ON ta.user_id = u.id
                   WHERE ta.task_id = ?""",
                (task_id,)
            ).fetchall()
        return [dict(r) for r in rows]
