"""案件CRUD

責務: HTTPルーティングのみ
データ操作はIssueServiceに委譲
HTML生成はissue_rendererに委譲
"""
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse
from services import IssueService
from .common import get_project_or_404
from .common.issue_renderer import render_row, render_thead

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["issues"])


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, sort: str = "cd", order: str = "asc", q: str = ""):
    """案件一覧取得（検索・ソート対応）"""
    get_project_or_404(project_id)
    # 1クエリで案件+見積合計+実績合計を取得
    rows = IssueService.get_all_with_totals(project_id=project_id, sort=sort, order=order, q=q)
    status_labels = IssueService.get_status_labels(project_id)
    tbody = "".join(render_row(r, project_id, status_labels, r['estimate_total'], r['actual_total']) for r in rows)
    thead = render_thead(sort, order, project_id)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, id: int):
    get_project_or_404(project_id)
    i = IssueService.get_by_id(id)
    if not i or i['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, id: int):
    get_project_or_404(project_id)
    i = IssueService.get_by_id(id)
    if not i or i['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, cd: str = Form(...), name: str = Form(...), status: str = Form("open")):
    get_project_or_404(project_id)
    i = IssueService.create(project_id=project_id, cd=cd, name=name, status=status)
    status_labels = IssueService.get_status_labels(project_id)
    return HTMLResponse(render_row(i, project_id, status_labels, 0))  # 新規作成時は見積0


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, id: int, cd: str = Form(...), name: str = Form(...), status: str = Form("open")):
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    i = IssueService.update(issue_id=id, cd=cd, name=name, status=status)
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.put("/{id}/status", response_class=HTMLResponse)
def update_status(project_id: int, id: int, status: str = Form(...)):
    """ステータスのみ更新"""
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    # 既存の値を保持してステータスのみ更新
    i = IssueService.update(issue_id=id, cd=existing['cd'], name=existing['name'], status=status)
    status_labels = IssueService.get_status_labels(project_id)
    estimate_total = IssueService.get_estimate_total(id)
    actual_total = IssueService.get_actual_total(id)
    return HTMLResponse(render_row(i, project_id, status_labels, estimate_total, actual_total))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, id: int):
    get_project_or_404(project_id)
    # 案件がこのprojectに属しているか確認
    existing = IssueService.get_by_id(id)
    if not existing or existing['project_id'] != project_id:
        raise HTTPException(status_code=404, detail="Issue not found")
    IssueService.delete(id)
    return HTMLResponse("")
