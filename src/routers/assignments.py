"""アサイン管理

責務: HTML生成 + HTTPルーティングのみ
グリッドレンダリングはassignment_grid_rendererに委譲
"""
from datetime import datetime

from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from services import TaskAssigneeService, TaskMonthlyPlanService, WorkLogService, TaskTagService, TaskStatusService
from .common import templates, FilterParams, get_filter_params
from .common.filters import render_common_filter_groups, render_assignment_month_nav
from .common.assignment_grid_renderer import render_assignment_grid, render_task_block, render_empty_sub_row
from .common.grid_data import load_grid_context

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _get_months(count: int = 7, base_month: str = None) -> list[str]:
    """基準月から指定月数分のYYYY-MMリストを生成"""
    if base_month:
        year, month = int(base_month[:4]), int(base_month[5:7])
    else:
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
                            exclude_done_issue, exclude_done_task,
                            base_month: str = None) -> str:
    """フィルターセクション生成"""
    common_groups = render_common_filter_groups(
        users, projects, issues, tags, selected_users, selected_projects, selected_issues, selected_tags,
        issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses,
        exclude_done_issue, exclude_done_task
    )
    month_nav = render_assignment_month_nav(base_month)
    return f'''<div class="filter-section">
        <div class="filter-row">{common_groups}{month_nav}</div>
    </div>'''


def _refresh_grid(filters: FilterParams, base_month: str = None) -> HTMLResponse:
    """フィルター+グリッドHTMLを生成して返す（共通処理）"""
    ctx = load_grid_context(filters, include_unassigned=True)

    filter_html = _render_filter_section(
        ctx.users, ctx.projects, ctx.issues, ctx.all_tags,
        filters.user, filters.project, filters.issue, filters.tag,
        ctx.issue_statuses, ctx.task_statuses_all,
        filters.issue_status, filters.task_status,
        filters.exclude_done_issue, filters.exclude_done_task,
        base_month
    )

    months = _get_months(7, base_month)

    plans = TaskMonthlyPlanService.get_plans_for_months(months)
    plan_totals = TaskMonthlyPlanService.get_plan_totals()
    grid_html = render_assignment_grid(months, ctx.rows, ctx.tags_map, ctx.status_labels_map, ctx.task_status_labels_map, plans, plan_totals)

    return HTMLResponse(filter_html + grid_html)


@router.get("", response_class=HTMLResponse)
def page(request: Request, filters: FilterParams = Depends(get_filter_params), base_month: str = None):
    """アサイン管理ページ"""
    return templates.TemplateResponse(request, "assignments.html", {
        "active": "assignments",
        "selected_users": filters.user, "selected_projects": filters.project,
        "selected_issues": filters.issue, "selected_tags": filters.tag,
        "selected_issue_statuses": filters.issue_status, "selected_task_statuses": filters.task_status,
        "exclude_done_issue": filters.exclude_done_issue, "exclude_done_task": filters.exclude_done_task,
        "filter_params": filters.to_dict(),
        "base_month": base_month or "",
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(filters: FilterParams = Depends(get_filter_params), base_month: str = None):
    """グリッド取得"""
    return _refresh_grid(filters, base_month)


def _render_task_block_html(task_id: int, months: list[str]) -> str:
    """単一タスクの task-row + サブ行群の HTML を返す"""
    rows = WorkLogService.get_assignee_rows(include_unassigned=True)
    task_rows = [r for r in rows if r['task_id'] == task_id]
    if not task_rows:
        return ''

    issue_ids = list({r['issue_id'] for r in task_rows})
    tags_map = TaskTagService.get_task_tags_map_bulk(issue_ids)
    task_status_labels_map = TaskStatusService.get_status_labels_bulk(issue_ids)
    plans = TaskMonthlyPlanService.get_plans_for_months(months)
    plan_totals = TaskMonthlyPlanService.get_plan_totals()

    iid = task_rows[0]['issue_id']
    return render_task_block(
        task_rows, months, plans, plan_totals,
        tags_map, task_status_labels_map.get(iid, {})
    )


@router.post("/assignees")
def add_assignee(
    task_id: int = Form(...),
    user_id: int = Form(...),
    base_month: str = Form(default=None),
):
    """担当者を追加し、更新後のタスクブロック HTML を返す"""
    user = TaskAssigneeService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    if user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーには割当できません")

    existing = TaskAssigneeService.get_assignment(task_id, user_id)
    if not existing:
        TaskAssigneeService.create(task_id, user_id)

    months = _get_months(7, base_month)
    html = _render_task_block_html(task_id, months)
    return HTMLResponse(html)


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
def remove_assignee(assignee_id: int, base_month: str = None):
    """担当者を削除し、更新後のタスクブロック HTML を返す"""
    assignment = TaskAssigneeService.get_assignment_by_id(assignee_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="割当が見つかりません")

    task_id = assignment['task_id']
    TaskAssigneeService.delete(assignee_id)

    months = _get_months(7, base_month)
    html = _render_task_block_html(task_id, months)
    return HTMLResponse(html)


@router.post("/tasks/{task_id}/add-row")
def add_empty_sub_row(task_id: int, base_month: str = Form(default=None)):
    """空の担当者サブ行 HTML を返す（マルチモード時の＋ボタン用）"""
    rows = WorkLogService.get_assignee_rows(include_unassigned=True)
    task_rows = [r for r in rows if r['task_id'] == task_id]
    if not task_rows:
        raise HTTPException(status_code=404, detail="作業が見つかりません")

    row = task_rows[0]
    months = _get_months(7, base_month)
    html = render_empty_sub_row(task_id, row['project_id'], row['issue_id'], months)
    return HTMLResponse(html)
