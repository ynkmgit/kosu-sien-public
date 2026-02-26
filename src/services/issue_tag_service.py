"""案件タグサービス

責務: 案件ごとのタグマスタのデータ操作のみ
"""
from database import get_db


class IssueTagService:
    """案件タグ関連のデータ操作"""

    @staticmethod
    def get_list() -> list[dict]:
        """全案件のタグ一覧を取得（フィルター用）"""
        with get_db() as conn:
            rows = conn.execute(
                """SELECT it.id, it.name, it.color, i.cd as issue_cd, i.name as issue_name
                   FROM issue_tag it
                   JOIN issue i ON it.issue_id = i.id
                   ORDER BY i.cd, it.sort_order""",
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all(issue_id: int) -> list[dict]:
        """案件のタグ一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM issue_tag WHERE issue_id = ? ORDER BY sort_order ASC",
                (issue_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(tag_id: int, issue_id: int) -> dict | None:
        """タグをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM issue_tag WHERE id = ? AND issue_id = ?",
                (tag_id, issue_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(issue_id: int, name: str, color: str = "#6b7280", sort_order: int = 0) -> dict:
        """タグ作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO issue_tag (issue_id, name, color, sort_order) VALUES (?, ?, ?, ?)",
                (issue_id, name, color, sort_order)
            )
            row = conn.execute("SELECT * FROM issue_tag WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(tag_id: int, issue_id: int, name: str, color: str = "#6b7280", sort_order: int = 0) -> dict | None:
        """タグ更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE issue_tag SET name = ?, color = ?, sort_order = ? WHERE id = ? AND issue_id = ?",
                (name, color, sort_order, tag_id, issue_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM issue_tag WHERE id = ?", (tag_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(tag_id: int, issue_id: int) -> bool:
        """タグ削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM issue_tag WHERE id = ? AND issue_id = ?",
                (tag_id, issue_id)
            )
        return cur.rowcount > 0

    @staticmethod
    def is_in_use(tag_id: int) -> bool:
        """タグが作業で使用中かチェック"""
        with get_db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM task_tag WHERE tag_id = ?",
                (tag_id,)
            ).fetchone()[0]
        return count > 0
