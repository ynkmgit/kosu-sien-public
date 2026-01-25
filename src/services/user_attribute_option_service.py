"""ユーザー属性選択肢サービス

責務: ユーザー属性選択肢のデータ操作のみ
"""
from database import get_db


class UserAttributeOptionService:
    """ユーザー属性選択肢関連のデータ操作"""

    @staticmethod
    def get_all(type_id: int) -> list[dict]:
        """属性タイプの選択肢一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM user_attribute_option WHERE type_id = ? ORDER BY sort_order ASC, id ASC",
                (type_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(option_id: int, type_id: int) -> dict | None:
        """選択肢をIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM user_attribute_option WHERE id = ? AND type_id = ?",
                (option_id, type_id)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(type_id: int, code: str, name: str, sort_order: int = 0) -> dict:
        """選択肢作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO user_attribute_option (type_id, code, name, sort_order) VALUES (?, ?, ?, ?)",
                (type_id, code, name, sort_order)
            )
            row = conn.execute("SELECT * FROM user_attribute_option WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(option_id: int, type_id: int, code: str, name: str, sort_order: int = 0) -> dict | None:
        """選択肢更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE user_attribute_option SET code = ?, name = ?, sort_order = ? WHERE id = ? AND type_id = ?",
                (code, name, sort_order, option_id, type_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM user_attribute_option WHERE id = ?", (option_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(option_id: int, type_id: int) -> bool:
        """選択肢削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM user_attribute_option WHERE id = ? AND type_id = ?",
                (option_id, type_id)
            )
        return cur.rowcount > 0

    @staticmethod
    def is_in_use(option_id: int) -> bool:
        """選択肢がユーザー属性で使用中かチェック"""
        with get_db() as conn:
            usage = conn.execute(
                "SELECT COUNT(*) FROM user_attribute WHERE option_id = ?",
                (option_id,)
            ).fetchone()[0]
        return usage > 0
