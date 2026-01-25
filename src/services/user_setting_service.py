"""ユーザー設定サービス

責務: ユーザー設定のデータ操作のみ
"""
from database import get_db


class UserSettingService:
    """ユーザー設定関連のデータ操作"""

    @staticmethod
    def get(user_id: int, key: str) -> str | None:
        """ユーザー設定を取得"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT setting_value FROM user_setting WHERE user_id = ? AND setting_key = ?",
                (user_id, key)
            ).fetchone()
        return row["setting_value"] if row else None

    @staticmethod
    def save(user_id: int, key: str, value: str | None) -> bool:
        """ユーザー設定を保存（upsert）"""
        with get_db() as conn:
            # ユーザー存在確認
            user = conn.execute("SELECT id FROM user WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return False

            conn.execute("""
                INSERT INTO user_setting (user_id, setting_key, setting_value)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """, (user_id, key, value))
        return True

    @staticmethod
    def delete(user_id: int, key: str) -> bool:
        """ユーザー設定を削除"""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM user_setting WHERE user_id = ? AND setting_key = ?",
                (user_id, key)
            )
        return True
