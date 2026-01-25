"""共通コア機能

責務: templates, 404ヘルパー, ソート検証, 消化率, 検索ユーティリティ
"""
from pathlib import Path

from fastapi import HTTPException
from fastapi.templating import Jinja2Templates
from services import ProjectService, IssueService, UserService, UserAttributeTypeService

templates = Jinja2Templates(directory=Path(__file__).parent.parent.parent / "templates")


# === フィルタークエリ生成 ===

def build_filter_query(filter_params: dict) -> str:
    """フィルターパラメータからクエリ文字列を生成

    Args:
        filter_params: {"user": [1,2], "project": [3], "issue": []}

    Returns:
        "?user=1&user=2&project=3" or "" (空の場合)
    """
    parts = []
    for u in filter_params.get('user', []):
        parts.append(f'user={u}')
    for p in filter_params.get('project', []):
        parts.append(f'project={p}')
    for i in filter_params.get('issue', []):
        parts.append(f'issue={i}')
    return '?' + '&'.join(parts) if parts else ''


# Jinja2グローバル関数として登録
templates.env.globals['filter_qs'] = build_filter_query


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


# === ソートユーティリティ ===

def validate_sort_params(
    sort: str,
    order: str,
    allowed_cols: set,
    default_col: str = "cd"
) -> tuple[str, str]:
    """ソートパラメータを検証し、(sort_col, order_dir)を返す"""
    sort = sort if sort in allowed_cols else default_col
    order = order if order in {"asc", "desc"} else "asc"
    order_dir = "DESC" if order == "desc" else "ASC"
    return sort, order_dir


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


# === 検索ユーティリティ ===

def build_like_params(q: str, count: int = 3) -> tuple[str, tuple]:
    """LIKE検索用のパターンとパラメータを生成

    Args:
        q: 検索文字列
        count: LIKEパラメータの数

    Returns:
        (like_pattern, params_tuple)
    """
    like = f"%{q}%"
    return like, tuple(like for _ in range(count))
