"""実績入力APIテスト"""
import re
import uuid
from datetime import date
import pytest

from database import get_db
from routers.work_logs import calculate_totals


@pytest.fixture
def user_id(client):
    """テスト用ユーザーを作成してIDを返す"""
    unique_cd = f"WL-{uuid.uuid4().hex[:6]}"
    response = client.post("/users", data={
        "cd": unique_cd,
        "name": "実績テストユーザー",
        "email": f"{unique_cd}@test.example.com"
    })
    match = re.search(r'id="user-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def project_id(client):
    """テスト用プロジェクトを作成してIDを返す"""
    unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
    response = client.post("/projects", data={
        "cd": unique_cd,
        "name": "実績テストPJ",
        "description": ""
    })
    match = re.search(r'id="project-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def issue_id(client, project_id):
    """テスト用案件を作成してIDを返す"""
    unique_cd = f"ISS-{uuid.uuid4().hex[:6]}"
    response = client.post(f"/projects/{project_id}/issues", data={
        "cd": unique_cd,
        "name": "実績テスト案件",
        "status": "open",
        "description": ""
    })
    match = re.search(r'id="issue-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def task_id(client, project_id, issue_id):
    """テスト用作業を作成してIDを返す"""
    unique_cd = f"T-{uuid.uuid4().hex[:6]}"
    response = client.post(f"/projects/{project_id}/issues/{issue_id}/tasks", data={
        "cd": unique_cd,
        "name": "実績テスト作業",
        "description": ""
    })
    match = re.search(r'id="task-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def assigned_task(client, project_id, task_id, user_id):
    """担当割当済みの作業を作成"""
    client.post(f"/projects/{project_id}/assignees/toggle", data={
        "task_id": task_id,
        "user_id": user_id
    })
    return {"task_id": task_id, "user_id": user_id}


class TestWorkLogPage:
    """ページ表示テスト"""

    def test_page_returns_200(self, client):
        """ページ表示が成功する"""
        response = client.get("/work-logs")
        assert response.status_code == 200
        assert "実績入力" in response.text

    def test_page_with_month_param(self, client):
        """月指定でページ表示"""
        response = client.get("/work-logs?month=2026-01")
        assert response.status_code == 200

    def test_page_with_filters(self, client, user_id, project_id):
        """フィルター付きでページ表示"""
        response = client.get(f"/work-logs?user={user_id}&project={project_id}&month=2026-01")
        assert response.status_code == 200


class TestWorkLogGrid:
    """グリッド取得テスト"""

    def test_grid_returns_200(self, client):
        """グリッド取得が成功する"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200

    def test_grid_with_month_param(self, client):
        """月指定でグリッド取得"""
        response = client.get("/work-logs/grid?month=2026-01")
        assert response.status_code == 200

    def test_grid_invalid_month_returns_400(self, client):
        """不正な月形式は400（view=monthの場合のみmonthパラメータが検証される）"""
        response = client.get("/work-logs/grid?month=invalid&view=month")
        assert response.status_code == 400

    def test_grid_shows_assigned_tasks(self, client, assigned_task):
        """グリッドに担当割当された作業が表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        # 割当されたタスクのdata-task-idがあることを確認
        assert f'data-task-id="{assigned_task["task_id"]}"' in response.text

    def test_grid_shows_filter_section(self, client):
        """グリッドにフィルターセクションが表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert "ユーザー" in response.text
        assert "プロジェクト" in response.text


class TestWorkLogUpsert:
    """実績追加/更新テスト"""

    def test_create_work_log(self, client, assigned_task):
        """実績追加が成功する"""
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-15",
            "hours": "2.0"
        })
        assert response.status_code == 200

    def test_update_work_log(self, client, assigned_task):
        """実績更新が成功する"""
        # 作成
        client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-16",
            "hours": "2.0"
        })
        # 更新
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-16",
            "hours": "4.0"
        })
        assert response.status_code == 200

    def test_delete_by_zero(self, client, assigned_task):
        """0入力で実績削除"""
        # 作成
        client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-17",
            "hours": "2.0"
        })
        # 0で削除
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-17",
            "hours": "0"
        })
        assert response.status_code == 200

    def test_negative_hours_returns_400(self, client, assigned_task):
        """負の時間は400"""
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-15",
            "hours": "-1"
        })
        assert response.status_code == 400

    def test_invalid_step_returns_400(self, client, assigned_task):
        """0.25刻み以外は400"""
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "2026-01-15",
            "hours": "1.3"
        })
        assert response.status_code == 400

    def test_not_assigned_returns_400(self, client, task_id, user_id):
        """担当割当なしは400"""
        # 別のユーザーを作成（担当なし）
        unique_cd = f"WL-{uuid.uuid4().hex[:6]}"
        response = client.post("/users", data={
            "cd": unique_cd,
            "name": "未担当ユーザー",
            "email": f"{unique_cd}@test.example.com"
        })
        match = re.search(r'id="user-(\d+)"', response.text)
        other_user_id = int(match.group(1))

        response = client.post("/work-logs", data={
            "task_id": task_id,
            "user_id": other_user_id,
            "work_date": "2026-01-15",
            "hours": "2.0"
        })
        assert response.status_code == 400
        assert "担当" in response.text

    def test_invalid_date_returns_400(self, client, assigned_task):
        """不正な日付形式は400"""
        response = client.post("/work-logs", data={
            "task_id": assigned_task["task_id"],
            "user_id": assigned_task["user_id"],
            "work_date": "invalid",
            "hours": "2.0"
        })
        assert response.status_code == 400


class TestWorkLogDelete:
    """実績削除テスト"""

    def test_delete_nonexistent_returns_404(self, client):
        """存在しない実績の削除は404"""
        response = client.delete("/work-logs/99999")
        assert response.status_code == 404


class TestProgressRate:
    """進捗率テスト"""

    def test_update_progress(self, client, task_id):
        """進捗率更新が成功する"""
        response = client.put(f"/tasks/{task_id}/progress", data={
            "progress_rate": "50"
        })
        assert response.status_code == 200

    def test_progress_100_percent(self, client, task_id):
        """100%が設定できる"""
        response = client.put(f"/tasks/{task_id}/progress", data={
            "progress_rate": "100"
        })
        assert response.status_code == 200

    def test_progress_0_percent(self, client, task_id):
        """0%が設定できる"""
        response = client.put(f"/tasks/{task_id}/progress", data={
            "progress_rate": "0"
        })
        assert response.status_code == 200

    def test_progress_over_100_returns_400(self, client, task_id):
        """100%超は400"""
        response = client.put(f"/tasks/{task_id}/progress", data={
            "progress_rate": "101"
        })
        assert response.status_code == 400

    def test_progress_negative_returns_400(self, client, task_id):
        """負の進捗率は400"""
        response = client.put(f"/tasks/{task_id}/progress", data={
            "progress_rate": "-1"
        })
        assert response.status_code == 400

    def test_progress_nonexistent_task_returns_404(self, client):
        """存在しない作業は404"""
        response = client.put("/tasks/99999/progress", data={
            "progress_rate": "50"
        })
        assert response.status_code == 404


class TestNavigationLink:
    """ナビゲーションリンクテスト"""

    def test_base_has_work_logs_link(self, client):
        """ベーステンプレートに実績入力リンクがある"""
        response = client.get("/")
        assert response.status_code == 200
        assert "/work-logs" in response.text
        assert "実績入力" in response.text


class TestCalculateTotals:
    """集計関数の単体テスト"""

    def test_empty_rows_returns_empty_dicts(self):
        """空のrowsは空の辞書を返す"""
        dates = [date(2026, 1, 20), date(2026, 1, 21)]
        project_totals, issue_totals = calculate_totals([], dates, {})
        assert project_totals == {}
        assert issue_totals == {}

    def test_single_row_calculates_correctly(self):
        """単一行の集計が正しく動作する"""
        dates = [date(2026, 1, 20), date(2026, 1, 21)]
        rows = [
            {'project_id': 1, 'issue_id': 10, 'task_id': 100, 'user_id': 1000}
        ]
        work_logs = {
            (100, 1000, '2026-01-20'): {'id': 1, 'hours': 2.0},
            (100, 1000, '2026-01-21'): {'id': 2, 'hours': 3.0},
        }

        project_totals, issue_totals = calculate_totals(rows, dates, work_logs)

        # プロジェクト集計
        assert project_totals[1]['2026-01-20'] == 2.0
        assert project_totals[1]['2026-01-21'] == 3.0
        assert project_totals[1]['total'] == 5.0

        # 案件集計
        assert issue_totals[(1, 10)]['2026-01-20'] == 2.0
        assert issue_totals[(1, 10)]['2026-01-21'] == 3.0
        assert issue_totals[(1, 10)]['total'] == 5.0

    def test_multiple_tasks_aggregate_correctly(self):
        """複数作業の集計が正しく動作する"""
        dates = [date(2026, 1, 20)]
        rows = [
            {'project_id': 1, 'issue_id': 10, 'task_id': 100, 'user_id': 1000},
            {'project_id': 1, 'issue_id': 10, 'task_id': 101, 'user_id': 1000},
            {'project_id': 1, 'issue_id': 11, 'task_id': 102, 'user_id': 1000},
        ]
        work_logs = {
            (100, 1000, '2026-01-20'): {'id': 1, 'hours': 2.0},
            (101, 1000, '2026-01-20'): {'id': 2, 'hours': 1.5},
            (102, 1000, '2026-01-20'): {'id': 3, 'hours': 3.0},
        }

        project_totals, issue_totals = calculate_totals(rows, dates, work_logs)

        # プロジェクト集計（全作業の合計）
        assert project_totals[1]['2026-01-20'] == 6.5
        assert project_totals[1]['total'] == 6.5

        # 案件10集計
        assert issue_totals[(1, 10)]['2026-01-20'] == 3.5
        assert issue_totals[(1, 10)]['total'] == 3.5

        # 案件11集計
        assert issue_totals[(1, 11)]['2026-01-20'] == 3.0
        assert issue_totals[(1, 11)]['total'] == 3.0

    def test_no_work_logs_returns_zeros(self):
        """実績なしの場合は0を返す"""
        dates = [date(2026, 1, 20)]
        rows = [
            {'project_id': 1, 'issue_id': 10, 'task_id': 100, 'user_id': 1000}
        ]
        work_logs = {}

        project_totals, issue_totals = calculate_totals(rows, dates, work_logs)

        assert project_totals[1]['2026-01-20'] == 0.0
        assert project_totals[1]['total'] == 0.0
        assert issue_totals[(1, 10)]['2026-01-20'] == 0.0
        assert issue_totals[(1, 10)]['total'] == 0.0


class TestGridWithTotals:
    """集計値付きグリッドの結合テスト"""

    def test_grid_shows_project_toggle(self, client, assigned_task):
        """グリッドにプロジェクト折り畳みアイコンが表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert 'class="toggle-icon"' in response.text
        assert 'toggleProject(' in response.text

    def test_grid_shows_issue_row(self, client, assigned_task):
        """グリッドに案件行が表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert 'class="issue-row"' in response.text
        assert 'toggleIssue(' in response.text

    def test_grid_shows_bulk_actions(self, client, assigned_task):
        """グリッドに一括操作ボタンが表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert 'class="bulk-actions"' in response.text
        assert '全て展開' in response.text
        assert '全て折り畳み' in response.text
        assert '案件のみ表示' in response.text

    def test_grid_shows_summary_cells(self, client, assigned_task):
        """グリッドに集計セルが表示される"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert 'class="summary-cell' in response.text

    def test_grid_project_row_has_data_attribute(self, client, assigned_task):
        """プロジェクト行にdata-project-id属性がある"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        assert 'data-project-id=' in response.text

    def test_grid_issue_row_has_data_attributes(self, client, assigned_task):
        """案件行にdata-project-idとdata-issue-id属性がある"""
        response = client.get("/work-logs/grid")
        assert response.status_code == 200
        # issue-rowにdata-project-idとdata-issue-idがあることを確認
        assert re.search(r'class="issue-row"[^>]*data-project-id=', response.text)
        assert re.search(r'class="issue-row"[^>]*data-issue-id=', response.text)
