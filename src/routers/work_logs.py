"""実績入力CRUD

責務: HTML生成 + HTTPルーティングのみ
実績のupsert/deleteはWorkLogServiceに委譲
グリッドレンダリングはgrid_rendererに委譲
"""
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from services import WorkLogService, UserService, ProjectService, IssueService, TaskStatusService, TaskTagService, IssueTagService, StatusService
from .common import (
    templates, get_current_month, parse_month, get_month_dates, get_prev_next_month,
    get_week_dates, get_prev_next_week, get_week_range_str, parse_week_date, WEEKDAY_NAMES,
    render_view_toggle,
    FilterParams, get_filter_params
)
from .common.filters import collect_unique_issue_statuses, collect_unique_task_statuses, render_common_filter_groups
from .common.grid_renderer import render_grid

router = APIRouter(prefix="/work-logs", tags=["work_logs"])


def _render_filter_groups_with_view(users, projects, issues, tags,
                                    selected_users, selected_projects, selected_issues, selected_tags,
                                    issue_statuses, task_statuses_all,
                                    selected_issue_statuses, selected_task_statuses,
                                    exclude_done_issue, exclude_done_task, view: str) -> str:
    """共通フィルター + 表示切替"""
    common = render_common_filter_groups(
        users, projects, issues, tags, selected_users, selected_projects, selected_issues, selected_tags,
        issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses,
        exclude_done_issue, exclude_done_task
    )
    view_group = f'''<div class="filter-group">
        <label class="filter-label">表示</label>
        {render_view_toggle(view)}
    </div>'''
    return f"{common}{view_group}"


def render_filter(users, projects, issues, tags,
                   selected_users: list[int], selected_projects: list[int], selected_issues: list[int], selected_tags: list[int],
                   issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses,
                   exclude_done_issue, exclude_done_task, year_month: str):
    """月表示用フィルターUI生成"""
    prev_month, next_month = get_prev_next_month(year_month)
    common_groups = _render_filter_groups_with_view(users, projects, issues, tags, selected_users, selected_projects, selected_issues, selected_tags,
                                          issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses, exclude_done_issue, exclude_done_task, "month")

    month_nav = f'''<div class="filter-group">
        <label class="filter-label">月</label>
        <div class="month-nav">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeMonth('{prev_month}')">←</button>
            <input type="month" class="month-input" value="{year_month}" onchange="changeMonth(this.value)">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeMonth('{next_month}')">→</button>
        </div>
    </div>'''

    return f'''<div class="filter-section">
        <div class="filter-row">{common_groups}{month_nav}</div>
    </div>'''


def render_week_filter(users, projects, issues, tags,
                        selected_users: list[int], selected_projects: list[int], selected_issues: list[int], selected_tags: list[int],
                        issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses,
                        exclude_done_issue, exclude_done_task, week_dates: list[date]):
    """週表示用フィルターUI生成"""
    target_date = week_dates[0]
    prev_monday, next_monday = get_prev_next_week(target_date)
    today = date.today()
    today_monday = today - timedelta(days=today.weekday())
    week_range = get_week_range_str(week_dates)
    common_groups = _render_filter_groups_with_view(users, projects, issues, tags, selected_users, selected_projects, selected_issues, selected_tags,
                                          issue_statuses, task_statuses_all, selected_issue_statuses, selected_task_statuses, exclude_done_issue, exclude_done_task, "week")

    week_nav = f'''<div class="filter-group">
        <label class="filter-label">週</label>
        <div class="week-nav">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeWeek('{prev_monday.isoformat()}')">◀</button>
            <span class="week-range">{week_range}</span>
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeWeek('{next_monday.isoformat()}')">▶</button>
            <button type="button" class="btn btn-ghost btn-sm ml-sm" onclick="changeWeek('{today_monday.isoformat()}')">今週</button>
        </div>
    </div>'''

    return f'''<div class="filter-section">
        <div class="filter-row">{common_groups}{week_nav}</div>
    </div>'''


