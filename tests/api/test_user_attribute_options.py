"""ユーザー属性選択肢APIテスト"""
import re
import pytest


@pytest.fixture
def attr_type(client, request):
    """テスト用の属性タイプを作成（テストごとにユニーク）"""
    import uuid
    unique_code = f"type_{uuid.uuid4().hex[:8]}"
    response = client.post("/user-attribute-types", data={
        "code": unique_code,
        "name": "テストタイプ",
        "sort_order": "0"
    })
    match = re.search(r'id="attr-type-(\d+)"', response.text)
    return int(match.group(1))


class TestAttributeOptionList:
    """一覧取得テスト"""

    def test_list_returns_200(self, client, attr_type):
        """一覧取得が成功する"""
        response = client.get(f"/user-attribute-types/{attr_type}/options/list")
        assert response.status_code == 200

    def test_list_with_invalid_type_returns_404(self, client):
        """存在しない属性タイプの選択肢一覧は404"""
        response = client.get("/user-attribute-types/99999/options/list")
        assert response.status_code == 404


class TestAttributeOptionCreate:
    """作成テスト"""

    def test_create_returns_200(self, client, attr_type):
        """作成が成功する"""
        response = client.post(f"/user-attribute-types/{attr_type}/options", data={
            "code": "employee",
            "name": "社員",
            "sort_order": "0"
        })
        assert response.status_code == 200
        assert "employee" in response.text
        assert "社員" in response.text

    def test_create_with_invalid_type_returns_404(self, client):
        """存在しない属性タイプへの選択肢作成は404"""
        response = client.post("/user-attribute-types/99999/options", data={
            "code": "test",
            "name": "テスト",
            "sort_order": "0"
        })
        assert response.status_code == 404


class TestAttributeOptionUpdate:
    """更新テスト"""

    def test_update_returns_200(self, client, attr_type):
        """更新が成功する"""
        # まず選択肢を作成
        create_resp = client.post(f"/user-attribute-types/{attr_type}/options", data={
            "code": "upd_opt",
            "name": "更新前",
            "sort_order": "10"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="attr-option-(\d+)"', create_resp.text)
        assert match
        option_id = match.group(1)

        # 更新
        response = client.put(f"/user-attribute-types/{attr_type}/options/{option_id}", data={
            "code": "upd_opt",
            "name": "更新後",
            "sort_order": "11"
        })
        assert response.status_code == 200
        assert "更新後" in response.text

    def test_update_nonexistent_returns_404(self, client, attr_type):
        """存在しない選択肢の更新は404"""
        response = client.put(f"/user-attribute-types/{attr_type}/options/99999", data={
            "code": "none",
            "name": "存在しない",
            "sort_order": "0"
        })
        assert response.status_code == 404


class TestAttributeOptionDelete:
    """削除テスト"""

    def test_delete_success(self, client, attr_type):
        """削除が成功する"""
        # まず選択肢を作成
        create_resp = client.post(f"/user-attribute-types/{attr_type}/options", data={
            "code": "del_opt",
            "name": "削除対象",
            "sort_order": "99"
        })
        assert create_resp.status_code == 200

        # IDを抽出
        match = re.search(r'id="attr-option-(\d+)"', create_resp.text)
        assert match
        option_id = match.group(1)

        # 削除
        response = client.delete(f"/user-attribute-types/{attr_type}/options/{option_id}")
        assert response.status_code == 200
        assert response.text == ""

    def test_delete_nonexistent_returns_404(self, client, attr_type):
        """存在しない選択肢の削除は404"""
        response = client.delete(f"/user-attribute-types/{attr_type}/options/99999")
        assert response.status_code == 404


class TestAttributeOptionRow:
    """行取得テスト"""

    def test_row_returns_200(self, client, attr_type):
        """行取得が成功する"""
        # まず選択肢を作成
        create_resp = client.post(f"/user-attribute-types/{attr_type}/options", data={
            "code": "row_opt",
            "name": "行テスト",
            "sort_order": "50"
        })
        match = re.search(r'id="attr-option-(\d+)"', create_resp.text)
        option_id = match.group(1)

        response = client.get(f"/user-attribute-types/{attr_type}/options/{option_id}/row")
        assert response.status_code == 200
        assert "row_opt" in response.text

    def test_row_nonexistent_returns_404(self, client, attr_type):
        """存在しない選択肢の行取得は404"""
        response = client.get(f"/user-attribute-types/{attr_type}/options/99999/row")
        assert response.status_code == 404


class TestAttributeOptionEdit:
    """編集フォーム取得テスト"""

    def test_edit_returns_200(self, client, attr_type):
        """編集フォーム取得が成功する"""
        # まず選択肢を作成
        create_resp = client.post(f"/user-attribute-types/{attr_type}/options", data={
            "code": "edit_opt",
            "name": "編集テスト",
            "sort_order": "60"
        })
        match = re.search(r'id="attr-option-(\d+)"', create_resp.text)
        option_id = match.group(1)

        response = client.get(f"/user-attribute-types/{attr_type}/options/{option_id}/edit")
        assert response.status_code == 200
        assert 'class="edit-input"' in response.text

    def test_edit_nonexistent_returns_404(self, client, attr_type):
        """存在しない選択肢の編集フォーム取得は404"""
        response = client.get(f"/user-attribute-types/{attr_type}/options/99999/edit")
        assert response.status_code == 404
