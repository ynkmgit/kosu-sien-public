"""案件見積サービスのテスト"""
import pytest
from services.issue_estimate_service import IssueEstimateService
from database import get_db


def _create_issue():
    """テスト用案件作成"""
    with get_db() as conn:
        conn.execute("INSERT INTO project (cd, name) VALUES ('EST', 'Estimate Test')")
        project_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO issue (project_id, cd, name) VALUES (?, 'I1', 'Issue1')", (project_id,))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_get_all_empty(clean_db):
    """見積なしで空リスト"""
    issue_id = _create_issue()
    result = IssueEstimateService.get_all(issue_id)
    assert result == []


def test_create_estimate(clean_db):
    """見積作成"""
    issue_id = _create_issue()
    estimate = IssueEstimateService.create(issue_id, "設計", 8.0)

    assert estimate["name"] == "設計"
    assert estimate["hours"] == 8.0
    assert estimate["issue_id"] == issue_id


def test_create_invalid_hours(clean_db):
    """0以下の工数でエラー"""
    issue_id = _create_issue()

    with pytest.raises(ValueError) as exc:
        IssueEstimateService.create(issue_id, "無効", 0)
    assert "0より大きい値" in str(exc.value)

    with pytest.raises(ValueError):
        IssueEstimateService.create(issue_id, "無効", -1)


def test_get_total(clean_db):
    """合計工数取得"""
    issue_id = _create_issue()
    IssueEstimateService.create(issue_id, "設計", 8.0)
    IssueEstimateService.create(issue_id, "実装", 16.0)
    IssueEstimateService.create(issue_id, "テスト", 4.0)

    total = IssueEstimateService.get_total(issue_id)
    assert total == 28.0


def test_get_total_empty(clean_db):
    """見積なしで0"""
    issue_id = _create_issue()
    total = IssueEstimateService.get_total(issue_id)
    assert total == 0


def test_get_by_id(clean_db):
    """IDで取得"""
    issue_id = _create_issue()
    created = IssueEstimateService.create(issue_id, "テスト", 4.0)

    result = IssueEstimateService.get_by_id(created["id"], issue_id)
    assert result is not None
    assert result["name"] == "テスト"


def test_get_by_id_wrong_issue(clean_db):
    """別案件のIDでNone"""
    issue_id = _create_issue()
    created = IssueEstimateService.create(issue_id, "テスト", 4.0)

    result = IssueEstimateService.get_by_id(created["id"], 99999)
    assert result is None


def test_update_estimate(clean_db):
    """見積更新"""
    issue_id = _create_issue()
    created = IssueEstimateService.create(issue_id, "旧名", 8.0)

    updated = IssueEstimateService.update(created["id"], issue_id, "新名", 12.0)
    assert updated is not None
    assert updated["name"] == "新名"
    assert updated["hours"] == 12.0


def test_update_invalid_hours(clean_db):
    """0以下の工数で更新エラー"""
    issue_id = _create_issue()
    created = IssueEstimateService.create(issue_id, "テスト", 8.0)

    with pytest.raises(ValueError):
        IssueEstimateService.update(created["id"], issue_id, "テスト", 0)


def test_update_not_found(clean_db):
    """存在しないIDで更新失敗"""
    issue_id = _create_issue()
    result = IssueEstimateService.update(99999, issue_id, "X", 1.0)
    assert result is None


def test_delete_estimate(clean_db):
    """見積削除"""
    issue_id = _create_issue()
    created = IssueEstimateService.create(issue_id, "削除用", 8.0)

    result = IssueEstimateService.delete(created["id"], issue_id)
    assert result is True
    assert IssueEstimateService.get_by_id(created["id"], issue_id) is None


def test_delete_not_found(clean_db):
    """存在しないIDで削除失敗"""
    issue_id = _create_issue()
    result = IssueEstimateService.delete(99999, issue_id)
    assert result is False


def test_sort_order_auto_increment(clean_db):
    """ソート順は自動インクリメント"""
    issue_id = _create_issue()
    e1 = IssueEstimateService.create(issue_id, "First", 1.0)
    e2 = IssueEstimateService.create(issue_id, "Second", 2.0)
    e3 = IssueEstimateService.create(issue_id, "Third", 3.0)

    assert e1["sort_order"] < e2["sort_order"] < e3["sort_order"]
