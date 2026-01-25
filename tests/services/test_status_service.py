"""ステータスサービスのテスト"""
from services.status_service import StatusService
from database import get_db


def _create_project():
    """テスト用プロジェクト作成"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('STAT', 'Status Test')")
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_get_all_empty(clean_db):
    """ステータスなしで空リスト"""
    project_id = _create_project()
    result = StatusService.get_all(project_id)
    assert result == []


def test_create_status(clean_db):
    """ステータス作成"""
    project_id = _create_project()
    status = StatusService.create(project_id, "todo", "TODO", 1)

    assert status["code"] == "todo"
    assert status["name"] == "TODO"
    assert status["sort_order"] == 1
    assert status["project_id"] == project_id


def test_get_all_sorted(clean_db):
    """ソート順で取得"""
    project_id = _create_project()
    StatusService.create(project_id, "done", "Done", 3)
    StatusService.create(project_id, "todo", "TODO", 1)
    StatusService.create(project_id, "doing", "Doing", 2)

    result = StatusService.get_all(project_id)
    assert len(result) == 3
    assert result[0]["code"] == "todo"
    assert result[1]["code"] == "doing"
    assert result[2]["code"] == "done"


def test_get_by_id(clean_db):
    """IDで取得"""
    project_id = _create_project()
    created = StatusService.create(project_id, "test", "Test", 0)

    result = StatusService.get_by_id(created["id"], project_id)
    assert result is not None
    assert result["code"] == "test"


def test_get_by_id_wrong_project(clean_db):
    """別プロジェクトのステータスは取得不可"""
    project_id = _create_project()
    created = StatusService.create(project_id, "test", "Test", 0)

    result = StatusService.get_by_id(created["id"], 99999)
    assert result is None


def test_update_status(clean_db):
    """ステータス更新"""
    project_id = _create_project()
    created = StatusService.create(project_id, "old", "Old Name", 0)

    updated = StatusService.update(created["id"], project_id, "new", "New Name", 5)
    assert updated is not None
    assert updated["code"] == "new"
    assert updated["name"] == "New Name"
    assert updated["sort_order"] == 5


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    project_id = _create_project()
    result = StatusService.update(99999, project_id, "x", "X", 0)
    assert result is None


def test_delete_status(clean_db):
    """ステータス削除"""
    project_id = _create_project()
    created = StatusService.create(project_id, "del", "Delete Me", 0)

    result = StatusService.delete(created["id"], project_id)
    assert result is True
    assert StatusService.get_by_id(created["id"], project_id) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    project_id = _create_project()
    result = StatusService.delete(99999, project_id)
    assert result is False


def test_is_in_use_false(clean_db):
    """未使用ステータス"""
    project_id = _create_project()
    created = StatusService.create(project_id, "unused", "Unused", 0)

    result = StatusService.is_in_use(created["id"])
    assert result is False


def test_is_in_use_true(clean_db):
    """使用中ステータス"""
    project_id = _create_project()
    created = StatusService.create(project_id, "used", "Used", 0)

    # ステータスを使う案件を作成
    with get_db() as conn:
        conn.execute(
            "INSERT INTO issue (project_id, cd, name, status) VALUES (?, 'I1', 'Issue1', 'used')",
            (project_id,)
        )

    result = StatusService.is_in_use(created["id"])
    assert result is True
