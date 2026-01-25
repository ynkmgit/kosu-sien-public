"""案件APIテスト"""
import re
import pytest


class TestIssueList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client):
        """一覧取得が成功する"""
        response = client.get("/projects/1/issues/list")
        assert response.status_code == 200

    def test_list_with_invalid_project_returns_404(self, client):
        """存在しないプロジェクトの案件一覧は404"""
        response = client.get("/projects/99999/issues/list")
        assert response.status_code == 404


class TestIssueCreate:
    """作成テスト"""

    def test_create_returns_200(self, client):
        """作成が成功する"""
        response = client.post("/projects/1/issues", data={
            "cd": "TEST001",
            "name": "テスト案件",
            "status": "open",
            "description": "テスト説明"
        })
        assert response.status_code == 200
        assert "TEST001" in response.text
        assert "テスト案件" in response.text

    def test_create_with_invalid_project_returns_404(self, client):
        """存在しないプロジェクトへの案件作成は404"""
        response = client.post("/projects/99999/issues", data={
            "cd": "TEST002",
            "name": "テスト案件",
            "status": "open",
            "description": ""
        })
        assert response.status_code == 404


class TestIssueUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client):
        """更新が成功する"""
        # まず案件を作成
        create_resp = client.post("/projects/1/issues", data={
            "cd": "UPD001",
            "name": "更新前",
            "status": "open",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="issue-(\d+)"', create_resp.text)
        assert match
        issue_id = match.group(1)

        # 更新
        response = client.put(f"/projects/1/issues/{issue_id}", data={
            "cd": "UPD001",
            "name": "更新後",
            "status": "in_progress",
            "description": "更新説明"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client):
        """存在しない案件の更新は404"""
        response = client.put("/projects/1/issues/99999", data={
            "cd": "NONE",
            "name": "存在しない",
            "status": "open",
            "description": ""
        })
        assert response.status_code == 404


class TestIssueStatusUpdate:
    """ステータス更新テスト"""

    def test_status_update_returns_200(self, client):
        """ステータス更新が成功する"""
        # まず案件を作成
        create_resp = client.post("/projects/1/issues", data={
            "cd": "STS001",
            "name": "ステータステスト",
            "status": "open",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="issue-(\d+)"', create_resp.text)
        assert match
        issue_id = match.group(1)

        # ステータス更新
        response = client.put(f"/projects/1/issues/{issue_id}/status", data={
            "status": "closed"
        })
        assert response.status_code == 200
        assert "status-closed" in response.text


class TestIssueDelete:
    """削除テスト"""

    def test_delete_success(self, client):
        """削除が成功する"""
        # まず案件を作成
        create_resp = client.post("/projects/1/issues", data={
            "cd": "DEL001",
            "name": "削除対象",
            "status": "open",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="issue-(\d+)"', create_resp.text)
        assert match
        issue_id = match.group(1)

        # 削除
        response = client.delete(f"/projects/1/issues/{issue_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client):
        """存在しない案件の削除は404"""
        response = client.delete("/projects/1/issues/99999")
        assert response.status_code == 404


class TestIssueRow:
    """行取得テスト"""

    def test_row_returns_200(self, client):
        """行取得が成功する"""
        # まず案件を作成
        create_resp = client.post("/projects/1/issues", data={
            "cd": "ROW001",
            "name": "行テスト",
            "status": "open",
            "description": ""
        })
        match = re.search(r'id="issue-(\d+)"', create_resp.text)
        issue_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/row")
        assert response.status_code == 200
        assert "ROW001" in response.text

    def test_row_nonexistent_returns_404(self, client):
        """存在しない案件の行取得は404"""
        response = client.get("/projects/1/issues/99999/row")
        assert response.status_code == 404


class TestIssueEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client):
        """編集フォーム取得が成功する"""
        # まず案件を作成
        create_resp = client.post("/projects/1/issues", data={
            "cd": "EDT001",
            "name": "編集テスト",
            "status": "open",
            "description": ""
        })
        match = re.search(r'id="issue-(\d+)"', create_resp.text)
        issue_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client):
        """存在しない案件の編集フォーム取得は404"""
        response = client.get("/projects/1/issues/99999/edit")
        assert response.status_code == 404
