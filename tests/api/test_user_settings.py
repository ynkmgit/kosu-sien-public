"""ユーザー設定APIテスト"""
import json
import pytest
from database import get_db


@pytest.fixture
def user_id(clean_db):
    """テスト用ユーザーIDを取得"""
    with get_db() as conn:
        row = conn.execute("SELECT id FROM user WHERE cd = 'U001'").fetchone()
        return row['id']


def test_get_setting_empty(client, user_id):
    """設定が存在しない場合、nullを返す"""
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.status_code == 200
    assert response.json() == {"value": None}


def test_save_and_get_setting(client, user_id):
    """設定を保存して取得できる"""
    # 保存
    response = client.post(
        f"/api/user-settings/{user_id}/test_key",
        json={"value": "test_value"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # 取得
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.status_code == 200
    assert response.json() == {"value": "test_value"}


def test_update_setting(client, user_id):
    """設定を上書きできる"""
    # 初回保存
    client.post(f"/api/user-settings/{user_id}/test_key", json={"value": "value1"})

    # 上書き
    client.post(f"/api/user-settings/{user_id}/test_key", json={"value": "value2"})

    # 確認
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.json() == {"value": "value2"}


def test_delete_setting(client, user_id):
    """設定を削除できる"""
    # 保存
    client.post(f"/api/user-settings/{user_id}/test_key", json={"value": "test_value"})

    # 削除
    response = client.delete(f"/api/user-settings/{user_id}/test_key")
    assert response.status_code == 200

    # 確認
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.json() == {"value": None}


def test_save_setting_user_not_found(client):
    """存在しないユーザーの場合、404を返す"""
    response = client.post(
        "/api/user-settings/99999/test_key",
        json={"value": "test_value"}
    )
    assert response.status_code == 404


def test_save_json_setting(client, user_id):
    """JSON文字列を保存できる"""
    options = {"hideZeroProgress": True, "theme": "dark"}

    response = client.post(
        f"/api/user-settings/{user_id}/work_report_options",
        json={"value": json.dumps(options)}
    )
    assert response.status_code == 200

    response = client.get(f"/api/user-settings/{user_id}/work_report_options")
    saved = json.loads(response.json()["value"])
    assert saved["hideZeroProgress"] is True
    assert saved["theme"] == "dark"


def test_multiple_users_settings(client, clean_db):
    """ユーザーごとに設定が分離される"""
    with get_db() as conn:
        users = conn.execute("SELECT id FROM user ORDER BY cd").fetchall()
        user1_id = users[0]['id']
        user2_id = users[1]['id']

    # ユーザー1の設定
    client.post(f"/api/user-settings/{user1_id}/template", json={"value": "user1_template"})

    # ユーザー2の設定
    client.post(f"/api/user-settings/{user2_id}/template", json={"value": "user2_template"})

    # 確認
    res1 = client.get(f"/api/user-settings/{user1_id}/template")
    res2 = client.get(f"/api/user-settings/{user2_id}/template")

    assert res1.json()["value"] == "user1_template"
    assert res2.json()["value"] == "user2_template"


def test_user_cascade_delete(client, clean_db):
    """ユーザー削除時に設定も削除される"""
    with get_db() as conn:
        # テスト用ユーザー作成
        conn.execute("INSERT INTO user (cd, name, email) VALUES ('DEL_TEST', 'Delete Test', 'del@test.com')")
        user_id = conn.execute("SELECT id FROM user WHERE cd = 'DEL_TEST'").fetchone()['id']

    # 設定保存
    client.post(f"/api/user-settings/{user_id}/test_key", json={"value": "test"})

    # 設定が存在することを確認
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.json()["value"] == "test"

    # ユーザー削除
    with get_db() as conn:
        conn.execute("DELETE FROM user WHERE id = ?", (user_id,))

    # 設定も削除されていることを確認（404ではなくnull）
    # ユーザーが存在しないのでGETはnullを返す（エラーではない）
    response = client.get(f"/api/user-settings/{user_id}/test_key")
    assert response.json()["value"] is None
