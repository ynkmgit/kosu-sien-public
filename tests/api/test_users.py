"""ユーザーAPIテスト"""
import pytest


class TestUserList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client):
        """一覧取得が成功する"""
        response = client.get("/users/list")
        assert response.status_code == 200

    def test_list_contains_users(self, client):
        """一覧にユーザーが含まれる"""
        response = client.get("/users/list")
        assert "U001" in response.text
        assert "U002" in response.text

    def test_list_with_sort_asc(self, client):
        """昇順ソートでU001が先頭"""
        response = client.get("/users/list?sort=cd&order=asc")
        assert response.status_code == 200
        # U001がU002より前に出現
        assert response.text.index("U001") < response.text.index("U002")

    def test_list_with_sort_desc(self, client):
        """降順ソートでU001が末尾"""
        response = client.get("/users/list?sort=cd&order=desc")
        assert response.status_code == 200
        # U002がU001より前に出現
        assert response.text.index("U002") < response.text.index("U001")

    def test_list_with_search(self, client):
        """検索で絞り込みできる"""
        response = client.get("/users/list?q=U001")
        assert response.status_code == 200
        assert "U001" in response.text
        assert "U002" not in response.text


class TestUserRow:
    """行取得テスト"""

    def test_row_returns_200(self, client):
        """行取得が成功する"""
        response = client.get("/users/1/row")
        assert response.status_code == 200
        assert "U001" in response.text

    def test_row_nonexistent_returns_404(self, client):
        """存在しないユーザーの行取得は404"""
        response = client.get("/users/99999/row")
        assert response.status_code == 404


class TestUserEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client):
        """編集フォーム取得が成功する"""
        response = client.get("/users/1/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client):
        """存在しないユーザーの編集フォーム取得は404"""
        response = client.get("/users/99999/edit")
        assert response.status_code == 404


class TestUserCreate:
    """作成テスト"""

    def test_create_returns_200(self, client):
        """作成が成功する"""
        response = client.post("/users", data={
            "cd": "U999",
            "name": "テスト太郎",
            "email": "test999@example.com"
        })
        assert response.status_code == 200
        assert "U999" in response.text
        assert "テスト太郎" in response.text


class TestUserUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client):
        """更新が成功する"""
        response = client.put("/users/1", data={
            "cd": "U001",
            "name": "更新太郎",
            "email": "updated@example.com"
        })
        assert response.status_code == 200
        assert "更新太郎" in response.text

    def test_update_nonexistent_returns_404(self, client):
        """存在しないユーザーの更新は404"""
        response = client.put("/users/99999", data={
            "cd": "U999",
            "name": "存在しない",
            "email": "none@example.com"
        })
        assert response.status_code == 404


class TestUserDelete:
    """削除テスト"""

    def test_delete_success(self, client):
        """削除が成功する"""
        # テスト用ユーザー作成
        create_resp = client.post("/users", data={
            "cd": "UDEL",
            "name": "削除対象",
            "email": "delete@example.com"
        })
        assert create_resp.status_code == 200

        # 作成されたユーザーのIDを取得（一覧から検索）
        list_resp = client.get("/users/list?q=UDEL")
        assert "UDEL" in list_resp.text

        # IDを抽出（id="user-{id}" から）
        import re
        match = re.search(r'id="user-(\d+)"', list_resp.text)
        assert match, "ユーザーIDが見つからない"
        user_id = match.group(1)

        # 削除実行
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.text == ""

        # 削除確認
        list_resp = client.get("/users/list?q=UDEL")
        assert "UDEL" not in list_resp.text

    def test_delete_nonexistent_returns_404(self, client):
        """存在しないユーザーの削除は404"""
        response = client.delete("/users/99999")
        assert response.status_code == 404
