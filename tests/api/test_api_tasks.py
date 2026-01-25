"""作業API テスト"""
import pytest


@pytest.fixture
def issue(client, clean_db):
    """テスト用案件"""
    project = client.post("/api/v1/projects", json={
        "cd": "PROJ",
        "name": "Test Project",
        "description": ""
    }).json()

    issue = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "ISS",
        "name": "Test Issue"
    }).json()

    return issue


def test_list_tasks(client, issue):
    """作業一覧取得"""
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_tasks_by_issue(client, issue):
    """案件でフィルタ"""
    # 作業作成
    client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "TSK1",
        "name": "Task 1"
    })

    response = client.get(f"/api/v1/tasks?issue_id={issue['id']}")
    assert response.status_code == 200
    data = response.json()
    assert all(t["issue_id"] == issue["id"] for t in data)


def test_create_task(client, issue):
    """作業作成"""
    response = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "NEW",
        "name": "New Task",
        "description": "Desc"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["cd"] == "NEW"
    assert data["issue_id"] == issue["id"]


def test_create_task_issue_not_found(client, clean_db):
    """存在しない案件で作成"""
    response = client.post("/api/v1/tasks", json={
        "issue_id": 99999,
        "cd": "X",
        "name": "Y"
    })
    assert response.status_code == 404


def test_get_task(client, issue):
    """作業詳細取得"""
    # 作成
    create_res = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "GET",
        "name": "Get Test"
    })
    task_id = create_res.json()["id"]

    # 取得
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["cd"] == "GET"


def test_get_task_not_found(client, clean_db):
    """存在しない作業"""
    response = client.get("/api/v1/tasks/99999")
    assert response.status_code == 404


def test_update_task(client, issue):
    """作業更新"""
    # 作成
    create_res = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "UPD",
        "name": "Update Test"
    })
    task_id = create_res.json()["id"]

    # 更新
    response = client.put(f"/api/v1/tasks/{task_id}", json={
        "cd": "UPD2",
        "name": "Updated",
        "description": "New Desc"
    })
    assert response.status_code == 200
    assert response.json()["cd"] == "UPD2"


def test_update_task_progress(client, issue):
    """進捗率更新"""
    # 作成
    create_res = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "PRG",
        "name": "Progress Test"
    })
    task_id = create_res.json()["id"]

    # 進捗更新
    response = client.put(f"/api/v1/tasks/{task_id}/progress", json={
        "progress_rate": 50
    })
    assert response.status_code == 204

    # 確認
    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert task["progress_rate"] == 50


def test_delete_task(client, issue):
    """作業削除"""
    # 作成
    create_res = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "DEL",
        "name": "Delete Test"
    })
    task_id = create_res.json()["id"]

    # 削除
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # 確認
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 404
