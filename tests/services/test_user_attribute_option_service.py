"""ユーザー属性選択肢サービスのテスト"""
import uuid
from services.user_attribute_option_service import UserAttributeOptionService
from database import get_db


def _create_type():
    """テスト用属性タイプ作成（ユニークコード生成）"""
    code = f"type_{uuid.uuid4().hex[:8]}"
    with get_db() as conn:
        conn.execute("INSERT INTO user_attribute_type (code, name) VALUES (?, 'Test Type')", (code,))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_get_all_empty(clean_db):
    """選択肢なしで空リスト"""
    type_id = _create_type()
    result = UserAttributeOptionService.get_all(type_id)
    assert result == []


def test_create_option(clean_db):
    """選択肢作成"""
    type_id = _create_type()
    option = UserAttributeOptionService.create(type_id, "opt1", "Option 1", 1)

    assert option["code"] == "opt1"
    assert option["name"] == "Option 1"
    assert option["sort_order"] == 1
    assert option["type_id"] == type_id


def test_get_all_sorted(clean_db):
    """ソート順で取得"""
    type_id = _create_type()
    UserAttributeOptionService.create(type_id, "c", "Third", 3)
    UserAttributeOptionService.create(type_id, "a", "First", 1)
    UserAttributeOptionService.create(type_id, "b", "Second", 2)

    result = UserAttributeOptionService.get_all(type_id)
    assert len(result) == 3
    assert result[0]["code"] == "a"
    assert result[1]["code"] == "b"
    assert result[2]["code"] == "c"


def test_get_by_id(clean_db):
    """IDで取得"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "test", "Test", 0)

    result = UserAttributeOptionService.get_by_id(created["id"], type_id)
    assert result is not None
    assert result["code"] == "test"


def test_get_by_id_wrong_type(clean_db):
    """別タイプのIDでNone"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "test", "Test", 0)

    result = UserAttributeOptionService.get_by_id(created["id"], 99999)
    assert result is None


def test_update_option(clean_db):
    """選択肢更新"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "old", "Old Name", 0)

    updated = UserAttributeOptionService.update(created["id"], type_id, "new", "New Name", 5)
    assert updated is not None
    assert updated["code"] == "new"
    assert updated["name"] == "New Name"
    assert updated["sort_order"] == 5


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    type_id = _create_type()
    result = UserAttributeOptionService.update(99999, type_id, "x", "X", 0)
    assert result is None


def test_delete_option(clean_db):
    """選択肢削除"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "del", "Delete Me", 0)

    result = UserAttributeOptionService.delete(created["id"], type_id)
    assert result is True
    assert UserAttributeOptionService.get_by_id(created["id"], type_id) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    type_id = _create_type()
    result = UserAttributeOptionService.delete(99999, type_id)
    assert result is False


def test_is_in_use_false(clean_db):
    """未使用選択肢"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "unused", "Unused", 0)

    result = UserAttributeOptionService.is_in_use(created["id"])
    assert result is False


def test_is_in_use_true(clean_db):
    """使用中選択肢"""
    type_id = _create_type()
    created = UserAttributeOptionService.create(type_id, "used", "Used", 0)

    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U1', 'User1', 'u1@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO user_attribute (user_id, type_id, option_id) VALUES (?, ?, ?)",
            (user_id, type_id, created["id"])
        )

    result = UserAttributeOptionService.is_in_use(created["id"])
    assert result is True
