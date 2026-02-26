"""作業タグ割当サービスのテスト"""
import pytest

from services.issue_tag_service import IssueTagService
from services.task_tag_service import TaskTagService
from database import get_db


@pytest.fixture
def issue_id(clean_db):
    """テスト用案件を作成してIDを返す"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('TTP', 'タグ割当テストPJ')")
        proj = conn.execute("SELECT id FROM project WHERE cd = 'TTP'").fetchone()
        conn.execute(
            "INSERT INTO issue (cd, project_id, name, status) VALUES ('TTI', ?, 'タグ割当テスト案件', 'open')",
            (proj[0],)
        )
        issue = conn.execute("SELECT id FROM issue WHERE cd = 'TTI'").fetchone()
    return issue[0]


@pytest.fixture
def task_id(issue_id):
    """テスト用作業を作成してIDを返す"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task (cd, issue_id, name, status) VALUES ('TT1', ?, 'テスト作業', 'open')",
            (issue_id,)
        )
        task = conn.execute("SELECT id FROM task WHERE cd = 'TT1' AND issue_id = ?", (issue_id,)).fetchone()
    return task[0]


def test_toggle_add(issue_id, task_id):
    """タグ付与"""
    tag = IssueTagService.create(issue_id, "テスト", "#000000", 0)
    result = TaskTagService.toggle(task_id, tag["id"])
    assert result is True

    tags = TaskTagService.get_tags_for_task(task_id)
    assert len(tags) == 1
    assert tags[0]["name"] == "テスト"


def test_toggle_remove(issue_id, task_id):
    """タグ解除"""
    tag = IssueTagService.create(issue_id, "テスト", "#000000", 0)
    TaskTagService.toggle(task_id, tag["id"])  # 付与
    result = TaskTagService.toggle(task_id, tag["id"])  # 解除
    assert result is False

    tags = TaskTagService.get_tags_for_task(task_id)
    assert len(tags) == 0


def test_get_tags_for_task_sorted(issue_id, task_id):
    """sort_order順で取得"""
    tag_b = IssueTagService.create(issue_id, "B", "#000000", 2)
    tag_a = IssueTagService.create(issue_id, "A", "#ffffff", 1)
    TaskTagService.toggle(task_id, tag_b["id"])
    TaskTagService.toggle(task_id, tag_a["id"])

    tags = TaskTagService.get_tags_for_task(task_id)
    assert len(tags) == 2
    assert tags[0]["name"] == "A"
    assert tags[1]["name"] == "B"


def test_get_task_tags_map(issue_id):
    """案件内の全作業タグマップ"""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO task (cd, issue_id, name, status) VALUES ('M1', ?, '作業1', 'open')",
            (issue_id,)
        )
        conn.execute(
            "INSERT INTO task (cd, issue_id, name, status) VALUES ('M2', ?, '作業2', 'open')",
            (issue_id,)
        )
        t1 = conn.execute("SELECT id FROM task WHERE cd = 'M1' AND issue_id = ?", (issue_id,)).fetchone()[0]
        t2 = conn.execute("SELECT id FROM task WHERE cd = 'M2' AND issue_id = ?", (issue_id,)).fetchone()[0]

    tag1 = IssueTagService.create(issue_id, "タグ1", "#ff0000", 0)
    tag2 = IssueTagService.create(issue_id, "タグ2", "#00ff00", 1)

    TaskTagService.toggle(t1, tag1["id"])
    TaskTagService.toggle(t1, tag2["id"])
    TaskTagService.toggle(t2, tag1["id"])

    tags_map = TaskTagService.get_task_tags_map(issue_id)
    assert len(tags_map[t1]) == 2
    assert len(tags_map[t2]) == 1
    assert tags_map[t1][0]["name"] == "タグ1"
