"""案件タグCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はIssueTagServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import IssueTagService
from .common import templates, get_project_or_404, get_issue_or_404, render_edit_actions, FilterParams, get_filter_params

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/issue-tags", tags=["issue_tags"])


def render_row(tag, project_id: int, issue_id: int, editing=False):
    """タグ行HTML生成"""
    name = escape(tag['name'])
    color = escape(tag['color'] or '#6b7280')
    sort_order = tag['sort_order']

    base_path = f"/projects/{project_id}/issues/{issue_id}/issue-tags"

    if editing:
        return f"""
        <tr id="issue-tag-{tag['id']}" class="editing-row">
            <td><input type="text" name="name" value="{name}" class="edit-input"></td>
            <td><input type="color" name="color" value="{color}" class="edit-input input-color"></td>
            <td><input type="number" name="sort_order" value="{sort_order}" class="edit-input" step="1" min="0"></td>
            <td>{render_edit_actions("issue-tag", tag['id'], base_path)}</td>
        </tr>"""

    return f"""
    <tr id="issue-tag-{tag['id']}">
        <td class="name-cell"><span class="tag-badge" style="background:{color}">{name}</span></td>
        <td><span class="color-preview" style="background:{color}"></span> {color}</td>
        <td>{sort_order}</td>
        <td><div class="actions-cell">
            <button hx-get="{base_path}/{tag['id']}/edit" hx-target="#issue-tag-{tag['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


@router.get("", response_class=HTMLResponse)
def page(request: Request, project_id: int, issue_id: int, filters: FilterParams = Depends(get_filter_params)):
    proj = get_project_or_404(project_id)
    iss = get_issue_or_404(project_id, issue_id)
    return templates.TemplateResponse(request, "issue_tags.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "filter_params": filters.to_dict(),
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int):
    """タグ一覧取得"""
    get_issue_or_404(project_id, issue_id)
    rows = IssueTagService.get_all(issue_id)
    tbody = "".join(render_row(r, project_id, issue_id) for r in rows)
    return HTMLResponse(f"<tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    tag = IssueTagService.get_by_id(id, issue_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return HTMLResponse(render_row(tag, project_id, issue_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    tag = IssueTagService.get_by_id(id, issue_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return HTMLResponse(render_row(tag, project_id, issue_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int, name: str = Form(...), color: str = Form("#6b7280"), sort_order: int = Form(0)):
    get_issue_or_404(project_id, issue_id)
    tag = IssueTagService.create(issue_id, name, color, sort_order)
    return HTMLResponse(render_row(tag, project_id, issue_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int, name: str = Form(...), color: str = Form("#6b7280"), sort_order: int = Form(0)):
    get_issue_or_404(project_id, issue_id)
    tag = IssueTagService.update(id, issue_id, name, color, sort_order)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return HTMLResponse(render_row(tag, project_id, issue_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    if IssueTagService.is_in_use(id):
        raise HTTPException(status_code=400, detail="このタグは使用中のため削除できません")
    if not IssueTagService.delete(id, issue_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return HTMLResponse("")
