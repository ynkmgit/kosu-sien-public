"""実績入力CRUD

責務: HTML生成 + HTTPルーティングのみ
実績のupsert/deleteはWorkLogServiceに委譲
"""
import calendar
from datetime import datetime, date, timedelta
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import WorkLogService, UserService, ProjectService, IssueService
from .common import (
    templates, get_current_month, parse_month, get_prev_next_month,
    get_week_dates, get_prev_next_week, get_week_range_str, parse_week_date, WEEKDAY_NAMES,
    render_filter_tags, render_autocomplete_filter_group, render_view_toggle,
    render_log_cell, render_progress_cell, render_row_label
)

router = APIRouter(prefix="/work-logs", tags=["work_logs"])


def get_month_dates(year_month: str) -> list[date]:
    """指定月の全日付リストを取得"""
    dt = datetime.strptime(year_month, "%Y-%m")
    year, month = dt.year, dt.month
    _, last_day = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last_day + 1)]


def render_filter(users, projects, issues, selected_users: list[int], selected_projects: list[int], selected_issues: list[int], year_month: str):
    """月表示用フィルターUI生成"""
    prev_month, next_month = get_prev_next_month(year_month)

    user_group = render_autocomplete_filter_group(
        "ユーザー",
        render_filter_tags(users, selected_users, "user"),
        "user",
        "ユーザーを検索..."
    )
    project_group = render_autocomplete_filter_group(
        "プロジェクト",
        render_filter_tags(projects, selected_projects, "project"),
        "project",
        "プロジェクトを検索..."
    )
    issue_group = render_autocomplete_filter_group(
        "案件",
        render_filter_tags(issues, selected_issues, "issue"),
        "issue",
        "案件を検索..."
    )
    view_group = f'''<div class="filter-group">
        <label class="filter-label">表示</label>
        {render_view_toggle("month")}
    </div>'''
    month_nav = f'''<div class="filter-group">
        <label class="filter-label">月</label>
        <div class="month-nav">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeMonth('{prev_month}')">←</button>
            <input type="month" class="month-input" value="{year_month}" onchange="changeMonth(this.value)">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeMonth('{next_month}')">→</button>
        </div>
    </div>'''

    return f'''<div class="filter-section">
        <div class="filter-row">{user_group}{project_group}{issue_group}{view_group}{month_nav}</div>
    </div>'''


def render_week_filter(users, projects, issues, selected_users: list[int], selected_projects: list[int], selected_issues: list[int], week_dates: list[date]):
    """週表示用フィルターUI生成"""
    target_date = week_dates[0]
    prev_monday, next_monday = get_prev_next_week(target_date)
    today = date.today()
    today_monday = today - timedelta(days=today.weekday())
    week_range = get_week_range_str(week_dates)

    user_group = render_autocomplete_filter_group(
        "ユーザー",
        render_filter_tags(users, selected_users, "user"),
        "user",
        "ユーザーを検索..."
    )
    project_group = render_autocomplete_filter_group(
        "プロジェクト",
        render_filter_tags(projects, selected_projects, "project"),
        "project",
        "プロジェクトを検索..."
    )
    issue_group = render_autocomplete_filter_group(
        "案件",
        render_filter_tags(issues, selected_issues, "issue"),
        "issue",
        "案件を検索..."
    )
    view_group = f'''<div class="filter-group">
        <label class="filter-label">表示</label>
        {render_view_toggle("week")}
    </div>'''
    week_nav = f'''<div class="filter-group">
        <label class="filter-label">週</label>
        <div class="week-nav">
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeWeek('{prev_monday.isoformat()}')">◀</button>
            <span class="week-range">{week_range}</span>
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeWeek('{next_monday.isoformat()}')">▶</button>
            <button type="button" class="btn btn-ghost btn-sm" onclick="changeWeek('{today_monday.isoformat()}')" style="margin-left: 8px;">今週</button>
        </div>
    </div>'''

    return f'''<div class="filter-section">
        <div class="filter-row">{user_group}{project_group}{issue_group}{view_group}{week_nav}</div>
    </div>'''


