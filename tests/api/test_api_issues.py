"""案件API テスト"""
import pytest


@pytest.fixture
def project(client, clean_db):
    """テスト用プロジェクト"""
    response = client.post("/api/v1/projects", json={
        "cd": "PROJ",
        "name": "Test Project",
        "description": ""
    })
    return response.json()


def test_list_issues(client, project):
    """案件一覧取得"""
    response = client.get("/api/v1/issues")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_issues_by_project(client, project):
    """プロジェクトでフィルタ"""
    # 案件作成
    client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "ISS1",
        "name": "Issue 1"
    })

    response = client.get(f"/api/v1/issues?project_id={project['id']}")
    assert response.status_code == 200
    data = response.json()
    assert all(i["project_id"] == project["id"] for i in data)


def test_create_issue(client, project):
    """案件作成"""
    response = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "NEW",
        "name": "New Issue",
        "status": "open",
        "description": "Desc"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["cd"] == "NEW"
    assert data["project_id"] == project["id"]


def test_create_issue_project_not_found(client, clean_db):
    """存在しないプロジェクトで作成"""
    response = client.post("/api/v1/issues", json={
        "project_id": 99999,
        "cd": "X",
        "name": "Y"
    })
    assert response.status_code == 404


def test_get_issue(client, project):
    """案件詳細取得"""
    # 作成
    create_res = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "GET",
        "name": "Get Test"
    })
    issue_id = create_res.json()["id"]

    # 取得
    response = client.get(f"/api/v1/issues/{issue_id}")
    assert response.status_code == 200
    assert response.json()["cd"] == "GET"


def test_get_issue_not_found(client, clean_db):
    """存在しない案件"""
    response = client.get("/api/v1/issues/99999")
    assert response.status_code == 404


def test_update_issue(client, project):
    """案件更新"""
    # 作成
    create_res = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "UPD",
        "name": "Update Test"
    })
    issue_id = create_res.json()["id"]

    # 更新
    response = client.put(f"/api/v1/issues/{issue_id}", json={
        "cd": "UPD2",
        "name": "Updated",
        "status": "closed",
        "description": "New Desc"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_delete_issue(client, project):
    """案件削除"""
    # 作成
    create_res = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "DEL",
        "name": "Delete Test"
    })
    issue_id = create_res.json()["id"]

    # 削除
    response = client.delete(f"/api/v1/issues/{issue_id}")
    assert response.status_code == 204

    # 確認
    response = client.get(f"/api/v1/issues/{issue_id}")
    assert response.status_code == 404
