"""オートコンプリート検索APIテスト"""
import uuid
import pytest


class TestSearchUsers:
    """ユーザー検索テスト"""

    def test_search_users_empty_query(self, client):
        """空クエリで全ユーザー取得"""
        response = client.get("/search/users")
        assert response.status_code == 200

    def test_search_users_with_query(self, client):
        """クエリでフィルタリング"""
        # テストユーザー作成
        unique_cd = f"SU-{uuid.uuid4().hex[:6]}"
        client.post("/users", data={
            "cd": unique_cd,
            "name": "検索テストユーザー",
            "email": f"{unique_cd}@test.example.com"
        })

        response = client.get(f"/search/users?q={unique_cd}")
        assert response.status_code == 200
        assert unique_cd in response.text

    def test_search_users_exclude(self, client):
        """excludeでフィルタリング"""
        response = client.get("/search/users?exclude=1&exclude=2")
        assert response.status_code == 200

    def test_search_users_no_match(self, client):
        """マッチなしで該当なし表示"""
        response = client.get("/search/users?q=NONEXISTENT_USER_12345")
        assert response.status_code == 200
        assert "該当なし" in response.text


class TestSearchProjects:
    """プロジェクト検索テスト"""

    def test_search_projects_empty_query(self, client):
        """空クエリで全プロジェクト取得"""
        response = client.get("/search/projects")
        assert response.status_code == 200

    def test_search_projects_with_query(self, client):
        """クエリでフィルタリング"""
        # テストプロジェクト作成
        unique_cd = f"SP-{uuid.uuid4().hex[:6]}"
        client.post("/projects", data={
            "cd": unique_cd,
            "name": "検索テストプロジェクト"
        })

        response = client.get(f"/search/projects?q={unique_cd}")
        assert response.status_code == 200
        assert unique_cd in response.text

    def test_search_projects_no_match(self, client):
        """マッチなしで該当なし表示"""
        response = client.get("/search/projects?q=NONEXISTENT_PROJECT_12345")
        assert response.status_code == 200
        assert "該当なし" in response.text


class TestSearchIssues:
    """案件検索テスト"""

    def test_search_issues_empty_query(self, client):
        """空クエリで全案件取得"""
        response = client.get("/search/issues")
        assert response.status_code == 200

    def test_search_issues_no_match(self, client):
        """マッチなしで該当なし表示"""
        response = client.get("/search/issues?q=NONEXISTENT_ISSUE_12345")
        assert response.status_code == 200
        assert "該当なし" in response.text
