"""ユーザーAPI テスト"""
import pytest


def test_list_users(client, clean_db):
    """ユーザー一覧取得"""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # clean_dbには2人のユーザーがいる


def test_create_user(client, clean_db):
    """ユーザー作成"""
    response = client.post("/api/v1/users", json={
        "cd": "NEW",
        "name": "New User",
        "email": "new@test.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["cd"] == "NEW"
    assert data["name"] == "New User"


def test_get_user(client, clean_db):
    """ユーザー詳細取得"""
    # 作成
    create_res = client.post("/api/v1/users", json={
        "cd": "GET",
        "name": "Get Test",
        "email": "get@test.com"
    })
    user_id = create_res.json()["id"]

    # 取得
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["cd"] == "GET"


def test_get_user_not_found(client, clean_db):
    """存在しないユーザー"""
    response = client.get("/api/v1/users/99999")
    assert response.status_code == 404


def test_update_user(client, clean_db):
    """ユーザー更新"""
    # 作成
    create_res = client.post("/api/v1/users", json={
        "cd": "UPD",
        "name": "Update Test",
        "email": "upd@test.com"
    })
    user_id = create_res.json()["id"]

    # 更新
    response = client.put(f"/api/v1/users/{user_id}", json={
        "cd": "UPD2",
        "name": "Updated",
        "email": "new@test.com"
    })
    assert response.status_code == 200
    assert response.json()["cd"] == "UPD2"


def test_delete_user(client, clean_db):
    """ユーザー削除"""
    # 作成
    create_res = client.post("/api/v1/users", json={
        "cd": "DEL",
        "name": "Delete Test",
        "email": "del@test.com"
    })
    user_id = create_res.json()["id"]

    # 削除
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    # 確認
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404


def test_list_users_active_only(client, clean_db):
    """有効ユーザーのみ"""
    response = client.get("/api/v1/users?active_only=true")
    assert response.status_code == 200
