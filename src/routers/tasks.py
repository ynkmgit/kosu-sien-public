"""作業CRUD

責務: HTTPルーティングのみ
データ操作はTaskServiceに委譲
HTML生成はtask_rendererに委譲
"""
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import TaskService, TaskStatusService, IssueTagService, TaskTagService
from .common import templates, get_project_or_404, get_issue_or_404, FilterParams, get_filter_params
from .common.task_renderer import render_row, render_thead, render_totals_row, parse_hours

router = APIRouter(prefix="/projects/{project_id}/issues/{issue_id}/tasks", tags=["tasks"])


@router.get("", response_class=HTMLResponse)
def page(request: Request, project_id: int, issue_id: int, filters: FilterParams = Depends(get_filter_params)):
    proj = get_project_or_404(project_id)
    iss = get_issue_or_404(project_id, issue_id)
    totals = TaskService.get_issue_totals(issue_id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    return templates.TemplateResponse(request, "tasks.html", {
        "active": "projects",
        "project": proj,
        "issue": iss,
        "totals": totals,
        "status_labels": status_labels,
        "filter_params": filters.to_dict(),
    })


@router.get("/list", response_class=HTMLResponse)
def list_all(project_id: int, issue_id: int):
    """作業一覧取得"""
    get_issue_or_404(project_id, issue_id)
    rows = TaskService.get_all_with_actuals(issue_id)
    totals = TaskService.get_issue_totals(issue_id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    all_tags = IssueTagService.get_all(issue_id)
    tags_map = TaskTagService.get_task_tags_map(issue_id)
    tbody = "".join(
        render_row(r, project_id, issue_id, status_labels,
                   task_tags=tags_map.get(r['id'], []), all_tags=all_tags)
        for r in rows
    )
    tbody += render_totals_row(totals)
    thead = render_thead(project_id, issue_id)
    return HTMLResponse(f"<thead>{thead}</thead><tbody>{tbody}</tbody>")


@router.get("/{id}/row", response_class=HTMLResponse)
def get_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id_with_actuals(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.get("/{id}/edit", response_class=HTMLResponse)
def edit_row(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    t = TaskService.get_by_id_with_actuals(id)
    if not t or t['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags, editing=True))


@router.post("", response_class=HTMLResponse)
def create(project_id: int, issue_id: int,
           cd: str = Form(...),
           name: str = Form(...),
           estimate_hours: str = Form(""),
           status: str = Form("open")):
    get_issue_or_404(project_id, issue_id)
    try:
        t = TaskService.create(
            issue_id=issue_id,
            cd=cd,
            name=name,
            estimate_hours=parse_hours(estimate_hours),
            status=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # actual_hoursを追加（新規なので0）
    t['actual_hours'] = 0
    status_labels = TaskStatusService.get_status_labels(issue_id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=[], all_tags=all_tags))


@router.put("/{id}", response_class=HTMLResponse)
def update(project_id: int, issue_id: int, id: int,
           cd: str = Form(...),
           name: str = Form(...),
           estimate_hours: str = Form(""),
           status: str = Form("open")):
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        TaskService.update(
            task_id=id,
            cd=cd,
            name=name,
            estimate_hours=parse_hours(estimate_hours),
            status=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # 実績付きで再取得
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.put("/{id}/status", response_class=HTMLResponse)
def update_status(project_id: int, issue_id: int, id: int, status: str = Form(...)):
    """ステータスのみ更新"""
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskService.update_status(id, status)
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.put("/{id}/tags/{tag_id}", response_class=HTMLResponse)
def toggle_tag(project_id: int, issue_id: int, id: int, tag_id: int):
    """タグ付与/解除トグル"""
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskTagService.toggle(id, tag_id)
    t = TaskService.get_by_id_with_actuals(id)
    status_labels = TaskStatusService.get_status_labels(issue_id)
    task_tags = TaskTagService.get_tags_for_task(id)
    all_tags = IssueTagService.get_all(issue_id)
    return HTMLResponse(render_row(t, project_id, issue_id, status_labels, task_tags=task_tags, all_tags=all_tags))


@router.delete("/{id}", response_class=HTMLResponse)
def delete(project_id: int, issue_id: int, id: int):
    get_issue_or_404(project_id, issue_id)
    existing = TaskService.get_by_id(id)
    if not existing or existing['issue_id'] != issue_id:
        raise HTTPException(status_code=404, detail="Task not found")
    TaskService.delete(id)
    return HTMLResponse("")


# 作業インライン更新用ルーター（/tasks/{id}/estimate, /tasks/{id}/status）
task_progress_router = APIRouter(prefix="/tasks", tags=["task_progress"])


@task_progress_router.put("/{task_id}/estimate", response_class=HTMLResponse)
def update_estimate_inline(task_id: int, estimate_hours: str = Form(default="")):
    """見積工数更新（グリッドインライン編集用）"""
    value = parse_hours(estimate_hours) if estimate_hours else None
    try:
        if not TaskService.update_estimate(task_id, value):
            raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return HTMLResponse("")


@task_progress_router.put("/{task_id}/status", response_class=HTMLResponse)
def update_task_status_light(task_id: int, status: str = Form(...)):
    """作業ステータス軽量更新（グリッド用）"""
    if not TaskService.update_status(task_id, status):
        raise HTTPException(status_code=404, detail="Task not found")
    return HTMLResponse("")
