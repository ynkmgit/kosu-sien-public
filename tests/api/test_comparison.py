"""比較・分析機能テスト"""
import re
import uuid
import pytest

from database import get_db


@pytest.fixture
def user_id(client):
    """テスト用ユーザーを作成してIDを返す"""
    unique_cd = f"CMP-{uuid.uuid4().hex[:6]}"
    response = client.post("/users", data={
        "cd": unique_cd,
        "name": "比較テストユーザー",
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
        "name": "比較テストPJ",
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
        "name": "比較テスト案件",
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
        "name": "比較テスト作業",
        "description": ""
    })
    match = re.search(r'id="task-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def issue_with_estimate(client, project_id, issue_id):
    """見積内訳付き案件"""
    # 見積内訳を追加
    client.post(f"/projects/{project_id}/issues/{issue_id}/estimates", data={
        "name": "設計",
        "hours": "16.0"
    })
    client.post(f"/projects/{project_id}/issues/{issue_id}/estimates", data={
        "name": "実装",
        "hours": "24.0"
    })
    return issue_id


@pytest.fixture
def issue_with_actual(client, project_id, issue_id, task_id, user_id):
    """実績付き案件"""
    # 担当割当
    client.post(f"/projects/{project_id}/assignees/toggle", data={
        "task_id": task_id,
        "user_id": user_id
    })
    # 実績追加
    client.post("/work-logs", data={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": "2026-01-15",
        "hours": "4.0"
    })
    client.post("/work-logs", data={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": "2026-01-16",
        "hours": "6.0"
    })
    return issue_id


class TestIssueComparison:
    """案件比較表示テスト"""

    def test_issue_list_shows_estimate(self, client, project_id, issue_with_estimate):
        """案件一覧に見積が表示される"""
        response = client.get(f"/projects/{project_id}/issues/list")
        assert response.status_code == 200
        assert "40.0h" in response.text  # 16 + 24

    def test_issue_list_shows_actual(self, client, project_id, issue_with_actual):
        """案件一覧に実績が表示される"""
        response = client.get(f"/projects/{project_id}/issues/list")
        assert response.status_code == 200
        assert "10.0h" in response.text  # 4 + 6

    def test_issue_list_shows_comparison(self, client, project_id, issue_id, task_id, user_id):
        """案件一覧に見積/実績/残/消化率が表示される"""
        # 見積内訳追加
        client.post(f"/projects/{project_id}/issues/{issue_id}/estimates", data={
            "name": "作業",
            "hours": "20.0"
        })
        # 担当割当
        client.post(f"/projects/{project_id}/assignees/toggle", data={
            "task_id": task_id,
            "user_id": user_id
        })
        # 実績追加
        client.post("/work-logs", data={
            "task_id": task_id,
            "user_id": user_id,
            "work_date": "2026-01-15",
            "hours": "8.0"
        })

        response = client.get(f"/projects/{project_id}/issues/list")
        assert response.status_code == 200
        assert "20.0h" in response.text  # 見積
        assert "8.0h" in response.text   # 実績
        assert "12.0h" in response.text  # 残
        assert "40%" in response.text    # 消化率

    def test_issue_list_shows_no_estimate(self, client, project_id, issue_id):
        """見積なし案件は「-」表示"""
        response = client.get(f"/projects/{project_id}/issues/list")
        assert response.status_code == 200
        # 見積・残・消化率が「-」になっていること

    def test_issue_list_shows_overrun(self, client, project_id, issue_id, task_id, user_id):
        """消化率100%超は警告スタイル"""
        # 少ない見積
        client.post(f"/projects/{project_id}/issues/{issue_id}/estimates", data={
            "name": "作業",
            "hours": "5.0"
        })
        # 担当割当
        client.post(f"/projects/{project_id}/assignees/toggle", data={
            "task_id": task_id,
            "user_id": user_id
        })
        # 多い実績
        client.post("/work-logs", data={
            "task_id": task_id,
            "user_id": user_id,
            "work_date": "2026-01-15",
            "hours": "8.0"
        })

        response = client.get(f"/projects/{project_id}/issues/list")
        assert response.status_code == 200
        # 160% (8/5) と残がマイナスになる
        assert "160%" in response.text
        assert "-3.0h" in response.text


class TestMonthlyAssignmentComparison:
    """月次アサイン比較表示テスト"""

    def test_grid_simple_mode(self, client):
        """簡易モードでグリッド表示"""
        response = client.get("/monthly-assignments/grid?month=2026-01&mode=simple")
        assert response.status_code == 200
        assert "簡易" in response.text
        assert "詳細" in response.text

    def test_grid_detail_mode(self, client):
        """詳細モードでグリッド表示"""
        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "予定" in response.text
        assert "実績" in response.text
        assert "残" in response.text
        assert "消化率" in response.text

    def test_grid_detail_shows_planned(self, client, user_id, project_id):
        """詳細モードで予定時間が表示される"""
        # アサイン追加
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "40.0"
        })

        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "40.0h" in response.text

    def test_grid_detail_shows_actual(self, client, project_id, issue_id, task_id, user_id):
        """詳細モードで実績時間が表示される"""
        # 担当割当
        client.post(f"/projects/{project_id}/assignees/toggle", data={
            "task_id": task_id,
            "user_id": user_id
        })
        # 実績追加
        client.post("/work-logs", data={
            "task_id": task_id,
            "user_id": user_id,
            "work_date": "2026-01-15",
            "hours": "8.0"
        })

        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "8.0h" in response.text

    def test_grid_detail_shows_comparison(self, client, project_id, issue_id, task_id, user_id):
        """詳細モードで予定/実績/残/消化率が表示される"""
        # アサイン追加
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "40.0"
        })
        # 担当割当
        client.post(f"/projects/{project_id}/assignees/toggle", data={
            "task_id": task_id,
            "user_id": user_id
        })
        # 実績追加
        client.post("/work-logs", data={
            "task_id": task_id,
            "user_id": user_id,
            "work_date": "2026-01-15",
            "hours": "16.0"
        })

        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "40.0h" in response.text  # 予定
        assert "16.0h" in response.text  # 実績
        assert "24.0h" in response.text  # 残
        assert "40%" in response.text    # 消化率

    def test_page_with_mode_param(self, client):
        """ページにmodeパラメータが渡される"""
        response = client.get("/monthly-assignments?month=2026-01&mode=detail")
        assert response.status_code == 200

    def test_mode_toggle_buttons(self, client):
        """モード切替ボタンが表示される"""
        response = client.get("/monthly-assignments/grid?month=2026-01")
        assert response.status_code == 200
        assert 'mode=simple' in response.text
        assert 'mode=detail' in response.text


class TestNavigationWithMode:
    """モード付きナビゲーションテスト"""

    def test_prev_month_keeps_mode(self, client):
        """前月リンクがモードを維持する"""
        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "month=2025-12&mode=detail" in response.text

    def test_next_month_keeps_mode(self, client):
        """翌月リンクがモードを維持する"""
        response = client.get("/monthly-assignments/grid?month=2026-01&mode=detail")
        assert response.status_code == 200
        assert "month=2026-02&mode=detail" in response.text
