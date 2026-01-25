"""実績サービスのテスト"""
import pytest
from datetime import date
from database import get_db
from services.project_service import ProjectService
from services.issue_service import IssueService
from services.task_service import TaskService
from services.user_service import UserService
from services.work_log_service import WorkLogService


@pytest.fixture
def assigned_task(clean_db):
    """担当割当済みの作業とユーザー"""
    project = ProjectService.create("PROJ", "Test Project", "")
    issue = IssueService.create(project["id"], "ISS", "Test Issue")
    task = TaskService.create(issue["id"], "TSK", "Test Task")
    user = UserService.create("WRK", "Worker", "work@test.com")

    # 担当割当
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task_assignee (task_id, user_id) VALUES (?, ?)",
            (task["id"], user["id"])
        )

    return {"task": task, "user": user, "project": project, "issue": issue}


def test_get_all(clean_db, assigned_task):
    """実績一覧取得"""
    WorkLogService.upsert(
        assigned_task["task"]["id"],
        assigned_task["user"]["id"],
        date.today(),
        2.0
    )
    logs = WorkLogService.get_all()
    assert isinstance(logs, list)


def test_upsert_create(clean_db, assigned_task):
    """実績作成"""
    result = WorkLogService.upsert(
        assigned_task["task"]["id"],
        assigned_task["user"]["id"],
        date.today(),
        2.5
    )
    assert result is not None
    assert result["hours"] == 2.5


def test_upsert_update(clean_db, assigned_task):
    """実績更新"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]
    work_date = date.today()

    # 作成
    WorkLogService.upsert(task_id, user_id, work_date, 2.0)
    # 更新
    result = WorkLogService.upsert(task_id, user_id, work_date, 3.0)

    assert result["hours"] == 3.0


def test_upsert_delete_on_zero(clean_db, assigned_task):
    """0時間で削除"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]
    work_date = date.today()

    # 作成
    WorkLogService.upsert(task_id, user_id, work_date, 2.0)
    # 0で削除
    result = WorkLogService.upsert(task_id, user_id, work_date, 0)

    assert result is None

    # 確認
    logs = WorkLogService.get_all(task_id=task_id, user_id=user_id)
    assert len([l for l in logs if l["work_date"] == work_date.isoformat()]) == 0


def test_upsert_not_assigned(clean_db):
    """担当でない場合エラー"""
    project = ProjectService.create("P", "Project", "")
    issue = IssueService.create(project["id"], "I", "Issue")
    task = TaskService.create(issue["id"], "T", "Task")
    user = UserService.create("U", "User", "u@test.com")

    with pytest.raises(ValueError, match="担当"):
        WorkLogService.upsert(task["id"], user["id"], date.today(), 1.0)


def test_upsert_invalid_hours(clean_db, assigned_task):
    """無効な時間でエラー"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]

    with pytest.raises(ValueError, match="0以上"):
        WorkLogService.upsert(task_id, user_id, date.today(), -1.0)

    with pytest.raises(ValueError, match="0.25刻み"):
        WorkLogService.upsert(task_id, user_id, date.today(), 1.3)


def test_get_by_id(clean_db, assigned_task):
    """IDで取得"""
    created = WorkLogService.upsert(
        assigned_task["task"]["id"],
        assigned_task["user"]["id"],
        date.today(),
        2.0
    )
    fetched = WorkLogService.get_by_id(created["id"])
    assert fetched is not None
    assert fetched["hours"] == 2.0


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    result = WorkLogService.get_by_id(99999)
    assert result is None


def test_delete(clean_db, assigned_task):
    """実績削除"""
    created = WorkLogService.upsert(
        assigned_task["task"]["id"],
        assigned_task["user"]["id"],
        date.today(),
        2.0
    )
    result = WorkLogService.delete(created["id"])
    assert result is True
    assert WorkLogService.get_by_id(created["id"]) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    result = WorkLogService.delete(99999)
    assert result is False


def test_get_daily_total(clean_db, assigned_task):
    """日次合計"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]

    WorkLogService.upsert(task_id, user_id, date.today(), 2.5)

    total = WorkLogService.get_daily_total(user_id, date.today())
    assert total == 2.5


def test_get_monthly_total(clean_db, assigned_task):
    """月次合計"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]

    WorkLogService.upsert(task_id, user_id, date.today(), 3.0)

    year_month = date.today().strftime("%Y-%m")
    total = WorkLogService.get_monthly_total(user_id=user_id, year_month=year_month)
    assert total >= 3.0
