"""案件見積内訳APIテスト"""
import re
import uuid
import pytest


@pytest.fixture
def issue_id(client):
    """テスト用案件を作成してIDを返す"""
    unique_cd = f"EST-{uuid.uuid4().hex[:6]}"
    response = client.post("/projects/1/issues", data={
        "cd": unique_cd,
        "name": "見積テスト用案件",
        "status": "open",
        "description": ""
    })
    match = re.search(r'id="issue-(\d+)"', response.text)
    return int(match.group(1))


class TestEstimateList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client, issue_id):
        """一覧取得が成功する"""
        response = client.get(f"/projects/1/issues/{issue_id}/estimates/list")
        assert response.status_code == 200

    def test_list_with_invalid_issue_returns_404(self, client):
        """存在しない案件の見積一覧は404"""
        response = client.get("/projects/1/issues/99999/estimates/list")
        assert response.status_code == 404

    def test_list_shows_total(self, client, issue_id):
        """一覧に合計行が表示される"""
        response = client.get(f"/projects/1/issues/{issue_id}/estimates/list")
        assert response.status_code == 200
        assert "合計" in response.text


class TestEstimateCreate:
    """作成テスト"""

    def test_create_returns_200(self, client, issue_id):
        """作成が成功する"""
        response = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "設計",
            "hours": "16.0"
        })
        assert response.status_code == 200
        assert "設計" in response.text
        assert "16.00" in response.text

    def test_create_with_invalid_issue_returns_404(self, client):
        """存在しない案件への見積作成は404"""
        response = client.post("/projects/1/issues/99999/estimates", data={
            "name": "設計",
            "hours": "16.0"
        })
        assert response.status_code == 404

    def test_create_with_zero_hours_returns_400(self, client, issue_id):
        """工数0は400エラー"""
        response = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "設計",
            "hours": "0"
        })
        assert response.status_code == 400

    def test_create_with_negative_hours_returns_400(self, client, issue_id):
        """負の工数は400エラー"""
        response = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "設計",
            "hours": "-1"
        })
        assert response.status_code == 400


class TestEstimateUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client, issue_id):
        """更新が成功する"""
        # まず見積を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "更新前",
            "hours": "8.0"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="estimate-(\d+)"', create_resp.text)
        assert match
        estimate_id = match.group(1)

        # 更新
        response = client.put(f"/projects/1/issues/{issue_id}/estimates/{estimate_id}", data={
            "name": "更新後",
            "hours": "16.0"
        })
        assert response.status_code == 200
        assert "更新後" in response.text
        assert "16.00" in response.text

    def test_update_nonexistent_returns_404(self, client, issue_id):
        """存在しない見積の更新は404"""
        response = client.put(f"/projects/1/issues/{issue_id}/estimates/99999", data={
            "name": "存在しない",
            "hours": "8.0"
        })
        assert response.status_code == 404

    def test_update_with_zero_hours_returns_400(self, client, issue_id):
        """更新時に工数0は400エラー"""
        # まず見積を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "テスト",
            "hours": "8.0"
        })
        match = re.search(r'id="estimate-(\d+)"', create_resp.text)
        estimate_id = match.group(1)

        # 工数0で更新
        response = client.put(f"/projects/1/issues/{issue_id}/estimates/{estimate_id}", data={
            "name": "テスト",
            "hours": "0"
        })
        assert response.status_code == 400


class TestEstimateDelete:
    """削除テスト"""

    def test_delete_success(self, client, issue_id):
        """削除が成功する"""
        # まず見積を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "削除対象",
            "hours": "8.0"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="estimate-(\d+)"', create_resp.text)
        assert match
        estimate_id = match.group(1)

        # 削除
        response = client.delete(f"/projects/1/issues/{issue_id}/estimates/{estimate_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client, issue_id):
        """存在しない見積の削除は404"""
        response = client.delete(f"/projects/1/issues/{issue_id}/estimates/99999")
        assert response.status_code == 404


class TestEstimateRow:
    """行取得テスト"""

    def test_row_returns_200(self, client, issue_id):
        """行取得が成功する"""
        # まず見積を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "行テスト",
            "hours": "8.0"
        })
        match = re.search(r'id="estimate-(\d+)"', create_resp.text)
        estimate_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/estimates/{estimate_id}/row")
        assert response.status_code == 200
        assert "行テスト" in response.text

    def test_row_nonexistent_returns_404(self, client, issue_id):
        """存在しない見積の行取得は404"""
        response = client.get(f"/projects/1/issues/{issue_id}/estimates/99999/row")
        assert response.status_code == 404


class TestEstimateEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client, issue_id):
        """編集フォーム取得が成功する"""
        # まず見積を作成
        create_resp = client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "編集テスト",
            "hours": "8.0"
        })
        match = re.search(r'id="estimate-(\d+)"', create_resp.text)
        estimate_id = match.group(1)

        response = client.get(f"/projects/1/issues/{issue_id}/estimates/{estimate_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client, issue_id):
        """存在しない見積の編集フォーム取得は404"""
        response = client.get(f"/projects/1/issues/{issue_id}/estimates/99999/edit")
        assert response.status_code == 404


class TestIssueListEstimateColumn:
    """案件一覧の見積列テスト"""

    def test_issue_list_shows_estimate_total(self, client, issue_id):
        """案件一覧に見積合計が表示される"""
        # 見積を追加
        client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "設計",
            "hours": "16.0"
        })
        client.post(f"/projects/1/issues/{issue_id}/estimates", data={
            "name": "実装",
            "hours": "24.0"
        })

        # 案件一覧を取得
        response = client.get("/projects/1/issues/list")
        assert response.status_code == 200
        assert "40.0h" in response.text  # 16 + 24 = 40

    def test_issue_list_shows_estimate_link(self, client, issue_id):
        """案件一覧に見積リンクが表示される"""
        response = client.get("/projects/1/issues/list")
        assert response.status_code == 200
        assert f"/projects/1/issues/{issue_id}/estimates" in response.text
        assert ">見積</a>" in response.text
