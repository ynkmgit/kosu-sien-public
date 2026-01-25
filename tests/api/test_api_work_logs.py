"""実績API テスト"""
import pytest
from datetime import date
from database import get_db


@pytest.fixture
def assigned_task(client, clean_db):
    """担当割当済みの作業とユーザー"""
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

    task = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "TSK",
        "name": "Test Task"
    }).json()

    user = client.post("/api/v1/users", json={
        "cd": "WRK",
        "name": "Worker",
        "email": "work@test.com"
    }).json()

    # 担当割当
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task_assignee (task_id, user_id) VALUES (?, ?)",
            (task["id"], user["id"])
        )

    return {"task": task, "user": user, "project": project, "issue": issue}


def test_list_work_logs(client, assigned_task):
    """実績一覧取得"""
    response = client.get("/api/v1/work-logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_work_log(client, assigned_task):
    """実績作成"""
    response = client.post("/api/v1/work-logs", json={
        "task_id": assigned_task["task"]["id"],
        "user_id": assigned_task["user"]["id"],
        "work_date": date.today().isoformat(),
        "hours": 2.5
    })
    assert response.status_code == 201
    data = response.json()
    assert data["hours"] == 2.5


def test_create_work_log_update(client, assigned_task):
    """実績更新（upsert）"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]
    work_date = date.today().isoformat()

    # 作成
    client.post("/api/v1/work-logs", json={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": work_date,
        "hours": 2.0
    })

    # 更新
    response = client.post("/api/v1/work-logs", json={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": work_date,
        "hours": 3.0
    })
    assert response.status_code == 201
    assert response.json()["hours"] == 3.0


def test_create_work_log_delete_on_zero(client, assigned_task):
    """0時間で削除"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]
    work_date = date.today().isoformat()

    # 作成
    client.post("/api/v1/work-logs", json={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": work_date,
        "hours": 2.0
    })

    # 0で削除
    response = client.post("/api/v1/work-logs", json={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": work_date,
        "hours": 0
    })
    assert response.status_code == 201
    assert response.json() is None


def test_create_work_log_not_assigned(client, clean_db):
    """担当でない場合エラー"""
    project = client.post("/api/v1/projects", json={
        "cd": "P",
        "name": "Project",
        "description": ""
    }).json()

    issue = client.post("/api/v1/issues", json={
        "project_id": project["id"],
        "cd": "I",
        "name": "Issue"
    }).json()

    task = client.post("/api/v1/tasks", json={
        "issue_id": issue["id"],
        "cd": "T",
        "name": "Task"
    }).json()

    user = client.post("/api/v1/users", json={
        "cd": "U",
        "name": "User",
        "email": "u@test.com"
    }).json()

    response = client.post("/api/v1/work-logs", json={
        "task_id": task["id"],
        "user_id": user["id"],
        "work_date": date.today().isoformat(),
        "hours": 1.0
    })
    assert response.status_code == 400


def test_get_work_log(client, assigned_task):
    """実績詳細取得"""
    # 作成
    create_res = client.post("/api/v1/work-logs", json={
        "task_id": assigned_task["task"]["id"],
        "user_id": assigned_task["user"]["id"],
        "work_date": date.today().isoformat(),
        "hours": 2.0
    })
    work_log_id = create_res.json()["id"]

    # 取得
    response = client.get(f"/api/v1/work-logs/{work_log_id}")
    assert response.status_code == 200
    assert response.json()["hours"] == 2.0


def test_get_work_log_not_found(client, clean_db):
    """存在しない実績"""
    response = client.get("/api/v1/work-logs/99999")
    assert response.status_code == 404


def test_delete_work_log(client, assigned_task):
    """実績削除"""
    # 作成
    create_res = client.post("/api/v1/work-logs", json={
        "task_id": assigned_task["task"]["id"],
        "user_id": assigned_task["user"]["id"],
        "work_date": date.today().isoformat(),
        "hours": 2.0
    })
    work_log_id = create_res.json()["id"]

    # 削除
    response = client.delete(f"/api/v1/work-logs/{work_log_id}")
    assert response.status_code == 204

    # 確認
    response = client.get(f"/api/v1/work-logs/{work_log_id}")
    assert response.status_code == 404


def test_list_work_logs_with_filters(client, assigned_task):
    """フィルタ付き一覧"""
    task_id = assigned_task["task"]["id"]
    user_id = assigned_task["user"]["id"]
    work_date = date.today().isoformat()

    client.post("/api/v1/work-logs", json={
        "task_id": task_id,
        "user_id": user_id,
        "work_date": work_date,
        "hours": 2.5
    })

    # ユーザーでフィルタ
    response = client.get(f"/api/v1/work-logs?user_id={user_id}")
    assert response.status_code == 200
    assert all(l["user_id"] == user_id for l in response.json())

    # 日付でフィルタ
    response = client.get(f"/api/v1/work-logs?start_date={work_date}&end_date={work_date}")
    assert response.status_code == 200
