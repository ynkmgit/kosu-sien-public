"""ステータスCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はStatusServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import StatusService
from .common import templates, get_project_or_404, render_edit_actions

router = APIRouter(prefix="/projects/{project_id}/statuses", tags=["statuses"])


def render_row(s, project_id: int, editing=False):
    """ステータス行HTML生成"""
    code = escape(s['code'])
    name = escape(s['name'])
    sort_order = s['sort_order']

    if editing:
        base_path = f"/projects/{project_id}/statuses"
        return f"""
        <tr id="status-{s['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="code" value="{code}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="number" name="sort_order" value="{sort_order}" class="edit-input" step="1" min="0"></td>
            <td>{render_edit_actions("status", s['id'], base_path)}</td>
        </tr>"""

    return f"""
    <tr id="status-{s['id']}">
        <td class="cd-cell">{code}</td>
        <td class="name-cell">{name}</td>
        <td>{sort_order}</td>
        <td><div class="actions-cell">
            <button hx-get="/projects/{project_id}/statuses/{s['id']}/edit" hx-target="#status-{s['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    project_id: int,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    proj = get_project_or_404(project_id)
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "statuses.html", {
        "active": "projects",
        "project": proj,
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int):
    """ステータス一覧取得"""
    get_project_or_404(project_id)
    rows = StatusService.get_all(project_id)
    tbody = "".join(render_row(r, project_id) for r in rows)
    return HTMLResponse(f"<tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, id: int):
    get_project_or_404(project_id)
    s = StatusService.get_by_id(id, project_id)
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")
    return HTMLResponse(render_row(s, project_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, id: int):
    get_project_or_404(project_id)
    s = StatusService.get_by_id(id, project_id)
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")
    return HTMLResponse(render_row(s, project_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    get_project_or_404(project_id)
    s = StatusService.create(project_id, code, name, sort_order)
    return HTMLResponse(render_row(s, project_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0)):
    get_project_or_404(project_id)
    s = StatusService.update(id, project_id, code, name, sort_order)
    if not s:
        raise HTTPException(status_code=404, detail="Status not found")
    return HTMLResponse(render_row(s, project_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, id: int):
    get_project_or_404(project_id)
    if StatusService.is_in_use(id):
        raise HTTPException(status_code=400, detail="このステータスは使用中のため削除できません")
    if not StatusService.delete(id, project_id):
        raise HTTPException(status_code=404, detail="Status not found")
    return HTMLResponse("")
