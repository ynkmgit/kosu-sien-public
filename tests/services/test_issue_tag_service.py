"""案件タグサービスのテスト"""
import pytest

from services.issue_tag_service import IssueTagService
from database import get_db


@pytest.fixture
def issue_id(clean_db):
    """テスト用案件を作成してIDを返す"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('TGP', 'タグテストPJ')")
        proj = conn.execute("SELECT id FROM project WHERE cd = 'TGP'").fetchone()
        conn.execute(
            "INSERT INTO issue (cd, project_id, name, status) VALUES ('TGI', ?, 'タグテスト案件', 'open')",
            (proj[0],)
        )
        issue = conn.execute("SELECT id FROM issue WHERE cd = 'TGI'").fetchone()
    return issue[0]


def test_get_all_empty(issue_id):
    """タグなしで空リスト"""
    result = IssueTagService.get_all(issue_id)
    assert result == []


def test_create_and_get_by_id(issue_id):
    """作成と単件取得"""
    tag = IssueTagService.create(issue_id, "重要", "#ef4444", 1)
    assert tag["name"] == "重要"
    assert tag["color"] == "#ef4444"
    assert tag["sort_order"] == 1

    fetched = IssueTagService.get_by_id(tag["id"], issue_id)
    assert fetched["name"] == "重要"


def test_get_all_sorted(issue_id):
    """sort_order順で取得"""
    IssueTagService.create(issue_id, "B", "#000000", 2)
    IssueTagService.create(issue_id, "A", "#ffffff", 1)
    result = IssueTagService.get_all(issue_id)
    assert result[0]["name"] == "A"
    assert result[1]["name"] == "B"


def test_update(issue_id):
    """更新"""
    tag = IssueTagService.create(issue_id, "旧", "#000000", 0)
    updated = IssueTagService.update(tag["id"], issue_id, "新", "#ff0000", 5)
    assert updated["name"] == "新"
    assert updated["color"] == "#ff0000"
    assert updated["sort_order"] == 5


def test_delete(issue_id):
    """削除"""
    tag = IssueTagService.create(issue_id, "削除用", "#000000", 0)
    assert IssueTagService.delete(tag["id"], issue_id) is True
    assert IssueTagService.get_by_id(tag["id"], issue_id) is None


def test_is_in_use(issue_id):
    """使用中チェック"""
    tag = IssueTagService.create(issue_id, "使用中", "#000000", 0)
    assert IssueTagService.is_in_use(tag["id"]) is False

    # 作業を作成してタグを付与
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task (cd, issue_id, name, status) VALUES ('T1', ?, 'テスト作業', 'open')",
            (issue_id,)
        )
        task = conn.execute("SELECT id FROM task WHERE cd = 'T1' AND issue_id = ?", (issue_id,)).fetchone()
        conn.execute(
            "INSERT INTO task_tag (task_id, tag_id) VALUES (?, ?)",
            (task[0], tag["id"])
        )
    assert IssueTagService.is_in_use(tag["id"]) is True
