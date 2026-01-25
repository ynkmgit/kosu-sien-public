"""作業APIテスト"""
import re
import uuid
import pytest


@pytest.fixture
def issue_id(client):
    """テスト用案件を作成してIDを返す"""
    unique_cd = f"TSK-{uuid.uuid4().hex[:6]}"
    response = client.post("/projects/1/issues", data={
        "cd": unique_cd,
        "name": "作業テスト用案件",
        "status": "open",
        "description": ""
    })
    match = re.search(r'id="issue-(\d+)"', response.text)
    return int(match.group(1))


class TestTaskList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client, issue_id):
        """一覧取得が成功する"""
        response = client.get(f"/projects/1/issues/{issue_id}/tasks/list")
        assert response.status_code == 200

    def test_list_with_invalid_issue_returns_404(self, client):
        """存在しない案件の作業一覧は404"""
        response = client.get("/projects/1/issues/99999/tasks/list")
        assert response.status_code == 404

    def test_list_with_invalid_project_returns_404(self, client, issue_id):
        """存在しないプロジェクトでの作業一覧は404"""
        response = client.get(f"/projects/99999/issues/{issue_id}/tasks/list")
        assert response.status_code == 404


class TestTaskCreate:
    """作成テスト"""

    def test_create_returns_200(self, client, issue_id):
        """作成が成功する"""
        response = client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "T001",
            "name": "テスト作業",
            "description": "テスト説明"
        })
        assert response.status_code == 200
        assert "T001" in response.text
        assert "テスト作業" in response.text

    def test_create_with_invalid_issue_returns_404(self, client):
        """存在しない案件への作業作成は404"""
        response = client.post("/projects/1/issues/99999/tasks", data={
            "cd": "T002",
            "name": "テスト作業",
            "description": ""
        })
        assert response.status_code == 404


class TestTaskUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client, issue_id):
        """更新が成功する"""
        # まず作業を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "UPD001",
            "name": "更新前",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="task-(\d+)"', create_resp.text)
        assert match
        task_id = match.group(1)

        # 更新
        response = client.put(f"/projects/1/issues/{issue_id}/tasks/{task_id}", data={
            "cd": "UPD001",
            "name": "更新後",
            "description": "更新説明"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client, issue_id):
        """存在しない作業の更新は404"""
        response = client.put(f"/projects/1/issues/{issue_id}/tasks/99999", data={
            "cd": "NONE",
            "name": "存在しない",
            "description": ""
        })
        assert response.status_code == 404


class TestTaskDelete:
    """削除テスト"""

    def test_delete_success(self, client, issue_id):
        """削除が成功する"""
        # まず作業を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "DEL001",
            "name": "削除対象",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="task-(\d+)"', create_resp.text)
        assert match
        task_id = match.group(1)

        # 削除
        response = client.delete(f"/projects/1/issues/{issue_id}/tasks/{task_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client, issue_id):
        """存在しない作業の削除は404"""
        response = client.delete(f"/projects/1/issues/{issue_id}/tasks/99999")
        assert response.status_code == 404


class TestTaskRow:
    """行取得テスト"""

    def test_row_returns_200(self, client, issue_id):
        """行取得が成功する"""
        # まず作業を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "ROW001",
            "name": "行テスト",
            "description": ""
        })
        match = re.search(r'id="task-(\d+)"', create_resp.text)
        task_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/tasks/{task_id}/row")
        assert response.status_code == 200
        assert "ROW001" in response.text

    def test_row_nonexistent_returns_404(self, client, issue_id):
        """存在しない作業の行取得は404"""
        response = client.get(f"/projects/1/issues/{issue_id}/tasks/99999/row")
        assert response.status_code == 404


class TestTaskEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client, issue_id):
        """編集フォーム取得が成功する"""
        # まず作業を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "EDT001",
            "name": "編集テスト",
            "description": ""
        })
        match = re.search(r'id="task-(\d+)"', create_resp.text)
        task_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/tasks/{task_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client, issue_id):
        """存在しない作業の編集フォーム取得は404"""
        response = client.get(f"/projects/1/issues/{issue_id}/tasks/99999/edit")
        assert response.status_code == 404


class TestTaskSearch:
    """検索テスト"""

    def test_search_by_name(self, client, issue_id):
        """名前で検索できる"""
        # 作業を作成
        client.post(f"/projects/1/issues/{issue_id}/tasks", data={
            "cd": "SRCH001",
            "name": "検索対象作業",
            "description": ""
        })

        response = client.get(f"/projects/1/issues/{issue_id}/tasks/list?q=検索対象")
        assert response.status_code == 200
        assert "検索対象作業" in response.text

    def test_search_no_results(self, client, issue_id):
        """検索結果がない場合は空"""
        response = client.get(f"/projects/1/issues/{issue_id}/tasks/list?q=存在しないキーワード")
        assert response.status_code == 200
        # tbodyは存在するがtrはない
        assert "<tbody>" in response.text
