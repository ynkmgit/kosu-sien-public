"""報告テンプレートサービス

責務: 報告テンプレートのデータ操作のみ
"""
from database import get_db


class ReportTemplateService:
    """報告テンプレート関連のデータ操作"""

    @staticmethod
    def get_all() -> list[dict]:
        """全テンプレートを取得（sort_order順）"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM report_template ORDER BY sort_order, id"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(template_id: int) -> dict | None:
        """テンプレートをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM report_template WHERE id = ?", (template_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name: str, body: str, options: str = '{}', sort_order: int = 0) -> dict:
        """テンプレート作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO report_template (name, body, options, sort_order) VALUES (?, ?, ?, ?)",
                (name, body, options, sort_order)
            )
            row = conn.execute(
                "SELECT * FROM report_template WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def update(template_id: int, name: str, body: str, options: str = '{}') -> dict | None:
        """テンプレート更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE report_template SET name = ?, body = ?, options = ? WHERE id = ?",
                (name, body, options, template_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT * FROM report_template WHERE id = ?", (template_id,)
            ).fetchone()
        return dict(row)

    @staticmethod
    def delete(template_id: int) -> bool:
        """テンプレート削除（最後の1件は削除不可）"""
        with get_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM report_template").fetchone()[0]
            if count <= 1:
                return False
            cur = conn.execute(
                "DELETE FROM report_template WHERE id = ?", (template_id,)
            )
        return cur.rowcount > 0