@router.get("", response_class=HTMLResponse)
def page(request: Request, filters: FilterParams = Depends(get_filter_params), month: str = None, week: str = None, view: str = "week"):
    """実績入力ページ"""
    if view not in ("week", "month"):
        view = "week"

    if view == "week":
        target_date = parse_week_date(week) if week else date.today()
        week_start = get_week_dates(target_date)[0].isoformat()
        year_month = None
    else:
        year_month = parse_month(month) if month else get_current_month()
        week_start = None

    return templates.TemplateResponse(request, "work_logs.html", {
        "active": "work_logs", "view": view,
        "year_month": year_month, "week_start": week_start,
        "selected_users": filters.user, "selected_projects": filters.project, "selected_issues": filters.issue, "selected_tags": filters.tag,
        "selected_issue_statuses": filters.issue_status, "selected_task_statuses": filters.task_status,
        "exclude_done_issue": filters.exclude_done_issue, "exclude_done_task": filters.exclude_done_task,
        "filter_params": filters.to_dict(),
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(filters: FilterParams = Depends(get_filter_params), month: str = None, week: str = None, view: str = "week"):
    """グリッド取得"""
    if view not in ("week", "month"):
        view = "week"

    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    issues = IssueService.get_list()
    all_tags = IssueTagService.get_list()

    # ステータス選択肢を全プロジェクト・全案件から収集（重複排除、ID付き）
    issue_statuses = collect_unique_issue_statuses(projects)
    task_statuses_all = collect_unique_task_statuses(issues)

    # ステータスIDをコードに変換してサービスに渡す
    issue_status_codes = StatusService.resolve_ids_to_codes(filters.issue_status) if filters.issue_status else None
    task_status_codes = TaskStatusService.resolve_ids_to_codes(filters.task_status) if filters.task_status else None

    rows = WorkLogService.get_assignee_rows(
        filters.user or None, filters.project or None, filters.issue or None, filters.tag or None,
        issue_status_codes, task_status_codes, filters.exclude_done_issue, filters.exclude_done_task
    )

    filter_args = (users, projects, issues, all_tags,
                   filters.user, filters.project, filters.issue, filters.tag,
                   issue_statuses, task_statuses_all,
                   filters.issue_status, filters.task_status,
                   filters.exclude_done_issue, filters.exclude_done_task)

    if view == "week":
        dates = get_week_dates(parse_week_date(week) if week else date.today())
        filter_html = render_week_filter(*filter_args, dates)
    else:
        year_month = parse_month(month) if month else get_current_month()
        dates = get_month_dates(year_month)
        filter_html = render_filter(*filter_args, year_month)

    work_logs = WorkLogService.get_work_logs_for_dates(
        dates,
        filters.user if filters.user else None,
        filters.project if filters.project else None,
        filters.issue if filters.issue else None
    )
    # 作業タグを一括取得
    issue_ids = list({r['issue_id'] for r in rows})
    tags_map: dict[int, list[dict]] = {}
    for iid in issue_ids:
        tags_map.update(TaskTagService.get_task_tags_map(iid))
    # ステータスラベルを一括取得
    project_ids = list({r['project_id'] for r in rows})
    status_labels_map = {pid: IssueService.get_status_labels(pid) for pid in project_ids}
    task_status_labels_map = {iid: TaskStatusService.get_status_labels(iid) for iid in issue_ids}
    grid_html = render_grid(dates, rows, work_logs, view, tags_map, status_labels_map, task_status_labels_map)

    return HTMLResponse(filter_html + grid_html)


@router.post("", response_class=HTMLResponse)
def upsert_work_log(
    task_id: int = Form(...),
    user_id: int = Form(...),
    work_date: str = Form(...),
    hours: float = Form(...)
):
    """実績追加/更新"""
    # 日付検証
    try:
        parsed_date = datetime.strptime(work_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        WorkLogService.upsert(
            task_id=task_id,
            user_id=user_id,
            work_date=parsed_date,
            hours=hours
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return HTMLResponse("")


@router.put("/issue-status/{issue_id}", response_class=HTMLResponse)
def update_issue_status(issue_id: int, status: str = Form(...)):
    """案件ステータス軽量更新（グリッド用）"""
    existing = IssueService.get_by_id(issue_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Issue not found")
    IssueService.update(issue_id=issue_id, cd=existing['cd'], name=existing['name'], status=status)
    return HTMLResponse("")


@router.delete("/{id}", response_class=HTMLResponse)
def delete_work_log(id: int):
    """実績削除"""
    if not WorkLogService.delete(id):
        raise HTTPException(status_code=404, detail="Work log not found")
    return HTMLResponse("")
