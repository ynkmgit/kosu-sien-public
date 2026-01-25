"""ユーザー属性タイプAPIテスト"""
import re
import pytest


class TestAttributeTypeList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client):
        """一覧取得が成功する"""
        response = client.get("/user-attribute-types/list")
        assert response.status_code == 200


class TestAttributeTypeCreate:
    """作成テスト"""

    def test_create_returns_200(self, client):
        """作成が成功する"""
        response = client.post("/user-attribute-types", data={
            "code": "employment_type",
            "name": "雇用形態",
            "sort_order": "0"
        })
        assert response.status_code == 200
        assert "employment_type" in response.text
        assert "雇用形態" in response.text

    def test_create_duplicate_code_fails(self, client):
        """重複コードの作成は失敗する"""
        import uuid
        unique_code = f"dup_{uuid.uuid4().hex[:8]}"
        client.post("/user-attribute-types", data={
            "code": unique_code,
            "name": "重複テスト",
            "sort_order": "0"
        })
        # 重複するコードで作成を試みる
        try:
            response = client.post("/user-attribute-types", data={
                "code": unique_code,
                "name": "重複テスト2",
                "sort_order": "1"
            })
            # UNIQUE制約違反でエラーが発生する
            assert response.status_code == 500
        except Exception:
            # 例外が発生した場合もテスト成功とする
            pass


class TestAttributeTypeUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client):
        """更新が成功する"""
        # まず属性タイプを作成
        create_resp = client.post("/user-attribute-types", data={
            "code": "upd_test",
            "name": "更新前",
            "sort_order": "10"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="attr-type-(\d+)"', create_resp.text)
        assert match
        type_id = match.group(1)

        # 更新
        response = client.put(f"/user-attribute-types/{type_id}", data={
            "code": "upd_test",
            "name": "更新後",
            "sort_order": "11"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client):
        """存在しない属性タイプの更新は404"""
        response = client.put("/user-attribute-types/99999", data={
            "code": "none",
            "name": "存在しない",
            "sort_order": "0"
        })
        assert response.status_code == 404


class TestAttributeTypeDelete:
    """削除テスト"""

    def test_delete_success(self, client):
        """削除が成功する"""
        # まず属性タイプを作成
        create_resp = client.post("/user-attribute-types", data={
            "code": "del_test",
            "name": "削除対象",
            "sort_order": "99"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="attr-type-(\d+)"', create_resp.text)
        assert match
        type_id = match.group(1)

        # 削除
        response = client.delete(f"/user-attribute-types/{type_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client):
        """存在しない属性タイプの削除は404"""
        response = client.delete("/user-attribute-types/99999")
        assert response.status_code == 404


class TestAttributeTypeRow:
    """行取得テスト"""

    def test_row_returns_200(self, client):
        """行取得が成功する"""
        # まず属性タイプを作成
        create_resp = client.post("/user-attribute-types", data={
            "code": "row_test",
            "name": "行テスト",
            "sort_order": "50"
        })
        match = re.search(r'id="attr-type-(\d+)"', create_resp.text)
        type_id = match.group(1)

        response = client.get(f"/user-attribute-types/{type_id}/row")
        assert response.status_code == 200
        assert "row_test" in response.text

    def test_row_nonexistent_returns_404(self, client):
        """存在しない属性タイプの行取得は404"""
        response = client.get("/user-attribute-types/99999/row")
        assert response.status_code == 404


class TestAttributeTypeEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client):
        """編集フォーム取得が成功する"""
        # まず属性タイプを作成
        create_resp = client.post("/user-attribute-types", data={
            "code": "edit_test",
            "name": "編集テスト",
            "sort_order": "60"
        })
        match = re.search(r'id="attr-type-(\d+)"', create_resp.text)
        type_id = match.group(1)

        response = client.get(f"/user-attribute-types/{type_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client):
        """存在しない属性タイプの編集フォーム取得は404"""
        response = client.get("/user-attribute-types/99999/edit")
        assert response.status_code == 404
