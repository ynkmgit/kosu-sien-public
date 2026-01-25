"""ステータスAPIテスト"""
import re
import pytest


class TestStatusList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client):
        """一覧取得が成功する"""
        response = client.get("/projects/1/statuses/list")
        assert response.status_code == 200

    def test_list_contains_default_statuses(self, client):
        """デフォルトステータスが含まれる"""
        response = client.get("/projects/1/statuses/list")
        assert response.status_code == 200
        assert "未着手" in response.text
        assert "進行中" in response.text
        assert "完了" in response.text

    def test_list_with_invalid_project_returns_404(self, client):
        """存在しないプロジェクトのステータス一覧は404"""
        response = client.get("/projects/99999/statuses/list")
        assert response.status_code == 404


class TestStatusCreate:
    """作成テスト"""

    def test_create_returns_200(self, client):
        """作成が成功する"""
        response = client.post("/projects/1/statuses", data={
            "code": "review",
            "name": "レビュー中",
            "sort_order": "3"
        })
        assert response.status_code == 200
        assert "review" in response.text
        assert "レビュー中" in response.text

    def test_create_with_invalid_project_returns_404(self, client):
        """存在しないプロジェクトへのステータス作成は404"""
        response = client.post("/projects/99999/statuses", data={
            "code": "test",
            "name": "テスト",
            "sort_order": "0"
        })
        assert response.status_code == 404


class TestStatusUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client):
        """更新が成功する"""
        # まずステータスを作成
        create_resp = client.post("/projects/1/statuses", data={
            "code": "upd_test",
            "name": "更新前",
            "sort_order": "10"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="status-(\d+)"', create_resp.text)
        assert match
        status_id = match.group(1)

        # 更新
        response = client.put(f"/projects/1/statuses/{status_id}", data={
            "code": "upd_test",
            "name": "更新後",
            "sort_order": "11"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client):
        """存在しないステータスの更新は404"""
        response = client.put("/projects/1/statuses/99999", data={
            "code": "none",
            "name": "存在しない",
            "sort_order": "0"
        })
        assert response.status_code == 404


class TestStatusDelete:
    """削除テスト"""

    def test_delete_success(self, client):
        """削除が成功する"""
        # まずステータスを作成
        create_resp = client.post("/projects/1/statuses", data={
            "code": "del_test",
            "name": "削除対象",
            "sort_order": "99"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="status-(\d+)"', create_resp.text)
        assert match
        status_id = match.group(1)

        # 削除
        response = client.delete(f"/projects/1/statuses/{status_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client):
        """存在しないステータスの削除は404"""
        response = client.delete("/projects/1/statuses/99999")
        assert response.status_code == 404

    def test_delete_used_status_returns_400(self, client):
        """使用中のステータスの削除は400"""
        # デフォルトステータス(open)を使う案件を作成
        client.post("/projects/1/issues", data={
            "cd": "STATUS_TEST",
            "name": "ステータステスト用",
            "status": "open",
            "description": ""
        })

        # openステータスのIDを取得
        list_resp = client.get("/projects/1/statuses/list")
        match = re.search(r'id="status-(\d+)"[^>]*>.*?<td[^>]*>open</td>', list_resp.text, re.DOTALL)
        if match:
            status_id = match.group(1)
            # 使用中のステータスを削除しようとする
            response = client.delete(f"/projects/1/statuses/{status_id}")
            assert response.status_code == 400


class TestStatusRow:
    """行取得テスト"""

    def test_row_returns_200(self, client):
        """行取得が成功する"""
        # まずステータスを作成
        create_resp = client.post("/projects/1/statuses", data={
            "code": "row_test",
            "name": "行テスト",
            "sort_order": "50"
        })
        match = re.search(r'id="status-(\d+)"', create_resp.text)
        status_id = match.group(1)

        response = client.get(f"/projects/1/statuses/{status_id}/row")
        assert response.status_code == 200
        assert "row_test" in response.text

    def test_row_nonexistent_returns_404(self, client):
        """存在しないステータスの行取得は404"""
        response = client.get("/projects/1/statuses/99999/row")
        assert response.status_code == 404


class TestStatusEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client):
        """編集フォーム取得が成功する"""
        # まずステータスを作成
        create_resp = client.post("/projects/1/statuses", data={
            "code": "edit_test",
            "name": "編集テスト",
            "sort_order": "60"
        })
        match = re.search(r'id="status-(\d+)"', create_resp.text)
        status_id = match.group(1)

        response = client.get(f"/projects/1/statuses/{status_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client):
        """存在しないステータスの編集フォーム取得は404"""
        response = client.get("/projects/1/statuses/99999/edit")
        assert response.status_code == 404


class TestProjectDefaultStatuses:
    """プロジェクト作成時のデフォルトステータステスト"""

    def test_new_project_has_default_statuses(self, client):
        """新規プロジェクト作成時にデフォルトステータスが作成される"""
        # 新規プロジェクト作成
        create_resp = client.post("/projects", data={
            "cd": "STATUS_PJ",
            "name": "ステータステストPJ",
            "description": ""
        })
        assert create_resp.status_code == 200

        # プロジェクトIDを抽出
        match = re.search(r'id="project-(\d+)"', create_resp.text)
        assert match
        project_id = match.group(1)

        # ステータス一覧を確認
        list_resp = client.get(f"/projects/{project_id}/statuses/list")
        assert list_resp.status_code == 200
        assert "未着手" in list_resp.text
        assert "進行中" in list_resp.text
        assert "完了" in list_resp.text
