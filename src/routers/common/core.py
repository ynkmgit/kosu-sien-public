"""共通コア機能

責務: templates初期化, 404ヘルパー, フィルタークエリ生成, 消化率計算
"""
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
from services import ProjectService, IssueService, UserService, UserAttributeTypeService

_BASE_DIR = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=_BASE_DIR / "templates")


# === フィルタークエリ生成 ===

def build_filter_query(filter_params: dict) -> str:
    """フィルターパラメータからクエリ文字列を生成

    Args:
        filter_params: {"user": [1,2], "project": [3], "issue": [], ...}

    Returns:
        "?user=1&user=2&project=3" or "" (空の場合)
    """
    parts = []
    for key in ('user', 'project', 'issue', 'tag', 'issue_status', 'task_status'):
        for v in filter_params.get(key, []):
            parts.append(f'{key}={v}')
    if filter_params.get('exclude_done_issue'):
        parts.append('exclude_done_issue=true')
    if filter_params.get('exclude_done_task'):
        parts.append('exclude_done_task=true')
    fold = filter_params.get('fold', '')
    if fold:
        parts.append(f'fold={fold}')
    return '?' + '&'.join(parts) if parts else ''


# Jinja2グローバル関数として登録
templates.env.globals['filter_qs'] = build_filter_query


def _static_url(path: str) -> str:
    """キャッシュバスティング付き静的ファイルURL"""
    full = _BASE_DIR / "static" / path
    try:
        mtime = int(os.path.getmtime(full))
    except OSError:
        mtime = 0
    return f"/static/{path}?v={mtime}"


templates.env.globals['static_url'] = _static_url


# === 404ヘルパー ===

def get_project_or_404(project_id: int):
    """プロジェクト取得（存在しなければ404）"""
    p = ProjectService.get_by_id(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def get_issue_or_404(project_id: int, issue_id: int):
    """案件取得（存在しなければ404）。親プロジェクトも検証"""
    get_project_or_404(project_id)
    i = IssueService.get_by_id_with_project(issue_id, project_id)
    if not i:
        raise HTTPException(status_code=404, detail="Issue not found")
    return i


def get_user_or_404(user_id: int):
    """ユーザー取得（存在しなければ404）"""
    u = UserService.get_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


def get_attribute_type_or_404(type_id: int):
    """属性タイプ取得（存在しなければ404）"""
    t = UserAttributeTypeService.get_by_id(type_id)
    if not t:
        raise HTTPException(status_code=404, detail="Attribute type not found")
    return t


# === 消化率ユーティリティ ===

def get_rate_class(rate: float) -> str:
    """消化率に応じた警告クラスを返す"""
    if rate <= 100:
        return "rate-normal"
    elif rate <= 120:
        return "rate-caution"
    elif rate <= 150:
        return "rate-alert"
    elif rate <= 200:
        return "rate-danger"
    else:
        return "rate-critical"
