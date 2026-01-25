"""案件見積サービス

責務: 案件見積内訳のデータ操作のみ
"""
from database import get_db


class IssueEstimateService:
    """案件見積内訳関連のデータ操作"""

    @staticmethod
    def get_all(issue_id: int) -> list[dict]:
        """案件の見積内訳一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM issue_estimate_item WHERE issue_id = ? ORDER BY sort_order, id",
                (issue_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_total(issue_id: int) -> float:
        """案件の見積合計を取得"""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(hours), 0) FROM issue_estimate_item WHERE issue_id = ?",
                (issue_id,)
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def get_by_id(item_id: int, issue_id: int) -> dict | None:
        """見積内訳をIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM issue_estimate_item WHERE id = ? AND issue_id = ?",
                (item_id, issue_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(issue_id: int, name: str, hours: float) -> dict:
        """見積内訳作成"""
        if hours <= 0:
            raise ValueError("工数は0より大きい値を入力してください")

        with get_db() as conn:
            max_order = conn.execute(
                "SELECT COALESCE(MAX(sort_order), 0) FROM issue_estimate_item WHERE issue_id = ?",
                (issue_id,)
            ).fetchone()[0]

            cur = conn.execute(
                "INSERT INTO issue_estimate_item (issue_id, name, hours, sort_order) VALUES (?, ?, ?, ?)",
                (issue_id, name, hours, max_order + 1)
            )
            row = conn.execute("SELECT * FROM issue_estimate_item WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(item_id: int, issue_id: int, name: str, hours: float) -> dict | None:
        """見積内訳更新"""
        if hours <= 0:
            raise ValueError("工数は0より大きい値を入力してください")

        with get_db() as conn:
            cur = conn.execute(
                "UPDATE issue_estimate_item SET name = ?, hours = ? WHERE id = ? AND issue_id = ?",
                (name, hours, item_id, issue_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM issue_estimate_item WHERE id = ?", (item_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(item_id: int, issue_id: int) -> bool:
        """見積内訳削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM issue_estimate_item WHERE id = ? AND issue_id = ?",
                (item_id, issue_id)
            )
        return cur.rowcount > 0
