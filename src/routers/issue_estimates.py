"""案件見積内訳CRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はIssueEstimateServiceに委譲
"""
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import IssueEstimateService
from .common import templates, get_project_or_404, get_issue_or_404, render_edit_actions

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/estimates", tags=["issue_estimates"])


def render_row(item, project_id: int, issue_id: int, editing=False):
    """見積内訳行HTML生成"""
    name = escape(item['name'])
    hours = item['hours'] or 0

    if editing:
        base_path = f"/projects/{project_id}/issues/{issue_id}/estimates"
        return f"""
        <tr id="estimate-{item['id']}" style="background: rgba(212, 165, 116, 0.08);">
            <td><input type="text" name="name" value="{name}" class="edit-input" required></td>
            <td><input type="number" name="hours" value="{hours}" class="edit-input" step="0.25" min="0.25" required></td>
            <td>{render_edit_actions("estimate", item['id'], base_path)}</td>
        </tr>"""

    return f"""
    <tr id="estimate-{item['id']}">
        <td class="name-cell">{name}</td>
        <td class="hours-cell">{hours:.2f}</td>
        <td><div class="actions-cell">
            <button hx-get="/projects/{project_id}/issues/{issue_id}/estimates/{item['id']}/edit" hx-target="#estimate-{item['id']}" hx-swap="outerHTML" class="btn btn-sm btn-ghost">編集</button>
        </div></td>
    </tr>"""


def render_total_row(total: float):
    """合計行HTML生成"""
    return f"""
    <tr class="total-row">
        <td>合計</td>
        <td class="hours-cell">{total:.2f}</td>
        <td></td>
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
    return templates.TemplateResponse(request, "issue_estimates.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "filter_params": filter_params,
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int):
    """見積内訳一覧取得"""
    get_issue_or_404(project_id, issue_id)
    rows = IssueEstimateService.get_all(issue_id)
    total = IssueEstimateService.get_total(issue_id)

    tbody = "".join(render_row(r, project_id, issue_id) for r in rows)
    tbody += render_total_row(total)
    thead = """<tr>
        <th class="col-pct-60">項目名</th>
        <th class="col-pct-20">工数(h)</th>
        <th class="col-pct-20">操作</th>
    </tr>"""
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    item = IssueEstimateService.get_by_id(id, issue_id)
    if not item:
        raise HTTPException(status_code=404, detail="Estimate item not found")
    return HTMLResponse(render_row(item, project_id, issue_id))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    item = IssueEstimateService.get_by_id(id, issue_id)
    if not item:
        raise HTTPException(status_code=404, detail="Estimate item not found")
    return HTMLResponse(render_row(item, project_id, issue_id, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int, name: str = Form(...), hours: float = Form(...)):
    get_issue_or_404(project_id, issue_id)
    try:
        item = IssueEstimateService.create(issue_id, name, hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return HTMLResponse(render_row(item, project_id, issue_id))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int, name: str = Form(...), hours: float = Form(...)):
    get_issue_or_404(project_id, issue_id)
    try:
        item = IssueEstimateService.update(id, issue_id, name, hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not item:
        raise HTTPException(status_code=404, detail="Estimate item not found")
    return HTMLResponse(render_row(item, project_id, issue_id))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    if not IssueEstimateService.delete(id, issue_id):
        raise HTTPException(status_code=404, detail="Estimate item not found")
    return HTMLResponse("")
