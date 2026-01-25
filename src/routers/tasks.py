"""作業CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はTaskServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import TaskService
from .common import templates, get_project_or_404, get_issue_or_404, render_edit_actions, render_sortable_th

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/tasks", tags=["tasks"])


def render_thead(sort: str, order: str, project_id: int, issue_id: int):
    """ソート状態を反映したテーブルヘッダー生成"""
    endpoint = f"/projects/{project_id}/issues/{issue_id}/tasks/list"
    def col(name, label, css_class=None):
        return render_sortable_th(name, label, sort, order, endpoint, "task-table", css_class)

    return f"""<tr>
        {col("cd", "CD", "col-cd")}
        {col("name", "作業名", "col-name-lg")}
        {col("description", "説明")}
        <th class="col-actions-sm">操作</th>
    </tr>"""


def render_row(t, project_id: int, issue_id: int, editing=False):
    """作業行HTML生成"""
    cd = escape(t['cd'] or '')
    name = escape(t['name'])
    desc = escape(t['description'] or '')

    if editing:
        base_path = f"/projects/{project_id}/issues/{issue_id}/tasks"
        return f"""
        <tr id="task-{t['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="cd" value="{cd}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="text" name="description" value="{desc}" class="edit-input"></td>
            <td>{render_edit_actions("task", t['id'], base_path)}</td>
        </tr>"""

    return f"""
    <tr id="task-{t['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell">{name}</td>
        <td class="desc-cell">{desc}</td>
        <td><div class="actions-cell">
            <button hx-get="/projects/{project_id}/issues/{issue_id}/tasks/{t['id']}/edit" hx-target="#task-{t['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    project_id: int,
    issue_id: int,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    proj = get_project_or_404(project_id)
    iss = get_issue_or_404(project_id, issue_id)
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "tasks.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int, sort: str = "cd", order: str = "asc", q: str = ""):
    """作業一覧取得（検索・ソート対応）"""
    get_issue_or_404(project_id, issue_id)
    rows = TaskService.get_all(issue_id=issue_id, sort=sort, order=order, q=q)
    tbody = "".join(render_row(r, project_id, issue_id) for r in rows)
    thead = render_thead(sort, order, project_id, issue_id)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return HTMLResponse(render_row(t, project_id, issue_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return HTMLResponse(render_row(t, project_id, issue_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int, cd: str = Form(...), name: str = Form(...), description: str = Form("")):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.create(issue_id=issue_id, cd=cd, name=name, description=description)
    return HTMLResponse(render_row(t, project_id, issue_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int, cd: str = Form(...), name: str = Form(...), description: str = Form("")):
    get_issue_or_404(project_id, issue_id)
    # タスクがこのissueに属しているか確認
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    t = TaskService.update(task_id=id, cd=cd, name=name, description=description)
    return HTMLResponse(render_row(t, project_id, issue_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    # タスクがこのissueに属しているか確認
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskService.delete(id)
    return HTMLResponse("")


# 進捗率更新用ルーター（/tasks/{id}/progress）
task_progress_router = APIRouter(prefix="/tasks", tags=["task_progress"])


@task_progress_router.put("/{task_id}/progress", response_class=HTMLResponse)
def update_progress(task_id: int, progress_rate: int = Form(...)):
    """進捗率更新"""
    try:
        if not TaskService.update_progress(task_id, progress_rate):
            raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return HTMLResponse("")
