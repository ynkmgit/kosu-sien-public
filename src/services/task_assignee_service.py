"""担当割当サービス

責務: 担当割当のデータ操作のみ
"""
from database import get_db


class TaskAssigneeService:
    """担当割当関連のデータ操作"""

    @staticmethod
    def get_project_tasks_with_issues(project_id: int) -> list[dict]:
        """プロジェクトの全作業を案件情報付きで取得"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT t.*, i.id as issue_id, i.cd as issue_cd, i.name as issue_name
                   FROM task t
                   JOIN issue i ON t.issue_id = i.id
                   WHERE i.project_id = ?
                   ORDER BY i.cd, t.sort_order, t.cd""",
                (project_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_assignments(project_id: int) -> dict:
        """プロジェクトの全担当割当を取得

        Returns:
            {(task_id, user_id): assignment_id}
        """
        with get_db() as conn:
            rows = conn.execute(
                """SELECT ta.id, ta.task_id, ta.user_id
                   FROM task_assignee ta
                   JOIN task t ON ta.task_id = t.id
                   JOIN issue i ON t.issue_id = i.id
                   WHERE i.project_id = ?""",
                (project_id,)
            ).fetchall()
        return {(r['task_id'], r['user_id']): r['id'] for r in rows}

    @staticmethod
    def get_task_in_project(task_id: int, project_id: int) -> dict | None:
        """作業の存在確認とプロジェクト所属確認"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT t.id FROM task t
                   JOIN issue i ON t.issue_id = i.id
                   WHERE t.id = ? AND i.project_id = ?""",
                (task_id, project_id)
            ).fetchone()
        return dict(row) if row else None

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
    def get_assignment(task_id: int, user_id: int) -> dict | None:
        """既存の割当を確認"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT id FROM task_assignee WHERE task_id = ? AND user_id = ?",
                (task_id, user_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_assignment_in_project(assignment_id: int, project_id: int) -> dict | None:
        """割当の存在確認とプロジェクト所属確認"""
        with get_db() as conn:
            row = conn.execute(
                """SELECT ta.id FROM task_assignee ta
                   JOIN task t ON ta.task_id = t.id
                   JOIN issue i ON t.issue_id = i.id
                   WHERE ta.id = ? AND i.project_id = ?""",
                (assignment_id, project_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(task_id: int, user_id: int) -> int:
        """担当割当作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO task_assignee (task_id, user_id) VALUES (?, ?)",
                (task_id, user_id)
            )
        return cur.lastrowid

    @staticmethod
    def delete(assignment_id: int) -> bool:
        """担当割当削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM task_assignee WHERE id = ?", (assignment_id,))
        return cur.rowcount > 0

    @staticmethod
    def toggle(task_id: int, user_id: int) -> bool:
        """担当割当のトグル（存在すれば削除、なければ追加）

        Returns:
            True if assigned after toggle, False if unassigned
        """
        with get_db() as conn:
            existing = conn.execute(
                "SELECT id FROM task_assignee WHERE task_id = ? AND user_id = ?",
                (task_id, user_id)
            ).fetchone()

            if existing:
                conn.execute("DELETE FROM task_assignee WHERE id = ?", (existing['id'],))
                return False
            else:
                conn.execute(
                    "INSERT INTO task_assignee (task_id, user_id) VALUES (?, ?)",
                    (task_id, user_id)
                )
                return True
