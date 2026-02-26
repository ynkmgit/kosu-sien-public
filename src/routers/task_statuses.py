"""作業ステータスCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はTaskStatusServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import TaskStatusService
from .common import templates, get_project_or_404, get_issue_or_404, render_edit_actions, FilterParams, get_filter_params

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/task-statuses", tags=["task_statuses"])


def render_row(s, project_id: int, issue_id: int, editing=False):
    """作業ステータス行HTML生成"""
    code = escape(s['code'])
    name = escape(s['name'])
    sort_order = s['sort_order']
    is_done = s.get('is_done', 0)

    base_path = f"/projects/{project_id}/issues/{issue_id}/task-statuses"

    if editing:
        checked = "checked" if is_done else ""
        return f"""
        <tr id="task-status-{s['id']}" class="editing-row">
            <td><input type="text" name="code" value="{code}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="number" name="sort_order" value="{sort_order}" class="edit-input" step="1" min="0"></td>
            <td class="center-cell"><input type="checkbox" name="is_done" value="1" {checked} class="edit-checkbox"></td>
            <td>{render_edit_actions("task-status", s['id'], base_path)}</td>
        </tr>"""

    done_badge = ' <span class="done-badge">完了</span>' if is_done else ""
    return f"""
    <tr id="task-status-{s['id']}">
        <td class="cd-cell">{code}</td>
        <td class="name-cell">{name}</td>
        <td>{sort_order}</td>
        <td class="center-cell">{done_badge}</td>
        <td><div class="actions-cell">
            <button hx-get="{base_path}/{s['id']}/edit" hx-target="#task-status-{s['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(request: Request, project_id: int, issue_id: int, filters: FilterParams = Depends(get_filter_params)):
    proj = get_project_or_404(project_id)
    iss = get_issue_or_404(project_id, issue_id)
    return templates.TemplateResponse(request, "task_statuses.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "filter_params": filters.to_dict(),
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int):
    """作業ステータス一覧取得"""
    get_issue_or_404(project_id, issue_id)
    rows = TaskStatusService.get_all(issue_id)
    tbody = "".join(render_row(r, project_id, issue_id) for r in rows)
    return HTMLResponse(f"<tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    s = TaskStatusService.get_by_id(id, issue_id)
    if not s:
        raise HTTPException(status_code=404, detail="Task status not found")
    return HTMLResponse(render_row(s, project_id, issue_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    s = TaskStatusService.get_by_id(id, issue_id)
    if not s:
        raise HTTPException(status_code=404, detail="Task status not found")
    return HTMLResponse(render_row(s, project_id, issue_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0), is_done: int = Form(0)):
    get_issue_or_404(project_id, issue_id)
    s = TaskStatusService.create(issue_id, code, name, sort_order, is_done)
    return HTMLResponse(render_row(s, project_id, issue_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int, code: str = Form(...), name: str = Form(...), sort_order: int = Form(0), is_done: int = Form(0)):
    get_issue_or_404(project_id, issue_id)
    s = TaskStatusService.update(id, issue_id, code, name, sort_order, is_done)
    if not s:
        raise HTTPException(status_code=404, detail="Task status not found")
    return HTMLResponse(render_row(s, project_id, issue_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    if TaskStatusService.is_in_use(id):
        raise HTTPException(status_code=400, detail="このステータスは使用中のため削除できません")
    if not TaskStatusService.delete(id, issue_id):
        raise HTTPException(status_code=404, detail="Task status not found")
    return HTMLResponse("")