def calculate_totals(
    rows: list[dict],
    dates: list[date],
    work_logs: dict
) -> tuple[dict, dict]:
    """プロジェクト・案件別の集計を計算

    責務: 集計計算のみ（単一目的）

    Args:
        rows: 担当割当の行データ
        dates: 日付リスト
        work_logs: {(task_id, user_id, date_str): {id, hours}}

    Returns:
        project_totals: {project_id: {date_str: hours, "total": hours}}
        issue_totals: {(project_id, issue_id): {date_str: hours, "total": hours}}
    """
    project_totals = {}
    issue_totals = {}

    for row in rows:
        pid = row['project_id']
        iid = row['issue_id']

        # プロジェクト集計の初期化
        if pid not in project_totals:
            project_totals[pid] = {d.isoformat(): 0.0 for d in dates}
            project_totals[pid]["total"] = 0.0

        # 案件集計の初期化
        key = (pid, iid)
        if key not in issue_totals:
            issue_totals[key] = {d.isoformat(): 0.0 for d in dates}
            issue_totals[key]["total"] = 0.0

        # 各日付の実績を集計
        for d in dates:
            date_str = d.isoformat()
            log = work_logs.get((row['task_id'], row['user_id'], date_str))
            hours = log['hours'] if log else 0
            project_totals[pid][date_str] += hours
            project_totals[pid]["total"] += hours
            issue_totals[key][date_str] += hours
            issue_totals[key]["total"] += hours

    return project_totals, issue_totals


def _get_date_cell_class(index: int, d: date, today: date, is_week: bool) -> str:
    """日付セルの追加クラスを取得"""
    if not is_week:
        return ""
    extra = ""
    if index >= 5:
        extra += " weekend-cell"
    if d == today:
        extra += " today-cell"
    return extra


def _render_grid_header(dates: list[date], is_week: bool, today: date) -> str:
    """グリッドヘッダー行を生成"""
    date_headers = ""
    for i, d in enumerate(dates):
        if is_week:
            extra = _get_date_cell_class(i, d, today, is_week).replace("-cell", "-header")
            date_headers += f'<th class="date-header weekday-header{extra}">{WEEKDAY_NAMES[i]}<br>{d.month}/{d.day}</th>'
        else:
            date_headers += f'<th class="date-header">{d.day}</th>'

    total_label = "週計" if is_week else "合計"
    return f'''<tr>
        <th class="row-header">PJ / 案件 / 作業 / 担当</th>
        <th class="progress-header">完了%</th>
        {date_headers}
        <th class="total-header">{total_label}</th>
    </tr>'''


def _render_project_row(row: dict, dates: list[date], project_totals: dict, is_week: bool, today: date) -> str:
    """プロジェクト集計行を生成"""
    pid = row['project_id']

    cells = ""
    for i, d in enumerate(dates):
        val = project_totals[pid][d.isoformat()]
        display = f"{val:.2f}" if val > 0 else "-"
        extra = _get_date_cell_class(i, d, today, is_week)
        cells += f'<td class="summary-cell{extra}">{display}</td>'

    total = project_totals[pid]["total"]
    total_display = f"{total:.2f}h" if total > 0 else "-"

    return (
        f'<tr class="project-row" data-project-id="{pid}">'
        f'<td class="project-name">'
        f'<span class="toggle-icon" onclick="toggleProject({pid})">▼</span> {escape(row["project_name"])}'
        f'</td>'
        f'<td></td>'
        f'{cells}'
        f'<td class="row-total project-total">{total_display}</td>'
        f'</tr>'
    )


def _render_issue_row(row: dict, dates: list[date], issue_totals: dict, is_week: bool, today: date) -> str:
    """案件集計行を生成"""
    pid = row['project_id']
    iid = row['issue_id']
    key = (pid, iid)

    cells = ""
    for i, d in enumerate(dates):
        val = issue_totals[key][d.isoformat()]
        display = f"{val:.2f}" if val > 0 else "-"
        extra = _get_date_cell_class(i, d, today, is_week)
        cells += f'<td class="summary-cell{extra}">{display}</td>'

    total = issue_totals[key]["total"]
    total_display = f"{total:.2f}h" if total > 0 else "-"

    return (
        f'<tr class="issue-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<td class="issue-name">'
        f'<span class="toggle-icon" onclick="toggleIssue({pid}, {iid})">▼</span> {escape(row["issue_cd"])} {escape(row["issue_name"])}'
        f'</td>'
        f'<td></td>'
        f'{cells}'
        f'<td class="row-total issue-total">{total_display}</td>'
        f'</tr>'
    )


def _render_log_row(row: dict, dates: list[date], work_logs: dict, is_week: bool, today: date) -> tuple[str, float, dict]:
    """作業入力行を生成

    Returns:
        (html, row_total, date_hours) - HTML、行合計、日付ごとの時間
    """
    pid = row['project_id']
    iid = row['issue_id']

    cells = []
    row_total = 0.0
    date_hours = {}

    for i, d in enumerate(dates):
        date_str = d.isoformat()
        log = work_logs.get((row['task_id'], row['user_id'], date_str))
        hours = log['hours'] if log else 0
        row_total += hours
        date_hours[date_str] = hours

        extra = _get_date_cell_class(i, d, today, is_week)
        cells.append(render_log_cell(row['task_id'], row['user_id'], date_str, hours, extra))

    row_total_display = f"{row_total:.2f}h" if row_total > 0 else "-"

    html = (
        f'<tr class="log-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<td class="row-label">{render_row_label(row["issue_name"], row["task_name"], row["user_name"])}</td>'
        f'{render_progress_cell(row["task_id"], row["progress_rate"])}'
        f'{"".join(cells)}'
        f'<td class="row-total">{row_total_display}</td>'
        f'</tr>'
    )
    return html, row_total, date_hours


