"""アサイン管理

責務: HTML生成 + HTTPルーティングのみ
グリッドレンダリングはassignment_grid_rendererに委譲
"""
from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from services import WorkLogService, UserService, ProjectService, IssueService, TaskStatusService, TaskTagService, IssueTagService, StatusService, TaskAssigneeService, TaskMonthlyPlanService
from .common import templates, FilterParams, get_filter_params
from .common.filters import collect_unique_issue_statuses, collect_unique_task_statuses, render_common_filter_groups
from .common.assignment_grid_renderer import render_assignment_grid

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _get_months(count: int = 7) -> list[str]:
    """当月から指定月数分のYYYY-MMリストを生成"""
    now = datetime.now()
    year, month = now.year, now.month
    months = []
    for _ in range(count):
        months.append(f"{year}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _render_filter_section(users, projects, issues, tags,
                            selected_users, selected_projects, selected_issues, selected_tags,
                            issue_statuses, task_statuses_all,
                            selected_issue_statuses, selected_task_statuses,
                            exclude_done_issue, exclude_done_task) -> str:
    """フィルターセクション生成"""
    common_groups = render_common_filter_groups(
        users, projects, issues, tags, selected_users, selected_projects, selected_issues, selected_tags,
        issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses,
        exclude_done_issue, exclude_done_task
    )
    return f'''<div class="filter-section">
        <div class="filter-row">{common_groups}</div>
    </div>'''


def _refresh_grid(filters: FilterParams) -> HTMLResponse:
    """フィルター+グリッドHTMLを生成して返す（共通処理）"""
    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    issues = IssueService.get_list()
    all_tags = IssueTagService.get_list()

    issue_statuses = collect_unique_issue_statuses(projects)
    task_statuses_all = collect_unique_task_statuses(issues)

    issue_status_codes = StatusService.resolve_ids_to_codes(filters.issue_status) if filters.issue_status else None
    task_status_codes = TaskStatusService.resolve_ids_to_codes(filters.task_status) if filters.task_status else None

    rows = WorkLogService.get_assignee_rows(
        filters.user or None, filters.project or None, filters.issue or None, filters.tag or None,
        issue_status_codes, task_status_codes, filters.exclude_done_issue, filters.exclude_done_task,
        include_unassigned=True
    )

    filter_html = _render_filter_section(
        users, projects, issues, all_tags,
        filters.user, filters.project, filters.issue, filters.tag,
        issue_statuses, task_statuses_all,
        filters.issue_status, filters.task_status,
        filters.exclude_done_issue, filters.exclude_done_task
    )

    months = _get_months(7)

    # タグ・ステータスラベル取得
    issue_ids = list({r['issue_id'] for r in rows})
    tags_map: dict[int, list[dict]] = {}
    for iid in issue_ids:
        tags_map.update(TaskTagService.get_task_tags_map(iid))
    project_ids = list({r['project_id'] for r in rows})
    status_labels_map = {pid: IssueService.get_status_labels(pid) for pid in project_ids}
    task_status_labels_map = {iid: TaskStatusService.get_status_labels(iid) for iid in issue_ids}

    plans = TaskMonthlyPlanService.get_plans_for_months(months)
    plan_totals = TaskMonthlyPlanService.get_plan_totals()
    grid_html = render_assignment_grid(months, rows, tags_map, status_labels_map, task_status_labels_map, plans, plan_totals)

    return HTMLResponse(filter_html + grid_html)


@router.get("", response_class=HTMLResponse)
def page(request: Request, filters: FilterParams = Depends(get_filter_params)):
    """アサイン管理ページ"""
    return templates.TemplateResponse(request, "assignments.html", {
        "active": "assignments",
        "selected_users": filters.user, "selected_projects": filters.project,
        "selected_issues": filters.issue, "selected_tags": filters.tag,
        "selected_issue_statuses": filters.issue_status, "selected_task_statuses": filters.task_status,
        "exclude_done_issue": filters.exclude_done_issue, "exclude_done_task": filters.exclude_done_task,
        "filter_params": filters.to_dict(),
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(filters: FilterParams = Depends(get_filter_params)):
    """グリッド取得"""
    return _refresh_grid(filters)


@router.post("/assignees")
def add_assignee(
    task_id: int = Form(...),
    user_id: int = Form(...),
):
    """担当者を追加（JSON応答）"""
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    if user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")

    existing = TaskAssigneeService.get_assignment(task_id, user_id)
    if existing:
        return JSONResponse({"assignee_id": existing['id'], "user_name": user['name'], "user_cd": user['cd']})

    assignee_id = TaskAssigneeService.create(task_id, user_id)
    return JSONResponse({"assignee_id": assignee_id, "user_name": user['name'], "user_cd": user['cd']})


@router.post("/plans")
def upsert_plan(
    task_id: int = Form(...),
    user_id: int = Form(...),
    year_month: str = Form(...),
    planned_hours: float = Form(...),
):
    """山積工数を保存（htmx hx-swap="none"）"""
    TaskMonthlyPlanService.upsert(task_id, user_id, year_month, planned_hours)
    return Response(status_code=204)


@router.put("/assignees/{assignee_id}/progress")
def update_assignee_progress(assignee_id: int, progress_rate: Optional[int] = Form(default=None)):
    """担当者の進捗率を更新"""
    value = None if progress_rate is None or progress_rate == 0 else progress_rate
    try:
        if not TaskAssigneeService.update_progress(assignee_id, value):
            raise HTTPException(status_code=404, detail="割当が見つかりません")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(status_code=204)


@router.delete("/assignees/{assignee_id}")
def remove_assignee(assignee_id: int):
    """担当者を削除（204応答）"""
    assignment = TaskAssigneeService.get_assignment_by_id(assignee_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="割当が見つかりません")

    TaskAssigneeService.delete(assignee_id)
    return Response(status_code=204)
