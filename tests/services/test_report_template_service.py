"""報告テンプレートサービスのテスト"""
import json
import sqlite3

import pytest

from services.report_template_service import ReportTemplateService


def test_get_all_empty(clean_db):
    """テンプレートなしで空リスト"""
    result = ReportTemplateService.get_all()
    assert result == []


def test_create_and_get_by_id(clean_db):
    """作成と単件取得"""
    t = ReportTemplateService.create("テスト報告", "本文テスト")
    assert t["name"] == "テスト報告"
    assert t["body"] == "本文テスト"
    assert t["id"] is not None

    fetched = ReportTemplateService.get_by_id(t["id"])
    assert fetched["name"] == "テスト報告"


def test_get_by_id_not_found(clean_db):
    """存在しないIDでNone"""
    assert ReportTemplateService.get_by_id(99999) is None


def test_create_duplicate_name_raises(clean_db):
    """重複名でIntegrityError"""
    ReportTemplateService.create("同名", "本文1")
    with pytest.raises(sqlite3.IntegrityError):
        ReportTemplateService.create("同名", "本文2")


def test_get_all_sorted(clean_db):
    """sort_order順で取得"""
    ReportTemplateService.create("B", "b", sort_order=2)
    ReportTemplateService.create("A", "a", sort_order=1)
    result = ReportTemplateService.get_all()
    assert result[0]["name"] == "A"
    assert result[1]["name"] == "B"


def test_update(clean_db):
    """更新"""
    t = ReportTemplateService.create("更新前", "旧本文")
    updated = ReportTemplateService.update(t["id"], "更新後", "新本文", '{"hideZeroProgress": true}')
    assert updated["name"] == "更新後"
    assert updated["body"] == "新本文"
    assert json.loads(updated["options"])["hideZeroProgress"] is True


def test_update_not_found(clean_db):
    """存在しないIDでNone"""
    assert ReportTemplateService.update(99999, "名前", "本文") is None


def test_delete(clean_db):
    """削除"""
    t1 = ReportTemplateService.create("削除用1", "本文1")
    ReportTemplateService.create("残す用", "本文2")
    assert ReportTemplateService.delete(t1["id"]) is True
    assert ReportTemplateService.get_by_id(t1["id"]) is None


def test_delete_last_fails(clean_db):
    """最後の1件は削除不可"""
    t = ReportTemplateService.create("唯一", "本文")
    assert ReportTemplateService.delete(t["id"]) is False
    assert ReportTemplateService.get_by_id(t["id"]) is not None


def test_options_stored_as_json(clean_db):
    """optionsがJSON文字列で保存される"""
    opts = json.dumps({"hideZeroProgress": True})
    t = ReportTemplateService.create("JSON", "本文", options=opts)
    fetched = ReportTemplateService.get_by_id(t["id"])
    parsed = json.loads(fetched["options"])
    assert parsed["hideZeroProgress"] is True