def _render_total_row(dates: list[date], date_totals: dict, grand_total: float, is_week: bool, today: date) -> str:
    """列合計行を生成"""
    cells = ""
    for i, d in enumerate(dates):
        val = date_totals[d.isoformat()]
        display = f"{val:.2f}" if val > 0 else "-"
        extra = _get_date_cell_class(i, d, today, is_week)
        cells += f'<td class="col-total{extra}">{display}</td>'

    return f'''<tr class="total-row">
        <td class="total-label">日計</td>
        <td></td>
        {cells}
        <td class="grand-total">{grand_total:.2f}h</td>
    </tr>'''


def render_grid(dates: list[date], rows, work_logs, view: str = "week"):
    """グリッドHTML生成（週/月共通）

    責務: レンダリングのみ（集計・個別行生成は別関数に委譲）
    """
    if not rows:
        return '<p class="empty-message">表示する行がありません。担当割当を行ってください。</p>'

    is_week = view == "week"
    today = date.today()

    # 集計を取得
    project_totals, issue_totals = calculate_totals(rows, dates, work_logs)

    # 一括操作ボタン
    bulk_actions = '''<div class="bulk-actions">
        <button type="button" class="btn btn-ghost btn-sm" onclick="expandAll()">全て展開</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="collapseAll()">全て折り畳み</button>
        <button type="button" class="btn btn-ghost btn-sm" onclick="collapseToIssues()">案件のみ表示</button>
    </div>'''

    # ヘッダー
    header = _render_grid_header(dates, is_week, today)

    # 行を生成
    html_rows = []
    current_project_id = None
    current_issue_id = None
    date_totals = {d.isoformat(): 0.0 for d in dates}
    grand_total = 0.0

    for row in rows:
        pid = row['project_id']
        iid = row['issue_id']

        # プロジェクトヘッダー
        if pid != current_project_id:
            current_project_id = pid
            current_issue_id = None
            html_rows.append(_render_project_row(row, dates, project_totals, is_week, today))

        # 案件ヘッダー
        if iid != current_issue_id:
            current_issue_id = iid
            html_rows.append(_render_issue_row(row, dates, issue_totals, is_week, today))

        # 作業行
        log_html, row_total, date_hours = _render_log_row(row, dates, work_logs, is_week, today)
        html_rows.append(log_html)
        grand_total += row_total
        for date_str, hours in date_hours.items():
            date_totals[date_str] += hours

    # 列合計行
    html_rows.append(_render_total_row(dates, date_totals, grand_total, is_week, today))

    table_class = "log-table week-table" if is_week else "log-table"
    return f'{bulk_actions}<table class="{table_class}"><thead>{header}</thead><tbody>{"".join(html_rows)}</tbody></table>'


@router.get("", response_class=HTMLResponse)
def page(request: Request, user: list[int] = Query(default=[]), project: list[int] = Query(default=[]),
         issue: list[int] = Query(default=[]), month: str = None, week: str = None, view: str = "week"):
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

    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "work_logs.html", {
        "active": "work_logs", "view": view,
        "year_month": year_month, "week_start": week_start,
        "selected_users": user, "selected_projects": project, "selected_issues": issue,
        "filter_params": filter_params,
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(user: list[int] = Query(default=[]), project: list[int] = Query(default=[]),
             issue: list[int] = Query(default=[]), month: str = None, week: str = None, view: str = "week"):
    """グリッド取得"""
    if view not in ("week", "month"):
        view = "week"

    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    issues = IssueService.get_list()
    rows = WorkLogService.get_assignee_rows(user or None, project or None, issue or None)

    if view == "week":
        dates = get_week_dates(parse_week_date(week) if week else date.today())
        filter_html = render_week_filter(users, projects, issues, user, project, issue, dates)
    else:
        year_month = parse_month(month) if month else get_current_month()
        dates = get_month_dates(year_month)
        filter_html = render_filter(users, projects, issues, user, project, issue, year_month)

    work_logs = WorkLogService.get_work_logs_for_dates(dates, user if user else None, project if project else None, issue if issue else None)
    grid_html = render_grid(dates, rows, work_logs, view)

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


@router.delete("/{id}", response_class=HTMLResponse)
def delete_work_log(id: int):
    """実績削除"""
    if not WorkLogService.delete(id):
        raise HTTPException(status_code=404, detail="Work log not found")
    return HTMLResponse("")
