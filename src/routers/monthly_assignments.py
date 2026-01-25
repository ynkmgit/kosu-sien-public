"""月次アサインCRUD

責務: HTML生成 + HTTPルーティングのみ
データ操作はMonthlyAssignmentServiceに委譲
"""
from datetime import datetime
from html import escape

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from services import MonthlyAssignmentService, UserService, ProjectService
from .common import (
    templates, get_current_month, parse_month, get_prev_next_month,
    get_rate_class
)

router = APIRouter(prefix="/monthly-assignments", tags=["monthly_assignments"])


def _render_navigation(year_month: str, mode: str) -> str:
    """ナビゲーションとモード切替ボタン"""
    prev_month, next_month = get_prev_next_month(year_month)
    dt = datetime.strptime(year_month, "%Y-%m")
    month_display = f"{dt.year}年{dt.month}月"

    simple_active = "btn-primary" if mode == "simple" else "btn-ghost"
    detail_active = "btn-primary" if mode == "detail" else "btn-ghost"
    mode_toggle = f'''<div style="display: flex; gap: 8px;">
        <a href="/monthly-assignments?month={year_month}&mode=simple" class="btn {simple_active}" style="font-size: 0.8rem; padding: 4px 12px;">簡易</a>
        <a href="/monthly-assignments?month={year_month}&mode=detail" class="btn {detail_active}" style="font-size: 0.8rem; padding: 4px 12px;">詳細</a>
    </div>'''

    return f'''<div class="grid-nav">
        <a href="/monthly-assignments?month={prev_month}&mode={mode}" class="btn btn-ghost">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            前月
        </a>
        <span class="grid-month">{month_display}</span>
        <a href="/monthly-assignments?month={next_month}&mode={mode}" class="btn btn-ghost">
            翌月
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
        </a>
        {mode_toggle}
    </div>'''


def _render_header(projects) -> str:
    """テーブルヘッダー行"""
    header_cells = "".join(
        f'<th class="project-header">{escape(p["cd"])}</th>' for p in projects
    )
    return f'<tr><th class="user-header">ユーザー</th>{header_cells}<th class="total-header">合計</th></tr>'


def _render_detail_stats(planned: float, actual: float) -> str:
    """詳細モードの予定/実績/残/消化率HTML"""
    planned_display = f"{planned:.1f}h" if planned > 0 else "-"
    actual_display = f"{actual:.1f}h" if actual > 0 else "-"
    if planned > 0:
        remaining = planned - actual
        rate = (actual / planned) * 100
        remaining_display = f"{remaining:.1f}h"
        rate_display = f"{rate:.0f}%"
        remaining_style = ' style="color: var(--danger);"' if remaining < 0 else ""
        rate_class = get_rate_class(rate)
    else:
        remaining_display = "-"
        rate_display = "-"
        remaining_style = ""
        rate_class = ""

    return f'''<div style="font-size: 0.75rem; color: var(--text-muted);">予定</div>
        <div style="font-weight: 500;">{planned_display}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">実績</div>
        <div style="font-weight: 500;">{actual_display}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">残</div>
        <div{remaining_style}>{remaining_display}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">消化率</div>
        <div class="{rate_class}">{rate_display}</div>'''


def _render_simple_cell(user_id: int, project_id: int, planned: float, year_month: str) -> str:
    """簡易モードの入力セル"""
    hours_display = f"{planned:.1f}" if planned > 0 else ""
    mm_display = f"{planned / 160:.2f}MM" if planned > 0 else ""
    return f'''<td class="assign-cell">
        <input type="number" class="assign-input" step="0.25" min="0.25"
               value="{hours_display}"
               data-user-id="{user_id}"
               data-project-id="{project_id}"
               data-year-month="{year_month}"
               hx-post="/monthly-assignments"
               hx-trigger="change"
               hx-vals='js:{{user_id: event.target.dataset.userId, project_id: event.target.dataset.projectId, year_month: event.target.dataset.yearMonth, planned_hours: event.target.value || 0}}'
               hx-swap="none">
        <div class="mm-display">{mm_display}</div>
    </td>'''


def _render_total_row(projects, project_totals: dict, grand_totals: dict, mode: str) -> str:
    """プロジェクト計行"""
    total_cells = []
    for project in projects:
        pt = project_totals[project['id']]
        if mode == "detail":
            planned = pt['planned']
            actual = pt['actual']
            planned_display = f"{planned:.1f}h" if planned > 0 else "-"
            actual_display = f"{actual:.1f}h" if actual > 0 else "-"
            total_cells.append(f'''<td class="col-total" style="padding: 4px 8px; vertical-align: top;">
                <div style="font-size: 0.75rem;">予定: {planned_display}</div>
                <div style="font-size: 0.75rem;">実績: {actual_display}</div>
            </td>''')
        else:
            hours_display = f"{pt['planned']:.1f}h" if pt['planned'] > 0 else "-"
            total_cells.append(f'<td class="col-total">{hours_display}</td>')

    if mode == "detail":
        grand_planned = f"{grand_totals['planned']:.1f}h" if grand_totals['planned'] > 0 else "-"
        grand_actual = f"{grand_totals['actual']:.1f}h" if grand_totals['actual'] > 0 else "-"
        grand_cell = f'''<td class="grand-total" style="padding: 4px 8px; vertical-align: top;">
            <div style="font-size: 0.75rem;">予定: {grand_planned}</div>
            <div style="font-size: 0.75rem;">実績: {grand_actual}</div>
        </td>'''
    else:
        grand_display = f"{grand_totals['planned']:.1f}h" if grand_totals['planned'] > 0 else "-"
        grand_cell = f'<td class="grand-total">{grand_display}</td>'

    return f'''<tr class="total-row">
        <td class="total-label">PJ計</td>
        {"".join(total_cells)}
        {grand_cell}
    </tr>'''


