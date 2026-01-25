"""ユーザーサービス

責務: ユーザーのデータ操作のみ
"""
from database import get_db


class UserService:
    """ユーザー関連のデータ操作"""

    @staticmethod
    def get_all(sort: str = "cd", order: str = "asc", q: str = "", active_only: bool = False) -> list[dict]:
        """ユーザー一覧を取得"""
        allowed_sorts = {"cd", "name", "email"}
        if sort not in allowed_sorts:
            sort = "cd"
        order_dir = "DESC" if order.lower() == "desc" else "ASC"

        with get_db() as conn:
            conditions = []
            params = []

            if active_only:
                conditions.append("(is_active = 1 OR is_active IS NULL)")

            if q:
                like = f"%{q}%"
                conditions.append("(cd LIKE ? OR name LIKE ? OR email LIKE ?)")
                params.extend([like, like, like])

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            rows = conn.execute(
                f"SELECT * FROM user {where} ORDER BY {sort} {order_dir}",
                params
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_active() -> list[dict]:
        """有効なユーザー一覧を取得"""
        return UserService.get_all(active_only=True)

    @staticmethod
    def get_active_list() -> list[dict]:
        """有効なユーザー一覧を取得（フィルター用の最小フィールド）"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT id, cd, name FROM user WHERE is_active = 1 OR is_active IS NULL ORDER BY cd"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(user_id: int) -> dict | None:
        """ユーザーをIDで取得"""
        with get_db() as conn:
            row = conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(cd: str, name: str, email: str) -> dict:
        """ユーザー作成"""
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO user (cd, name, email) VALUES (?, ?, ?)",
                (cd, name, email)
            )
            row = conn.execute("SELECT * FROM user WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)

    @staticmethod
    def update(user_id: int, cd: str, name: str, email: str) -> dict | None:
        """ユーザー更新"""
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE user SET cd = ?, name = ?, email = ? WHERE id = ?",
                (cd, name, email, user_id)
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        return dict(row)

    @staticmethod
    def delete(user_id: int) -> bool:
        """ユーザー削除"""
        with get_db() as conn:
            cur = conn.execute("DELETE FROM user WHERE id = ?", (user_id,))
        return cur.rowcount > 0

    @staticmethod
    def get_attributes(user_id: int) -> dict:
        """ユーザーの属性値を取得（type_id -> {option_id, option_name}）"""
        with get_db() as conn:
            attrs = conn.execute(
                """SELECT ua.type_id, ua.option_id, uao.name as option_name
                   FROM user_attribute ua
                   JOIN user_attribute_option uao ON ua.option_id = uao.id
                   WHERE ua.user_id = ?""",
                (user_id,)
            ).fetchall()
        return {a['type_id']: {'option_id': a['option_id'], 'option_name': a['option_name']} for a in attrs}

    @staticmethod
    def set_attribute(user_id: int, type_id: int, option_id: int | None) -> bool:
        """ユーザー属性を設定"""
        with get_db() as conn:
            if option_id:
                conn.execute(
                    """INSERT INTO user_attribute (user_id, type_id, option_id)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, type_id) DO UPDATE SET option_id = ?""",
                    (user_id, type_id, option_id, option_id)
                )
            else:
                conn.execute(
                    "DELETE FROM user_attribute WHERE user_id = ? AND type_id = ?",
                    (user_id, type_id)
                )
        return True

    @staticmethod
    def get_attribute_types() -> list[dict]:
        """全属性タイプと選択肢を取得"""
        with get_db() as conn:
            types = conn.execute(
                "SELECT * FROM user_attribute_type ORDER BY sort_order ASC, id ASC"
            ).fetchall()
            result = []
            for t in types:
                options = conn.execute(
                    "SELECT * FROM user_attribute_option WHERE type_id = ? ORDER BY sort_order ASC, id ASC",
                    (t['id'],)
                ).fetchall()
                result.append({
                    'id': t['id'],
                    'code': t['code'],
                    'name': t['name'],
                    'options': [{'id': o['id'], 'code': o['code'], 'name': o['name']} for o in options]
                })
        return result
