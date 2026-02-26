"""報告テンプレートAPIのテスト"""


def test_list_templates(client, clean_db):
    """空の一覧取得"""
    resp = client.get("/api/report-templates")
    assert resp.status_code == 200
    assert resp.json()["templates"] == []


def test_create_template(client, clean_db):
    """テンプレート作成"""
    resp = client.post("/api/report-templates", json={
        "name": "通常報告",
        "body": "業務終了します。",
        "options": {"hideZeroProgress": False}
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "通常報告"
    assert data["body"] == "業務終了します。"
    assert data["id"] is not None


def test_create_duplicate_name(client, clean_db):
    """重複名で409"""
    client.post("/api/report-templates", json={"name": "重複", "body": "本文1"})
    resp = client.post("/api/report-templates", json={"name": "重複", "body": "本文2"})
    assert resp.status_code == 409


def test_update_template(client, clean_db):
    """テンプレート更新"""
    create = client.post("/api/report-templates", json={"name": "更新前", "body": "旧"})
    tid = create.json()["id"]
    resp = client.put(f"/api/report-templates/{tid}", json={
        "name": "更新後", "body": "新", "options": {"hideZeroProgress": True}
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "更新後"


def test_update_not_found(client, clean_db):
    """存在しないIDで404"""
    resp = client.put("/api/report-templates/99999", json={"name": "x", "body": "x"})
    assert resp.status_code == 404


def test_delete_template(client, clean_db):
    """テンプレート削除"""
    r1 = client.post("/api/report-templates", json={"name": "削除用", "body": "1"})
    client.post("/api/report-templates", json={"name": "残す用", "body": "2"})
    resp = client.delete(f"/api/report-templates/{r1.json()['id']}")
    assert resp.status_code == 200


def test_delete_last_template_fails(client, clean_db):
    """最後の1件は削除不可"""
    r1 = client.post("/api/report-templates", json={"name": "唯一", "body": "1"})
    resp = client.delete(f"/api/report-templates/{r1.json()['id']}")
    assert resp.status_code == 400


def test_list_after_create(client, clean_db):
    """作成後に一覧に反映"""
    client.post("/api/report-templates", json={"name": "A", "body": "a"})
    client.post("/api/report-templates", json={"name": "B", "body": "b"})
    resp = client.get("/api/report-templates")
    names = [t["name"] for t in resp.json()["templates"]]
    assert "A" in names
    assert "B" in names
