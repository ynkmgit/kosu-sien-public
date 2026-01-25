"""ユーザー設定サービスのテスト"""
from services.user_setting_service import UserSettingService
from database import get_db


def test_get_not_exists(clean_db):
    """設定なしでNone"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U1', 'User1', 'u1@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    result = UserSettingService.get(user_id, "nonexistent_key")
    assert result is None


def test_save_and_get(clean_db):
    """設定保存と取得"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U2', 'User2', 'u2@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    result = UserSettingService.save(user_id, "theme", "dark")
    assert result is True

    value = UserSettingService.get(user_id, "theme")
    assert value == "dark"


def test_save_upsert(clean_db):
    """設定更新（upsert）"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U3', 'User3', 'u3@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    UserSettingService.save(user_id, "lang", "ja")
    UserSettingService.save(user_id, "lang", "en")

    value = UserSettingService.get(user_id, "lang")
    assert value == "en"


def test_save_nonexistent_user(clean_db):
    """存在しないユーザーでFalse"""
    result = UserSettingService.save(99999, "key", "value")
    assert result is False


def test_delete(clean_db):
    """設定削除"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U4', 'User4', 'u4@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    UserSettingService.save(user_id, "delete_me", "value")
    result = UserSettingService.delete(user_id, "delete_me")
    assert result is True

    value = UserSettingService.get(user_id, "delete_me")
    assert value is None