def render_grid(year_month: str, users, projects, assignments, actuals=None, mode: str = "simple"):
    """グリッドHTML生成"""
    if not users:
        return '<p class="empty-message">有効なユーザーがいません</p>'
    if not projects:
        return '<p class="empty-message">プロジェクトがありません</p>'

    if actuals is None:
        actuals = {}

    nav = _render_navigation(year_month, mode)
    header = _render_header(projects)

    # 集計用
    rows = []
    project_totals = {p['id']: {'planned': 0.0, 'actual': 0.0} for p in projects}
    grand_totals = {'planned': 0.0, 'actual': 0.0}

    # ユーザー行生成
    for user in users:
        cells = []
        user_totals = {'planned': 0.0, 'actual': 0.0}

        for project in projects:
            assignment = assignments.get((user['id'], project['id']))
            planned = assignment['hours'] if assignment else 0
            actual = actuals.get((user['id'], project['id']), 0)
            user_totals['planned'] += planned
            user_totals['actual'] += actual
            project_totals[project['id']]['planned'] += planned
            project_totals[project['id']]['actual'] += actual

            if mode == "detail":
                cells.append(f'<td class="assign-cell" style="padding: 4px 8px; vertical-align: top; min-width: 80px;">{_render_detail_stats(planned, actual)}</td>')
            else:
                cells.append(_render_simple_cell(user['id'], project['id'], planned, year_month))

        grand_totals['planned'] += user_totals['planned']
        grand_totals['actual'] += user_totals['actual']

        if mode == "detail":
            row_total = f'<td class="row-total" style="padding: 4px 8px; vertical-align: top;">{_render_detail_stats(user_totals["planned"], user_totals["actual"])}</td>'
        else:
            mm_total = f"{user_totals['planned'] / 160:.2f}MM" if user_totals['planned'] > 0 else ""
            hours_total = f"{user_totals['planned']:.1f}h" if user_totals['planned'] > 0 else "-"
            row_total = f'<td class="row-total"><div class="total-hours">{hours_total}</div><div class="total-mm">{mm_total}</div></td>'

        rows.append(f'''<tr class="user-row">
            <td class="user-name">{escape(user['cd'])} {escape(user['name'])}</td>
            {"".join(cells)}
            {row_total}
        </tr>''')

    # 合計行
    rows.append(_render_total_row(projects, project_totals, grand_totals, mode))

    tbody = "".join(rows)
    return f'''{nav}
    <table class="assign-table">
        <thead>{header}</thead>
        <tbody>{tbody}</tbody>
    </table>'''


@router.get("", response_class=HTMLResponse)
def page(
    request: Request,
    month: str = None,
    mode: str = "simple",
    user: list[int] = Query(default=[]),
    project: list[int] = Query(default=[]),
    issue: list[int] = Query(default=[])
):
    """月次アサインページ"""
    if month:
        year_month = parse_month(month)
    else:
        year_month = get_current_month()

    # modeの検証
    if mode not in ("simple", "detail"):
        mode = "simple"

    filter_params = {"user": user, "project": project, "issue": issue}
    return templates.TemplateResponse(request, "monthly_assignments.html", {
        "active": "monthly_assignments",
        "year_month": year_month,
        "mode": mode,
        "filter_params": filter_params,
    })


@router.get("/grid", response_class=HTMLResponse)
def get_grid(month: str = None, mode: str = "simple"):
    """グリッド取得"""
    if month:
        year_month = parse_month(month)
    else:
        year_month = get_current_month()

    # modeの検証
    if mode not in ("simple", "detail"):
        mode = "simple"

    users = UserService.get_active_list()
    projects = ProjectService.get_list()
    assignments = MonthlyAssignmentService.get_assignments_for_month(year_month)
    actuals = MonthlyAssignmentService.get_actuals_for_month(year_month) if mode == "detail" else {}

    return HTMLResponse(render_grid(year_month, users, projects, assignments, actuals, mode))


@router.post("", response_class=HTMLResponse)
def upsert_assignment(
    user_id: int = Form(...),
    project_id: int = Form(...),
    year_month: str = Form(...),
    planned_hours: float = Form(...)
):
    """アサイン追加/更新"""
    year_month = parse_month(year_month)

    # ユーザーの存在確認と有効確認
    user = MonthlyAssignmentService.get_user_with_status(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # プロジェクトの存在確認
    project = MonthlyAssignmentService.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 新規作成時の無効ユーザーチェック
    existing = MonthlyAssignmentService.get_assignment(user_id, project_id, year_month)
    if not existing and planned_hours > 0 and user['is_active'] == 0:
        raise HTTPException(status_code=400, detail="無効なユーザーにはアサインできません")

    try:
        MonthlyAssignmentService.upsert(user_id, project_id, year_month, planned_hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return HTMLResponse("")


@router.delete("/{id}", response_class=HTMLResponse)
def delete_assignment(id: int):
    """アサイン削除"""
    existing = MonthlyAssignmentService.get_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Assignment not found")

    MonthlyAssignmentService.delete(id)
    return HTMLResponse("")
