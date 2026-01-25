"""ユーザー属性タイプサービス

責務: ユーザー属性タイプのデータ操作のみ
"""
from database import get_db


class UserAttributeTypeService:
    """ユーザー属性タイプ関連のデータ操作"""

    @staticmethod
    def get_all() -> list[dict]:
        """属性タイプ一覧を取得"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM user_attribute_type ORDER BY sort_order ASC, id ASC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_option_counts() -> dict[int, int]:
        """各タイプの選択肢数を取得（type_id -> count）"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT type_id, COUNT(*) as cnt FROM user_attribute_option GROUP BY type_id"
            ).fetchall()
        return {r['type_id']: r['cnt'] for r in rows}

    @staticmethod
    def get_by_id(type_id: int) -> dict | None:
        """属性タイプをIDで取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM user_attribute_type WHERE id = ?",
                (type_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_option_count(type_id: int) -> int:
        """属性タイプの選択肢数を取得"""
        with get_db() as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM user_attribute_option WHERE type_id = ?",
                (type_id,)
            ).fetchone()
        return result[0] if result else 0

    @staticmethod
    def create(code: str, name: str, sort_order: int = 0) -> dict:
        """属性タイプ作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO user_attribute_type (code, name, sort_order) VALUES (?, ?, ?)",
                (code, name, sort_order)
            )
            row = conn.execute("SELECT * FROM user_attribute_type WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(type_id: int, code: str, name: str, sort_order: int = 0) -> dict | None:
        """属性タイプ更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE user_attribute_type SET code = ?, name = ?, sort_order = ? WHERE id = ?",
                (code, name, sort_order, type_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM user_attribute_type WHERE id = ?", (type_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(type_id: int) -> bool:
        """属性タイプ削除"""
        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM user_attribute_type WHERE id = ?",
                (type_id,)
            )
        return cur.rowcount > 0

    @staticmethod
    def is_in_use(type_id: int) -> bool:
        """属性タイプがユーザー属性で使用中かチェック"""
        with get_db() as conn:
            usage = conn.execute(
                "SELECT COUNT(*) FROM user_attribute WHERE type_id = ?",
                (type_id,)
            ).fetchone()[0]
        return usage > 0
