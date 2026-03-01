"""月次アサイングリッドのHTML生成

責務: 月次アサイン画面のグリッド部品（ナビゲーション・ヘッダー・行・集計行）を生成
renders.py と同パターンのプレゼンテーション専用モジュール
"""
from datetime import datetime
from html import escape

from services import MonthlyAssignmentService
from .core import get_rate_class
from .dates import get_prev_next_month


def _render_navigation(year_month: str, mode: str) -> str:
    """ナビゲーションとモード切替ボタン"""
    prev_month, next_month = get_prev_next_month(year_month)
    dt = datetime.strptime(year_month, "%Y-%m")
    month_display = f"{dt.year}年{dt.month}月"

    simple_active = "btn-primary" if mode == "simple" else "btn-ghost"
    detail_active = "btn-primary" if mode == "detail" else "btn-ghost"
    mode_toggle = f'''<div class="mode-toggle">
        <a href="/monthly-assignments?month={year_month}&mode=simple" class="btn {simple_active}">簡易</a>
        <a href="/monthly-assignments?month={year_month}&mode=detail" class="btn {detail_active}">詳細</a>
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
        remaining_class = ' class="text-danger"' if remaining < 0 else ""
        rate_class = get_rate_class(rate)
    else:
        remaining_display = "-"
        rate_display = "-"
        remaining_class = ""
        rate_class = ""

    return f'''<div class="detail-label">予定</div>
        <div class="detail-value">{planned_display}</div>
        <div class="detail-label-mt">実績</div>
        <div class="detail-value">{actual_display}</div>
        <div class="detail-label-mt">残</div>
        <div{remaining_class}>{remaining_display}</div>
        <div class="detail-label-mt">消化率</div>
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
            total_cells.append(f'''<td class="col-total detail-cell-plain">
                <div class="detail-summary">予定: {planned_display}</div>
                <div class="detail-summary">実績: {actual_display}</div>
            </td>''')
        else:
            hours_display = f"{pt['planned']:.1f}h" if pt['planned'] > 0 else "-"
            total_cells.append(f'<td class="col-total">{hours_display}</td>')

    if mode == "detail":
        grand_planned = f"{grand_totals['planned']:.1f}h" if grand_totals['planned'] > 0 else "-"
        grand_actual = f"{grand_totals['actual']:.1f}h" if grand_totals['actual'] > 0 else "-"
        grand_cell = f'''<td class="grand-total detail-cell-plain">
            <div class="detail-summary">予定: {grand_planned}</div>
            <div class="detail-summary">実績: {grand_actual}</div>
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
    """グリッドHTML生成

    責務: HTML生成のみ（集計計算はサービス層に委譲）
    """
    if not users:
        return '<p class="empty-message">有効なユーザーがいません</p>'
    if not projects:
        return '<p class="empty-message">プロジェクトがありません</p>'

    if actuals is None:
        actuals = {}

    nav = _render_navigation(year_month, mode)
    header = _render_header(projects)

    # 集計をサービス層から取得
    user_totals, project_totals, grand_totals = MonthlyAssignmentService.calculate_grid_totals(
        users, projects, assignments, actuals
    )

    # ユーザー行生成
    rows = []
    for user in users:
        cells = []
        uid = user['id']

        for project in projects:
            pid = project['id']
            assignment = assignments.get((uid, pid))
            planned = assignment['hours'] if assignment else 0
            actual = actuals.get((uid, pid), 0)

            if mode == "detail":
                cells.append(f'<td class="assign-cell detail-cell">{_render_detail_stats(planned, actual)}</td>')
            else:
                cells.append(_render_simple_cell(uid, pid, planned, year_month))

        ut = user_totals[uid]
        if mode == "detail":
            row_total = f'<td class="row-total detail-cell-plain">{_render_detail_stats(ut["planned"], ut["actual"])}</td>'
        else:
            mm_total = f"{ut['planned'] / 160:.2f}MM" if ut['planned'] > 0 else ""
            hours_total = f"{ut['planned']:.1f}h" if ut['planned'] > 0 else "-"
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
