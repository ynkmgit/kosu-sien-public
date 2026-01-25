"""プロジェクトサービス

責務: プロジェクトのデータ操作のみ
"""
from database import get_db, create_default_statuses


class ProjectService:
    """プロジェクト関連のデータ操作"""

    @staticmethod
    def get_all(sort: str = "cd", order: str = "asc", q: str = "") -> list[dict]:
        """プロジェクト一覧を取得"""
        allowed_sorts = {"cd", "name", "description"}
        if sort not in allowed_sorts:
            sort = "cd"
        order_dir = "DESC" if order.lower() == "desc" else "ASC"

        with get_db() as conn:
            if q:
                like = f"%{q}%"
                rows = conn.execute(
                    f"SELECT * FROM project WHERE cd LIKE ? OR name LIKE ? OR description LIKE ? ORDER BY {sort} {order_dir}",
                    (like, like, like)
                ).fetchall()
            else:
                rows = conn.execute(f"SELECT * FROM project ORDER BY {sort} {order_dir}").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(project_id: int) -> dict | None:
        """プロジェクトをIDで取得"""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_list() -> list[dict]:
        """プロジェクト一覧を取得（フィルター用の最小フィールド）"""
        with get_db() as conn:
            rows = conn.execute("SELECT id, cd, name FROM project ORDER BY cd").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def create(cd: str, name: str, description: str = "") -> dict:
        """プロジェクト作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO project (cd, name, description) VALUES (?, ?, ?)",
                (cd, name, description)
            )
            project_id = cur.lastrowid
            create_default_statuses(conn, project_id)
            row = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
        return dict(row)

    @staticmethod
    def update(project_id: int, cd: str, name: str, description: str = "") -> dict | None:
        """プロジェクト更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE project SET cd = ?, name = ?, description = ? WHERE id = ?",
                (cd, name, description, project_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM project WHERE id = ?", (project_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(project_id: int) -> bool:
        """プロジェクト削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM project WHERE id = ?", (project_id,))
        return cur.rowcount > 0

    @staticmethod
    def get_summary(project_id: int) -> dict:
        """プロジェクトサマリー取得"""
        with get_db() as conn:
            issue_count = conn.execute(
                "SELECT COUNT(*) FROM issue WHERE project_id = ?", (project_id,)
            ).fetchone()[0]

            task_count = conn.execute(
                "SELECT COUNT(*) FROM task t JOIN issue i ON t.issue_id = i.id WHERE i.project_id = ?",
                (project_id,)
            ).fetchone()[0]

            estimate_total = conn.execute(
                """SELECT COALESCE(SUM(e.hours), 0)
                   FROM issue_estimate_item e
                   JOIN issue i ON e.issue_id = i.id
                   WHERE i.project_id = ?""",
                (project_id,)
            ).fetchone()[0] or 0

            actual_total = conn.execute(
                """SELECT COALESCE(SUM(w.hours), 0)
                   FROM work_log w
                   JOIN task t ON w.task_id = t.id
                   JOIN issue i ON t.issue_id = i.id
                   WHERE i.project_id = ?""",
                (project_id,)
            ).fetchone()[0] or 0

        consumption_rate = (actual_total / estimate_total * 100) if estimate_total > 0 else 0

        return {
            "issue_count": issue_count,
            "task_count": task_count,
            "estimate_total": estimate_total,
            "actual_total": actual_total,
            "consumption_rate": round(consumption_rate, 1),
        }

    @staticmethod
    def get_recent_issues(project_id: int, limit: int = 5) -> list[dict]:
        """最近の案件取得（見積・実績付き）"""
        with get_db() as conn:
            issues = conn.execute(
                """SELECT i.*, ps.name as status_name,
                          COALESCE((SELECT SUM(hours) FROM issue_estimate_item WHERE issue_id = i.id), 0) as estimate,
                          COALESCE((SELECT SUM(w.hours) FROM work_log w JOIN task t ON w.task_id = t.id WHERE t.issue_id = i.id), 0) as actual
                   FROM issue i
                   LEFT JOIN project_status ps ON i.project_id = ps.project_id AND i.status = ps.code
                   WHERE i.project_id = ?
                   ORDER BY i.id DESC
                   LIMIT ?""",
                (project_id, limit)
            ).fetchall()
        return [dict(row) for row in issues]
