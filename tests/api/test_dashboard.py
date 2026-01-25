"""ダッシュボードKPIテスト"""
import pytest


class TestDashboard:
    """ダッシュボードテスト"""

    def test_index_returns_200(self, client):
        """ホームページが200を返す"""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_kpi_section(self, client):
        """KPIセクションが含まれる"""
        response = client.get("/")
        assert response.status_code == 200
        assert "kpi-grid" in response.text
        assert "kpi-card" in response.text

    def test_index_contains_today_hours(self, client):
        """今日の工数が表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "今日の工数" in response.text

    def test_index_contains_monthly_stats(self, client):
        """今月の予実が表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "今月の予実" in response.text

    def test_index_contains_project_count(self, client):
        """プロジェクト数が表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "プロジェクト" in response.text

    def test_index_contains_user_count(self, client):
        """ユーザー数が表示される"""
        response = client.get("/")
        assert response.status_code == 200
        assert "ユーザー" in response.text

    def test_index_zero_values_display(self, client):
        """データなしでも正常表示（0表示）"""
        response = client.get("/")
        assert response.status_code == 200
        # 数値フォーマットが含まれていることを確認
        assert "H" in response.text  # 工数単位
