"""プロジェクトCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はProjectServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import ProjectService
from .common import templates, render_edit_actions, render_sortable_th, get_project_or_404

router = APIRouter(prefix="/projects", tags=["projects"])


def render_thead(sort: str, order: str):
    """ソート状態を反映したテーブルヘッダー生成"""
    def col(name, label, css_class=None):
        return render_sortable_th(name, label, sort, order, "/projects/list", "project-table", css_class)

    return f"""<tr>
        {col("cd", "CD", "col-cd")}
        {col("name", "名前", "col-name")}
        {col("description", "説明")}
        <th class="col-actions">操作</th>
    </tr>"""


def render_row(p, editing=False):
    """プロジェクト行HTML生成"""
    cd = escape(p['cd'] or '')
    name = escape(p['name'])
    desc = escape(p['description'] or '')

    if editing:
        return f"""
        <tr id="project-{p['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="cd" value="{cd}" class="edit-input"></td>
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="text" name="description" value="{desc}" class="edit-input"></td>
            <td>{render_edit_actions("project", p['id'], "/projects")}</td>
        </tr>"""
    return f"""
    <tr id="project-{p['id']}">
        <td class="cd-cell">{cd}</td>
        <td class="name-cell"><a href="/projects/{p['id']}" style="color: inherit; text-decoration: none;">{name}</a></td>
        <td class="desc-cell">{desc}</td>
        <td><div class="actions-cell">
            <a href="/projects/{p['id']}" class="btn btn-sm btn-primary">詳細</a>
            <button hx-get="/projects/{p['id']}/edit" hx-target="#project-{p['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "projects.html", {
        "active": "projects", "filter_params": filter_params
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(sort: str = "cd", order: str = "asc", q: str = ""):
    """プロジェクト一覧取得（検索・ソート対応）"""
    rows = ProjectService.get_all(sort=sort, order=order, q=q)
    tbody = "".join(render_row(r) for r in rows)
    thead = render_thead(sort, order)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}", response_class=HTMLResponse)
def detail(request: Request, id: int):
    """プロジェクト詳細画面"""
    project = ProjectService.get_by_id(id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    summary = ProjectService.get_summary(id)
    recent_issues = ProjectService.get_recent_issues(id)
    return templates.TemplateResponse(request, "project_detail.html", {
        "active": "projects",
        "project": project,
        "summary": summary,
        "recent_issues": recent_issues,
    })


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(id: int):
    p = get_project_or_404(id)
    return HTMLResponse(render_row(p))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(id: int):
    p = get_project_or_404(id)
    return HTMLResponse(render_row(p, editing=True))


@router.post("", response_class=HTMLResponse)
def create(cd: str = Form(...), name: str = Form(...), description: str = Form("")):
    p = ProjectService.create(cd=cd, name=name, description=description)
    return HTMLResponse(render_row(p))


@router.put("/{id}", response_class=HTMLResponse)
def update(id: int, cd: str = Form(...), name: str = Form(...), description: str = Form("")):
    p = ProjectService.update(project_id=id, cd=cd, name=name, description=description)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return HTMLResponse(render_row(p))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(id: int):
    if not ProjectService.delete(id):
        raise HTTPException(status_code=404, detail="Project not found")
    return HTMLResponse("")
