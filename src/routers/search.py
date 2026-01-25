"""オートコンプリート検索API

責務: エンティティ検索のHTMLフラグメント返却のみ
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from markupsafe import escape

from services import UserService, ProjectService, IssueService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/users", response_class=HTMLResponse)
def search_users(q: str = "", exclude: list[int] = Query(default=[])):
    """ユーザー検索（オートコンプリート用）"""
    users = UserService.get_active_list()

    results = []
    q_lower = q.lower()
    for u in users:
        if u['id'] in exclude:
            continue
        if q and q_lower not in u['cd'].lower() and q_lower not in u['name'].lower():
            continue
        results.append(u)
        if len(results) >= 10:
            break

    if not results:
        return HTMLResponse('<div class="autocomplete-empty">該当なし</div>')

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

    results = []
    q_lower = q.lower()
    for p in projects:
        if p['id'] in exclude:
            continue
        if q and q_lower not in p['cd'].lower() and q_lower not in p['name'].lower():
            continue
        results.append(p)
        if len(results) >= 10:
            break

    if not results:
        return HTMLResponse('<div class="autocomplete-empty">該当なし</div>')

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

    results = []
    q_lower = q.lower()
    for i in issues:
        if i['id'] in exclude:
            continue
        if q and q_lower not in i['cd'].lower() and q_lower not in i['name'].lower() and q_lower not in i['project_cd'].lower():
            continue
        results.append(i)
        if len(results) >= 10:
            break

    if not results:
        return HTMLResponse('<div class="autocomplete-empty">該当なし</div>')

    items = "".join(
        f'<div class="autocomplete-item" onclick="selectAutocomplete(\'issue\', {i["id"]}, \'{escape(i["cd"])}\')">'
        f'[{escape(i["project_cd"])}] {escape(i["cd"])} {escape(i["name"])}</div>'
        for i in results
    )
    return HTMLResponse(items)
