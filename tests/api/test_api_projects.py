"""プロジェクトAPI テスト"""
import pytest


def test_list_projects(client, clean_db):
    """プロジェクト一覧取得"""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_project(client, clean_db):
    """プロジェクト作成"""
    response = client.post("/api/v1/projects", json={
        "cd": "NEW",
        "name": "New Project",
        "description": "Description"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["cd"] == "NEW"
    assert data["name"] == "New Project"
    assert "id" in data


def test_get_project(client, clean_db):
    """プロジェクト詳細取得"""
    # 作成
    create_res = client.post("/api/v1/projects", json={
        "cd": "GET",
        "name": "Get Test",
        "description": ""
    })
    project_id = create_res.json()["id"]

    # 取得
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["cd"] == "GET"


def test_get_project_not_found(client, clean_db):
    """存在しないプロジェクト"""
    response = client.get("/api/v1/projects/99999")
    assert response.status_code == 404


def test_update_project(client, clean_db):
    """プロジェクト更新"""
    # 作成
    create_res = client.post("/api/v1/projects", json={
        "cd": "UPD",
        "name": "Update Test",
        "description": ""
    })
    project_id = create_res.json()["id"]

    # 更新
    response = client.put(f"/api/v1/projects/{project_id}", json={
        "cd": "UPD2",
        "name": "Updated",
        "description": "New Desc"
    })
    assert response.status_code == 200
    assert response.json()["cd"] == "UPD2"


def test_update_project_not_found(client, clean_db):
    """存在しないプロジェクト更新"""
    response = client.put("/api/v1/projects/99999", json={
        "cd": "X",
        "name": "Y",
        "description": ""
    })
    assert response.status_code == 404


def test_delete_project(client, clean_db):
    """プロジェクト削除"""
    # 作成
    create_res = client.post("/api/v1/projects", json={
        "cd": "DEL",
        "name": "Delete Test",
        "description": ""
    })
    project_id = create_res.json()["id"]

    # 削除
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    # 確認
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 404


def test_delete_project_not_found(client, clean_db):
    """存在しないプロジェクト削除"""
    response = client.delete("/api/v1/projects/99999")
    assert response.status_code == 404


def test_get_project_summary(client, clean_db):
    """プロジェクトサマリー取得"""
    # 作成
    create_res = client.post("/api/v1/projects", json={
        "cd": "SUM",
        "name": "Summary Test",
        "description": ""
    })
    project_id = create_res.json()["id"]

    # サマリー取得
    response = client.get(f"/api/v1/projects/{project_id}/summary")
    assert response.status_code == 200
    data = response.json()
    assert "issue_count" in data
    assert "task_count" in data
    assert "estimate_total" in data


def test_list_projects_with_search(client, clean_db):
    """検索付き一覧"""
    client.post("/api/v1/projects", json={
        "cd": "SRCH",
        "name": "Searchable",
        "description": "unique_keyword"
    })

    response = client.get("/api/v1/projects?q=unique_keyword")
    assert response.status_code == 200
    results = response.json()
    assert any(p["cd"] == "SRCH" for p in results)
