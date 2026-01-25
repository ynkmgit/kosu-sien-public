"""月次アサインサービスのテスト"""
import pytest
from services.monthly_assignment_service import MonthlyAssignmentService
from database import get_db


def _setup_user_and_project():
    """テスト用ユーザー・プロジェクト作成"""
    with get_db() as conn:
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('MA_USER', 'MA User', 'ma@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO project (cd, name) VALUES ('MA_PROJ', 'MA Project')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return user_id, project_id


def test_get_assignments_for_month_empty(clean_db):
    """アサインなしで空辞書"""
    result = MonthlyAssignmentService.get_assignments_for_month("2099-01")
    assert result == {}


def test_get_assignments_for_month(clean_db):
    """アサインを辞書で取得"""
    user_id, project_id = _setup_user_and_project()

    assignment_id = MonthlyAssignmentService.upsert(user_id, project_id, "2099-02", 40.0)

    result = MonthlyAssignmentService.get_assignments_for_month("2099-02")
    assert (user_id, project_id) in result
    assert result[(user_id, project_id)]["id"] == assignment_id
    assert result[(user_id, project_id)]["hours"] == 40.0


def test_get_actuals_for_month_empty(clean_db):
    """実績なしで空辞書"""
    result = MonthlyAssignmentService.get_actuals_for_month("2099-03")
    assert result == {}


def test_get_actuals_for_month(clean_db):
    """実績を集計"""
    user_id, project_id = _setup_user_and_project()

    with get_db() as conn:
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I1', 'Issue1')", (project_id,))
        issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T1', 'Task1')", (issue_id,))
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 実績投入
        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-04-10', 8)",
            (task_id, user_id)
        )
        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-04-15', 4)",
            (task_id, user_id)
        )

    result = MonthlyAssignmentService.get_actuals_for_month("2099-04")
    assert (user_id, project_id) in result
    assert result[(user_id, project_id)] == 12


def test_get_user_with_status(clean_db):
    """ユーザー状態取得"""
    user_id, _ = _setup_user_and_project()

    result = MonthlyAssignmentService.get_user_with_status(user_id)
    assert result is not None
    assert result["id"] == user_id


def test_get_user_with_status_not_found(clean_db):
    """存在しないユーザーはNone"""
    result = MonthlyAssignmentService.get_user_with_status(99999)
    assert result is None


def test_get_project(clean_db):
    """プロジェクト存在確認"""
    _, project_id = _setup_user_and_project()

    result = MonthlyAssignmentService.get_project(project_id)
    assert result is not None


def test_get_project_not_found(clean_db):
    """存在しないプロジェクトはNone"""
    result = MonthlyAssignmentService.get_project(99999)
    assert result is None


def test_upsert_create(clean_db):
    """アサイン新規作成"""
    user_id, project_id = _setup_user_and_project()

    assignment_id = MonthlyAssignmentService.upsert(user_id, project_id, "2099-05", 80.0)
    assert assignment_id is not None

    # 確認
    assignment = MonthlyAssignmentService.get_assignment(user_id, project_id, "2099-05")
    assert assignment is not None


def test_upsert_update(clean_db):
    """アサイン更新"""
    user_id, project_id = _setup_user_and_project()

    MonthlyAssignmentService.upsert(user_id, project_id, "2099-06", 40.0)
    MonthlyAssignmentService.upsert(user_id, project_id, "2099-06", 60.0)

    result = MonthlyAssignmentService.get_assignments_for_month("2099-06")
    assert result[(user_id, project_id)]["hours"] == 60.0


def test_upsert_delete_when_zero(clean_db):
    """工数0で削除"""
    user_id, project_id = _setup_user_and_project()

    MonthlyAssignmentService.upsert(user_id, project_id, "2099-07", 40.0)
    result = MonthlyAssignmentService.upsert(user_id, project_id, "2099-07", 0)
    assert result is None

    assignment = MonthlyAssignmentService.get_assignment(user_id, project_id, "2099-07")
    assert assignment is None


def test_upsert_negative_hours(clean_db):
    """負の工数でエラー"""
    user_id, project_id = _setup_user_and_project()

    with pytest.raises(ValueError) as exc:
        MonthlyAssignmentService.upsert(user_id, project_id, "2099-08", -10.0)
    assert "0以上" in str(exc.value)


def test_get_assignment(clean_db):
    """既存アサイン確認"""
    user_id, project_id = _setup_user_and_project()

    # アサインなし
    result = MonthlyAssignmentService.get_assignment(user_id, project_id, "2099-09")
    assert result is None

    # アサインあり
    MonthlyAssignmentService.upsert(user_id, project_id, "2099-09", 40.0)
    result = MonthlyAssignmentService.get_assignment(user_id, project_id, "2099-09")
    assert result is not None


def test_get_by_id(clean_db):
    """IDでアサイン取得"""
    user_id, project_id = _setup_user_and_project()
    assignment_id = MonthlyAssignmentService.upsert(user_id, project_id, "2099-10", 40.0)

    result = MonthlyAssignmentService.get_by_id(assignment_id)
    assert result is not None
    assert result["id"] == assignment_id


def test_get_by_id_not_found(clean_db):
    """存在しないIDはNone"""
    result = MonthlyAssignmentService.get_by_id(99999)
    assert result is None


def test_delete_assignment(clean_db):
    """アサイン削除"""
    user_id, project_id = _setup_user_and_project()
    assignment_id = MonthlyAssignmentService.upsert(user_id, project_id, "2099-11", 40.0)

    result = MonthlyAssignmentService.delete(assignment_id)
    assert result is True

    assert MonthlyAssignmentService.get_by_id(assignment_id) is None


def test_delete_not_found(clean_db):
    """存在しない削除は失敗"""
    result = MonthlyAssignmentService.delete(99999)
    assert result is False


def test_get_actuals_december(clean_db):
    """12月の実績取得（年跨ぎ処理）"""
    user_id, project_id = _setup_user_and_project()

    with get_db() as conn:
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I2', 'Issue2')", (project_id,))
        issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T2', 'Task2')", (issue_id,))
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO work_log (task_id, user_id, work_date, hours) VALUES (?, ?, '2099-12-15', 8)",
            (task_id, user_id)
        )

    result = MonthlyAssignmentService.get_actuals_for_month("2099-12")
    assert (user_id, project_id) in result
    assert result[(user_id, project_id)] == 8
