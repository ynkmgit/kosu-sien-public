"""ステータスサービス

責務: プロジェクトステータスのデータ操作のみ
"""
from database import get_db


class StatusService:
    """プロジェクトステータス関連のデータ操作"""

    @staticmethod
    def get_all(project_id: int) -> list[dict]:
        """プロジェクトのステータス一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM project_status WHERE project_id = ? ORDER BY sort_order ASC",
                (project_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(status_id: int, project_id: int) -> dict | None:
        """ステータスをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM project_status WHERE id = ? AND project_id = ?",
                (status_id, project_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(project_id: int, code: str, name: str, sort_order: int = 0) -> dict:
        """ステータス作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO project_status (project_id, code, name, sort_order) VALUES (?, ?, ?, ?)",
                (project_id, code, name, sort_order)
            )
            row = conn.execute("SELECT * FROM project_status WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(status_id: int, project_id: int, code: str, name: str, sort_order: int = 0) -> dict | None:
        """ステータス更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE project_status SET code = ?, name = ?, sort_order = ? WHERE id = ? AND project_id = ?",
                (code, name, sort_order, status_id, project_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM project_status WHERE id = ?", (status_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(status_id: int, project_id: int) -> bool:
        """ステータス削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM project_status WHERE id = ? AND project_id = ?",
                (status_id, project_id)
            )
        return cur.rowcount > 0

    @staticmethod
    def is_in_use(status_id: int) -> bool:
        """ステータスが案件で使用中かチェック"""
        with get_db() as conn:
            usage = conn.execute(
                "SELECT COUNT(*) FROM issue i JOIN project_status ps ON i.status = ps.code AND i.project_id = ps.project_id WHERE ps.id = ?",
                (status_id,)
            ).fetchone()[0]
        return usage > 0
