"""ユーザー属性タイプサービスのテスト"""
from services.user_attribute_type_service import UserAttributeTypeService
from database import get_db


def test_get_all_empty(clean_db):
    """属性タイプは空またはリスト"""
    result = UserAttributeTypeService.get_all()
    assert isinstance(result, list)


def test_create_type(clean_db):
    """属性タイプ作成"""
    attr_type = UserAttributeTypeService.create("dept", "部署", 1)

    assert attr_type["code"] == "dept"
    assert attr_type["name"] == "部署"
    assert attr_type["sort_order"] == 1


def test_get_all_sorted(clean_db):
    """ソート順で取得"""
    UserAttributeTypeService.create("c", "Third", 3)
    UserAttributeTypeService.create("a", "First", 1)
    UserAttributeTypeService.create("b", "Second", 2)

    result = UserAttributeTypeService.get_all()
    # 既存データを除いて確認
    created = [t for t in result if t["code"] in ("a", "b", "c")]
    assert len(created) == 3
    assert created[0]["code"] == "a"
    assert created[1]["code"] == "b"
    assert created[2]["code"] == "c"


def test_get_by_id(clean_db):
    """IDで取得"""
    created = UserAttributeTypeService.create("test", "Test", 0)

    result = UserAttributeTypeService.get_by_id(created["id"])
    assert result is not None
    assert result["code"] == "test"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = UserAttributeTypeService.get_by_id(99999)
    assert result is None


def test_update_type(clean_db):
    """属性タイプ更新"""
    created = UserAttributeTypeService.create("old", "Old Name", 0)

    updated = UserAttributeTypeService.update(created["id"], "new", "New Name", 5)
    assert updated is not None
    assert updated["code"] == "new"
    assert updated["name"] == "New Name"
    assert updated["sort_order"] == 5


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    result = UserAttributeTypeService.update(99999, "x", "X", 0)
    assert result is None


def test_delete_type(clean_db):
    """属性タイプ削除"""
    created = UserAttributeTypeService.create("del", "Delete Me", 0)

    result = UserAttributeTypeService.delete(created["id"])
    assert result is True
    assert UserAttributeTypeService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = UserAttributeTypeService.delete(99999)
    assert result is False


def test_get_option_count_zero(clean_db):
    """選択肢なしで0"""
    created = UserAttributeTypeService.create("no_opts", "No Options", 0)

    count = UserAttributeTypeService.get_option_count(created["id"])
    assert count == 0


def test_get_option_count_with_options(clean_db):
    """選択肢ありでカウント"""
    created = UserAttributeTypeService.create("with_opts", "With Options", 0)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'opt1', 'Option1')",
            (created["id"],)
        )
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'opt2', 'Option2')",
            (created["id"],)
        )

    count = UserAttributeTypeService.get_option_count(created["id"])
    assert count == 2


def test_get_option_counts(clean_db):
    """複数タイプの選択肢数を一括取得"""
    t1 = UserAttributeTypeService.create("t1", "Type1", 0)
    t2 = UserAttributeTypeService.create("t2", "Type2", 0)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'o1', 'Opt1')",
            (t1["id"],)
        )
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'o2', 'Opt2')",
            (t2["id"],)
        )
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'o3', 'Opt3')",
            (t2["id"],)
        )

    counts = UserAttributeTypeService.get_option_counts()
    assert counts.get(t1["id"]) == 1
    assert counts.get(t2["id"]) == 2


def test_is_in_use_false(clean_db):
    """未使用タイプ"""
    created = UserAttributeTypeService.create("unused", "Unused", 0)

    result = UserAttributeTypeService.is_in_use(created["id"])
    assert result is False


def test_is_in_use_true(clean_db):
    """使用中タイプ"""
    created = UserAttributeTypeService.create("used", "Used", 0)

    with get_db() as conn:
        # 選択肢を作成
        conn.execute(
            "INSERT INTO user_attribute_option (type_id, code, name) VALUES (?, 'opt', 'Option')",
            (created["id"],)
        )
        option_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # ユーザーを作成
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('U1', 'User1', 'u1@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # ユーザー属性を設定
        conn.execute(
            "INSERT INTO user_attribute (user_id, type_id, option_id) VALUES (?, ?, ?)",
            (user_id, created["id"], option_id)
        )

    result = UserAttributeTypeService.is_in_use(created["id"])
    assert result is True
