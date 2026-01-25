"""グローバルフィルターURL基盤テスト"""
import pytest


class TestBuildFilterQuery:
    """build_filter_query関数のテスト"""

    def test_empty_params(self):
        """パラメータが空の場合は空文字を返す"""
        from routers.common import build_filter_query

        assert build_filter_query({}) == ""
        assert build_filter_query({"user": [], "project": [], "issue": []}) == ""

    def test_single_user(self):
        """ユーザー単一選択"""
        from routers.common import build_filter_query

        result = build_filter_query({"user": [1], "project": [], "issue": []})
        assert result == "?user=1"

    def test_multiple_users(self):
        """ユーザー複数選択"""
        from routers.common import build_filter_query

        result = build_filter_query({"user": [1, 2, 3], "project": [], "issue": []})
        assert result == "?user=1&user=2&user=3"

    def test_single_project(self):
        """プロジェクト単一選択"""
        from routers.common import build_filter_query

        result = build_filter_query({"user": [], "project": [10], "issue": []})
        assert result == "?project=10"

    def test_combined_filters(self):
        """複合フィルター"""
        from routers.common import build_filter_query

        result = build_filter_query({"user": [1], "project": [2], "issue": [3]})
        assert result == "?user=1&project=2&issue=3"

    def test_all_multiple(self):
        """全パラメータ複数"""
        from routers.common import build_filter_query

        result = build_filter_query({
            "user": [1, 2],
            "project": [3, 4],
            "issue": [5, 6]
        })
        assert result == "?user=1&user=2&project=3&project=4&issue=5&issue=6"


class TestPageFilterParams:
    """各ページがフィルターパラメータを受け入れるかテスト"""

    def test_index_accepts_filters(self, client):
        """インデックスページ"""
        response = client.get("/?user=1&project=2")
        assert response.status_code == 200

    def test_work_logs_accepts_filters(self, client):
        """実績入力ページ"""
        response = client.get("/work-logs?user=1&project=2&issue=3")
        assert response.status_code == 200

    def test_projects_accepts_filters(self, client):
        """プロジェクト一覧ページ"""
        response = client.get("/projects?user=1&project=2")
        assert response.status_code == 200

    def test_users_accepts_filters(self, client):
        """ユーザー一覧ページ"""
        response = client.get("/users?user=1&project=2")
        assert response.status_code == 200

    def test_monthly_assignments_accepts_filters(self, client):
        """月次アサインページ"""
        response = client.get("/monthly-assignments?user=1&project=2")
        assert response.status_code == 200

    def test_work_report_accepts_filters(self, client):
        """業務終了報告ページ"""
        response = client.get("/work-report?user=1&project=2")
        assert response.status_code == 200


class TestNavLinksPreserveFilters:
    """ナビリンクがフィルターを保持するかテスト"""

    def test_nav_links_contain_filter_params(self, client):
        """フィルターパラメータ付きでアクセス時、ナビリンクにも含まれる"""
        response = client.get("/?user=1&user=2&project=3")
        assert response.status_code == 200

        html = response.text
        # ナビリンクにフィルターパラメータが含まれることを確認
        assert 'href="/work-logs?user=1&amp;user=2&amp;project=3"' in html
        assert 'href="/projects?user=1&amp;user=2&amp;project=3"' in html
        assert 'href="/users?user=1&amp;user=2&amp;project=3"' in html

    def test_nav_links_no_filters_when_empty(self, client):
        """フィルターなしでアクセス時、ナビリンクもフィルターなし"""
        response = client.get("/")
        assert response.status_code == 200

        html = response.text
        # クエリパラメータなしのリンク
        assert 'href="/work-logs"' in html
        assert 'href="/projects"' in html
        assert 'href="/users"' in html

    def test_filter_preserved_across_pages(self, client):
        """ページ間でフィルターが保持される"""
        # projectsページにフィルター付きでアクセス
        response = client.get("/projects?user=5&issue=10")
        assert response.status_code == 200

        html = response.text
        # 他のナビリンクにも同じフィルターが含まれる
        assert 'href="/work-logs?user=5&amp;issue=10"' in html
        assert 'href="/monthly-assignments?user=5&amp;issue=10"' in html

    def test_work_logs_filter_preserved_in_nav(self, client):
        """実績入力ページでフィルターがナビリンクに保持される"""
        response = client.get("/work-logs?user=1&project=2")
        assert response.status_code == 200

        html = response.text
        # ナビリンクにフィルターが含まれる
        assert 'href="/projects?user=1&amp;project=2"' in html
        assert 'href="/monthly-assignments?user=1&amp;project=2"' in html
        assert 'href="/users?user=1&amp;project=2"' in html

    def test_work_report_filter_preserved_in_nav(self, client):
        """業務終了報告ページでproject/issueフィルターが保持される"""
        response = client.get("/work-report?project=2&issue=3")
        assert response.status_code == 200

        html = response.text
        # ナビリンクにproject/issueフィルターが含まれる
        assert 'href="/work-logs?project=2&amp;issue=3"' in html
        assert 'href="/projects?project=2&amp;issue=3"' in html
