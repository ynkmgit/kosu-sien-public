"""実績入力グリッドレンダラー

責務: 実績入力グリッドのHTML生成のみ
"""
from datetime import date
from html import escape

from services import WorkLogService
from .renders import render_log_cell, render_progress_cell, render_row_label, render_tag_badges, render_user_cell, render_task_status_cell, render_issue_status_cell
from .dates import WEEKDAY_NAMES


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
    date_headers = "".join(
        f'<div class="gc date-header weekday-header{_get_date_cell_class(i, d, today, is_week).replace("-cell", "-header")}">'
        f'{WEEKDAY_NAMES[i]}<br>{d.month}/{d.day}</div>'
        if is_week else
        f'<div class="gc date-header">{d.day}</div>'
        for i, d in enumerate(dates)
    )

    total_label = "週計" if is_week else "合計"
    return f'''<div class="grid-row grid-header">
        <div class="gc gc-frozen row-header">作業</div>
        <div class="gc user-header">担当</div>
        <div class="gc status-header">状態</div>
        <div class="gc progress-header">完了%</div>
        {date_headers}
        <div class="gc total-header">{total_label}</div>
    </div>'''


def _render_project_row(row: dict, dates: list[date], project_totals: dict, is_week: bool, today: date) -> str:
    """プロジェクト集計行を生成"""
    pid = row['project_id']

    cells = "".join(
        f'<div class="gc summary-cell numeric{_get_date_cell_class(i, d, today, is_week)}">'
        f'{f"{val:.2f}" if val > 0 else "-"}</div>'
        for i, d in enumerate(dates)
        for val in [project_totals[pid][d.isoformat()]]
    )

    total = project_totals[pid]["total"]
    total_display = f"{total:.2f}h" if total > 0 else "-"

    return (
        f'<div class="grid-row project-row" data-project-id="{pid}">'
        f'<div class="gc gc-frozen project-name">'
        f'<span class="toggle-icon" onclick="toggleProject({pid})">▼</span> {escape(row["project_name"])}'
        f'</div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'<div class="gc"></div>'
        f'{cells}'
        f'<div class="gc row-total numeric project-total">{total_display}</div>'
        f'</div>'
    )


def _render_issue_row(row: dict, dates: list[date], issue_totals: dict, is_week: bool, today: date, status_labels: dict = None) -> str:
    """案件集計行を生成"""
    pid = row['project_id']
    iid = row['issue_id']
    key = (pid, iid)

    cells = "".join(
        f'<div class="gc summary-cell numeric{_get_date_cell_class(i, d, today, is_week)}">'
        f'{f"{val:.2f}" if val > 0 else "-"}</div>'
        for i, d in enumerate(dates)
        for val in [issue_totals[key][d.isoformat()]]
    )

    total = issue_totals[key]["total"]
    total_display = f"{total:.2f}h" if total > 0 else "-"

    issue_status_cell = render_issue_status_cell(iid, row.get('issue_status', 'open'), status_labels or {})

    return (
        f'<div class="grid-row issue-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<div class="gc gc-frozen issue-name">'
        f'<span class="toggle-icon" onclick="toggleIssue({pid}, {iid})">▼</span> {escape(row["issue_cd"])} {escape(row["issue_name"])}'
        f'</div>'
        f'<div class="gc"></div>'
        f'{issue_status_cell}'
        f'<div class="gc"></div>'
        f'{cells}'
        f'<div class="gc row-total numeric issue-total">{total_display}</div>'
        f'</div>'
    )


def _render_log_row(row: dict, dates: list[date], work_logs: dict, is_week: bool, today: date, task_tags: list[dict] = None, task_status_labels: dict = None) -> tuple[str, float, dict]:
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
    tag_html = render_tag_badges(task_tags or [])
    status_cell = render_task_status_cell(row['task_id'], row.get('task_status', 'open'), task_status_labels or {})

    html = (
        f'<div class="grid-row log-row" data-project-id="{pid}" data-issue-id="{iid}">'
        f'<div class="gc gc-frozen row-label">{render_row_label(row["task_name"])}{tag_html}</div>'
        f'{render_user_cell(row["user_name"])}'
        f'{status_cell}'
        f'{render_progress_cell(row["assignee_id"], row["progress_rate"])}'
        f'{"".join(cells)}'
        f'<div class="gc row-total numeric">{row_total_display}</div>'
        f'</div>'
    )
    return html, row_total, date_hours


def _render_total_row(dates: list[date], date_totals: dict, grand_total: float, is_week: bool, today: date) -> str:
    """列合計行を生成"""
    cells = "".join(
        f'<div class="gc col-total numeric{_get_date_cell_class(i, d, today, is_week)}">'
        f'{f"{val:.2f}" if val > 0 else "-"}</div>'
        for i, d in enumerate(dates)
        for val in [date_totals[d.isoformat()]]
    )

    return f'''<div class="grid-row total-row">
        <div class="gc gc-frozen total-label">日計</div>
        <div class="gc"></div>
        <div class="gc"></div>
        <div class="gc"></div>
        {cells}
        <div class="gc grand-total numeric">{grand_total:.2f}h</div>
    </div>'''


def render_grid(dates: list[date], rows, work_logs, view: str = "week", tags_map: dict = None,
                status_labels_map: dict = None, task_status_labels_map: dict = None):
    """グリッドHTML生成（週/月共通）

    責務: レンダリングのみ（集計・個別行生成は別関数に委譲）
    """
    if tags_map is None:
        tags_map = {}
    if status_labels_map is None:
        status_labels_map = {}
    if task_status_labels_map is None:
        task_status_labels_map = {}
    if not rows:
        return '<p class="empty-message">表示する行がありません。担当割当を行ってください。</p>'

    is_week = view == "week"
    today = date.today()

    # 集計を取得（サービス層に委譲）
    project_totals, issue_totals = WorkLogService.calculate_grid_totals(rows, dates, work_logs)

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
            html_rows.append(_render_issue_row(row, dates, issue_totals, is_week, today, status_labels_map.get(pid, {})))

        # 作業行
        task_tags = tags_map.get(row['task_id'], [])
        log_html, row_total, date_hours = _render_log_row(row, dates, work_logs, is_week, today, task_tags, task_status_labels_map.get(iid, {}))
        html_rows.append(log_html)
        grand_total += row_total
        for date_str, hours in date_hours.items():
            date_totals[date_str] += hours

    # 列合計行（ヘッダー直後に配置）
    total_row = _render_total_row(dates, date_totals, grand_total, is_week, today)
    html_rows.insert(0, total_row)

    num_dates = len(dates)
    col_width = "70px" if is_week else "55px"
    grid_cols = f"minmax(180px, 1fr) 120px 80px 70px repeat({num_dates}, {col_width}) 65px"
    week_class = " week-table" if is_week else ""
    return f'{bulk_actions}<div class="grid{week_class}" style="--grid-cols: {grid_cols}">{header}{"".join(html_rows)}</div>'
