"""担当割当サービスのテスト"""
from services.task_assignee_service import TaskAssigneeService
from database import get_db


def _setup_project_with_task():
    """テスト用プロジェクト・案件・作業作成"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('ASSIGN', 'Assign Test')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I1', 'Issue1')", (project_id,))
        issue_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO task (issue_id, cd, name) VALUES (?, 'T1', 'Task1')", (issue_id,))
        task_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('ASSIGNEE', 'Assignee', 'assignee@test.com')")
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return project_id, task_id, user_id


def test_get_project_tasks_with_issues_empty(clean_db):
    """作業なしで空リスト"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('EMPTY', 'Empty')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    result = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assert result == []


def test_get_project_tasks_with_issues(clean_db):
    """作業を案件情報付きで取得"""
    project_id, task_id, _ = _setup_project_with_task()

    result = TaskAssigneeService.get_project_tasks_with_issues(project_id)
    assert len(result) == 1
    assert result[0]["id"] == task_id
    assert result[0]["issue_cd"] == "I1"
    assert result[0]["issue_name"] == "Issue1"


def test_get_all_assignments_empty(clean_db):
    """割当なしで空辞書"""
    project_id, _, _ = _setup_project_with_task()

    result = TaskAssigneeService.get_all_assignments(project_id)
    assert result == {}


def test_get_all_assignments(clean_db):
    """割当を辞書で取得"""
    project_id, task_id, user_id = _setup_project_with_task()

    assignment_id = TaskAssigneeService.create(task_id, user_id)

    result = TaskAssigneeService.get_all_assignments(project_id)
    assert (task_id, user_id) in result
    assert result[(task_id, user_id)] == assignment_id


def test_get_task_in_project(clean_db):
    """作業の存在確認"""
    project_id, task_id, _ = _setup_project_with_task()

    result = TaskAssigneeService.get_task_in_project(task_id, project_id)
    assert result is not None
    assert result["id"] == task_id


def test_get_task_in_project_wrong_project(clean_db):
    """別プロジェクトの作業はNone"""
    _, task_id, _ = _setup_project_with_task()

    result = TaskAssigneeService.get_task_in_project(task_id, 99999)
    assert result is None


def test_get_user_with_status(clean_db):
    """ユーザー状態取得"""
    _, _, user_id = _setup_project_with_task()

    result = TaskAssigneeService.get_user_with_status(user_id)
    assert result is not None
    assert result["id"] == user_id
    assert "is_active" in result


def test_get_user_with_status_not_found(clean_db):
    """存在しないユーザーはNone"""
    result = TaskAssigneeService.get_user_with_status(99999)
    assert result is None


def test_create_assignment(clean_db):
    """割当作成"""
    project_id, task_id, user_id = _setup_project_with_task()

    assignment_id = TaskAssigneeService.create(task_id, user_id)
    assert assignment_id is not None
    assert isinstance(assignment_id, int)


def test_get_assignment(clean_db):
    """既存割当確認"""
    project_id, task_id, user_id = _setup_project_with_task()

    # 割当なし
    result = TaskAssigneeService.get_assignment(task_id, user_id)
    assert result is None

    # 割当あり
    TaskAssigneeService.create(task_id, user_id)
    result = TaskAssigneeService.get_assignment(task_id, user_id)
    assert result is not None


def test_get_assignment_in_project(clean_db):
    """割当のプロジェクト所属確認"""
    project_id, task_id, user_id = _setup_project_with_task()
    assignment_id = TaskAssigneeService.create(task_id, user_id)

    result = TaskAssigneeService.get_assignment_in_project(assignment_id, project_id)
    assert result is not None

    result = TaskAssigneeService.get_assignment_in_project(assignment_id, 99999)
    assert result is None


def test_delete_assignment(clean_db):
    """割当削除"""
    project_id, task_id, user_id = _setup_project_with_task()
    assignment_id = TaskAssigneeService.create(task_id, user_id)

    result = TaskAssigneeService.delete(assignment_id)
    assert result is True

    # 削除確認
    assert TaskAssigneeService.get_assignment(task_id, user_id) is None


def test_delete_not_found(clean_db):
    """存在しない割当の削除は失敗"""
    result = TaskAssigneeService.delete(99999)
    assert result is False


def test_toggle_add(clean_db):
    """トグル: 割当追加"""
    project_id, task_id, user_id = _setup_project_with_task()

    result = TaskAssigneeService.toggle(task_id, user_id)
    assert result is True  # 追加された

    # 割当が存在することを確認
    assert TaskAssigneeService.get_assignment(task_id, user_id) is not None


def test_toggle_remove(clean_db):
    """トグル: 割当削除"""
    project_id, task_id, user_id = _setup_project_with_task()
    TaskAssigneeService.create(task_id, user_id)

    result = TaskAssigneeService.toggle(task_id, user_id)
    assert result is False  # 削除された

    # 割当が存在しないことを確認
    assert TaskAssigneeService.get_assignment(task_id, user_id) is None


def test_toggle_twice(clean_db):
    """トグル2回で元に戻る"""
    project_id, task_id, user_id = _setup_project_with_task()

    # 追加
    result1 = TaskAssigneeService.toggle(task_id, user_id)
    assert result1 is True

    # 削除
    result2 = TaskAssigneeService.toggle(task_id, user_id)
    assert result2 is False

    # 再追加
    result3 = TaskAssigneeService.toggle(task_id, user_id)
    assert result3 is True
