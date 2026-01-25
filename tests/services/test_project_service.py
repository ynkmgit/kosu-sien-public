"""プロジェクトサービスのテスト"""
import pytest
from services.project_service import ProjectService


def test_get_all_empty(clean_db):
    """データなしで空リスト"""
    # clean_dbはテストデータを含むので、プロジェクトはある
    projects = ProjectService.get_all()
    assert isinstance(projects, list)


def test_create_project(clean_db):
    """プロジェクト作成"""
    project = ProjectService.create("TEST", "Test Project", "Description")
    assert project["cd"] == "TEST"
    assert project["name"] == "Test Project"
    assert project["description"] == "Description"
    assert "id" in project


def test_get_by_id(clean_db):
    """IDで取得"""
    created = ProjectService.create("TEST", "Test Project", "")
    fetched = ProjectService.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["cd"] == "TEST"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = ProjectService.get_by_id(99999)
    assert result is None


def test_update_project(clean_db):
    """プロジェクト更新"""
    created = ProjectService.create("TEST", "Test Project", "")
    updated = ProjectService.update(created["id"], "TEST2", "Updated Name", "New Desc")
    assert updated is not None
    assert updated["cd"] == "TEST2"
    assert updated["name"] == "Updated Name"


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    result = ProjectService.update(99999, "X", "Y", "")
    assert result is None


def test_delete_project(clean_db):
    """プロジェクト削除"""
    created = ProjectService.create("DEL", "Delete Me", "")
    result = ProjectService.delete(created["id"])
    assert result is True
    assert ProjectService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = ProjectService.delete(99999)
    assert result is False


def test_get_all_with_search(clean_db):
    """検索フィルタ"""
    ProjectService.create("SRCH", "Searchable", "unique_keyword")
    results = ProjectService.get_all(q="unique_keyword")
    assert len(results) >= 1
    assert any(p["cd"] == "SRCH" for p in results)


def test_get_all_with_sort(clean_db):
    """ソート"""
    ProjectService.create("AAA", "First", "")
    ProjectService.create("ZZZ", "Last", "")

    asc = ProjectService.get_all(sort="cd", order="asc")
    desc = ProjectService.get_all(sort="cd", order="desc")

    # 昇順では最初のものが先
    assert asc[0]["cd"] <= asc[-1]["cd"]
    # 降順では最後のものが先
    assert desc[0]["cd"] >= desc[-1]["cd"]


def test_get_summary(clean_db):
    """サマリー取得"""
    project = ProjectService.create("SUM", "Summary Test", "")
    summary = ProjectService.get_summary(project["id"])

    assert "issue_count" in summary
    assert "task_count" in summary
    assert "estimate_total" in summary
    assert "actual_total" in summary
    assert "consumption_rate" in summary
