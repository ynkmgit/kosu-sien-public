"""プロジェクトAPIテスト"""
import re
import uuid


class TestProjectList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client):
        """一覧取得が成功する"""
        response = client.get("/projects/list")
        assert response.status_code == 200

    def test_list_contains_projects(self, client):
        """一覧にプロジェクトが含まれる"""
        response = client.get("/projects/list")
        assert "PJ001" in response.text
        assert "PJ002" in response.text

    def test_list_with_sort_asc(self, client):
        """昇順ソートでPJ001が先頭"""
        response = client.get("/projects/list?sort=cd&order=asc")
        assert response.status_code == 200
        assert response.text.index("PJ001") < response.text.index("PJ002")

    def test_list_with_sort_desc(self, client):
        """降順ソートでPJ001が末尾"""
        response = client.get("/projects/list?sort=cd&order=desc")
        assert response.status_code == 200
        assert response.text.index("PJ002") < response.text.index("PJ001")

    def test_list_with_search(self, client):
        """検索で絞り込みできる"""
        response = client.get("/projects/list?q=PJ001")
        assert response.status_code == 200
        assert "PJ001" in response.text
        assert "PJ002" not in response.text


class TestProjectRow:
    """行取得テスト"""

    def test_row_returns_200(self, client):
        """行取得が成功する"""
        response = client.get("/projects/1/row")
        assert response.status_code == 200
        assert "PJ001" in response.text

    def test_row_nonexistent_returns_404(self, client):
        """存在しないプロジェクトの行取得は404"""
        response = client.get("/projects/99999/row")
        assert response.status_code == 404


class TestProjectEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client):
        """編集フォーム取得が成功する"""
        response = client.get("/projects/1/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client):
        """存在しないプロジェクトの編集フォーム取得は404"""
        response = client.get("/projects/99999/edit")
        assert response.status_code == 404


class TestProjectCreate:
    """作成テスト"""

    def test_create_returns_200(self, client):
        """作成が成功する"""
        unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
        response = client.post("/projects", data={
            "cd": unique_cd,
            "name": "テストプロジェクト",
            "description": "テスト用"
        })
        assert response.status_code == 200
        assert unique_cd in response.text
        assert "テストプロジェクト" in response.text

    def test_create_with_empty_description(self, client):
        """説明なしでも作成できる"""
        unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
        response = client.post("/projects", data={
            "cd": unique_cd,
            "name": "説明なしPJ",
            "description": ""
        })
        assert response.status_code == 200
        assert unique_cd in response.text

    def test_create_generates_default_statuses(self, client):
        """作成時にデフォルトステータスが生成される"""
        unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
        response = client.post("/projects", data={
            "cd": unique_cd,
            "name": "ステータス確認PJ",
            "description": ""
        })
        assert response.status_code == 200

        # 作成されたプロジェクトのIDを取得
        match = re.search(r'id="project-(\d+)"', response.text)
        assert match
        project_id = match.group(1)

        # ステータス一覧を確認
        status_response = client.get(f"/projects/{project_id}/statuses/list")
        assert status_response.status_code == 200
        assert "open" in status_response.text
        assert "closed" in status_response.text


class TestProjectUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client):
        """更新が成功する"""
        # テスト用プロジェクト作成
        unique_cd = f"PJ-{uuid.uuid4().hex[:6]}"
        create_resp = client.post("/projects", data={
            "cd": unique_cd,
            "name": "更新前",
            "description": ""
        })
        match = re.search(r'id="project-(\d+)"', create_resp.text)
        project_id = match.group(1)

        # 更新
        response = client.put(f"/projects/{project_id}", data={
            "cd": unique_cd,
            "name": "更新後",
            "description": "更新しました"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client):
        """存在しないプロジェクトの更新は404"""
        response = client.put("/projects/99999", data={
            "cd": "PJXXX",
            "name": "存在しない",
            "description": ""
        })
        assert response.status_code == 404


class TestProjectDelete:
    """削除テスト"""

    def test_delete_success(self, client):
        """削除が成功する"""
        # テスト用プロジェクト作成
        unique_cd = f"PJDEL-{uuid.uuid4().hex[:6]}"
        create_resp = client.post("/projects", data={
            "cd": unique_cd,
            "name": "削除対象",
            "description": ""
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="project-(\d+)"', create_resp.text)
        assert match, "プロジェクトIDが見つからない"
        project_id = match.group(1)

        # 削除実行
        response = client.delete(f"/projects/{project_id}")
        assert response.status_code == 200
        assert response.text == ""

        # 削除確認
        list_resp = client.get(f"/projects/list?q={unique_cd}")
        assert unique_cd not in list_resp.text

    def test_delete_nonexistent_returns_404(self, client):
        """存在しないプロジェクトの削除は404"""
        response = client.delete("/projects/99999")
        assert response.status_code == 404
