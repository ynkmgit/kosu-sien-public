"""月次アサインAPIテスト"""
import uuid
import pytest

from database import get_db


@pytest.fixture
def user_id(client):
    """テスト用ユーザーを作成してIDを返す"""
    import re
    unique_cd = f"MA-{uuid.uuid4().hex[:6]}"
    response = client.post("/users", data={
        "cd": unique_cd,
        "name": "月次テストユーザー",
        "email": f"{unique_cd}@test.example.com"
    })
    match = re.search(r'id="user-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def project_id(client):
    """テスト用プロジェクトを作成してIDを返す"""
    import re
    unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
    response = client.post("/projects", data={
        "cd": unique_cd,
        "name": "月次テストPJ",
        "description": ""
    })
    match = re.search(r'id="project-(\d+)"', response.text)
    return int(match.group(1))


@pytest.fixture
def inactive_user_id():
    """無効ユーザーをDBに直接作成してIDを返す"""
    unique_cd = f"MA-{uuid.uuid4().hex[:6]}"
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO user (cd, name, email, is_active) VALUES (?, ?, ?, 0)",
            (unique_cd, "無効ユーザー", f"{unique_cd}@test.example.com")
        )
        return cursor.lastrowid


class TestMonthlyAssignmentPage:
    """ページ表示テスト"""

    def test_page_returns_200(self, client):
        """ページ表示が成功する"""
        response = client.get("/monthly-assignments")
        assert response.status_code == 200
        assert "月次アサイン" in response.text

    def test_page_with_month_param(self, client):
        """月指定でページ表示"""
        response = client.get("/monthly-assignments?month=2026-01")
        assert response.status_code == 200


class TestMonthlyAssignmentGrid:
    """グリッド取得テスト"""

    def test_grid_returns_200(self, client):
        """グリッド取得が成功する"""
        response = client.get("/monthly-assignments/grid")
        assert response.status_code == 200

    def test_grid_with_month_param(self, client):
        """月指定でグリッド取得"""
        response = client.get("/monthly-assignments/grid?month=2026-01")
        assert response.status_code == 200

    def test_grid_invalid_month_returns_400(self, client):
        """不正な月形式は400"""
        response = client.get("/monthly-assignments/grid?month=invalid")
        assert response.status_code == 400

    def test_grid_shows_users(self, client, user_id):
        """グリッドにユーザーが表示される"""
        response = client.get("/monthly-assignments/grid")
        assert response.status_code == 200
        assert "月次テストユーザー" in response.text

    def test_grid_shows_projects(self, client, project_id):
        """グリッドにプロジェクトが表示される"""
        response = client.get("/monthly-assignments/grid")
        assert response.status_code == 200
        assert "PJ-" in response.text

    def test_grid_shows_navigation(self, client):
        """グリッドに月ナビゲーションが表示される"""
        response = client.get("/monthly-assignments/grid?month=2026-01")
        assert response.status_code == 200
        assert "前月" in response.text
        assert "翌月" in response.text
        assert "2026年1月" in response.text


class TestMonthlyAssignmentUpsert:
    """アサイン追加/更新テスト"""

    def test_create_assignment(self, client, user_id, project_id):
        """アサイン追加が成功する"""
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "80.0"
        })
        assert response.status_code == 200

        # グリッドで確認
        grid_response = client.get("/monthly-assignments/grid?month=2026-01")
        assert "80.0" in grid_response.text or "80" in grid_response.text

    def test_update_assignment(self, client, user_id, project_id):
        """アサイン更新が成功する"""
        # 作成
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-02",
            "planned_hours": "80.0"
        })
        # 更新
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-02",
            "planned_hours": "120.0"
        })
        assert response.status_code == 200

    def test_delete_by_zero(self, client, user_id, project_id):
        """0入力でアサイン削除"""
        # 作成
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-03",
            "planned_hours": "80.0"
        })
        # 0で削除
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-03",
            "planned_hours": "0"
        })
        assert response.status_code == 200

    def test_negative_hours_returns_400(self, client, user_id, project_id):
        """負の工数は400"""
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "-10"
        })
        assert response.status_code == 400

    def test_invalid_user_returns_404(self, client, project_id):
        """存在しないユーザーは404"""
        response = client.post("/monthly-assignments", data={
            "user_id": 99999,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "80.0"
        })
        assert response.status_code == 404

    def test_invalid_project_returns_404(self, client, user_id):
        """存在しないプロジェクトは404"""
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": 99999,
            "year_month": "2026-01",
            "planned_hours": "80.0"
        })
        assert response.status_code == 404

    def test_inactive_user_new_assignment_returns_400(self, client, inactive_user_id, project_id):
        """無効ユーザーへの新規アサインは400"""
        response = client.post("/monthly-assignments", data={
            "user_id": inactive_user_id,
            "project_id": project_id,
            "year_month": "2026-01",
            "planned_hours": "80.0"
        })
        assert response.status_code == 400
        assert "無効なユーザー" in response.text

    def test_invalid_month_format_returns_400(self, client, user_id, project_id):
        """不正な月形式は400"""
        response = client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "invalid",
            "planned_hours": "80.0"
        })
        assert response.status_code == 400


class TestMonthlyAssignmentDelete:
    """アサイン削除テスト"""

    def test_delete_nonexistent_returns_404(self, client):
        """存在しないアサインの削除は404"""
        response = client.delete("/monthly-assignments/99999")
        assert response.status_code == 404


class TestMonthlyAssignmentCalculations:
    """計算テスト"""

    def test_mm_calculation(self, client, user_id, project_id):
        """人月(MM)計算が正しい"""
        # 160h = 1.00MM
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": project_id,
            "year_month": "2026-04",
            "planned_hours": "160.0"
        })
        response = client.get("/monthly-assignments/grid?month=2026-04")
        assert response.status_code == 200
        assert "1.00MM" in response.text

    def test_row_total(self, client, user_id):
        """行合計が計算される"""
        import re
        # 2つのプロジェクトを作成
        response1 = client.post("/projects", data={
            "cd": f"P1-{uuid.uuid4().hex[:6]}",
            "name": "PJ1",
            "description": ""
        })
        match1 = re.search(r'id="project-(\d+)"', response1.text)
        pj1_id = int(match1.group(1))

        response2 = client.post("/projects", data={
            "cd": f"P2-{uuid.uuid4().hex[:6]}",
            "name": "PJ2",
            "description": ""
        })
        match2 = re.search(r'id="project-(\d+)"', response2.text)
        pj2_id = int(match2.group(1))

        # 両方にアサイン
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": pj1_id,
            "year_month": "2026-05",
            "planned_hours": "80.0"
        })
        client.post("/monthly-assignments", data={
            "user_id": user_id,
            "project_id": pj2_id,
            "year_month": "2026-05",
            "planned_hours": "80.0"
        })

        response = client.get("/monthly-assignments/grid?month=2026-05")
        assert response.status_code == 200
        assert "160.0h" in response.text  # 合計


class TestNavigationLink:
    """ナビゲーションリンクテスト"""

    def test_base_has_monthly_assignments_link(self, client):
        """ベーステンプレートに月次アサインリンクがある"""
        response = client.get("/")
        assert response.status_code == 200
        assert "/monthly-assignments" in response.text
        assert "月次アサイン" in response.text
