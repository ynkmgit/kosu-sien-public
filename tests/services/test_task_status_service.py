"""作業ステータスサービスのテスト"""
import sqlite3

import pytest

from services.task_status_service import TaskStatusService
from database import get_db


@pytest.fixture
def issue_id(clean_db):
    """テスト用案件を作成してIDを返す"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('TSP', 'テストPJ')")
        proj = conn.execute("SELECT id FROM project WHERE cd = 'TSP'").fetchone()
        conn.execute(
            "INSERT INTO issue (cd, project_id, name, status) VALUES ('TSI', ?, 'テスト案件', 'open')",
            (proj[0],)
        )
        issue = conn.execute("SELECT id FROM issue WHERE cd = 'TSI'").fetchone()
    return issue[0]


def test_get_all_empty(issue_id):
    """デフォルトステータスなしで空リスト（clean_dbでクリア済み）"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    result = TaskStatusService.get_all(issue_id)
    assert result == []


def test_create_and_get_by_id(issue_id):
    """作成と単件取得"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    s = TaskStatusService.create(issue_id, "review", "レビュー中", 5)
    assert s["code"] == "review"
    assert s["name"] == "レビュー中"
    assert s["sort_order"] == 5
    assert s["is_done"] == 0

    fetched = TaskStatusService.get_by_id(s["id"], issue_id)
    assert fetched["code"] == "review"


def test_create_with_is_done(issue_id):
    """完了扱いステータス作成"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    s = TaskStatusService.create(issue_id, "done", "完了", 2, is_done=1)
    assert s["code"] == "done"
    assert s["is_done"] == 1


def test_get_all_sorted(issue_id):
    """sort_order順で取得"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    TaskStatusService.create(issue_id, "b", "B", 2)
    TaskStatusService.create(issue_id, "a", "A", 1)
    result = TaskStatusService.get_all(issue_id)
    assert result[0]["code"] == "a"
    assert result[1]["code"] == "b"


def test_get_status_labels(issue_id):
    """code->name辞書が取得できる"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    TaskStatusService.create(issue_id, "open", "未着手", 0)
    TaskStatusService.create(issue_id, "done", "完了", 1)
    labels = TaskStatusService.get_status_labels(issue_id)
    assert labels == {"open": "未着手", "done": "完了"}


def test_update(issue_id):
    """更新"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    s = TaskStatusService.create(issue_id, "old", "旧", 0)
    updated = TaskStatusService.update(s["id"], issue_id, "new", "新", 5, is_done=1)
    assert updated["code"] == "new"
    assert updated["name"] == "新"
    assert updated["is_done"] == 1


def test_delete(issue_id):
    """削除"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    s = TaskStatusService.create(issue_id, "del", "削除用", 0)
    assert TaskStatusService.delete(s["id"], issue_id) is True
    assert TaskStatusService.get_by_id(s["id"], issue_id) is None


def test_is_in_use(issue_id):
    """使用中チェック"""
    with get_db() as conn:
        conn.execute("DELETE FROM task_status WHERE issue_id = ?", (issue_id,))
    s = TaskStatusService.create(issue_id, "used", "使用中", 0)
    # 作業を作成してステータスを設定
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task (cd, issue_id, name, status) VALUES ('T1', ?, 'テスト作業', 'used')",
            (issue_id,)
        )
    assert TaskStatusService.is_in_use(s["id"]) is True
