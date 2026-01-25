"""ユーザーサービスのテスト"""
import pytest
from services.user_service import UserService


def test_get_all(clean_db):
    """ユーザー一覧取得"""
    users = UserService.get_all()
    assert isinstance(users, list)
    assert len(users) >= 2  # clean_dbには2人のユーザーがいる


def test_get_active(clean_db):
    """有効ユーザーのみ取得"""
    users = UserService.get_active()
    assert isinstance(users, list)


def test_create_user(clean_db):
    """ユーザー作成"""
    user = UserService.create("NEW", "New User", "new@test.com")
    assert user["cd"] == "NEW"
    assert user["name"] == "New User"
    assert user["email"] == "new@test.com"


def test_get_by_id(clean_db):
    """IDで取得"""
    created = UserService.create("TEST", "Test User", "test@test.com")
    fetched = UserService.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["cd"] == "TEST"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = UserService.get_by_id(99999)
    assert result is None


def test_update_user(clean_db):
    """ユーザー更新"""
    created = UserService.create("UPD", "Update Me", "upd@test.com")
    updated = UserService.update(created["id"], "UPD2", "Updated", "new@test.com")
    assert updated is not None
    assert updated["cd"] == "UPD2"
    assert updated["name"] == "Updated"


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    result = UserService.update(99999, "X", "Y", "z@test.com")
    assert result is None


def test_delete_user(clean_db):
    """ユーザー削除"""
    created = UserService.create("DEL", "Delete Me", "del@test.com")
    result = UserService.delete(created["id"])
    assert result is True
    assert UserService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = UserService.delete(99999)
    assert result is False


def test_get_all_with_search(clean_db):
    """検索フィルタ"""
    UserService.create("SRCH", "Searchable", "unique@search.com")
    results = UserService.get_all(q="unique@search")
    assert len(results) >= 1


def test_get_attributes_empty(clean_db):
    """属性なしで空dict"""
    created = UserService.create("ATTR", "Attr Test", "attr@test.com")
    attrs = UserService.get_attributes(created["id"])
    assert attrs == {}
