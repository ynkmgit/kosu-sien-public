"""案件サービスのテスト"""
import pytest
from services.project_service import ProjectService
from services.issue_service import IssueService


@pytest.fixture
def project(clean_db):
    """テスト用プロジェクト"""
    return ProjectService.create("PROJ", "Test Project", "")


def test_get_all(clean_db, project):
    """案件一覧取得"""
    IssueService.create(project["id"], "ISS1", "Issue 1")
    issues = IssueService.get_all()
    assert isinstance(issues, list)


def test_get_all_by_project(clean_db, project):
    """プロジェクトでフィルタ"""
    IssueService.create(project["id"], "ISS1", "Issue 1")
    issues = IssueService.get_all(project_id=project["id"])
    assert len(issues) >= 1
    assert all(i["project_id"] == project["id"] for i in issues)


def test_create_issue(clean_db, project):
    """案件作成"""
    issue = IssueService.create(project["id"], "NEW", "New Issue", "open", "Desc")
    assert issue["cd"] == "NEW"
    assert issue["name"] == "New Issue"
    assert issue["status"] == "open"
    assert issue["project_id"] == project["id"]


def test_get_by_id(clean_db, project):
    """IDで取得"""
    created = IssueService.create(project["id"], "TEST", "Test Issue")
    fetched = IssueService.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["cd"] == "TEST"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = IssueService.get_by_id(99999)
    assert result is None


def test_update_issue(clean_db, project):
    """案件更新"""
    created = IssueService.create(project["id"], "UPD", "Update Me")
    updated = IssueService.update(created["id"], "UPD2", "Updated", "closed", "New Desc")
    assert updated is not None
    assert updated["cd"] == "UPD2"
    assert updated["status"] == "closed"


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    result = IssueService.update(99999, "X", "Y", "open", "")
    assert result is None


def test_delete_issue(clean_db, project):
    """案件削除"""
    created = IssueService.create(project["id"], "DEL", "Delete Me")
    result = IssueService.delete(created["id"])
    assert result is True
    assert IssueService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = IssueService.delete(99999)
    assert result is False


def test_get_estimate_total_zero(clean_db, project):
    """見積なしで0"""
    issue = IssueService.create(project["id"], "EST", "Estimate Test")
    total = IssueService.get_estimate_total(issue["id"])
    assert total == 0


def test_get_actual_total_zero(clean_db, project):
    """実績なしで0"""
    issue = IssueService.create(project["id"], "ACT", "Actual Test")
    total = IssueService.get_actual_total(issue["id"])
    assert total == 0
