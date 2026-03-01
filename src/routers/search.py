"""オートコンプリート検索API

責務: エンティティ検索のHTMLフラグメント返却のみ
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from html import escape

from services import UserService, ProjectService, IssueService, IssueTagService, StatusService, TaskStatusService, TaskAssigneeService
from .common.renders import TAG_DEFAULT_COLOR

router = APIRouter(prefix="/search", tags=["search"])

# 検索結果の最大件数
MAX_RESULTS = 10


def _filter_items(items: list[dict], q: str, exclude: list[int], search_fields: list[str]) -> list[dict]:
    """汎用フィルタリング関数

    Args:
        items: 検索対象のアイテムリスト
        q: 検索クエリ
        exclude: 除外するID
        search_fields: 検索対象フィールド名のリスト

    Returns:
        フィルタリング済みリスト（最大MAX_RESULTS件）
    """
    results = []
    q_lower = q.lower()

    for item in items:
        if item['id'] in exclude:
            continue
        if q:
            matched = any(q_lower in str(item.get(field, '')).lower() for field in search_fields)
            if not matched:
                continue
        results.append(item)
        if len(results) >= MAX_RESULTS:
            break

    return results


def _render_empty() -> HTMLResponse:
    """空結果のHTML"""
    return HTMLResponse('<div class="autocomplete-empty">該当なし</div>')


def _collect_unique_from_bulk(bulk: dict[int, list[dict]]) -> list[dict]:
    """バルク取得結果からcode重複排除で収集"""
    seen = set()
    result = []
    for statuses in bulk.values():
        for s in statuses:
            if s['code'] not in seen:
                seen.add(s['code'])
                result.append(s)
    return result


@router.get("/users", response_class=HTMLResponse)
def search_users(q: str = "", exclude: list[int] = Query(default=[])):
    """ユーザー検索（オートコンプリート用）"""
    users = UserService.get_active_list()
    results = _filter_items(users, q, exclude, ['cd', 'name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'user\', {u["id"]}, \'{escape(u["cd"])}\')">'
        f'{escape(u["cd"])} {escape(u["name"])}</div>'
        for u in results
    )
    return HTMLResponse(items)


@router.get("/projects", response_class=HTMLResponse)
def search_projects(q: str = "", exclude: list[int] = Query(default=[])):
    """プロジェクト検索（オートコンプリート用）"""
    projects = ProjectService.get_list()
    results = _filter_items(projects, q, exclude, ['cd', 'name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'project\', {p["id"]}, \'{escape(p["cd"])}\')">'
        f'{escape(p["cd"])} {escape(p["name"])}</div>'
        for p in results
    )
    return HTMLResponse(items)


@router.get("/issues", response_class=HTMLResponse)
def search_issues(q: str = "", exclude: list[int] = Query(default=[])):
    """案件検索（オートコンプリート用）"""
    issues = IssueService.get_list()
    results = _filter_items(issues, q, exclude, ['cd', 'name', 'project_cd'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'issue\', {i["id"]}, \'{escape(i["cd"])}\')">'
        f'[{escape(i["project_cd"])}] {escape(i["cd"])} {escape(i["name"])}</div>'
        for i in results
    )
    return HTMLResponse(items)


@router.get("/tags", response_class=HTMLResponse)
def search_tags(q: str = "", exclude: list[int] = Query(default=[])):
    """タグ検索（オートコンプリート用・名前重複排除）"""
    tags = IssueTagService.get_list()
    # 名前で重複排除（最初に見つかったものを代表として使用）
    seen_names = set()
    unique_tags = []
    for t in tags:
        if t['name'] not in seen_names:
            seen_names.add(t['name'])
            unique_tags.append(t)
    results = _filter_items(unique_tags, q, exclude, ['name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'tag\', {t["id"]}, \'{escape(t["name"])}\')">'
        f'<span class="color-preview" style="background:{escape(t["color"] or TAG_DEFAULT_COLOR)}"></span>'
        f'{escape(t["name"])}</div>'
        for t in results
    )
    return HTMLResponse(items)


@router.get("/task_users", response_class=HTMLResponse)
def search_task_users(task_id: int, q: str = ""):
    """作業の担当追加用ユーザー検索（既存担当除外）"""
    users = UserService.get_active_list()
    exclude = TaskAssigneeService.get_user_ids_for_task(task_id)
    results = _filter_items(users, q, exclude, ['cd', 'name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAssignee({task_id}, {u["id"]})">'
        f'{escape(u["cd"])} {escape(u["name"])}</div>'
        for u in results
    )
    return HTMLResponse(items)


@router.get("/issue_statuss", response_class=HTMLResponse)
def search_issue_statuses(q: str = "", exclude: list[int] = Query(default=[])):
    """案件ステータス検索（オートコンプリート用）"""
    projects = ProjectService.get_list()
    bulk = StatusService.get_all_bulk([p['id'] for p in projects])
    all_statuses = _collect_unique_from_bulk(bulk)
    results = _filter_items(all_statuses, q, exclude, ['name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'issue_status\', {s["id"]}, \'{escape(s["name"])}\')">'
        f'{escape(s["name"])}</div>'
        for s in results
    )
    return HTMLResponse(items)


@router.get("/task_statuss", response_class=HTMLResponse)
def search_task_statuses(q: str = "", exclude: list[int] = Query(default=[])):
    """作業ステータス検索（オートコンプリート用）"""
    issues = IssueService.get_list()
    bulk = TaskStatusService.get_all_bulk([i['id'] for i in issues])
    all_statuses = _collect_unique_from_bulk(bulk)
    results = _filter_items(all_statuses, q, exclude, ['name'])

    if not results:
        return _render_empty()

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'task_status\', {s["id"]}, \'{escape(s["name"])}\')">'
        f'{escape(s["name"])}</div>'
        for s in results
    )
    return HTMLResponse(items)
