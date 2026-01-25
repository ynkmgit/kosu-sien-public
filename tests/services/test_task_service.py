"""作業サービスのテスト"""
import pytest
from services.project_service import ProjectService
from services.issue_service import IssueService
from services.task_service import TaskService


@pytest.fixture
def issue(clean_db):
    """テスト用案件"""
    project = ProjectService.create("PROJ", "Test Project", "")
    return IssueService.create(project["id"], "ISS", "Test Issue")


def test_get_all(clean_db, issue):
    """作業一覧取得"""
    TaskService.create(issue["id"], "TSK1", "Task 1")
    tasks = TaskService.get_all()
    assert isinstance(tasks, list)


def test_get_all_by_issue(clean_db, issue):
    """案件でフィルタ"""
    TaskService.create(issue["id"], "TSK1", "Task 1")
    tasks = TaskService.get_all(issue_id=issue["id"])
    assert len(tasks) >= 1
    assert all(t["issue_id"] == issue["id"] for t in tasks)


def test_create_task(clean_db, issue):
    """作業作成"""
    task = TaskService.create(issue["id"], "NEW", "New Task", "Desc")
    assert task["cd"] == "NEW"
    assert task["name"] == "New Task"
    assert task["issue_id"] == issue["id"]


def test_get_by_id(clean_db, issue):
    """IDで取得"""
    created = TaskService.create(issue["id"], "TEST", "Test Task")
    fetched = TaskService.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["cd"] == "TEST"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = TaskService.get_by_id(99999)
    assert result is None


def test_update_task(clean_db, issue):
    """作業更新"""
    created = TaskService.create(issue["id"], "UPD", "Update Me")
    updated = TaskService.update(created["id"], "UPD2", "Updated", "New Desc")
    assert updated is not None
    assert updated["cd"] == "UPD2"


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    result = TaskService.update(99999, "X", "Y", "")
    assert result is None


def test_delete_task(clean_db, issue):
    """作業削除"""
    created = TaskService.create(issue["id"], "DEL", "Delete Me")
    result = TaskService.delete(created["id"])
    assert result is True
    assert TaskService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = TaskService.delete(99999)
    assert result is False


def test_update_progress(clean_db, issue):
    """進捗率更新"""
    task = TaskService.create(issue["id"], "PRG", "Progress Test")
    result = TaskService.update_progress(task["id"], 50)
    assert result is True

    updated = TaskService.get_by_id(task["id"])
    assert updated["progress_rate"] == 50


def test_update_progress_invalid_range(clean_db, issue):
    """無効な進捗率でエラー"""
    task = TaskService.create(issue["id"], "PRG", "Progress Test")

    with pytest.raises(ValueError):
        TaskService.update_progress(task["id"], -1)

    with pytest.raises(ValueError):
        TaskService.update_progress(task["id"], 101)


def test_get_assignees_empty(clean_db, issue):
    """担当なしで空リスト"""
    task = TaskService.create(issue["id"], "ASG", "Assignee Test")
    assignees = TaskService.get_assignees(task["id"])
    assert assignees == []
